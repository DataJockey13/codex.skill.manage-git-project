"""Coordinated automatic workspaces and integration. Python standard library only."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def coordination(project):
    path = project / ".local/manage-git-project"
    if not path.resolve().is_relative_to(project.resolve()):
        raise OSError("Shared coordination escapes the canonical project")
    return path


def ensure_ignored(p, project, repo):
    result = p.git(project, "rev-parse", "--show-toplevel", allow_failure=True)
    if result.returncode == 0:
        enclosing = Path(result.stdout.strip()).resolve()
        relative = coordination(project).relative_to(enclosing)
        p.require(p.git(enclosing, "check-ignore", "--quiet", "--", str(relative / "probe"),
                        allow_failure=True).returncode == 0,
                  "Ignore .local/manage-git-project/ before using shared coordination")


@contextmanager
def lease(path, timeout, busy):
    """OS advisory lease; closing/crashing releases it without deleting its file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(b"\0")
                stream.flush()
            def acquire():
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            def acquire():
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deadline = time.monotonic() + timeout
        while True:
            try:
                acquire()
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise OSError(busy)
                time.sleep(0.05)
        yield


@contextmanager
def guard(project):
    with lease(coordination(project) / "operation.lock", 30,
               "Project coordination is busy; retry without stealing its lease"):
        yield


@contextmanager
def invocation(project, task):
    with lease(coordination(project) / "invocations" / (task + ".lock"), 0,
               "Another complete invocation is running for this task"):
        yield


def common_dir(p, repo):
    return str(p.absolute(repo, p.value(repo, "rev-parse", "--git-common-dir")).resolve())


def registry(p, project):
    path = coordination(project) / "registry.json"
    return json.loads(path.read_text()) if path.exists() else {}


def reserve_id(p, project, path, task):
    records = registry(p, project)
    p.require(task not in records and not path.exists()
              and not (coordination(project) / "tasks" / (task + ".json")).exists(),
              "Task ID already exists; use a new task ID")


def register(p, project, path, data):
    records = registry(p, project)
    records[data["task"]] = str(path)
    p.write_json(coordination(project) / "registry.json", records)


def peers(p, project, repo, task_path):
    paths = {Path(raw) for raw in registry(p, project).values()}
    paths.update((coordination(project) / "tasks").glob("*.json"))
    common = common_dir(p, repo)
    result = []
    for path in paths:
        if path == task_path or not path.is_file():
            continue
        data = json.loads(path.read_text())
        if data.get("project") != str(project) or data.get("state") not in {"active", "handoff"}:
            continue
        other_common = data.get("git_common_dir")
        if other_common is None and Path(data["repo"]).exists():
            other_common = common_dir(p, Path(data["repo"]))
        if common == other_common:
            result.append(data)
    return result


def resources(tasks):
    branches, trees = set(), set()
    for data in tasks:
        branches.update(data["branches"])
        trees.update(raw for item in data["branches"].values() for raw in item["worktrees"])
        trees.update(data.get("automatic", {}).get("infrastructure", []))
    return branches, trees


