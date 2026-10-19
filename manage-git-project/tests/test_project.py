#!/usr/bin/env python3
"""Behavior tests against disposable real Git repositories; no network services."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/project.py"
SPEC = importlib.util.spec_from_file_location("manage_git_project", SCRIPT)
project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(project)
SCRATCH = None


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "project with spaces"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Lifecycle Fixture")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        (self.repo / ".gitignore").write_text(".local/\nignored/\n")
        (self.repo / "file.txt").write_text("baseline\n")
        self.git("add", ".")
        self.git("commit", "-m", "baseline")
        self.task = "fixture"

    def git(self, *args, repo=None, check=True):
        result = subprocess.run(["git", "-C", str(repo or self.repo), *args],
                                capture_output=True, text=True)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def cli(self, *args, expect=0, task=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = project.main(["--project-root", str(self.repo), "--task", task or self.task, *args])
        result = json.loads(output.getvalue())
        self.assertEqual(code, expect, result)
        return result

    def begin(self, *args):
        return self.cli("begin", "--target", "main", *args)

    def branch(self, name="codex/change", worktree=False):
        if worktree:
            directory = self.repo / ".local/worktrees/change"
            directory.parent.mkdir(parents=True, exist_ok=True)
            self.git("worktree", "add", "-b", name, str(directory), "main")
        else:
            directory = self.repo
            self.git("switch", "-c", name)
        self.cli("track-branch", "--branch", name)
        (directory / "feature.txt").write_text("task output\n")
        self.git("add", "feature.txt", repo=directory)
        self.git("commit", "-m", "task feature", repo=directory)
        return directory

    def merge(self, name="codex/change", squash=False):
        self.git("switch", "main")
        self.git("merge", "--squash" if squash else "--no-ff", name,
                 *( [] if squash else ["-m", "integrate task"] ))
        if squash:
            self.git("commit", "-m", "squashed feature")

    def test_inspect_is_read_only_and_handles_spaces(self):
        report = self.cli("inspect")
        self.assertEqual(report["branch"], "main")
        self.assertEqual(report["repo"], str(self.repo))
        self.assertFalse((self.repo / ".local").exists())

    def test_task_locks_conflicting_writer_until_finish(self):
        self.begin()
        self.cli("begin", "--target", "main", task="other", expect=2)
        self.cli("finish")
        self.cli("begin", "--target", "main", task="other")
        self.cli("finish", task="other")

    def test_cannot_overwrite_finished_task_history(self):
        self.begin()
        self.cli("finish")
        self.cli("begin", "--target", "main", expect=2)

    def test_missing_ignore_is_not_silently_written(self):
        (self.repo / ".gitignore").write_text("ignored/\n")
        self.cli("begin", "--target", "main", expect=2)
        self.assertFalse((self.repo / ".local").exists())

    def test_state_cannot_escape_through_symlink(self):
        outside = self.base / "outside"
        outside.mkdir()
        try:
            (self.repo / ".local").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation not available")
        self.cli("begin", "--target", "main", expect=2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_preexisting_change_is_preserved_without_blanket_clean(self):
        (self.repo / "file.txt").write_text("user draft\n")
        self.begin()
        self.cli("finish")
        self.assertEqual((self.repo / "file.txt").read_text(), "user draft\n")

    def test_accidental_commit_of_user_change_blocks_closure(self):
        (self.repo / "file.txt").write_text("user draft\n")
        self.begin()
        self.git("add", "file.txt")
        self.git("commit", "-m", "incorrectly include user draft")
        report = self.cli("check", expect=1)
        self.assertTrue(any("Pre-existing" in x for x in report["errors"]))

    def test_uncommitted_task_output_blocks_completion(self):
        self.begin()
        (self.repo / "new output.txt").write_text("not committed")
        self.cli("finish", expect=2)
        self.assertTrue((self.repo / "new output.txt").exists())

    def test_bootstrap_adoption_requires_reason(self):
        (self.repo / "bootstrap.txt").write_text("own bootstrap work")
        self.cli("begin", "--target", "main", "--adopt-path", "bootstrap.txt", expect=2)
        self.cli("begin", "--target", "main", "--adopt-path", "bootstrap.txt",
                 "--adopt-reason", "This task generated the file before its checker existed")
        self.git("add", "bootstrap.txt")
        self.git("commit", "-m", "bootstrap own checker")
        self.cli("finish")

    def test_unregistered_new_branch_is_detected(self):
        self.begin()
        self.git("branch", "codex/unrecorded")
        self.cli("check", expect=1)

    def test_target_and_foreign_branch_are_protected(self):
        self.git("branch", "foreign")
        self.begin()
        self.cli("track-branch", "--branch", "main", expect=2)
        self.cli("remove-branch", "--branch", "main", expect=2)
        self.cli("remove-branch", "--branch", "foreign", expect=2)
        self.assertIn("foreign", self.git("branch", "--format=%(refname:short)").splitlines())

    def test_open_work_is_handoff_not_completed(self):
        self.begin()
        self.branch()
        self.cli("retain", "--branch", "codex/change", "--reason", "PR review pending")
        self.cli("check", expect=1)
        report = self.cli("finish", "--outcome", "handoff", "--reason", "Await requested review")
        self.assertEqual(report["outcome"], "handoff")
        self.assertEqual(self.git("branch", "--show-current"), "codex/change")

    def test_unique_unmerged_commits_are_not_removed(self):
        self.begin()
        self.branch()
        tip = self.git("rev-parse", "HEAD")
        self.git("switch", "main")
        self.cli("remove-branch", "--branch", "codex/change", expect=2)
        self.assertEqual(self.git("rev-parse", "codex/change"), tip)

    def test_regular_merge_cleanup_preserves_commit_history(self):
        self.begin()
        self.branch()
        tip = self.git("rev-parse", "HEAD")
        self.merge()
        self.cli("remove-branch", "--branch", "codex/change")
        report = self.cli("finish")
        self.assertTrue(report["passed"])
        self.git("merge-base", "--is-ancestor", tip, "main")
        self.assertEqual(self.git("branch", "--format=%(refname:short)"), "main")

    def test_squash_requires_exact_integration_commit(self):
        self.begin()
        self.branch()
        self.merge(squash=True)
        integration = self.git("rev-parse", "HEAD")
        self.cli("remove-branch", "--branch", "codex/change", expect=2)
        receipt = self.cli("remove-branch", "--branch", "codex/change", "--integration-commit", integration)
        self.assertEqual(receipt["integration_evidence"]["kind"], "exact-patch")
        self.cli("finish")
        self.assertEqual((self.repo / "feature.txt").read_text(), "task output\n")

    def test_unrelated_integration_commit_cannot_discard_unique_patch(self):
        self.begin()
        self.branch()
        self.git("switch", "main")
        (self.repo / "different.txt").write_text("different task\n")
        self.git("add", ".")
        self.git("commit", "-m", "unrelated integration")
        integration = self.git("rev-parse", "HEAD")
        self.cli("remove-branch", "--branch", "codex/change", "--integration-commit", integration, expect=2)
        self.assertTrue(self.git("rev-parse", "codex/change"))

    def test_worktree_with_untracked_file_is_preserved(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        (directory / "private-note.txt").write_text("unique")
        self.cli("remove-worktree", "--path", str(directory), "--idle-evidence", "fixture idle", expect=2)
        self.assertTrue((directory / "private-note.txt").exists())

    def test_ignored_file_is_not_discarded_even_when_git_status_is_clean(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        (directory / "ignored").mkdir()
        secret = directory / "ignored/secret.txt"
        secret.write_text("unique secret test fixture")
        self.assertEqual(self.git("status", "--porcelain", repo=directory), "")
        self.cli("remove-worktree", "--path", str(directory), "--idle-evidence", "fixture idle", expect=2)
        self.assertEqual(secret.read_text(), "unique secret test fixture")

    def test_clean_worktree_is_removed_before_branch(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        self.cli("remove-branch", "--branch", "codex/change", expect=2)
        self.cli("remove-worktree", "--path", str(directory), "--idle-evidence", "Only this synthetic test owns this worktree")
        self.assertFalse(directory.exists())
        self.cli("remove-branch", "--branch", "codex/change")
        self.cli("finish")

    def test_locked_worktree_is_preserved(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        self.git("worktree", "lock", str(directory), "--reason", "active author")
        self.cli("remove-worktree", "--path", str(directory), "--idle-evidence", "fixture", expect=2)
        self.assertTrue(directory.exists())

    @unittest.skipUnless(shutil.which("lsof"), "Real process inspection requires lsof")
    def test_real_process_using_worktree_prevents_removal(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        child = subprocess.Popen([sys.executable, "-u", "-c", "import time; print('ready'); time.sleep(30)"],
                                 cwd=directory, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), "ready")
            self.cli("remove-worktree", "--path", str(directory), "--idle-evidence", "Check actual process", expect=2)
            self.assertTrue(directory.exists())
        finally:
            child.terminate()
            child.wait(timeout=5)
            child.stdout.close()

    def test_temp_and_external_artifact_must_be_accounted_for(self):
        self.begin()
        external = self.base / "external output.bin"
        external.write_bytes(b"all content\0including binary")
        self.cli("artifact", "--path", str(external), "--disposition", "retain", expect=2)
        destination = self.repo / "output.bin"
        self.cli("artifact", "--path", str(external), "--disposition", "migrate", "--destination", "output.bin")
        self.cli("check", expect=1)
        shutil.move(external, destination)
        self.git("add", "output.bin")
        self.git("commit", "-m", "preserve output")
        self.cli("finish")
        self.assertEqual(destination.read_bytes(), b"all content\0including binary")

    def test_changed_migration_content_is_detected(self):
        self.begin()
        source = self.base / "external.txt"
        source.write_text("original")
        self.cli("artifact", "--path", str(source), "--disposition", "migrate", "--destination", ".local/result.txt")
        shutil.move(source, self.repo / ".local/result.txt")
        (self.repo / ".local/result.txt").write_text("lost original")
        self.cli("check", expect=1)

    def test_known_temporary_file_blocks_until_removed(self):
        self.begin()
        temporary = self.repo / ".local/temporary.txt"
        temporary.write_text("reproducible output")
        self.cli("artifact", "--path", str(temporary), "--disposition", "temporary")
        self.cli("check", expect=1)
        temporary.unlink()
        self.cli("finish")

    def test_symlink_to_outside_is_not_a_canonical_deliverable(self):
        self.begin()
        source = self.base / "outside.txt"
        source.write_text("outside")
        link = self.repo / ".local/result.txt"
        try:
            link.symlink_to(source)
        except OSError:
            self.skipTest("symlink creation not available")
        self.cli("artifact", "--path", str(link), "--disposition", "retain", expect=2)

    def test_external_user_configuration_requires_specific_reason(self):
        self.begin()
        config = self.base / "AGENTS.md"
        config.write_text("User-approved global instructions")
        self.cli("artifact", "--path", str(config), "--disposition", "external-control", expect=2)
        self.cli("artifact", "--path", str(config), "--disposition", "external-control",
                 "--reason", "User explicitly requested this global AGENTS.md change")
        self.cli("finish")

    def test_dangling_retained_symlink_blocks_closure(self):
        self.begin()
        source = self.repo / ".local/source.txt"
        source.write_text("needed output")
        link = self.repo / ".local/result.txt"
        try:
            link.symlink_to(source)
        except OSError:
            self.skipTest("symlink creation not available")
        self.cli("artifact", "--path", str(link), "--disposition", "retain")
        source.unlink()
        self.cli("check", expect=1)

    def test_branch_configuration_is_removed_with_integrated_branch(self):
        self.begin()
        self.branch()
        self.git("config", "branch.codex/change.remote", "origin")
        self.git("config", "branch.codex/change.merge", "refs/heads/codex/change")
        self.merge()
        self.cli("remove-branch", "--branch", "codex/change")
        config = self.git("config", "--get-regexp", "^branch\\.codex/change\\.", check=False)
        self.assertEqual(config, "")
        self.cli("finish")

    def test_discard_and_integration_evidence_cannot_be_mixed(self):
        self.begin()
        self.branch()
        self.merge(squash=True)
        self.cli("remove-branch", "--branch", "codex/change", "--integration-commit", "main",
                 "--discard-reason", "Synthetic rejection", expect=2)
        self.assertTrue(self.git("rev-parse", "codex/change"))

    def remote(self):
        remote = self.base / "origin.git"
        self.git("init", "--bare", str(remote))
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "-u", "origin", "main")
        return remote

    def test_remote_branch_blocks_local_cleanup_until_target_published_and_remote_removed(self):
        self.remote()
        self.begin("--remote", "origin", "--require-push")
        self.branch()
        self.git("push", "-u", "origin", "codex/change")
        self.merge()
        self.cli("remove-branch", "--branch", "codex/change", expect=2)
        self.git("push", "origin", "main")
        self.cli("remove-branch", "--branch", "codex/change", expect=2)
        self.git("push", "origin", "--delete", "codex/change")
        self.cli("remove-branch", "--branch", "codex/change")
        self.cli("finish")

    def test_live_remote_recreation_is_not_hidden_by_stale_tracking_refs(self):
        remote = self.remote()
        self.begin("--remote", "origin")
        self.branch()
        self.merge()
        self.git("push", "origin", "main")
        tip = self.git("rev-parse", "codex/change")
        self.cli("remove-branch", "--branch", "codex/change")
        self.git("update-ref", "refs/heads/codex/change", tip, repo=remote)
        self.cli("check", expect=1)

    def test_remote_outage_does_not_become_a_successful_closure(self):
        remote = self.remote()
        self.begin("--remote", "origin")
        remote.rename(self.base / "unavailable.git")
        self.cli("check", expect=1)

    def test_target_is_project_specific_not_hardcoded_main(self):
        self.git("branch", "-m", "develop")
        self.cli("begin", "--target", "develop")
        self.cli("finish")

    def test_compare_and_delete_does_not_remove_a_changed_branch_tip(self):
        self.begin()
        self.branch()
        self.merge()
        alternative = self.git("rev-parse", "main")
        original_git = project.git
        raced = False
        def racing_git(repo, *args, **kwargs):
            nonlocal raced
            if args[:2] == ("update-ref", "--stdin") and not raced:
                raced = True
                self.git("update-ref", "refs/heads/codex/change", alternative)
            return original_git(repo, *args, **kwargs)
        with mock.patch.object(project, "git", side_effect=racing_git):
            self.cli("remove-branch", "--branch", "codex/change", expect=2)
        self.assertEqual(self.git("rev-parse", "codex/change"), alternative)

    def test_atomic_cleanup_refuses_if_integration_target_moves_back(self):
        self.begin()
        self.branch()
        tip = self.git("rev-parse", "HEAD")
        self.merge()
        baseline = self.git("rev-list", "--max-parents=0", "main")
        original_git = project.git
        raced = False
        def racing_git(repo, *args, **kwargs):
            nonlocal raced
            if args[:2] == ("update-ref", "--stdin") and not raced:
                raced = True
                self.git("update-ref", "refs/heads/main", baseline)
            return original_git(repo, *args, **kwargs)
        with mock.patch.object(project, "git", side_effect=racing_git):
            self.cli("remove-branch", "--branch", "codex/change", expect=2)
        self.assertEqual(self.git("rev-parse", "codex/change"), tip)

    def test_user_discard_is_recorded_without_merging_rejected_experiment(self):
        self.begin()
        self.branch()
        self.git("switch", "main")
        main = self.git("rev-parse", "HEAD")
        receipt = self.cli("remove-branch", "--branch", "codex/change", "--discard-reason",
                           "Synthetic user explicitly rejected this experiment and requested its deletion")
        self.assertEqual(receipt["integration_evidence"]["kind"], "discard")
        self.cli("finish")
        self.assertEqual(self.git("rev-parse", "main"), main)
        self.assertFalse((self.repo / "feature.txt").exists())

    def test_discard_does_not_bypass_unique_ignored_worktree_files(self):
        self.begin()
        directory = self.branch(worktree=True)
        (directory / "ignored").mkdir()
        file = directory / "ignored/private.txt"
        file.write_text("still preserve this unreviewed data")
        self.cli("remove-worktree", "--path", str(directory), "--idle-evidence", "synthetic fixture", "--discard-reason",
                 "Synthetic user rejected the committed experiment", expect=2)
        self.assertTrue(file.exists())

    def test_detaching_owned_worktree_does_not_allow_complete_closure(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        self.git("switch", "--detach", repo=directory)
        (directory / "ignored").mkdir()
        private = directory / "ignored/private.txt"
        private.write_text("unique unfinished work")
        self.cli("remove-branch", "--branch", "codex/change")
        self.cli("finish", expect=2)
        self.assertEqual(private.read_text(), "unique unfinished work")
        state = json.loads((self.repo / ".local/manage-git-project/tasks/fixture.json").read_text())
        self.assertEqual(state["state"], "active")

    def test_pruning_registration_does_not_hide_owned_worktree_files(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        private = directory / "private.txt"
        private.write_text("unregistered but still needed")
        (directory / ".git").unlink()
        self.git("worktree", "prune", "--expire", "now")
        self.cli("remove-branch", "--branch", "codex/change")
        self.cli("check", expect=1)
        self.assertEqual(private.read_text(), "unregistered but still needed")

    def test_missing_retained_branch_cannot_be_reported_as_handoff(self):
        self.begin()
        self.branch()
        self.cli("retain", "--branch", "codex/change", "--reason", "Review is pending")
        self.git("switch", "main")
        self.git("branch", "-D", "codex/change")
        self.cli("finish", "--outcome", "handoff", "--reason", "Await review", expect=2)

    def test_active_worktree_task_prevents_removal_after_its_cli_exits(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        with contextlib.redirect_stdout(io.StringIO()):
            code = project.main(["--project-root", str(self.repo), "--repo", str(directory),
                                 "--task", "other-author", "begin", "--target", "main"])
        self.assertEqual(code, 0)
        self.cli("remove-worktree", "--path", str(directory), "--idle-evidence",
                 "No running CLI; cooperative task is still active", expect=2)
        self.assertTrue(directory.exists())

    @unittest.skipUnless(shutil.which("lsof"), "Real process inspection requires lsof")
    def test_ignored_file_created_during_process_check_is_preserved(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        private = directory / "ignored/private.txt"
        original_run = subprocess.run

        def late_file(command, *args, **kwargs):
            result = original_run(command, *args, **kwargs)
            if command[0] == "lsof":
                private.parent.mkdir()
                private.write_text("created while lsof was checking")
            return result

        with mock.patch.object(project.subprocess, "run", side_effect=late_file):
            self.cli("remove-worktree", "--path", str(directory), "--idle-evidence",
                     "Actual process check with a concurrent file writer", expect=2)
        self.assertEqual(private.read_text(), "created while lsof was checking")

    def test_incomplete_process_scan_does_not_allow_worktree_removal(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        original_run = subprocess.run

        def incomplete_scan(command, *args, **kwargs):
            if command[0] == "lsof":
                return subprocess.CompletedProcess(command, 1, b"", b"WARNING: cannot stat; output may be incomplete")
            return original_run(command, *args, **kwargs)

        with mock.patch.object(project.shutil, "which", return_value="lsof"), \
                mock.patch.object(project.subprocess, "run", side_effect=incomplete_scan):
            self.cli("remove-worktree", "--path", str(directory), "--idle-evidence",
                     "Host process inspection reported an incomplete scan", expect=2)
        self.assertTrue(directory.exists())

    @unittest.skipUnless(shutil.which("lsof"), "Real process inspection requires lsof")
    def test_worktree_branch_switch_during_process_check_prevents_removal(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        original_run = subprocess.run

        def late_switch(command, *args, **kwargs):
            result = original_run(command, *args, **kwargs)
            if command[0] == "lsof":
                self.git("switch", "-c", "foreign-author", repo=directory)
            return result

        with mock.patch.object(project.subprocess, "run", side_effect=late_switch):
            self.cli("remove-worktree", "--path", str(directory), "--idle-evidence",
                     "Actual process check with a concurrent branch switch", expect=2)
        self.assertEqual(self.git("branch", "--show-current", repo=directory), "foreign-author")

    @unittest.skipUnless(shutil.which("lsof"), "Real process inspection requires lsof")
    def test_new_commit_during_process_check_prevents_worktree_removal(self):
        self.begin()
        directory = self.branch(worktree=True)
        self.merge()
        original_run = subprocess.run

        def late_commit(command, *args, **kwargs):
            result = original_run(command, *args, **kwargs)
            if command[0] == "lsof":
                (directory / "feature.txt").write_text("new unmerged work")
                self.git("commit", "-am", "additional work", repo=directory)
            return result

        with mock.patch.object(project.subprocess, "run", side_effect=late_commit):
            self.cli("remove-worktree", "--path", str(directory), "--idle-evidence",
                     "Actual process check with a concurrent commit", expect=2)
        self.assertEqual((directory / "feature.txt").read_text(), "new unmerged work")

    def test_remote_target_rollback_invalidates_cleanup_receipt_without_require_push(self):
        remote = self.remote()
        baseline = self.git("rev-parse", "main")
        self.begin("--remote", "origin")
        self.branch()
        self.merge()
        self.git("push", "origin", "main")
        self.cli("remove-branch", "--branch", "codex/change")
        self.git("update-ref", "refs/heads/main", baseline, repo=remote)
        self.cli("check", expect=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch-root", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    SCRATCH = Path(args.scratch_root).resolve()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
    os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Lifecycle)
    start = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "seconds": round(time.monotonic() - start, 3),
              "platform": sys.platform, "git": subprocess.check_output(["git", "--version"], text=True).strip(),
              "scratch_root": str(SCRATCH), "remaining_test_fixtures": list(SCRATCH.iterdir())}
    report["remaining_test_fixtures"] = [str(p) for p in report["remaining_test_fixtures"]]
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(not result.wasSuccessful())
