"""Tests for review/scripts/pr_threads.py finding-to-thread matching.

The risk this module carries is a *wrong* match: resolving a reviewer's thread
with an answer to a different finding. So most of these assert a refusal -- no
match on a different file, no match on file alone, no action on a tie -- rather
than a match. Run with:

    python3 -m unittest discover review/tests
"""
import importlib.util
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pr_threads.py"
_spec = importlib.util.spec_from_file_location("pr_threads", _SCRIPT)
pr_threads = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_threads)

parse_threads = pr_threads.parse_threads
match = pr_threads.match
score = pr_threads.score


def gql(*threads):
    """Wrap thread nodes in the shape `gh api graphql` returns."""
    return {
        "data": {
            "repository": {
                "pullRequest": {"reviewThreads": {"nodes": list(threads)}}
            }
        }
    }


def thread(
    tid="PRRT_x",
    path="src/db.rs",
    line=88,
    body="**issue (blocking):** Swallowed error in the retry path `Critical`",
    resolved=False,
    outdated=False,
    author="reviewer",
    original_line=None,
):
    return {
        "id": tid,
        "isResolved": resolved,
        "isOutdated": outdated,
        "comments": {
            "nodes": [
                {
                    "author": {"login": author},
                    "path": path,
                    "line": line,
                    "originalLine": original_line if original_line is not None else line,
                    "body": body,
                    "databaseId": 4242,
                }
            ]
        },
    }


def finding(
    fid="F001",
    path="src/db.rs",
    line=88,
    title="Swallowed error in the retry path",
    status="committed",
    sha="abc1234",
    **extra,
):
    f = {
        "id": fid,
        "path": path,
        "line": line,
        "title": title,
        "status": status,
        "resolved_by_sha": sha,
    }
    f.update(extra)
    return f


def ledger(*findings):
    return {"findings": list(findings)}


class ParseTest(unittest.TestCase):
    def test_flattens_the_graphql_response(self):
        got = parse_threads(gql(thread()))
        self.assertEqual(len(got), 1)
        t = got[0]
        self.assertEqual(t["thread_id"], "PRRT_x")
        self.assertEqual(t["path"], "src/db.rs")
        self.assertEqual(t["comment_id"], 4242)
        self.assertTrue(t["from_review"])
        self.assertEqual(t["label"], "issue")

    def test_recognises_a_review_comment_by_its_conventional_marker(self):
        """Attribution must not depend on who posted the review."""
        for body, expected in [
            ("**issue (blocking):** Something", True),
            ("**nitpick:** Something", True),
            ("> [!CAUTION]\n> **issue (blocking):** Something", True),
            ("**suggestion (non-blocking):** Something", True),
            ("Can you explain this?", False),
            ("**Note:** not a conventional label", False),
            ("LGTM", False),
        ]:
            got = parse_threads(gql(thread(body=body)))[0]
            self.assertEqual(got["from_review"], expected, body)

    def test_subject_is_extracted_from_the_marker(self):
        got = parse_threads(gql(thread()))[0]
        self.assertTrue(got["subject"].startswith("Swallowed error in the retry path"))

    def test_an_empty_or_malformed_response_yields_no_threads(self):
        self.assertEqual(parse_threads({}), [])
        self.assertEqual(parse_threads({"data": None}), [])
        self.assertEqual(parse_threads(gql()), [])

    def test_a_thread_with_no_comments_does_not_crash(self):
        got = parse_threads(gql({"id": "PRRT_y", "comments": {"nodes": []}}))
        self.assertEqual(len(got), 1)
        self.assertFalse(got[0]["from_review"])


class ScoreTest(unittest.TestCase):
    def test_same_file_line_and_title_scores_highest(self):
        s = score(finding(), parse_threads(gql(thread()))[0])
        self.assertIsNotNone(s)
        self.assertGreaterEqual(s[0], 3)
        self.assertIn("line", s[1])
        self.assertIn("title", s[1])

    def test_a_different_file_never_matches(self):
        t = parse_threads(gql(thread(path="src/other.rs")))[0]
        self.assertIsNone(score(finding(path="src/db.rs"), t))

    def test_same_file_alone_is_not_enough(self):
        """File-only matching would pair two unrelated findings in a long file."""
        t = parse_threads(gql(thread(line=10, body="**issue:** Totally other problem")))[0]
        self.assertIsNone(score(finding(line=900, title="Unrelated finding here"), t))

    def test_a_resolved_thread_is_never_matched(self):
        t = parse_threads(gql(thread(resolved=True)))[0]
        self.assertIsNone(score(finding(), t))

    def test_a_non_review_thread_is_never_matched(self):
        t = parse_threads(gql(thread(body="Please explain this line")))[0]
        self.assertIsNone(score(finding(), t))

    def test_a_finding_with_no_path_never_matches(self):
        t = parse_threads(gql(thread()))[0]
        self.assertIsNone(score(finding(path=None, line=None), t))

    def test_title_alone_matches_when_the_line_moved(self):
        t = parse_threads(gql(thread(line=140, original_line=140)))[0]
        s = score(finding(line=88), t)
        self.assertIsNotNone(s)
        self.assertEqual(s[1], "title")

    def test_original_line_matches_after_the_code_shifted(self):
        t = parse_threads(gql(thread(line=200, original_line=88, body="**issue:** Other text")))[0]
        s = score(finding(title="x"), t)
        self.assertIsNotNone(s)
        self.assertIn("line", s[1])

    def test_an_outdated_thread_ranks_below_a_live_one(self):
        live = score(finding(), parse_threads(gql(thread()))[0])
        stale = score(finding(), parse_threads(gql(thread(outdated=True)))[0])
        self.assertLess(stale[0], live[0])