def start(p, args):
    project, repo, base = p.locations(args)
    ensure_ignored(p, project, repo)
    with guard(project):
        path = base / "tasks" / (args.task + ".json")
        reserve_id(p, project, path, args.task)
        initial = p.inspect(project, repo, args.target)
        p.require(initial["repo"] == str(repo) and initial["checkout_inside_project"], "Pass a project-local checkout root")
        p.require(args.target in initial["branches"], "Integration target must be an existing local branch")
        p.require(not args.require_push or args.remote, "--require-push needs an explicitly selected remote")
        p.require(not args.remote or args.remote in p.value(repo, "remote").splitlines(), "Unknown configured remote")
        p.require(not args.adopt_path or args.adopt_reason.strip(), "Adopting existing work requires a reason")
        enclosing = p.git(project, "rev-parse", "--show-toplevel", allow_failure=True)
        state_repo = Path(enclosing.stdout.strip()).resolve() if enclosing.returncode == 0 else repo
        if base.is_relative_to(state_repo):
            p.require(p.git(state_repo, "check-ignore", "--quiet", "--", str(base / "probe"),
                            allow_failure=True).returncode == 0, "Ignore the selected task state directory before start")
        reasons = []
        if p.lock_path(coordination(project), repo).exists():
            reasons.append("checkout reserved by another task")
        if initial["status"]:
            reasons.append("pre-existing file or index changes")
        if initial["branch"] != args.target:
            reasons.append("checkout is not on the integration target")
        if peers(p, project, repo, path):
            reasons.append("other project tasks are active")
        if args.collision_reason.strip():
            reasons.append(args.collision_reason.strip())
        workspace, branch = repo, None
        if reasons:
            workspace = project / ".local/worktrees" / args.task
            p.require(p.contained(project, workspace) and not workspace.exists() and not workspace.is_symlink(),
                      "Automatic workspace path is occupied or escapes the project")
            if enclosing.returncode == 0:
                p.require(p.git(Path(enclosing.stdout.strip()), "check-ignore", "--quiet", "--", str(workspace / "probe"),
                                allow_failure=True).returncode == 0, "Ignore the project-local worktree directory first")
            branch = "codex/" + args.task
            p.require(not p.oid(repo, "refs/heads/" + branch), "Automatic task branch already exists")
            p.require(not args.adopt_path, "Existing changes cannot be adopted into an isolated checkout")
            workspace.parent.mkdir(parents=True, exist_ok=True)
            p.git(repo, "worktree", "add", "-b", branch, str(workspace), args.target)
        nested = p.SimpleNamespace(**vars(args))
        nested.repo = str(workspace)
        result = p._begin(nested)
        data = json.loads(path.read_text())
        data["automatic"] = {"mode": "worktree" if branch else "direct", "origin_repo": str(repo),
                             "workspace": str(workspace), "branch": branch, "phase": "working",
                             "collision_reasons": reasons, "infrastructure": []}
        if branch:
            data["branches"][branch] = {"initial_oid": p.oid(repo, branch), "worktrees": [str(workspace)],
                                        "ownership_reason": "Automatically isolated task", "retained_reason": None}
        p.write_json(path, data)
        return {"task_file": result["task_file"], "working_directory": str(workspace),
                "branch": branch or initial["branch"], "mode": data["automatic"]["mode"],
                "collision_reasons": reasons, "task": args.task}


