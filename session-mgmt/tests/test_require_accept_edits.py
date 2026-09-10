"""Tests for session-mgmt/hooks/require-accept-edits.sh.

The hook runs on every user prompt in the session, so both halves matter: it
must block /exit-session in the modes where the sweep cannot run prompt-free,
and it must stay completely silent for everything else. Run with:

    python3 -m unittest discover session-mgmt/tests
"""
import json
import subprocess
import unittest
from pathlib import Path

_HOOK = Path(__file__).resolve().parents[1] / "hooks" / "require-accept-edits.sh"


def run_hook(payload):
    """Feed the hook a UserPromptSubmit payload; return (returncode, stdout, stderr).

    `payload` is a dict sent as JSON, or a raw string for malformed-input cases.
    """
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [str(_HOOK)], input=stdin, capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout, proc.stderr


def block_reason(prompt, mode):
    """Assert-free helper: the hook's block reason, or None if it passed through."""
    rc, out, _ = run_hook({"prompt": prompt, "permission_mode": mode})
    assert rc == 0, f"hook exited {rc}"
    if not out.strip():
        return None
    return json.loads(out)["reason"]


class BlockedModesTest(unittest.TestCase):
    def test_auto_mode_blocks_with_the_allow_rule_explanation(self):
        """auto strips the Bash allow rules, so the sweep must not start."""
        reason = block_reason("/exit-session", "auto")
        self.assertIsNotNone(reason)
        self.assertIn("auto mode", reason)
        self.assertIn("accept edits on", reason)

    def test_plan_mode_blocks_for_a_different_reason(self):
        reason = block_reason("/exit-session", "plan")
        self.assertIsNotNone(reason)
        self.assertIn("plan mode", reason)
        self.assertIn("accept edits on", reason)

    def test_block_output_is_a_well_formed_hook_decision(self):
        rc, out, err = run_hook({"prompt": "/exit-session", "permission_mode": "auto"})
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_scope_argument_still_blocks(self):
        """`/exit-session worktree` is the same sweep, just narrower."""
        self.assertIsNotNone(block_reason("/exit-session worktree", "auto"))

    def test_namespaced_invocation_still_blocks(self):
        self.assertIsNotNone(block_reason("/session-mgmt:exit-session", "auto"))

    def test_leading_whitespace_still_blocks(self):
        self.assertIsNotNone(block_reason("  /exit-session", "auto"))


class AllowedModesTest(unittest.TestCase):
    def test_modes_that_honor_allow_rules_pass_through(self):
        for mode in ("acceptEdits", "default", "bypassPermissions", "dontAsk"):
            with self.subTest(mode=mode):
                self.assertIsNone(block_reason("/exit-session", mode))

    def test_absent_permission_mode_passes_through(self):
        """An unknown mode is not a reason to refuse to clean up."""
        rc, out, _ = run_hook({"prompt": "/exit-session"})
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")


class UnrelatedPromptsTest(unittest.TestCase):
    def test_unrelated_prompt_is_untouched(self):
        rc, out, err = run_hook({"prompt": "fix the flaky test", "permission_mode": "auto"})
        self.assertEqual((rc, out, err), (0, "", ""))

    def test_prose_mentioning_the_skill_is_not_an_invocation(self):
        """Only the slash command counts; the skill is disable-model-invocation."""
        self.assertIsNone(block_reason("what does exit-session do?", "auto"))

    def test_bare_exit_is_not_exit_session(self):
        self.assertIsNone(block_reason("/exit", "auto"))

    def test_malformed_payload_fails_open_and_silently(self):
        """A parse error must not warn on a prompt the hook has no business gating."""
        rc, out, err = run_hook("not json at all exit-session")
        self.assertEqual((rc, out, err), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