class MatchTest(unittest.TestCase):
    def test_a_committed_finding_is_replied_to_and_resolved(self):
        got = match(ledger(finding()), parse_threads(gql(thread())))
        self.assertEqual(len(got["matched"]), 1)
        m = got["matched"][0]
        self.assertEqual(m["action"], "reply+resolve")
        self.assertEqual(m["thread_id"], "PRRT_x")
        self.assertEqual(m["resolved_by_sha"], "abc1234")
        self.assertEqual(m["confidence"], "high")

    def test_a_deferred_finding_is_replied_to_but_left_unresolved(self):
        """Resolving a deferral would bury the finding that most needs a human."""
        f = finding(
            status="deferred",
            sha=None,
            deferral={"decision_needed": "Outbox table, CDC, or accept the window?"},
        )
        got = match(ledger(f), parse_threads(gql(thread())))
        m = got["matched"][0]
        self.assertEqual(m["action"], "reply")
        self.assertEqual(m["decision_needed"], "Outbox table, CDC, or accept the window?")

    def test_an_open_finding_is_not_acknowledged(self):
        got = match(ledger(finding(status="open")), parse_threads(gql(thread())))
        self.assertEqual(got["matched"], [])

    def test_a_tie_is_reported_ambiguous_and_acted_on_by_neither(self):
        a = finding("F001", line=88, title="Same title here")
        b = finding("F002", line=88, title="Same title here")
        got = match(ledger(a, b), parse_threads(gql(thread(body="**issue:** Same title here"))))
        self.assertEqual(got["matched"], [])
        self.assertEqual(len(got["ambiguous"]), 1)
        self.assertEqual(got["ambiguous"][0]["candidates"], ["F001", "F002"])

    def test_one_thread_is_used_by_at_most_one_finding(self):
        a = finding("F001", line=88, title="Swallowed error in the retry path")
        b = finding("F002", line=99, title="Swallowed error in the retry path elsewhere")
        got = match(ledger(a, b), parse_threads(gql(thread())))
        self.assertEqual(len(got["matched"]), 1)
        self.assertEqual(len({m["thread_id"] for m in got["matched"]}), 1)

    def test_an_already_acknowledged_finding_is_skipped(self):
        """Guards against replying twice to one reviewer across runs."""
        f = finding(acknowledged=[{"thread_id": "PRRT_x", "action": "reply+resolve"}])
        got = match(ledger(f), parse_threads(gql(thread())))
        self.assertEqual(got["matched"], [])
        self.assertEqual(got["unmatched_findings"], [])

    def test_a_pathless_finding_is_reported_as_no_path(self):
        f = finding("F009", path=None, line=None, title="clippy failed")
        got = match(ledger(f), parse_threads(gql(thread())))
        self.assertEqual(got["matched"], [])
        self.assertEqual(got["unmatched_findings"][0]["reason"], "no-path")

    def test_a_finding_with_a_path_but_no_thread_is_distinguished(self):
        f = finding("F009", path="src/elsewhere.rs", title="Something else entirely")
        got = match(ledger(f), parse_threads(gql(thread())))
        self.assertEqual(got["unmatched_findings"][0]["reason"], "no-matching-thread")

    def test_unanswered_review_threads_are_surfaced(self):
        got = match(ledger(finding()), parse_threads(gql(thread(), thread(tid="PRRT_z", path="a.rs", line=1, body="**issue:** Unrelated"))))
        self.assertEqual(len(got["matched"]), 1)
        self.assertEqual([u["thread_id"] for u in got["unmatched_threads"]], ["PRRT_z"])

    def test_resolved_threads_are_not_reported_as_unanswered(self):
        got = match(ledger(), parse_threads(gql(thread(resolved=True))))
        self.assertEqual(got["unmatched_threads"], [])

    def test_low_confidence_is_flagged_rather_than_hidden(self):
        t = parse_threads(gql(thread(line=500, original_line=500, body="**issue:** Swallowed error in the retry")))[0]
        got = match(ledger(finding(line=88, title="Swallowed error in the retry")), [t])
        self.assertEqual(got["matched"][0]["confidence"], "low")


if __name__ == "__main__":
    unittest.main()
