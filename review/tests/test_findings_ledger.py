"""Tests for review/scripts/findings_ledger.py normalization.

Four review passes emit four incompatible finding shapes; these cover the
differences that break a naive reader -- the location key, the remedy key, a
severity one producer emits and another does not -- plus the cases where a
finding legitimately carries no location at all. Run with:

    python3 -m unittest discover review/tests
"""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "findings_ledger.py"
_spec = importlib.util.spec_from_file_location("findings_ledger", _SCRIPT)
findings_ledger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(findings_ledger)

normalize = findings_ledger.normalize
build_ledger = findings_ledger.build_ledger
append_findings = findings_ledger.append_findings
parse_pr_url = findings_ledger.parse_pr_url
repo_slug = findings_ledger.repo_slug
match_refactoring = findings_ledger.match_refactoring

PR_URL = "https://github.com/acme/widgets/pull/42"


def _only(findings):
    assert len(findings) == 1, f"expected exactly one finding, got {len(findings)}"
    return findings[0]


class PrUrlTest(unittest.TestCase):
    def test_parses_owner_repo_number(self):
        got = parse_pr_url(PR_URL)
        self.assertEqual(got["owner"], "acme")
        self.assertEqual(got["name"], "widgets")
        self.assertEqual(got["number"], 42)

    def test_parses_enterprise_host(self):
        got = parse_pr_url("https://github.acme-corp.net/team/svc/pull/7")
        self.assertEqual(got["name_with_owner"], "team/svc")
        self.assertEqual(got["number"], 7)

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/acme/widgets/issues/42")

    def test_slug_cannot_collide_across_owner_boundary(self):
        """`a/b-c` and `a-b/c` must not land on the same directory."""
        self.assertNotEqual(repo_slug("a", "b-c"), repo_slug("a-b", "c"))


class PathCommandTest(unittest.TestCase):
    """`path` exists so callers need no shell slug logic."""

    def test_path_from_pr_url(self):
        p = findings_ledger.ledger_path("acme", "widgets", 42, home="/h")
        self.assertEqual(
            str(p), "/h/.claude/review-findings/acme__widgets/pr-42.json"
        )

    def test_underscore_in_repo_name_survives(self):
        p = findings_ledger.ledger_path("acme", "my_repo", 7, home="/h")
        self.assertIn("acme__my_repo", str(p))


class BugFinderShapeTest(unittest.TestCase):
    def test_suggestion_becomes_remedy_and_refactoring_is_matched(self):
        f = _only(normalize("bug-finder", {"findings": [{
            "severity": "high", "path": "src/a.rs", "line": 12,
            "title": "Handler reaches into Config internals",
            "body": "Reads three private fields.",
            "suggestion": "Move Function onto Config.",
        }]}))
        self.assertEqual(f["remedy"], "Move Function onto Config.")
        self.assertEqual(f["refactoring"], "Move Function")
        self.assertEqual(f["kind"], "code-smell")
        self.assertTrue(f["blocking"])

    def test_finding_with_neither_path_nor_line_survives(self):
        """Architectural findings omit both by design and must not be dropped."""
        f = _only(normalize("domain-architecture", {"findings": [{
            "severity": "high",
            "title": "Dependency direction inverted",
            "body": "Core imports the HTTP adapter.",
            "suggestion": "Extract Interface in core; adapter implements it.",
        }]}))
        self.assertIsNone(f["path"])
        self.assertIsNone(f["line"])
        self.assertEqual(f["refactoring"], "Extract Interface")
        self.assertTrue(f["dedupe_key"])

    def test_explicit_decoration_overrides_severity_default(self):
        f = _only(normalize("change-evolution", {"findings": [{
            "severity": "critical", "label": "suggestion",
            "decoration": "non-blocking", "title": "Prefer a newtype",
        }]}))
        self.assertEqual(f["severity"], "critical")
        self.assertFalse(f["blocking"])

    def test_question_label_routes_to_design_decision(self):
        f = _only(normalize("data-contracts", {"findings": [{
            "severity": "medium", "label": "question",
            "title": "Is the dual write intentional?",
        }]}))
        self.assertEqual(f["kind"], "design-decision")

    def test_medium_severity_does_not_block(self):
        f = _only(normalize("bug-finder", {"findings": [{
            "severity": "medium", "title": "Extract helper",
        }]}))
        self.assertFalse(f["blocking"])

    def test_unknown_severity_falls_back_to_medium(self):
        f = _only(normalize("bug-finder", {"findings": [{
            "severity": "catastrophic", "title": "Whatever",
        }]}))
        self.assertEqual(f["severity"], "medium")
        self.assertFalse(f["blocking"])

    def test_empty_findings_list_is_valid(self):
        self.assertEqual(normalize("bug-finder", {"findings": []}), [])


