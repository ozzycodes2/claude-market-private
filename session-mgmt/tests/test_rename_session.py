"""Tests for session-mgmt/skills/start-session/scripts/rename-session.py.

The script is driven as a subprocess with HOME pointed at a temp tree, which is
how the skill invokes it and the only way to exercise the `~` expansion that
decides which files it touches. Run with:

    python3 session-mgmt/tests/test_rename_session.py

`unittest discover` does not work on this directory: it has no __init__.py, and
Python refuses a start directory that is not importable.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills" / "start-session" / "scripts" / "rename-session.py"
)

_SID = "97cffcd7-3996-4a4c-82c4-26c083a5cb58"


class RenameSessionTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.projects = self.home / ".claude" / "projects" / "-Users-someone-repo"
        self.projects.mkdir(parents=True)
        self.sessions = self.home / ".claude" / "sessions"
        self.sessions.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def run_script(self, *args):
        """Return (returncode, stdout) with HOME pointed at this test's tree."""
        proc = subprocess.run(
            ["python3", str(_SCRIPT), *args],
            capture_output=True, text=True, check=False,
            env={"HOME": str(self.home), "PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(proc.stderr, "")
        return proc.returncode, proc.stdout

    def write_transcript(self, body=""):
        p = self.projects / f"{_SID}.jsonl"
        p.write_text(body)
        return p

    def write_pid_file(self, filename="12345.json", **fields):
        p = self.sessions / filename
        p.write_text(json.dumps(fields))
        return p

    def test_title_records_land_in_the_matching_transcript(self):
        t = self.write_transcript()
        rc, out = self.run_script(_SID, "ABC-123")
        self.assertEqual(rc, 0)
        self.assertIn("renamed session -> ABC-123", out)
        records = [json.loads(line) for line in t.read_text().splitlines()]
        self.assertEqual(
            [(r["type"], r.get("customTitle") or r.get("agentName")) for r in records],
            [("custom-title", "ABC-123"), ("agent-name", "ABC-123")],
        )
        self.assertTrue(all(r["sessionId"] == _SID for r in records))

    def test_existing_transcript_content_survives(self):
        """The session is still writing this file; a rewrite would eat its history."""
        t = self.write_transcript('{"type":"user","content":"hello"}\n')
        self.run_script(_SID, "scratch")
        self.assertTrue(t.read_text().startswith('{"type":"user","content":"hello"}\n'))

    def test_other_sessions_transcripts_are_untouched(self):
        other = self.projects / "11111111-2222-3333-4444-555555555555.jsonl"
        other.write_text("")
        self.write_transcript()
        self.run_script(_SID, "scratch")
        self.assertEqual(other.read_text(), "")

    def test_no_transcript_skips_without_failing(self):
        rc, out = self.run_script(_SID, "scratch")
        self.assertEqual(rc, 0)
        self.assertIn("no transcript file matched", out)

    def test_pid_file_for_this_session_is_mirrored(self):
        self.write_transcript()
        p = self.write_pid_file(sessionId=_SID, name="old")
        rc, out = self.run_script(_SID, "ABC-123")
        self.assertEqual(rc, 0)
        self.assertIn("mirrored into the live pid file", out)
        self.assertEqual(json.loads(p.read_text())["name"], "ABC-123")

    def test_another_sessions_pid_file_is_left_alone(self):
        self.write_transcript()
        theirs = self.write_pid_file("999.json", sessionId="someone-else", name="theirs")
        _, out = self.run_script(_SID, "ABC-123")
        self.assertNotIn("mirrored", out)
        self.assertEqual(json.loads(theirs.read_text())["name"], "theirs")

    def test_unparseable_pid_file_does_not_stop_the_mirror(self):
        self.write_transcript()
        (self.sessions / "corrupt.json").write_text("{not json")
        mine = self.write_pid_file(sessionId=_SID)
        _, out = self.run_script(_SID, "ABC-123")
        self.assertIn("mirrored into the live pid file", out)
        self.assertEqual(json.loads(mine.read_text())["name"], "ABC-123")

    def test_missing_arguments_skip_rather_than_fail(self):
        for args in ((), (_SID,), (_SID, ""), ("", "name"), (_SID, "name", "extra")):
            with self.subTest(args=args):
                rc, out = self.run_script(*args)
                self.assertEqual(rc, 0)
                self.assertIn("skipping rename", out)


if __name__ == "__main__":
    unittest.main()