def validate(p, repo, command, timeout):
    before = p.oid(repo, "HEAD")
    p.require(not p.status(repo), "Commit only the task changes before automatic completion")
    result = subprocess.run(command, cwd=repo, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                            capture_output=True, timeout=timeout)
    receipt = {"command": command, "commit": before, "exit_code": result.returncode,
               "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(), "at": p.now()}
    p.require(p.oid(repo, "HEAD") == before and not p.status(repo), "Validation modified tracked or untracked project contents")
    return receipt


def idle(p, directory, evidence):
    p.require(evidence.strip(), "Supply the actual agent/process activity inspection")
    p.require(not p.status(directory) and not p.worktree_payload(directory),
              "Worktree has tracked, untracked or ignored data; preserve it before cleanup")
    if shutil.which("lsof"):
        result = subprocess.run(["lsof", "-nP", "+D", str(directory)], capture_output=True, timeout=15)
        p.require(result.returncode == 1 and not result.stdout and not result.stderr,
                  "Worktree is in use or process inspection was incomplete")
    p.require(not p.status(directory) and not p.worktree_payload(directory), "Worktree contents changed during process inspection")


def remove_stage(p, project, repo, path, data, evidence):
    auto = data["automatic"]
    raw = auto.get("staging")
    if not raw:
        return
    directory = Path(raw)
    p.require(p.contained(project, directory) and directory != repo, "Protected integration worktree")
    lock = p.lock_path(coordination(project), directory)
    p.require(not lock.exists(), "Integration worktree is reserved by another task")
    records = [item for item in p.worktrees(repo) if Path(item["worktree"]) == directory]
    intent = {"path": raw, "oid": auto["candidate"]}
    if not records and not directory.exists() and not directory.is_symlink():
        p.require(auto.get("stage_removal") == intent, "Missing integration worktree has no recorded removal intent")
        data["receipts"].append(dict(intent, action="remove-integration-worktree", recovered=True, at=p.now()))
        auto["infrastructure"].remove(raw)
        auto.pop("staging")
        auto.pop("stage_removal")
        p.write_json(path, data)
        return
    p.require(len(records) == 1 and not records[0].get("branch") and not records[0].get("locked"),
              "Integration worktree identity changed")
    p.require(p.oid(directory, "HEAD") == auto.get("candidate"), "Integration worktree contains unrecorded commits")
    idle(p, directory, evidence)
    p.require(not lock.exists(), "Integration worktree was reserved during process inspection")
    p.require([item for item in p.worktrees(repo) if Path(item["worktree"]) == directory] == records,
              "Integration worktree changed during process inspection")
    auto["stage_removal"] = intent
    p.write_json(path, data)
    p.git(repo, "worktree", "remove", "--", str(directory))
    data["receipts"].append({"action": "remove-integration-worktree", "path": raw, "oid": auto["candidate"], "at": p.now()})
    auto["infrastructure"].remove(raw)
    auto.pop("staging")
    auto.pop("stage_removal")
    p.write_json(path, data)


def complete(p, args):
    project, _, _ = p.locations(args)
    with invocation(project, args.task):
        return _complete(p, args)


def _complete(p, args):
    p.require(args.test_command, "Choose the project's validation command")
    p.require(args.idle_evidence.strip(), "Inspect active agents and processes before completion")
    p.require(0 <= args.wait <= 60, "Wait must be between 0 and 60 seconds")
    project, workspace, path, data = p.load_task(args)
    auto = data.get("automatic")
    p.require(auto, "Use start for the automatic workflow; legacy tasks still use check/finish")
    p.require(args.test_timeout > 0, "Validation timeout must be positive")
    if auto["branch"]:
        p.require(not data["branches"][auto["branch"]]["retained_reason"], "Task is retained for handoff; do not integrate it")
    command = list(args.test_command)
    if command[0] == "--":
        command.pop(0)
    p.require(command, "Validation command is empty")
    if auto["mode"] == "direct":
        receipt = validate(p, workspace, command, args.test_timeout)
        data["receipts"].append(dict(receipt, action="validation"))
        p.write_json(path, data)
        p.require(receipt["exit_code"] == 0, "Validation failed; task remains active")
        if args.push:
            p.require(data["remote"], "Select the remote when starting the task")
            p.require(p.value(workspace, "symbolic-ref", "--short", "HEAD") == data["target"], "Direct task left its integration branch")
            p.git(workspace, "push", data["remote"], "HEAD:refs/heads/" + data["target"])
        return p.finish(p.SimpleNamespace(**dict(vars(args), outcome="complete", reason="")))

    # Hold the real target checkout lock throughout validation, publication and
    # cleanup. Other workers can continue editing their own worktrees meanwhile.
    deadline = time.monotonic() + args.wait
    target_repo = None
    acquired = False
    while True:
        with guard(project):
            anchor = Path(data["git_common_dir"])
            targets = [item for item in p.worktrees(anchor) if item.get("branch") == "refs/heads/" + data["target"]]
            p.require(len(targets) == 1 and p.contained(project, Path(targets[0]["worktree"])),
                      "Integration target needs a project-local checkout; preserve the worker until it is available")
            target_repo = Path(targets[0]["worktree"])
            target_lock = p.lock_path(coordination(project), target_repo)
            owner = target_lock / "owner.json"
            if not target_lock.exists():
                target_lock.mkdir(parents=True)
                p.write_json(owner, {"task": data["task"], "token": data["token"], "started_at": p.now()})
                acquired = True
            elif owner.is_file() and json.loads(owner.read_text()).get("token") == data["token"]:
                acquired = True
        if acquired:
            break
        if time.monotonic() >= deadline:
            return {"passed": False, "pending": True, "task": data["task"],
                    "reason": "Integration checkout is reserved by another task; retry complete", "working_directory": str(workspace)}
        time.sleep(0.2)

    try:
        if auto["phase"] == "publishing" and Path(auto["workspace"]).exists():
            current_source = p.oid(Path(auto["workspace"]), "HEAD")
            if current_source != auto["source_oid"]:
                p.require(p.ancestor(target_repo, auto["source_oid"], current_source),
                          "Worker history was rewritten; preserve its previously validated work")
                auto["phase"] = "working"
                p.write_json(path, data)
        if auto["phase"] == "working":
            p.require(not p.status(target_repo), "Integration checkout has foreign changes; preserve them and retry later")
            p.require(p.value(target_repo, "symbolic-ref", "--short", "HEAD") == data["target"], "Integration checkout switched branches")
            source = p.oid(workspace, "HEAD")
            p.require(p.value(workspace, "symbolic-ref", "--short", "HEAD") == auto["branch"], "Worker switched branches")
            receipt = validate(p, workspace, command, args.test_timeout)
            data["receipts"].append(dict(receipt, action="source-validation"))
            p.write_json(path, data)
            p.require(receipt["exit_code"] == 0, "Source validation failed; branch and worktree remain active")
            target = p.oid(target_repo, "HEAD")
            if auto.get("staging"):
                p.require(p.ancestor(target_repo, auto["source_oid"], source), "Worker history was rewritten; preserve the previous integration candidate")
                with guard(project):
                    remove_stage(p, project, target_repo, path, data, args.idle_evidence)
            stage = project / ".local/worktrees" / ("integration-" + args.task + "-" + data["token"][:12])
            p.require(not stage.exists() and not stage.is_symlink(), "Integration workspace path is occupied")
            with guard(project):
                p.git(target_repo, "worktree", "add", "--detach", str(stage), target)
                auto.update(staging=str(stage), source_oid=source, target_base=target, candidate=target)
                auto["infrastructure"].append(str(stage))
                p.write_json(path, data)
            merged = p.git(stage, "merge", "--no-ff", "--no-edit", source, allow_failure=True)
            p.require(merged.returncode == 0, "Merge conflict; target is unchanged. Abort the generated stage merge, merge the target into the worker and resolve there, commit and retry complete")
            auto["candidate"] = p.oid(stage, "HEAD")
            p.write_json(path, data)
            candidate_test = validate(p, stage, command, args.test_timeout)
            data["receipts"].append(dict(candidate_test, action="integration-validation", source_oid=source, target_base=target))
            p.write_json(path, data)
            p.require(candidate_test["exit_code"] == 0, "Integration validation failed; main is unchanged and both worktrees remain")
            p.require(p.oid(workspace, "HEAD") == source and not p.status(workspace), "Worker changed after validation")
            p.require(p.oid(target_repo, "HEAD") == target and not p.status(target_repo), "Integration target changed; retry and validate a fresh candidate")
            # Persist the validated candidate before touching the target, so an
            # interruption immediately after fast-forward can be resumed safely.
            auto["phase"] = "publishing"
            auto["test_command"] = command
            auto["target_repo"] = str(target_repo)
            auto["target_baseline"] = p.inspect(project, target_repo, data["target"])
            p.write_json(path, data)
        candidate = auto["candidate"]
        p.require(command == auto["test_command"], "Resume publication with the recorded validation command")
        if not p.ancestor(target_repo, candidate, "refs/heads/" + data["target"]):
            if p.oid(target_repo, "HEAD") != auto["target_base"]:
                auto["phase"] = "working"
                p.write_json(path, data)
                raise p.Refused("Integration target changed; retry complete to validate a fresh candidate")
            p.require(p.oid(target_repo, "HEAD") == auto["target_base"] and not p.status(target_repo),
                      "Integration target changed before publication; preserve the validated candidate")
            p.require(p.oid(Path(auto["workspace"]), "HEAD") == auto["source_oid"]
                      and not p.status(Path(auto["workspace"])), "Worker changed before publication")
            p.git(target_repo, "merge", "--ff-only", candidate)
        if args.push:
            p.require(data["remote"], "Select the remote when starting the task")
            p.git(target_repo, "push", data["remote"], "HEAD:refs/heads/" + data["target"])
        # Do not release/delete the worker if its validated tip changed while
        # publication was in progress, even if that new work is already committed.
        worker = Path(auto["workspace"])
        branch_tip = p.oid(target_repo, "refs/heads/" + auto["branch"])
        pending = data.get("pending_branch_removal")
        if branch_tip is None and pending and pending["branch"] == auto["branch"]:
            p.require(pending["oid"] == auto["source_oid"]
                      and pending["integration_evidence"]["kind"] == "ancestor"
                      and p.ancestor(target_repo, pending["oid"], "refs/heads/" + data["target"])
                      and not any(item.get("branch") == "refs/heads/" + auto["branch"] for item in p.worktrees(target_repo)),
                      "Interrupted branch removal no longer matches the integration proof")
            data["receipts"].append(dict(pending, recovered=True))
            data.pop("pending_branch_removal")
            p.write_json(path, data)
        removed = any(item["action"] == "remove-branch" and item.get("branch") == auto["branch"]
                      and item.get("oid") == auto["source_oid"] for item in data["receipts"])
        p.require(branch_tip == auto["source_oid"] or (branch_tip is None and removed
                  and p.ancestor(target_repo, auto["source_oid"], "refs/heads/" + data["target"])),
                  "Worker branch advanced or disappeared without a cleanup receipt; preserve its work")
        with guard(project):
            if branch_tip is None:
                p.remove_branch_config(target_repo, auto["branch"])
            if auto.get("staging"):
                remove_stage(p, project, target_repo, path, data, args.idle_evidence)
            for item in data["artifacts"]:
                source_path = Path(item["source"])
                if item["disposition"] == "retain" and source_path.is_relative_to(worker):
                    destination = target_repo / source_path.relative_to(worker)
                    p.require(source_path.exists() and p.fingerprint(source_path) == p.fingerprint(destination),
                              "Retained worker artifact has no identical canonical destination")
                    data["receipts"].append({"action": "canonicalize-artifact", "source": str(source_path), "destination": str(destination), "at": p.now()})
                    item["source"] = str(destination)
            old_lock = p.lock_path(coordination(project), worker)
            if data["repo"] != str(target_repo):
                p.require(json.loads((old_lock / "owner.json").read_text())["token"] == data["token"], "Worker checkout ownership changed")
                data["workspace_baseline"] = data["baseline"]
                data["baseline"] = auto["target_baseline"]
                data["repo"] = str(target_repo)
                p.write_json(path, data)
                shutil.rmtree(old_lock)
            nested = p.SimpleNamespace(**dict(vars(args), repo=str(target_repo), outcome="complete", reason=""))
            nested.integration_commit = None
            nested.discard_reason = None
            if worker.exists():
                nested.path = str(worker)
                p.remove_worktree(nested)
                data = json.loads(path.read_text())
                auto = data["automatic"]
            if p.oid(target_repo, "refs/heads/" + auto["branch"]):
                nested.branch = auto["branch"]
                p.remove_branch(nested)
        return p.finish(nested)
    finally:
        # On failure keep the worker reservation and all task data. A target
        # reservation is short-lived and never blocks another task indefinitely.
        if acquired and target_lock.exists():
            with guard(project):
                current = json.loads(path.read_text())
                worker = Path(current["automatic"]["workspace"])
                if current["state"] == "active" and current["repo"] == str(target_repo) and worker.exists():
                    worker_lock = p.lock_path(coordination(project), worker)
                    if not worker_lock.exists():
                        worker_lock.mkdir(parents=True)
                        p.write_json(worker_lock / "owner.json", {"task": current["task"], "token": current["token"], "started_at": p.now()})
                    p.require(json.loads((worker_lock / "owner.json").read_text())["token"] == current["token"], "Worker reservation changed during cleanup")
                    current["repo"] = str(worker)
                    current["baseline"] = current["workspace_baseline"]
                    p.write_json(path, current)
                if (target_lock / "owner.json").is_file() and json.loads((target_lock / "owner.json").read_text()).get("token") == data["token"]:
                    shutil.rmtree(target_lock)
