"""Tests for session-mgmt/skills/exit-session/scripts/discover-resources.sh.

The script's job is attribution: deciding which worktrees a teardown sweep may
remove. Getting that wrong in either direction is expensive — a false
FOREIGN-LIVE leaks a worktree on every run, a false THIS-SESSION deletes a
working agent's checkout — so every classification branch is pinned here
against a real git repo with real locks and real pids. Run with:

    python3 session-mgmt/tests/test_discover_resources.py

`unittest discover` does not work on this directory: it has no __init__.py, and
Python refuses a start directory that is not importable.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills" / "exit-session" / "scripts" / "discover-resources.sh"
)

# A pid that cannot be alive. Linux and macOS both cap well below this, and
# kill -0 on it fails with ESRCH rather than EPERM.
_DEAD_PID = 4194303


# The developer's own git config is hostile to a test fixture: commit.gpgsign
# with a hardware/agent signer blocks `git commit` on an approval prompt that
# never comes in a test runner. Neutralise user and system config outright.
_GIT_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_SYSTEM=os.devnull,
    GIT_CONFIG_NOSYSTEM="1",
    GIT_TERMINAL_PROMPT="0",
)


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True, env=_GIT_ENV,
    ).stdout


class DiscoverHarness(unittest.TestCase):
    """A real repo with worktrees, a stubbed `docker`, and disposable processes."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="exit-session-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "test")
        (self.repo / "README").write_text("x\n")
        git(self.repo, "add", "README")
        git(self.repo, "commit", "-qm", "init")

        # Stub docker so the inventory never reaches the real daemon: `have
        # docker` stays true (exercising the label-filter code path) while every
        # query returns empty.
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        stub = self.bin / "docker"
        stub.write_text("#!/bin/sh\nexit 0\n")
        stub.chmod(0o755)
        self.env = dict(_GIT_ENV, PATH=f"{self.bin}:{os.environ['PATH']}")

    def add_worktree(self, name, lock_reason=None, dirty=False):
        path = self.repo / ".claude" / "worktrees" / name
        git(self.repo, "worktree", "add", "-q", "-b", f"worktree-{name}", str(path))
        if dirty:
            (path / "scratch.txt").write_text("uncommitted\n")
        if lock_reason is not None:
            git(self.repo, "worktree", "lock", "--reason", lock_reason, str(path))
            # Locked worktrees cannot be removed by rmtree-time git; unlock on
            # teardown so the temp dir cleanup is not fighting git's admin files.
            self.addCleanup(
                subprocess.run,
                ["git", "-C", str(self.repo), "worktree", "unlock", str(path)],
                capture_output=True,
            )
        return path

    def spawn(self, comm):
        """Start a live process whose `ps -o comm=` contains `comm`. Returns pid.

        Symlink, not copy: macOS invalidates a copied system binary's signature
        and kills it on exec, leaving a zombie that `kill -0` still reports as
        alive — which is a different classifier branch than the one under test.
        """
        exe = self.bin / comm
        exe.symlink_to("/bin/sleep")
        proc = subprocess.Popen([str(exe), "120"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(proc.wait)
        self.addCleanup(proc.kill)
        comm_reported = subprocess.run(
            ["ps", "-o", "comm=", "-p", str(proc.pid)],
            capture_output=True, text=True, check=False,
        ).stdout
        self.assertIn(comm, comm_reported, "fixture process did not start")
        return proc.pid

    def run_discover(self, arg=None, full=False):
        """Run discovery; default to --worktrees-only.

        The full pass spends ~25s in `pgrep -f` on a developer machine, which
        across this suite is minutes of waiting for sections no classification
        test reads. `full=True` exercises the rest.

        The timeout is load-bearing, not belt-and-braces: discovery shells out
        to gh, lsof and docker, and any one of them blocking on stdin turns a
        failure into a hung suite. Fail loudly instead.
        """
        cmd = ["bash", str(_SCRIPT), str(arg or self.repo)]
        if not full:
            cmd.append("--worktrees-only")
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=self.env, check=False,
            stdin=subprocess.DEVNULL, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    @staticmethod
    def classified_section(out):
        """Just the classification table — the self-worktree banner also ends in a path."""
        return out.split("WORKTREES CLASSIFIED")[1].split("=== UNREGISTERED")[0]

    def classification(self, out, name):
        """The tag the report gave the worktree directory `name`."""
        match = re.search(rf"^([A-Z-]+)\s+.*/\.claude/worktrees/{re.escape(name)}$",
                          self.classified_section(out), re.MULTILINE)
        return match.group(1) if match else None

    def detail_line(self, out, name):
        lines = self.classified_section(out).split("\n")
        for i, line in enumerate(lines):
            if line.endswith(f"/.claude/worktrees/{name}"):
                return lines[i + 1]
        return ""

    def unregistered_section(self, out):
        return out.split("UNREGISTERED WORKTREE DIRS")[1].split("=== GIT WORKTREES")[0]


class ClassificationTest(DiscoverHarness):
    def test_unlocked_worktree_is_stale(self):
        """A released lock is the signal that the agent finished."""
        self.add_worktree("released")
        self.assertEqual(
            self.classification(self.run_discover(), "released"), "STALE-UNLOCKED"
        )

    def test_lock_held_by_an_ancestor_pid_is_this_session(self):
        """The test process is an ancestor of the script's shell."""
        self.add_worktree(
            "mine", f"claude agent agent-mine (pid {os.getpid()} start now)"
        )
        self.assertEqual(self.classification(self.run_discover(), "mine"),
                         "THIS-SESSION")

    def test_lock_held_by_a_live_claude_is_foreign(self):
        pid = self.spawn("claude")
        self.add_worktree("theirs", f"claude agent agent-theirs (pid {pid} start now)")
        out = self.run_discover()
        self.assertEqual(self.classification(out, "theirs"), "FOREIGN-LIVE")
        self.assertIn("holder=", self.detail_line(out, "theirs"))
        self.assertIn("claude", self.detail_line(out, "theirs"))

    def test_lock_held_by_a_dead_pid_is_an_orphan(self):
        self.add_worktree("crashed", f"claude agent x (pid {_DEAD_PID} start now)")
        self.assertEqual(self.classification(self.run_discover(), "crashed"),
                         "ORPHAN-DEAD-PID")

    def test_lock_pid_recycled_into_another_program_is_an_orphan(self):
        """A live pid only protects a worktree while it is still claude.

        `notclaude` also pins the basename comparison: matching the holder as a
        substring would read this as a live session and leak the worktree.
        """
        pid = self.spawn("notclaude")
        self.add_worktree("recycled", f"claude agent x (pid {pid} start now)")
        self.assertEqual(self.classification(self.run_discover(), "recycled"),
                         "ORPHAN-PID-RECYCLED")

    def test_zombie_holder_is_an_orphan_despite_passing_kill_0(self):
        """An unreaped process still answers kill -0 but holds nothing.

        A process that has exited but not been waited on stays in the table, so
        liveness alone would protect its worktree forever.
        """
        exe = self.bin / "claude"
        exe.symlink_to("/usr/bin/true")
        proc = subprocess.Popen([str(exe)], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(proc.wait)  # deliberately not reaped until teardown
        proc.poll()
        reported = subprocess.run(
            ["ps", "-o", "comm=", "-p", str(proc.pid)],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        # Empty on Linux, `<defunct>` on macOS — neither names a session holder.
        self.assertIn(reported, ("", "<defunct>"),
                      "fixture did not produce an unreaped process")
        self.add_worktree("zombie", f"claude agent x (pid {proc.pid} start now)")
        self.assertEqual(self.classification(self.run_discover(), "zombie"),
                         "ORPHAN-PID-RECYCLED")

    def test_lock_without_a_parseable_pid_is_not_mistaken_for_ours(self):
        """A hand-written lock reason must not fall through to THIS-SESSION."""
        self.add_worktree("manual", "do not touch, migrating by hand")
        self.assertEqual(self.classification(self.run_discover(), "manual"),
                         "ORPHAN-DEAD-PID")

    def test_main_checkout_is_not_listed_as_a_teardown_target(self):
        out = self.run_discover()
        self.assertNotRegex(out, rf"^\S+\s+{re.escape(str(self.repo))}$")

    def test_self_worktree_is_tagged_self_when_the_arg_is_the_worktree(self):
        """Callers routinely pass their own worktree; it must not read as foreign."""
        path = self.add_worktree("self", f"claude agent x (pid {_DEAD_PID} start now)")
        out = self.run_discover(arg=path)
        # SELF outranks the dead lock pid: the session is standing in it.
        self.assertEqual(self.classification(out, "self"), "SELF")
        self.assertIn(f"SELF_WORKTREE: {path.resolve()}", out)
        # The repo line must be the main checkout, not the worktree that was passed.
        self.assertIn(f"repo: {self.repo.resolve()}", out)


class DockerAttributionTest(DiscoverHarness):
    """Compose labels the project with the worktree's directory basename."""

    def stub_docker(self, body):
        stub = self.bin / "docker"
        stub.write_text(f"#!/bin/sh\n{body}\n")
        stub.chmod(0o755)

    def test_project_labelled_resources_are_listed_under_their_worktree(self):
        self.stub_docker(
            'case "$1" in\n'
            '  volume)  echo stack_pgdata ;;\n'
            '  network) echo abc123 ;;\n'
            'esac\n'
            'exit 0'
        )
        self.add_worktree("stack")
        out = self.classified_section(self.run_discover())
        self.assertIn("docker volume:   stack_pgdata", out)
        self.assertIn("docker network:  abc123", out)

    def test_stopped_containers_are_included(self):
        """A finished agent's containers are exited, not running."""
        self.stub_docker(
            'if [ "$1" = container ] && [ "$2" = ls ] && [ "$3" = -a ]; then\n'
            '  echo deadbeef\n'
            'fi\n'
            'exit 0'
        )
        self.add_worktree("stack")
        self.assertIn("docker container: deadbeef",
                      self.classified_section(self.run_discover()))

    def test_empty_docker_output_adds_no_noise(self):
        self.add_worktree("stack")
        self.assertNotIn("docker ", self.classified_section(self.run_discover()))


class ReportDetailTest(DiscoverHarness):
    def test_uncommitted_count_is_reported_for_the_preserve_rule(self):
        self.add_worktree("dirty", dirty=True)
        self.assertIn("uncommitted=1", self.detail_line(self.run_discover(), "dirty"))

    def test_clean_worktree_reports_zero(self):
        self.add_worktree("clean")
        self.assertIn("uncommitted=0", self.detail_line(self.run_discover(), "clean"))

    def test_branch_name_is_reported_so_only_worktree_prefixed_ones_are_deleted(self):
        self.add_worktree("named")
        git(self.repo / ".claude" / "worktrees" / "named",
            "checkout", "-q", "-b", "fix-something-real")
        self.assertIn("branch=fix-something-real",
                      self.detail_line(self.run_discover(), "named"))

    def test_ancestor_pids_are_published_for_hand_verification(self):
        out = self.run_discover()
        self.assertRegex(out, r"ancestor pids \(this session\): .*\d")
        self.assertIn(str(os.getpid()), out)


class UnregisteredDirTest(DiscoverHarness):
    def test_leftover_directory_is_flagged_for_rm(self):
        """`worktree prune` clears the admin ref but leaves the checkout on disk."""
        path = self.add_worktree("pruned")
        git(self.repo, "worktree", "remove", "--force", str(path))
        path.mkdir(parents=True)
        (path / "leftover").write_text("x\n")
        self.assertIn(str(path), self.unregistered_section(self.run_discover()))

    def test_registered_worktree_is_not_flagged_as_unregistered(self):
        """git reports resolved paths; the fixture lives under a symlinked /var."""
        path = self.add_worktree("live")
        self.assertNotIn(str(path), self.unregistered_section(self.run_discover()))
        self.assertNotIn(str(path.resolve()),
                         self.unregistered_section(self.run_discover()))


class RobustnessTest(DiscoverHarness):
    def test_repo_without_an_origin_remote_completes(self):
        """`gh --repo ""` blocks on input forever; discovery must not reach it."""
        self.add_worktree("released")
        self.assertIn("END INVENTORY", self.run_discover(full=True))

    def test_non_repo_argument_does_not_abort_the_inventory(self):
        plain = self.tmp / "not-a-repo"
        plain.mkdir()
        self.assertIn("END INVENTORY", self.run_discover(arg=plain))

    def test_worktrees_only_skips_the_expensive_process_scan(self):
        self.add_worktree("released")
        out = self.run_discover()
        self.assertIn("WORKTREES CLASSIFIED", out)
        self.assertNotIn("CANDIDATE SESSION PROCESSES", out)

    def test_flag_order_does_not_decide_which_arg_is_the_repo(self):
        self.add_worktree("released")
        proc = subprocess.run(
            ["bash", str(_SCRIPT), "--worktrees-only", str(self.repo)],
            capture_output=True, text=True, env=self.env, check=False,
            stdin=subprocess.DEVNULL, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"repo: {self.repo}", proc.stdout)

    def test_missing_docker_is_skipped_rather_than_fatal(self):
        (self.bin / "docker").unlink()
        self.add_worktree("released")
        out = subprocess.run(
            ["bash", str(_SCRIPT), str(self.repo), "--worktrees-only"],
            capture_output=True, text=True, check=False, timeout=120,
            stdin=subprocess.DEVNULL,
            env=dict(_GIT_ENV, PATH=f"{self.bin}:/bin:/usr/bin"),
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("END INVENTORY", out.stdout)

    def test_help_flag_prints_usage_without_scanning(self):
        out = subprocess.run(
            ["bash", str(_SCRIPT), "--help"],
            capture_output=True, text=True, check=False, env=self.env, timeout=60,
        )
        self.assertEqual(out.returncode, 0)
        self.assertIn("discover-resources.sh", out.stdout)
        self.assertIn("--worktrees-only", out.stdout)
        self.assertNotIn("END INVENTORY", out.stdout)

    def test_script_is_run_through_bash_not_executed_directly(self):
        """Plugin packagers strip the executable bit; the skill documents `bash <path>`."""
        skill = _SCRIPT.resolve().parents[1] / "SKILL.md"
        self.assertIn("bash <skill-dir>/scripts/discover-resources.sh",
                      skill.read_text())


class SkillContractTest(unittest.TestCase):
    """The script classifies; SKILL.md must dispose of every tag it can emit."""

    def setUp(self):
        self.script = _SCRIPT.read_text()
        self.skill = (_SCRIPT.resolve().parents[1] / "SKILL.md").read_text()

    def test_every_emitted_tag_is_handled_by_the_skill(self):
        tags = set(re.findall(r'cls="([A-Z-]+)"', self.script))
        self.assertTrue(tags)
        for tag in tags:
            with self.subTest(tag=tag):
                self.assertIn(tag, self.skill)

    def test_unscoped_docker_prunes_are_forbidden(self):
        for cmd in ("docker system prune", "docker image prune -a",
                    "docker volume prune"):
            with self.subTest(cmd=cmd):
                self.assertIn(cmd, self.skill)
        self.assertIn("Never run at all", self.skill)

    def test_subagent_worktree_phase_exists(self):
        self.assertIn("3c", self.skill)
        self.assertIn("com.docker.compose.project", self.skill)


if __name__ == "__main__":
    unittest.main(verbosity=2)