class DocsDriftShapeTest(unittest.TestCase):
    """docs-drift puts the remedy in `fix`, not `suggestion`."""

    def test_fix_key_becomes_remedy(self):
        f = _only(normalize("docs-drift", {"findings": [{
            "severity": "high", "facet": "drift", "drift_class": "superseded-model",
            "path": "docs/api.md", "line": 42, "title": "Doc names a retired model",
            "body": "README still cites the old default.",
            "doc_says": "defaults to v1", "code_says": "defaults to v2",
            "fix": "Update the sentence to v2.",
        }]}))
        self.assertEqual(f["remedy"], "Update the sentence to v2.")
        self.assertEqual(f["kind"], "docs-prose")
        self.assertEqual(f["extra"]["doc_says"], "defaults to v1")
        self.assertEqual(f["extra"]["code_says"], "defaults to v2")
        self.assertIn("doc says: defaults to v1", f["body"])

    def test_low_severity_is_preserved_not_coerced(self):
        """docs-drift emits `low`; the bug-finder does not. Keep it."""
        f = _only(normalize("docs-drift", {"findings": [{
            "severity": "low", "path": "README.md", "title": "Wordy intro",
            "fix": "Tighten it.",
        }]}))
        self.assertEqual(f["severity"], "low")
        self.assertFalse(f["blocking"])

    def test_rendered_lag_is_a_generated_artifact(self):
        """A regenerated artifact must never be routed to a prose rewrite."""
        f = _only(normalize("docs-drift", {"findings": [{
            "severity": "medium", "drift_class": "rendered-lag",
            "path": "docs/cli.md", "title": "Rendered CLI help is stale",
            "fix": "regenerate docs/cli.md",
        }]}))
        self.assertEqual(f["kind"], "generated-artifact")
        self.assertEqual(f["extra"]["drift_class"], "rendered-lag")

    def test_stale_comment_routes_to_code_comment(self):
        f = _only(normalize("docs-drift", {"findings": [{
            "severity": "medium", "drift_class": "stale-comment",
            "path": "src/a.rs", "line": 9, "title": "Comment contradicts the code",
            "fix": "Correct it from the implementation.",
        }]}))
        self.assertEqual(f["kind"], "code-comment")


class SecurityScanShapeTest(unittest.TestCase):
    """security-scan locates findings with `file`, and its bucket keys vary."""

    def test_file_key_becomes_path(self):
        f = _only(normalize("security-scan", {"critical_findings": [{
            "file": "src/db.py", "line": 88, "message": "SQL injection via f-string.",
            "fix": "Use a parameterized query.", "category": "injection", "cwe": "CWE-89",
        }]}))
        self.assertEqual(f["path"], "src/db.py")
        self.assertEqual(f["remedy"], "Use a parameterized query.")
        self.assertEqual(f["kind"], "security")
        self.assertEqual(f["extra"]["cwe"], "CWE-89")
        self.assertTrue(f["blocking"])

    def test_all_findings_buckets_are_globbed(self):
        """The skill's template and its builder disagree on which buckets exist."""
        got = normalize("security-scan", {
            "critical_findings": [{"file": "a.py", "message": "one"}],
            "high_findings": [{"file": "b.py", "message": "two"}],
            "medium_findings": [{"file": "c.py", "message": "three"}],
        })
        self.assertEqual(len(got), 3)
        self.assertEqual(
            {f["severity"] for f in got}, {"critical", "high", "medium"}
        )

    def test_bucket_name_supplies_severity_when_absent(self):
        f = _only(normalize("security-scan", {"high_findings": [
            {"file": "a.py", "message": "no severity key"}
        ]}))
        self.assertEqual(f["severity"], "high")

    def test_title_is_first_clause_of_message(self):
        f = _only(normalize("security-scan", {"critical_findings": [{
            "file": "a.py", "message": "Auth check missing. Any caller can read it.",
        }]}))
        self.assertEqual(f["title"], "Auth check missing")

    def test_code_excerpt_is_bounded(self):
        f = _only(normalize("security-scan", {"critical_findings": [{
            "file": "a.py", "message": "long line", "code": "x" * 5000,
        }]}))
        self.assertLessEqual(len(f["extra"]["code"]), 260)

    def test_secret_value_is_fingerprinted_never_stored(self):
        """The ledger is durable; a reported secret must not be written to it."""
        secret = "AKIAIOSFODNN7EXAMPLE"
        f = _only(normalize("security-scan", {"secrets_found": [{
            "file": "config.py", "line": 3, "type": "aws_access_key", "secret": secret,
        }]}))
        blob = json.dumps(f)
        self.assertNotIn(secret, blob)
        self.assertTrue(f["extra"]["secret_fingerprint"].startswith("sha256:"))
        self.assertEqual(f["severity"], "critical")

    def test_same_secret_fingerprints_identically(self):
        fp = findings_ledger.fingerprint
        self.assertEqual(fp("hunter2"), fp("hunter2"))
        self.assertNotEqual(fp("hunter2"), fp("hunter3"))

    def test_dependency_vulnerability_routes_to_dependency(self):
        f = _only(normalize("security-scan", {"dependency_vulnerabilities": [{
            "package": "urllib3", "severity": "high", "cve": "CVE-2024-0001",
            "installed_version": "1.0", "fixed_version": "1.2",
        }]}))
        self.assertEqual(f["kind"], "dependency")
        self.assertIn("urllib3", f["title"])
        self.assertEqual(f["extra"]["cve"], "CVE-2024-0001")


