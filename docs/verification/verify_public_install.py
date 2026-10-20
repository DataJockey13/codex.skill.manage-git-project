#!/usr/bin/env python3
"""Acceptance check of the public v1.0.0 distribution, without user credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile


REPOSITORY = "DataJockey13/codex.skill.manage-git-project"
VERSION = "v1.0.0"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    return {str(path.relative_to(directory)): digest(path)
            for path in sorted(directory.rglob("*")) if path.is_file()}


def verify(work, evidence, installer):
    work.mkdir(parents=True, exist_ok=False)
    evidence.mkdir(parents=True, exist_ok=True)
    for name in ["home", "tmp", "cache", "downloads"]:
        (work / name).mkdir()
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "en_US.UTF-8",
        "HOME": str(work / "home"), "CODEX_HOME": str(work / "codex-home"),
        "TMPDIR": str(work / "tmp"), "XDG_CACHE_HOME": str(work / "cache"),
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/usr/bin/false",
        "GIT_SSH_COMMAND": "ssh -F /dev/null -o BatchMode=yes -o IdentityAgent=none -o IdentitiesOnly=yes",
    }
    commands = []

    def run(label, arguments, expected=0, env=None, timeout=60):
        result = subprocess.run([str(arg) for arg in arguments], cwd=work,
                                env=env or environment, capture_output=True,
                                text=True, timeout=timeout)
        prefix = f"{len(commands) + 1:02d}-{label}"
        stdout = evidence / (prefix + ".stdout.log")
        stderr = evidence / (prefix + ".stderr.log")
        stdout.write_text(result.stdout)
        stderr.write_text(result.stderr)
        commands.append({"step": label, "arguments": [str(arg) for arg in arguments],
                         "exit_code": result.returncode, "expected": expected,
                         "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr)})
        (evidence / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if result.returncode != expected:
            raise RuntimeError(f"{label}: exit {result.returncode}, expected {expected}; {result.stderr[:1200]}")
        return result.stdout

    def public(url):
        request = urllib.request.Request(url, headers={"User-Agent": "manage-git-project-public-install-check"})
        # No Authorization header, token, cookies, user Git config or proxy credentials.
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=30) as response:
            return response.read()

    print("Checking anonymous public provenance and creating an empty Python environment", flush=True)
    release = json.loads(public(f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{VERSION}"))
    assert release["tag_name"] == VERSION and not release["draft"] and not release["prerelease"]
    source_report = json.loads(public(f"https://raw.githubusercontent.com/{REPOSITORY}/{VERSION}/docs/verification/2026-10-19-v1.0.0.json"))
    expected_sources = source_report["source_sha256"]
    refs = run("anonymous-tag", ["git", "ls-remote", f"https://github.com/{REPOSITORY}.git",
                                 f"refs/tags/{VERSION}", f"refs/tags/{VERSION}^{{}}"])
    tag_commit = next(line.split()[0] for line in refs.splitlines() if line.endswith("^{}"))
    run("create-venv", [sys.executable, "-B", "-m", "venv", "--without-pip", work / "python"])
    python = work / "python/bin/python3"
    runtime = json.loads(run("runtime", [python, "-B", "-I", "-c",
        "import importlib.metadata,json,platform,sys; print(json.dumps({'python':sys.version,'platform':sys.platform,'machine':platform.machine(),'prefix':sys.prefix,'packages':[d.metadata['Name'] for d in importlib.metadata.distributions()]}))"]))
    assert runtime["packages"] == []
    assert Path(runtime["prefix"]) == work / "python"

    print("Installing the tagged skill anonymously using both download and Git", flush=True)
    for method in ["download", "git"]:
        method_environment = dict(environment, CODEX_HOME=str(work / (method + "-codex-home")))
        run("install-" + method, [python, "-B", "-s", installer, "--repo", REPOSITORY,
                                  "--path", "manage-git-project", "--ref", VERSION,
                                  "--method", method], env=method_environment)
        installed = Path(method_environment["CODEX_HOME"]) / "skills/manage-git-project"
        assert not any(path.is_symlink() for path in installed.rglob("*"))
        assert inventory(installed) == expected_sources
    installed = work / "download-codex-home/skills/manage-git-project"
    environment["CODEX_HOME"] = str(work / "download-codex-home")
    assert not list((work / "tmp/codex").iterdir()), "Installer left temporary downloads/checkouts"

    print("Verifying the independently downloaded release package and checksum", flush=True)
    asset_paths = {}
    for asset in release["assets"]:
        if asset["name"] in {"manage-git-project-v1.0.0.zip", "manage-git-project-v1.0.0.zip.sha256"}:
            path = work / "downloads" / asset["name"]
            path.write_bytes(public(asset["browser_download_url"]))
            assert asset["digest"] == "sha256:" + digest(path)
            asset_paths[asset["name"]] = path
    archive = asset_paths["manage-git-project-v1.0.0.zip"]
    assert digest(archive) == asset_paths[archive.name + ".sha256"].read_text().split()[0]
    with zipfile.ZipFile(archive) as package:
        archive_sources = {name.removeprefix("manage-git-project/"): hashlib.sha256(package.read(name)).hexdigest()
                           for name in package.namelist() if not name.endswith("/")}
    assert archive_sources == expected_sources

    print("Running a complete task with the installed CLI and a local bare remote", flush=True)
    project = work / "project with spaces"
    project.mkdir()

    def git(*arguments, label="git", repo=project):
        return run(label, ["git", "-C", repo, *arguments]).strip()

    git("init", "-b", "develop", label="init-project")
    git("config", "user.name", "Public Installation Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    (project / ".gitignore").write_text(".local/\n")
    (project / "notes.txt").write_text("committed baseline\n")
    git("add", ".gitignore", "notes.txt")
    git("commit", "-m", "fixture baseline")
    remote = project / ".local/origin.git"
    git("init", "--bare", "--initial-branch=develop", str(remote), label="init-local-remote")
    git("remote", "add", "origin", str(remote))
    git("push", "-u", "origin", "develop")
    foreign = "synthetic foreign draft; preserve unchanged\n"
    (project / "notes.txt").write_text(foreign)
    cli = [python, "-B", "-I", installed / "scripts/project.py", "--project-root", project]

    def skill(label, *arguments, expected=0, task="installation-smoke"):
        return json.loads(run(label, [*cli, "--task", task, *arguments], expected=expected))

    skill("inspect-before", "inspect", "--target", "develop")
    skill("begin", "begin", "--target", "develop", "--remote", "origin", "--require-push")
    skill("lock-conflict", "begin", "--target", "develop", task="conflicting-author", expected=2)
    branch = "codex/public-install-smoke"
    tree = project / ".local/worktrees/feature"
    git("worktree", "add", "-b", branch, str(tree), "develop", label="add-worktree")
    skill("track-branch", "track-branch", "--branch", branch)
    (tree / "greet.py").write_text("import sys\nprint('Hello, ' + sys.argv[1] + '!')\n")
    assert run("verify-change", [python, "-B", "-I", tree / "greet.py", "Codex"]) == "Hello, Codex!\n"
    git("add", "greet.py", repo=tree)
    git("commit", "-m", "add verified greeting", repo=tree)
    branch_tip = git("rev-parse", branch)
    git("push", "origin", branch)
    skill("retain-result", "artifact", "--path", "greet.py", "--disposition", "retain")
    transient = project / ".local/transient.txt"
    transient.write_text("known disposable fixture output\n")
    skill("temporary-result", "artifact", "--path", ".local/transient.txt", "--disposition", "temporary")
    skill("early-finish-blocked", "finish", expected=2)
    skill("unmerged-removal-blocked", "remove-worktree", "--path", str(tree),
          "--idle-evidence", "Only synchronous fixture subprocesses; no other author", expected=2)
    git("merge", "--no-ff", branch, "-m", "integrate verified greeting", label="integrate")
    unpublished = skill("unpublished-target-blocked", "check", expected=1)
    assert any("not proven published" in error for error in unpublished["errors"])
    git("push", "origin", "develop")
    private = tree / ".local/private-note.txt"
    private.parent.mkdir()
    private.write_text("unique synthetic ignored content\n")
    skill("ignored-removal-blocked", "remove-worktree", "--path", str(tree),
          "--idle-evidence", "Only this isolated fixture owns the worktree", expected=2)
    skill("migrate-ignored-content", "artifact", "--path", str(private), "--disposition", "migrate",
          "--destination", ".local/preserved/private-note.txt")
    preserved = project / ".local/preserved/private-note.txt"
    preserved.parent.mkdir()
    shutil.move(str(private), preserved)
    skill("remove-worktree", "remove-worktree", "--path", str(tree),
          "--idle-evidence", "Fixture subprocesses have exited; no other agent uses this isolated worktree")
    assert not tree.exists()
    skill("remote-branch-blocked", "remove-branch", "--branch", branch, expected=2)
    git("push", "origin", "--delete", branch, label="delete-local-remote-branch")
    skill("remove-branch", "remove-branch", "--branch", branch)
    skill("temporary-artifact-blocked", "check", expected=1)
    transient.unlink()
    check = skill("final-check", "check")
    closure = skill("finish", "finish")
    assert check["passed"] and closure["passed"] and closure["outcome"] == "complete"
    assert not list((project / ".local/manage-git-project/locks").iterdir())
    assert (project / "notes.txt").read_text() == foreign
    assert preserved.read_text() == "unique synthetic ignored content\n"
    assert run("verify-integrated-change", [python, "-B", "-I", project / "greet.py", "Codex"]) == "Hello, Codex!\n"
    assert git("branch", "--format=%(refname:short)") == "develop"
    assert len(json.loads(run("inspect-after", [*cli, "inspect"]))["worktrees"]) == 1
    assert git("ls-remote", "--heads", "origin") == git("rev-parse", "develop") + "\trefs/heads/develop"
    final_status = git("status", "--porcelain=v1")
    assert final_status == "M notes.txt"
    (evidence / "fixture-closure.json").write_text(json.dumps(closure, indent=2) + "\n")

    print("Running all behavior tests from the isolated installed copy", flush=True)
    run("installed-behavior-tests", [python, "-B", "-I", installed / "tests/test_project.py",
        "--scratch-root", work / "behavior-repositories", "--report", evidence / "behavior-tests.json"], timeout=60)
    tests = json.loads((evidence / "behavior-tests.json").read_text())
    assert tests["tests"] == 46 and tests["failures"] == tests["errors"] == tests["skipped"] == 0
    assert not tests["remaining_test_fixtures"]
    assert inventory(installed) == expected_sources
    result = {
        "release": VERSION, "repository": f"https://github.com/{REPOSITORY}",
        "tag_commit": tag_commit, "anonymous_network_access": True,
        "installation_methods": ["download", "git"], "installed_source_sha256": expected_sources,
        "release_archive_sha256": digest(archive), "release_archive_matches_installation": True,
        "installer_sha256": digest(installer), "runtime": runtime,
        "workflow": {"target": "develop", "remote": "local bare repository", "passed": True,
                     "integration_commit": git("rev-parse", "develop"), "task_branch_tip": branch_tip,
                     "own_branches_remaining": [], "additional_worktrees_remaining": [],
                     "task_locks_remaining": [], "foreign_draft_preserved": True,
                     "ignored_content_migrated": True, "closure_passed": closure["passed"]},
        "behavior_tests": tests, "subprocess_checks": len(commands),
        "harness_sha256": digest(Path(__file__)),
        "limits": ["Isolated environment variables, Python venv and test directories on macOS; no OS sandbox, container or VM.",
                   "No live Codex session or automatic skill selection was exercised.",
                   "No native Windows or Linux execution."],
    }
    # Every file here was created by this run in a previously absent directory.
    # Successful closure and preserved synthetic contents are checked above.
    shutil.rmtree(work)
    result["isolated_environment_removed"] = not work.exists()
    (evidence / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Public installation, complete workflow, all 46 tests and cleanup passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--installer", type=Path,
                        default=Path.home() / ".codex/skills/.system/skill-installer/scripts/install-skill-from-github.py")
    arguments = parser.parse_args()
    verify(arguments.work_root.resolve(), arguments.evidence_root.resolve(), arguments.installer.resolve())
