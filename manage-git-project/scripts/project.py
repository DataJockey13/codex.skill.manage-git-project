#!/usr/bin/env python3
"""Task-scoped Git inventory, artifact receipts and guarded local cleanup.

Python >=3.9, Git with `worktree list --porcelain -z`. No shell, remote writes,
implicit merges, force deletion, reset, stash, repository-wide clean, or home scan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


class Refused(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def git(repo, *args, allow_failure=False, input=None):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            env=env, text=True, errors="surrogateescape", input=input)
    if result.returncode and not allow_failure:
        # Do not copy credential-bearing remote URLs from Git diagnostics.
        raise Refused(f"Git {args[0]} failed (exit {result.returncode}); inspect Git locally")
    return result


def value(repo, *args):
    return git(repo, *args).stdout.strip()


def oid(repo, ref):
    result = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", allow_failure=True)
    return result.stdout.strip() if result.returncode == 0 else None


def ancestor(repo, old, new):
    return git(repo, "merge-base", "--is-ancestor", old, new,
               allow_failure=True).returncode == 0


def absolute(project, raw):
    p = Path(raw).expanduser()
    return Path(os.path.abspath(p if p.is_absolute() else project / p))


def contained(project, path):
    return path.resolve().is_relative_to(project.resolve())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(path):
    """Do not follow links; include ignored files when a directory is explicit."""
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "missing"}
    if path.is_file():
        return {"kind": "file", "bytes": path.stat().st_size, "sha256": sha(path)}
    require(path.is_dir(), f"Special file requires manual handling: {path}")
    entries = []
    def unreadable(error):
        raise error
    for folder, dirs, files in os.walk(path, followlinks=False, onerror=unreadable):
        for name in list(dirs):
            p = Path(folder) / name
            if p.is_symlink():
                entries.append([str(p.relative_to(path)), fingerprint(p)])
                dirs.remove(name)
        for name in files:
            p = Path(folder) / name
            entries.append([str(p.relative_to(path)), fingerprint(p)])
    data = json.dumps(sorted(entries), sort_keys=True, ensure_ascii=True).encode()
    return {"kind": "directory", "entries": len(entries),
            "sha256": hashlib.sha256(data).hexdigest()}


def status(repo):
    records = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout.split("\0")
    result = {}
    i = 0
    while i < len(records):
        entry = records[i]
        i += 1
        if not entry:
            continue
        code, name = entry[:2], entry[3:]
        result[name] = {"status": code, "content": fingerprint(repo / name)}
        if "R" in code or "C" in code:
            previous = records[i]
            i += 1
            result[previous] = {"status": "rename-source", "content": fingerprint(repo / previous)}
    return result


def worktrees(repo):
    result, item = [], {}
    for record in git(repo, "worktree", "list", "--porcelain", "-z").stdout.split("\0"):
        if not record:
            if item:
                result.append(item)
                item = {}
        else:
            key, _, val = record.partition(" ")
            item[key] = val or True
    if item:
        result.append(item)
    return result


def heads(repo):
    return dict(line.split("\t", 1) for line in value(
        repo, "for-each-ref", "--format=%(refname:strip=2)\t%(objectname)", "refs/heads").splitlines())


def remote_heads(repo, remote):
    require(remote in value(repo, "remote").splitlines(), "Unknown configured remote")
    return {ref: commit for commit, ref in (line.split("\t", 1) for line in
            git(repo, "ls-remote", "--heads", remote).stdout.splitlines())}


def inspect(project, repo, target=None):
    top = Path(value(repo, "rev-parse", "--show-toplevel")).resolve()
    current = git(top, "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True)
    upstream = git(top, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", allow_failure=True)
    ahead = behind = None
    if upstream.returncode == 0:
        ahead, behind = map(int, value(top, "rev-list", "--left-right", "--count", "HEAD...@{upstream}").split())
    return {"project": str(project), "repo": str(top), "head": oid(top, "HEAD"),
            "branch": current.stdout.strip() or None, "target": target,
            "upstream": upstream.stdout.strip() if upstream.returncode == 0 else None,
            "ahead": ahead, "behind": behind, "status": status(top), "branches": heads(top),
            "worktrees": worktrees(top), "checkout_inside_project": contained(project, top)}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".state-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, path)


def locations(args):
    project = Path(args.project_root).expanduser().resolve()
    require(project.is_dir(), "Project root does not exist")
    repo = absolute(project, args.repo or ".").resolve()
    state = absolute(project, args.state_dir)
    require(contained(project, state), "State directory escapes the canonical project")
    require(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}", args.task or "inspect"), "Invalid task ID")
    return project, repo, state


def lock_path(state, repo):
    key = hashlib.sha256(os.path.normcase(str(repo.resolve())).encode()).hexdigest()[:24]
    return state / "locks" / key


def load_task(args):
    project, repo, base = locations(args)
    path = base / "tasks" / f"{args.task}.json"
    require(path.is_file(), "Task has not been started")
    data = json.loads(path.read_text())
    require(data["project"] == str(project) and data["repo"] == str(repo), "Task belongs to another checkout")
    require(data["state"] == "active", "Task is already closed; use a new task ID")
    lock = lock_path(base, repo)
    require((lock / "owner.json").is_file(), "Task lock is missing")
    owner = json.loads((lock / "owner.json").read_text())
    require(owner["token"] == data["token"], "Another task owns this checkout")
    return project, repo, path, data


def begin(args):
    project, repo, base = locations(args)
    snapshot = inspect(project, repo, args.target)
    require(snapshot["repo"] == str(repo), "Pass the actual Git checkout root as --repo")
    require(snapshot["checkout_inside_project"], "Checkout must be inside the canonical project")
    require(oid(repo, args.target), "Integration target must name an existing local commit")
    require(args.target in snapshot["branches"], "Integration target must be a local branch")
    enclosing = git(project, "rev-parse", "--show-toplevel", allow_failure=True)
    state_repo = Path(enclosing.stdout.strip()).resolve() if enclosing.returncode == 0 else repo
    if base.is_relative_to(state_repo):
        relative = str(base.relative_to(state_repo))
        require(git(state_repo, "check-ignore", "--quiet", "--", relative + "/probe",
                    allow_failure=True).returncode == 0,
                "Task state would enter Git; configure a narrow ignore for its project-local directory first")
    require(not args.require_push or args.remote, "--require-push needs an explicitly selected remote")
    path = base / "tasks" / f"{args.task}.json"
    require(not path.exists(), "Task ID already exists; inspect it instead of overwriting its history")
    adopted = [str(absolute(repo, p).relative_to(repo)) for p in args.adopt_path]
    require(not adopted or args.adopt_reason.strip(), "Adopting existing own work requires its authorization/reason")
    lock = lock_path(base, repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock.mkdir()
    except FileExistsError:
        raise Refused("Checkout is reserved by another task; do not steal or infer expiry from a dead CLI PID")
    token = uuid.uuid4().hex
    data = {"version": 1, "task": args.task, "token": token, "project": str(project),
            "repo": str(repo), "target": args.target, "remote": args.remote,
            "require_push": args.require_push, "started_at": now(), "state": "active",
            "baseline": snapshot, "adopted_paths": adopted, "adopt_reason": args.adopt_reason,
            "branches": {}, "artifacts": [], "resource_exceptions": {}, "receipts": []}
    try:
        write_json(lock / "owner.json", {"task": args.task, "token": token, "started_at": now()})
        write_json(path, data)
    except BaseException:
        shutil.rmtree(lock)
        raise
    return {"task_file": str(path), "lock": str(lock), "baseline": snapshot}


def track_branch(args):
    project, repo, path, data = load_task(args)
    require(args.branch != data["target"], "Never own/delete the integration target")
    commit = oid(repo, "refs/heads/" + args.branch)
    require(commit, "Branch does not exist locally")
    existed = args.branch in data["baseline"]["branches"]
    require(not existed or args.reason.strip(), "Existing branch requires explicit task ownership and reason")
    trees = [x["worktree"] for x in worktrees(repo) if x.get("branch") == "refs/heads/" + args.branch]
    require(all(contained(project, Path(p)) for p in trees), "Move external worktrees into the project before tracking")
    require(args.branch not in data["branches"], "Branch is already tracked")
    data["branches"][args.branch] = {"initial_oid": commit, "worktrees": trees,
                                      "ownership_reason": args.reason, "retained_reason": None}
    write_json(path, data)
    return data["branches"][args.branch]


def artifact(args):
    project, repo, path, data = load_task(args)
    source = absolute(project, args.path)
    disposition = args.disposition
    require(disposition in {"temporary", "migrate", "external-control"} or contained(project, source),
            "Retained project artifacts must be inside the canonical project, including symlink targets")
    require(disposition != "external-control" or args.reason.strip(), "External control file needs explicit authorization/reason")
    destination = absolute(project, args.destination) if args.destination else None
    require(disposition != "migrate" or (destination and contained(project, destination)),
            "Migration destination must be inside the project")
    original = fingerprint(source)
    require(disposition != "migrate" or original["kind"] != "missing", "Cannot receipt a missing migration source")
    data["artifacts"].append({"source": str(source), "disposition": disposition,
                              "destination": str(destination) if destination else None,
                              "original": original, "reason": args.reason})
    write_json(path, data)
    return data["artifacts"][-1]


def retain(args):
    project, repo, path, data = load_task(args)
    require(args.reason.strip(), "A concrete reason is required")
    if args.branch:
        require(args.branch in data["branches"], "Only task-owned branches can be retained")
        data["branches"][args.branch]["retained_reason"] = args.reason
    else:
        resource = absolute(project, args.path).resolve()
        baseline = {str(Path(x["worktree"]).resolve()) for x in data["baseline"]["worktrees"]}
        require(str(resource) in baseline, "Only pre-existing worktrees may be classified as external resources")
        data["resource_exceptions"][str(resource)] = args.reason
    write_json(path, data)
    return {"reason": args.reason}


def worktree_payload(repo):
    # Unlike `git status`, this also sees ignored files and nested ignored repos.
    return git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").stdout.split("\0")[:-1]


def patch(repo, base, tip):
    return git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-color", "--no-renames",
               "--binary", "--full-index", base, tip, "--").stdout


def eligible(repo, data, name, integration_commit=None, discard_reason=None):
    require(not (integration_commit and discard_reason), "Choose integration evidence or an explicit discard decision, not both")
    require(name in data["branches"], "Branch is not owned by this task")
    require(not data["branches"][name]["retained_reason"], "Branch is explicitly retained")
    commit = oid(repo, "refs/heads/" + name)
    require(commit, "Branch no longer exists")
    target = oid(repo, "refs/heads/" + data["target"])
    if discard_reason:
        require(discard_reason.strip(), "Discard requires the actual user's decision and its evidence")
        return commit, target, {"kind": "discard", "authorization": discard_reason}
    evidence = {"kind": "ancestor"}
    if not ancestor(repo, commit, target):
        integrated = oid(repo, integration_commit) if integration_commit else None
        require(integrated and ancestor(repo, integrated, target),
                "Branch is not an ancestor; supply the actual squash/cherry-pick integration commit for exact patch verification")
        parents = value(repo, "rev-list", "--parents", "-n", "1", integrated).split()
        require(len(parents) == 2, "Patch-equivalence receipt requires a single-parent integration commit")
        base = value(repo, "merge-base", commit, target)
        original = patch(repo, base, commit)
        require(original and original == patch(repo, parents[1], integrated),
                "Integration commit does not exactly preserve the task branch patch; retain for review")
        evidence = {"kind": "exact-patch", "source_base": base, "integration_commit": integrated,
                    "patch_sha256": hashlib.sha256(original.encode("utf-8", "surrogateescape")).hexdigest()}
    return commit, target, evidence


def remove_worktree(args):
    project, repo, path, data = load_task(args)
    candidate = absolute(project, args.path).resolve()
    require(candidate != project and candidate != repo and contained(project, candidate), "Protected/outside checkout")
    require(args.idle_evidence.strip(), "Verify active agents/processes and provide concrete idle evidence")
    candidate_lock = lock_path(path.parent.parent, candidate)
    require(not candidate_lock.exists(), "Worktree is reserved by an active cooperative task")
    records = [x for x in worktrees(repo) if Path(x["worktree"]).resolve() == candidate]
    require(len(records) == 1 and "branch" in records[0], "Worktree must be registered with a task branch")
    item = records[0]
    name = item["branch"].removeprefix("refs/heads/")
    require(name in data["branches"] and str(candidate) in data["branches"][name]["worktrees"], "Unowned worktree")
    commit, target, evidence = eligible(repo, data, name, args.integration_commit, args.discard_reason)
    require(not item.get("locked") and not item.get("prunable"), "Locked/stale worktree requires separate diagnosis")
    require(not status(candidate), "Tracked or untracked worktree changes remain")
    require(not worktree_payload(candidate), "Ignored files remain; preserve or explicitly remove their proven-disposable contents first")
    if shutil.which("lsof"):
        try:
            active = subprocess.run(["lsof", "-nP", "+D", str(candidate)], capture_output=True, timeout=15)
        except subprocess.TimeoutExpired:
            raise Refused("Process inspection timed out; worktree was preserved")
        require(active.returncode == 1 and not active.stdout and not active.stderr,
                "Open files/processes remain or process check failed")
    # Process inspection can take seconds. Revalidate ownership, refs and files
    # afterwards; Git's own removal check does not protect ignored files.
    require(not candidate_lock.exists(), "Worktree is reserved by an active cooperative task")
    current = [x for x in worktrees(repo) if Path(x["worktree"]).resolve() == candidate]
    require(current == records and oid(repo, "refs/heads/" + name) == commit
            and oid(repo, "refs/heads/" + data["target"]) == target,
            "Worktree or integration refs changed during activity inspection; inspect again")
    require(not status(candidate), "Tracked or untracked worktree changes appeared during activity inspection")
    require(not worktree_payload(candidate), "Ignored files appeared during activity inspection; preserve them first")
    git(repo, "worktree", "remove", "--", str(candidate))
    receipt = {"action": "remove-worktree", "path": str(candidate), "branch": name,
               "oid": commit, "target_oid": target, "integration_evidence": evidence,
               "idle_evidence": args.idle_evidence, "at": now()}
    data["receipts"].append(receipt)
    write_json(path, data)
    return receipt


def remove_branch(args):
    project, repo, path, data = load_task(args)
    commit, target, evidence = eligible(repo, data, args.branch, args.integration_commit, args.discard_reason)
    require(value(repo, "symbolic-ref", "--short", "HEAD") == data["target"], "Switch this checkout to its integration target first")
    require(not any(x.get("branch") == "refs/heads/" + args.branch for x in worktrees(repo)), "Branch is checked out in a worktree")
    if data["remote"]:
        live = remote_heads(repo, data["remote"])
        published_target = live.get("refs/heads/" + data["target"])
        published_evidence = evidence.get("integration_commit", commit)
        require(evidence["kind"] == "discard" or (published_target and ancestor(repo, published_evidence, published_target)),
                "Integrated branch tip is not proven present on the live remote target")
        require("refs/heads/" + args.branch not in live,
                "Published task branch remains; remove it only within the authorized remote workflow, then recheck")
    # Atomically verify both refs; another worktree may otherwise move the target.
    transaction = (f"start\nverify refs/heads/{data['target']} {target}\n"
                   f"delete refs/heads/{args.branch} {commit}\nprepare\ncommit\n")
    git(repo, "update-ref", "--stdin", input=transaction)
    receipt = {"action": "remove-branch", "branch": args.branch, "oid": commit,
               "target_oid": target, "integration_evidence": evidence,
               "remote_checked": data["remote"], "at": now()}
    data["receipts"].append(receipt)
    write_json(path, data)
    configured = git(repo, "config", "--local", "--get-regexp", "^branch\\." + re.escape(args.branch) + "\\.", allow_failure=True)
    require(configured.returncode in (0, 1), "Could not inspect branch configuration")
    if configured.returncode == 0:
        git(repo, "config", "--local", "--remove-section", "branch." + args.branch)
    return receipt


def adopted(name, data):
    return any(name == p or name.startswith(p.rstrip("/") + "/") for p in data["adopted_paths"])


def check(args):
    project, repo, path, data = load_task(args)
    snapshot = inspect(project, repo, data["target"])
    errors, retained = [], []
    if args.outcome == "complete" and not ancestor(repo, snapshot["head"], "refs/heads/" + data["target"]):
        errors.append("Current checkout contains work not integrated into the configured target")
    untracked_branches = set(snapshot["branches"]) - set(data["baseline"]["branches"]) - set(data["branches"])
    if untracked_branches:
        errors.append("New branches lack task ownership records: " + ", ".join(sorted(untracked_branches)))
    known_worktrees = {x["worktree"] for x in data["baseline"]["worktrees"]}
    known_worktrees.update(p for branch in data["branches"].values() for p in branch["worktrees"])
    if any(x["worktree"] not in known_worktrees for x in snapshot["worktrees"]):
        errors.append("New worktrees lack task ownership records")
    for name, original in data["baseline"]["status"].items():
        if not adopted(name, data) and snapshot["status"].get(name) != original:
            errors.append(f"Pre-existing change was altered or committed: {name}")
    new_dirty = [name for name in snapshot["status"] if name not in data["baseline"]["status"] or adopted(name, data)]
    if new_dirty and args.outcome == "complete":
        errors.append("Task changes are still uncommitted: " + ", ".join(new_dirty))
    if args.outcome == "handoff" and not args.reason.strip():
        errors.append("An unfinished handoff needs a concrete reason")
    for item in data["artifacts"]:
        source = Path(item["source"])
        kind = item["disposition"]
        current = fingerprint(source)
        if kind == "temporary" and current["kind"] != "missing":
            errors.append(f"Temporary artifact remains: {source}")
        elif kind == "migrate":
            destination = Path(item["destination"])
            if not contained(project, destination) or current["kind"] != "missing" or fingerprint(destination) != item["original"]:
                errors.append(f"Migration is incomplete or content changed: {source}")
        elif kind in {"retain", "external-control"}:
            if not source.exists() or (kind == "retain" and not contained(project, source)):
                errors.append(f"Canonical artifact missing or escapes project: {source}")
    live = None
    if data["remote"]:
        try:
            live = remote_heads(repo, data["remote"])
        except Refused as exc:
            errors.append(str(exc))
    for name, item in data["branches"].items():
        reason = item["retained_reason"]
        if reason:
            retained.append({"branch": name, "reason": reason})
            if name not in snapshot["branches"]:
                errors.append(f"Retained task branch is missing: {name}")
            if args.outcome == "complete":
                errors.append(f"Task branch is retained; use documented handoff: {name}")
            continue
        for location in item["worktrees"]:
            candidate = Path(location)
            if candidate == repo:
                continue
            registered = any(Path(x["worktree"]) == candidate for x in snapshot["worktrees"])
            if registered or candidate.exists() or candidate.is_symlink():
                errors.append(f"Task worktree remains, including detached or unregistered files: {location}")
        if name in snapshot["branches"]:
            errors.append(f"Task branch remains: {name}")
        receipts = [x for x in data["receipts"] if x["action"] == "remove-branch" and x["branch"] == name]
        if not receipts:
            errors.append(f"No integration/deletion receipt for task branch: {name}")
        for receipt in receipts:
            proof = receipt["integration_evidence"]
            if proof["kind"] == "discard":
                if not proof.get("authorization", "").strip():
                    errors.append(f"Discard lacks user decision evidence: {name}")
                continue
            integrated_oid = proof.get("integration_commit", receipt["oid"])
            if not ancestor(repo, integrated_oid, "refs/heads/" + data["target"]):
                errors.append(f"Previously removed branch tip no longer reachable: {name}")
            if live is not None:
                published_target = live.get("refs/heads/" + data["target"])
                if not published_target or not ancestor(repo, integrated_oid, published_target):
                    errors.append(f"Previously removed branch integration is no longer on the live remote target: {name}")
        if live is not None and "refs/heads/" + name in live:
            errors.append(f"Remote task branch remains: {name}")
    for item in snapshot["worktrees"]:
        location = str(Path(item["worktree"]).resolve())
        if not contained(project, Path(location)) and location not in data["resource_exceptions"]:
            errors.append(f"External worktree needs consolidation or documented existing-resource classification: {location}")
    if data["require_push"]:
        target_oid = oid(repo, "refs/heads/" + data["target"])
        remote_oid = live.get("refs/heads/" + data["target"]) if live is not None else None
        if not remote_oid or not ancestor(repo, target_oid, remote_oid):
            errors.append("Current integration target is not proven published on the live remote")
    return {"task": data["task"], "outcome": args.outcome, "reason": args.reason,
            "passed": not errors, "errors": errors, "retained_branches": retained,
            "resource_exceptions": data["resource_exceptions"], "snapshot": snapshot,
            "receipts": data["receipts"], "checked_at": now()}


def finish(args):
    result = check(args)
    require(result["passed"], "Closure blocked: " + "; ".join(result["errors"]))
    project, repo, path, data = load_task(args)
    data["state"] = args.outcome
    data["final_check"] = result
    data["finished_at"] = now()
    write_json(path, data)
    shutil.rmtree(lock_path(path.parent.parent, repo))
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", required=True)
    p.add_argument("--repo", help="Checkout root relative to the canonical project (default: project root)")
    p.add_argument("--state-dir", default=".local/manage-git-project")
    p.add_argument("--task")
    commands = p.add_subparsers(dest="command", required=True)
    command = commands.add_parser("inspect")
    command.add_argument("--target")
    command = commands.add_parser("begin")
    command.add_argument("--target", required=True)
    command.add_argument("--remote", help="Configured remote name; only queried, never modified")
    command.add_argument("--require-push", action="store_true")
    command.add_argument("--adopt-path", action="append", default=[])
    command.add_argument("--adopt-reason", default="")
    command = commands.add_parser("track-branch")
    command.add_argument("--branch", required=True)
    command.add_argument("--reason", default="")
    command = commands.add_parser("artifact")
    command.add_argument("--path", required=True)
    command.add_argument("--disposition", choices=["retain", "temporary", "migrate", "external-control"], required=True)
    command.add_argument("--destination")
    command.add_argument("--reason", default="")
    command = commands.add_parser("retain")
    group = command.add_mutually_exclusive_group(required=True)
    group.add_argument("--branch")
    group.add_argument("--path")
    command.add_argument("--reason", required=True)
    command = commands.add_parser("remove-worktree")
    command.add_argument("--path", required=True)
    command.add_argument("--idle-evidence", required=True)
    command.add_argument("--integration-commit")
    command.add_argument("--discard-reason")
    command = commands.add_parser("remove-branch")
    command.add_argument("--branch", required=True)
    command.add_argument("--integration-commit")
    command.add_argument("--discard-reason")
    for name in ["check", "finish"]:
        command = commands.add_parser(name)
        command.add_argument("--outcome", choices=["complete", "handoff"], default="complete")
        command.add_argument("--reason", default="")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        require(args.command == "inspect" or args.task, "--task is required")
        if args.command == "inspect":
            project, repo, _ = locations(args)
            result = inspect(project, repo, args.target)
        else:
            functions = {"begin": begin, "track-branch": track_branch, "artifact": artifact,
                         "retain": retain, "remove-worktree": remove_worktree,
                         "remove-branch": remove_branch, "check": check, "finish": finish}
            result = functions[args.command](args)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result.get("passed", True) else 1
    except (Refused, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