class CiShapeTest(unittest.TestCase):
    def test_transient_infra_failure_is_not_a_finding(self):
        """`info` means re-run the check -- there is no code change to make."""
        self.assertEqual(normalize("ci", {
            "auto_fixable": False, "fix_type": None, "severity": "info",
            "summary": "Infrastructure failure (timeout/network)",
            "suggestion": "Re-run the CI check — likely transient",
        }), [])

    def test_ci_finding_with_only_a_check_name_has_no_path(self):
        f = _only(normalize("ci", {
            "auto_fixable": True, "fix_type": "lint", "severity": "medium",
            "summary": "Plugin lint check failed", "suggestion": "Run the linter",
            "check_name": "lint (rust)",
        }))
        self.assertIsNone(f["path"])
        self.assertIsNone(f["line"])
        self.assertEqual(f["kind"], "lint")
        self.assertEqual(f["external_ref"]["kind"], "ci_check")
        self.assertEqual(f["external_ref"]["check_name"], "lint (rust)")

    def test_sync_derived_routes_to_generated_artifact(self):
        f = _only(normalize("ci", {
            "auto_fixable": True, "fix_type": "sync_derived", "severity": "medium",
            "summary": "Derived files out of sync", "suggestion": "Run the sync script",
        }))
        self.assertEqual(f["kind"], "generated-artifact")

    def test_security_check_failure_routes_to_security(self):
        f = _only(normalize("ci", {
            "auto_fixable": False, "fix_type": None, "severity": "high",
            "summary": "Security check failure",
            "suggestion": "Review security findings — never auto-fix",
        }))
        self.assertEqual(f["kind"], "security")


class ReviewThreadShapeTest(unittest.TestCase):
    def test_thread_id_is_preserved_as_the_return_path(self):
        f = _only(normalize("review-thread", {"threads": [{
            "thread_id": "PRRT_kwDO", "comment_id": 9911, "author": "octocat",
            "path": "src/a.rs", "line": 5, "severity": "high",
            "body": "This swallows the error.\nPlease propagate it.",
        }]}))
        self.assertEqual(f["external_ref"]["thread_id"], "PRRT_kwDO")
        self.assertEqual(f["external_ref"]["author"], "octocat")
        self.assertEqual(f["title"], "This swallows the error.")
        self.assertTrue(f["blocking"])

    def test_bare_thread_object_is_accepted(self):
        f = _only(normalize("review-thread", {
            "thread_id": "T1", "path": "a.py", "body": "nit: rename this",
        }))
        self.assertEqual(f["external_ref"]["thread_id"], "T1")


class RefactoringMatchTest(unittest.TestCase):
    def test_longest_name_wins(self):
        """`Extract Class` must not be shadowed by `Extract Function`."""
        self.assertEqual(match_refactoring("apply Extract Class here"), "Extract Class")

    def test_guard_clause_name_matches_in_full(self):
        got = match_refactoring("Replace Nested Conditional with Guard Clauses")
        self.assertEqual(got, "Replace Nested Conditional with Guard Clauses")

    def test_kerievsky_names_are_matched(self):
        self.assertEqual(
            match_refactoring("use Unify Interfaces with Adapter"),
            "Unify Interfaces with Adapter",
        )

    def test_matching_is_case_insensitive(self):
        self.assertEqual(match_refactoring("move function onto Config"), "Move Function")

    def test_no_match_returns_none(self):
        self.assertIsNone(match_refactoring("just tidy it up a bit"))


class BuildLedgerTest(unittest.TestCase):
    def setUp(self):
        self.sources = {
            "bug-finder": {"findings": [
                {"severity": "critical", "path": "src/a.rs", "line": 1,
                 "title": "Null deref", "suggestion": "Guard it."}
            ]},
            "docs-drift": {"findings": [
                {"severity": "low", "path": "README.md", "title": "Wordy",
                 "fix": "Tighten.", "facet": "drift", "drift_class": "duplicated-claim"}
            ]},
            "security-scan": {"critical_findings": [
                {"file": "src/db.py", "line": 8, "message": "SQLi", "fix": "Parameterize."}
            ]},
        }
        self.analysis = {
            "languages": {"primary": "rust"},
            "test_setup": {"test_command": "just test", "can_run_safely": True,
                           "safety_notes": ""},
            "build_system": {"commands": {"lint": "just lint", "test": "just test"}},
            "risk_class": ["domain"],
            "head_sha": "abc123",
            "head_branch": "feat/x",
        }

    def test_every_source_contributes_and_ids_are_unique(self):
        led = build_ledger(pr_url=PR_URL, sources=self.sources, analysis=self.analysis)
        self.assertEqual(len(led["findings"]), 3)
        ids = [f["id"] for f in led["findings"]]
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(led["action_order"], ids)

    def test_context_is_copied_in_not_referenced(self):
        """The analysis JSON lives in a /tmp dir that is gone when `fix` runs."""
        led = build_ledger(pr_url=PR_URL, sources=self.sources, analysis=self.analysis)
        self.assertEqual(led["context"]["test_setup"]["test_command"], "just test")
        self.assertTrue(led["context"]["test_setup"]["can_run_safely"])
        self.assertEqual(led["context"]["build_system"]["commands"]["lint"], "just lint")
        self.assertEqual(led["context"]["languages"]["primary"], "rust")

    def test_raw_sources_round_trip_losslessly(self):
        led = build_ledger(pr_url=PR_URL, sources=self.sources, analysis=self.analysis)
        self.assertEqual(led["raw_sources"], self.sources)
        reloaded = json.loads(json.dumps(led))
        self.assertEqual(reloaded["raw_sources"], self.sources)

    def test_no_secret_survives_anywhere_in_the_ledger(self):
        """Fingerprinting the finding is not enough -- raw_sources holds it too."""
        secret = "AKIAIOSFODNN7EXAMPLE"
        led = build_ledger(pr_url=PR_URL, analysis=self.analysis, sources={
            "security-scan": {"secrets_found": [
                {"file": "config.py", "line": 3, "type": "aws_access_key",
                 "secret": secret},
            ]},
        })
        self.assertNotIn(secret, json.dumps(led))
        raw = led["raw_sources"]["security-scan"]["secrets_found"][0]
        self.assertTrue(raw["secret"].startswith("sha256:"))
        # Non-credential fields are still preserved verbatim.
        self.assertEqual(raw["file"], "config.py")
        self.assertEqual(raw["type"], "aws_access_key")

    def test_appended_payloads_are_sanitized_too(self):
        secret = "ghp_000111222333444555666777888999aaabbb"
        led = build_ledger(pr_url=PR_URL, sources={})
        append_findings(led, "security-scan", {"secrets_found": [
            {"file": "ci.yml", "type": "github_pat", "secret": secret},
        ]})
        self.assertNotIn(secret, json.dumps(led))

    def test_raw_source_code_excerpts_are_bounded(self):
        led = build_ledger(pr_url=PR_URL, sources={
            "security-scan": {"critical_findings": [
                {"file": "a.py", "message": "m", "code": "y" * 9000},
            ]},
        })
        raw = led["raw_sources"]["security-scan"]["critical_findings"][0]
        self.assertLessEqual(len(raw["code"]), 260)

    def test_repo_and_pr_identity_come_from_the_url(self):
        led = build_ledger(pr_url=PR_URL, sources=self.sources, analysis=self.analysis)
        self.assertEqual(led["repo"]["name_with_owner"], "acme/widgets")
        self.assertEqual(led["pr"]["number"], 42)
        self.assertEqual(led["pr"]["head_sha"], "abc123")

    def test_ledger_starts_unlocked_with_no_runs(self):
        led = build_ledger(pr_url=PR_URL, sources=self.sources)
        self.assertIsNone(led["lock"])
        self.assertEqual(led["runs"], [])

    def test_build_with_no_sources_is_valid(self):
        led = build_ledger(pr_url=PR_URL, sources={})
        self.assertEqual(led["findings"], [])
        self.assertEqual(led["schema_version"], findings_ledger.SCHEMA_VERSION)


class AppendTest(unittest.TestCase):
    def setUp(self):
        self.led = build_ledger(pr_url=PR_URL, sources={"bug-finder": {"findings": [
            {"severity": "high", "path": "a.rs", "line": 1, "title": "One"}
        ]}})

    def test_appended_findings_continue_the_id_sequence(self):
        added = append_findings(self.led, "ci", {
            "auto_fixable": True, "fix_type": "lint", "severity": "medium",
            "summary": "lint failed", "check_name": "lint",
        })
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["id"], "F002")
        self.assertEqual(len(self.led["findings"]), 2)
        self.assertIn("F002", self.led["action_order"])

    def test_duplicate_thread_is_not_appended_twice(self):
        """monitor-pr re-polls the same unresolved thread every tick."""
        thread = {"thread_id": "T1", "path": "a.rs", "line": 5, "body": "fix this"}
        first = append_findings(self.led, "review-thread", {"threads": [thread]})
        second = append_findings(self.led, "review-thread", {"threads": [thread]})
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(len(self.led["findings"]), 2)

    def test_transient_ci_failure_appends_nothing(self):
        added = append_findings(self.led, "ci", {
            "severity": "info", "summary": "timeout", "suggestion": "re-run"
        })
        self.assertEqual(added, [])
        self.assertEqual(len(self.led["findings"]), 1)


class AppendCreateTest(unittest.TestCase):
    """`monitor-pr` can run on a PR `/review:review` never looked at."""

    CI = json.dumps({
        "auto_fixable": True, "fix_type": "lint", "severity": "medium",
        "summary": "lint failed", "check_name": "lint",
    })

    def _run(self, argv, stdin):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with unittest.mock.patch("sys.stdin", io.StringIO(stdin)):
                rc = findings_ledger.main(argv)
        return rc, buf.getvalue()

    def test_append_refuses_a_missing_ledger_without_create(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "pr-42.json"
            with self.assertRaises(SystemExit) as cm:
                self._run(["append", "--ledger", str(target), "--source", "ci"], self.CI)
            self.assertIn("review:review", str(cm.exception))
            self.assertFalse(target.exists())

    def test_create_starts_a_ledger_with_no_context(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "pr-42.json"
            rc, out = self._run(
                ["append", "--ledger", str(target), "--source", "ci",
                 "--create", "--pr-url", PR_URL],
                self.CI,
            )
            self.assertEqual(rc, 0)
            self.assertIn("no analysis context", out)
            led = findings_ledger.read_ledger(target)
            self.assertEqual(led["pr"]["number"], 42)
            self.assertEqual(led["repo"]["owner"], "acme")
            self.assertEqual(len(led["findings"]), 1)
            self.assertEqual(led["findings"][0]["id"], "F001")
            # The absence is the point: a consumer gets no local test command.
            self.assertEqual(led["context"], {})

    def test_create_without_pr_url_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "pr-42.json"
            with self.assertRaises(SystemExit) as cm:
                self._run(
                    ["append", "--ledger", str(target), "--source", "ci", "--create"],
                    self.CI,
                )
            self.assertIn("--pr-url", str(cm.exception))

    def test_create_is_ignored_when_the_ledger_already_exists(self):
        """The flag must not clobber a real review's context block."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "pr-42.json"
            findings_ledger.write_ledger(target, build_ledger(
                pr_url=PR_URL, sources={}, analysis={"languages": {"primary": "rust"}}))
            rc, out = self._run(
                ["append", "--ledger", str(target), "--source", "ci",
                 "--create", "--pr-url", PR_URL],
                self.CI,
            )
            self.assertEqual(rc, 0)
            self.assertNotIn("no analysis context", out)
            led = findings_ledger.read_ledger(target)
            self.assertEqual(led["context"]["languages"]["primary"], "rust")


class AckTest(unittest.TestCase):
    """Acknowledgement is recorded so a re-run cannot reply to a reviewer twice."""

    def _ledger(self, td):
        led = build_ledger(pr_url=PR_URL, sources={"bug-finder": {"findings": [
            {"severity": "high", "path": "a.rs", "line": 1, "title": "One"}
        ]}})
        target = Path(td) / "pr-42.json"
        findings_ledger.write_ledger(target, led)
        return target

    def _ack(self, target, extra=()):
        argv = ["ack", "--ledger", str(target), "--id", "F001",
                "--thread", "PRRT_x", "--action", "reply+resolve", *extra]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = findings_ledger.main(argv)
        return rc, buf.getvalue()

    def test_ack_records_the_thread_and_action(self):
        with tempfile.TemporaryDirectory() as td:
            target = self._ledger(td)
            rc, _ = self._ack(target, ["--url", "https://gh/c/1", "--run", "fix-1"])
            self.assertEqual(rc, 0)
            f = findings_ledger.read_ledger(target)["findings"][0]
            self.assertEqual(len(f["acknowledged"]), 1)
            a = f["acknowledged"][0]
            self.assertEqual(a["thread_id"], "PRRT_x")
            self.assertEqual(a["action"], "reply+resolve")
            self.assertEqual(a["url"], "https://gh/c/1")
            self.assertEqual(a["by"], "fix-1")

    def test_ack_does_not_change_status(self):
        with tempfile.TemporaryDirectory() as td:
            target = self._ledger(td)
            before = findings_ledger.read_ledger(target)["findings"][0]["status"]
            self._ack(target)
            f = findings_ledger.read_ledger(target)["findings"][0]
            self.assertEqual(f["status"], before)
            self.assertIn("acknowledged", f["history"][-1]["note"])

    def test_a_second_ack_on_the_same_thread_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as td:
            target = self._ledger(td)
            self._ack(target)
            rc, out = self._ack(target)
            self.assertEqual(rc, 0)
            self.assertIn("already acknowledged", out)
            f = findings_ledger.read_ledger(target)["findings"][0]
            self.assertEqual(len(f["acknowledged"]), 1)

    def test_a_different_thread_appends_a_second_entry(self):
        with tempfile.TemporaryDirectory() as td:
            target = self._ledger(td)
            self._ack(target)
            self._ack(target, [])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                findings_ledger.main(["ack", "--ledger", str(target), "--id", "F001",
                                      "--thread", "PRRT_y", "--action", "reply"])
            f = findings_ledger.read_ledger(target)["findings"][0]
            self.assertEqual([a["thread_id"] for a in f["acknowledged"]], ["PRRT_x", "PRRT_y"])

    def test_an_unknown_action_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            target = self._ledger(td)
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    findings_ledger.main(["ack", "--ledger", str(target), "--id", "F001",
                                          "--thread", "T", "--action", "close"])

    def test_an_unknown_finding_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            target = self._ledger(td)
            with self.assertRaises(KeyError):
                findings_ledger.main(["ack", "--ledger", str(target), "--id", "F404",
                                      "--thread", "T", "--action", "reply"])


class LedgerIoTest(unittest.TestCase):
    def test_write_is_atomic_and_owner_only(self):
        led = build_ledger(pr_url=PR_URL, sources={})
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "acme__widgets" / "pr-42.json"
            findings_ledger.write_ledger(target, led)
            self.assertTrue(target.exists())
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(findings_ledger.read_ledger(target)["pr"]["number"], 42)

    def test_round_trip_preserves_the_document(self):
        led = build_ledger(pr_url=PR_URL, sources={"bug-finder": {"findings": [
            {"severity": "high", "path": "a.rs", "line": 2, "title": "T",
             "suggestion": "Extract Function"}
        ]}})
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "pr-42.json"
            findings_ledger.write_ledger(target, led)
            self.assertEqual(findings_ledger.read_ledger(target), led)


class StatusTransitionTest(unittest.TestCase):
    def setUp(self):
        self.led = build_ledger(pr_url=PR_URL, sources={"bug-finder": {"findings": [
            {"severity": "high", "path": "a.rs", "line": 1, "title": "One"}
        ]}})
        self.f = self.led["findings"][0]

    def test_new_findings_start_open_with_history(self):
        self.assertEqual(self.f["status"], "open")
        self.assertEqual(self.f["history"][0]["to"], "open")

    def test_transition_appends_history(self):
        findings_ledger._transition(self.f, "claimed", "run-1")
        self.assertEqual(self.f["status"], "claimed")
        self.assertEqual(self.f["history"][-1]["from"], "open")
        self.assertEqual(self.f["history"][-1]["to"], "claimed")


if __name__ == "__main__":
    unittest.main()
