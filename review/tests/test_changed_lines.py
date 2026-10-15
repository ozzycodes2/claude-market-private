"""Tests for review/scripts/changed_lines.py.

The filter decides which analyzer findings survive, so the cases that matter
are the ones where a wrong answer silently loses a real finding: multi-hunk
files, renames, deletions, multi-line spans straddling the hunk edge, and the
path mismatch between an analyzer's cwd and the diff's repo root. Run with:

    python3 -m unittest discover review/tests
"""
import importlib.util
import io
import json
import unittest
import unittest.mock
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "changed_lines.py"
_spec = importlib.util.spec_from_file_location("changed_lines", _SCRIPT)
changed_lines = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(changed_lines)

parse_diff = changed_lines.parse_diff
lines_for = changed_lines.lines_for
filter_findings = changed_lines.filter_findings

DIFF = """\
diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -10,6 +10,8 @@ def handler(req):
     ctx = build(req)
-    token = req.get("token")
+    token = req.headers["token"]
+    audit(token)
     return dispatch(ctx, token)

@@ -40,3 +42,4 @@ def dispatch(ctx, token):
     if not token:
         raise Unauthorized()
+    log.info("dispatching %s", token)
     return ctx.run()
"""


class ParseDiffTest(unittest.TestCase):
    def test_only_added_lines_are_changed(self):
        """Context lines are unchanged code; the analyzer would flag them on base too."""
        self.assertEqual(parse_diff(DIFF), {"src/app.py": {11, 12, 44}})

    def test_removed_lines_do_not_advance_the_new_file_counter(self):
        got = parse_diff(
            "--- a/a.py\n+++ b/a.py\n@@ -1,3 +1,2 @@\n a\n-b\n-c\n+d\n"
        )
        self.assertEqual(got, {"a.py": {2}})

    def test_single_line_hunk_header_without_a_count(self):
        got = parse_diff("--- a/a.py\n+++ b/a.py\n@@ -5 +5 @@\n-old\n+new\n")
        self.assertEqual(got, {"a.py": {5}})

    def test_deleted_file_contributes_nothing(self):
        got = parse_diff("--- a/gone.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-a\n-b\n")
        self.assertEqual(got, {})

    def test_new_file_is_entirely_changed(self):
        got = parse_diff("--- /dev/null\n+++ b/new.py\n@@ -0,0 +1,3 @@\n+a\n+b\n+c\n")
        self.assertEqual(got, {"new.py": {1, 2, 3}})

    def test_rename_is_recorded_under_the_new_path(self):
        got = parse_diff(
            "--- a/old/name.py\n+++ b/new/name.py\n@@ -1,1 +1,2 @@\n a\n+b\n"
        )
        self.assertEqual(got, {"new/name.py": {2}})

    def test_no_newline_marker_is_not_counted_as_a_line(self):
        got = parse_diff("--- a/a.py\n+++ b/a.py\n@@ -1,1 +1,1 @@\n+a\n\\ No newline\n")
        self.assertEqual(got, {"a.py": {1}})

    def test_two_files_stay_separate(self):
        got = parse_diff(
            "--- a/x.py\n+++ b/x.py\n@@ -1,0 +1,1 @@\n+x\n"
            "--- a/y.py\n+++ b/y.py\n@@ -9,0 +9,1 @@\n+y\n"
        )
        self.assertEqual(got, {"x.py": {1}, "y.py": {9}})

    def test_empty_diff(self):
        self.assertEqual(parse_diff(""), {})


class PathResolutionTest(unittest.TestCase):
    def setUp(self):
        self.changed = {"svc/api/handler.py": {4}}

    def test_exact_match(self):
        self.assertEqual(lines_for(self.changed, "svc/api/handler.py"), {4})

    def test_analyzer_run_from_a_subdirectory(self):
        self.assertEqual(lines_for(self.changed, "api/handler.py"), {4})

    def test_leading_dot_slash_is_tolerated(self):
        self.assertEqual(lines_for(self.changed, "./svc/api/handler.py"), {4})

    def test_unrelated_file_resolves_to_nothing(self):
        self.assertEqual(lines_for(self.changed, "svc/api/other.py"), set())

    def test_suffix_match_respects_the_path_separator(self):
        """`handler.py` must not match `my_handler.py`."""
        self.assertEqual(lines_for({"a/my_handler.py": {1}}, "handler.py"), set())

    def test_missing_path(self):
        self.assertEqual(lines_for(self.changed, None), set())


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.changed = {"src/app.py": {12, 13, 45}}

    def _semgrep(self, *lines):
        return {"results": [
            {"path": "src/app.py", "start": {"line": n}, "end": {"line": n},
             "check_id": f"r{n}"}
            for n in lines
        ]}

    def test_keeps_findings_on_changed_lines_only(self):
        out, dropped = filter_findings(self._semgrep(12, 30, 45), self.changed, "semgrep")
        self.assertEqual([f["check_id"] for f in out["results"]], ["r12", "r45"])
        self.assertEqual(dropped, 1)

    def test_multiline_span_touching_one_changed_line_survives(self):
        doc = {"results": [{"path": "src/app.py", "start": {"line": 8},
                            "end": {"line": 14}, "check_id": "span"}]}
        out, dropped = filter_findings(doc, self.changed, "semgrep")
        self.assertEqual(len(out["results"]), 1)
        self.assertEqual(dropped, 0)

    def test_multiline_span_missing_every_changed_line_is_dropped(self):
        doc = {"results": [{"path": "src/app.py", "start": {"line": 20},
                            "end": {"line": 30}}]}
        out, _ = filter_findings(doc, self.changed, "semgrep")
        self.assertEqual(out["results"], [])

    def test_finding_in_an_untouched_file_is_dropped(self):
        doc = {"results": [{"path": "src/other.py", "start": {"line": 12},
                            "end": {"line": 12}}]}
        out, dropped = filter_findings(doc, self.changed, "semgrep")
        self.assertEqual(out["results"], [])
        self.assertEqual(dropped, 1)

    def test_other_document_keys_are_preserved(self):
        doc = dict(self._semgrep(12), errors=["x"], version="1.2.3")
        out, _ = filter_findings(doc, self.changed, "semgrep")
        self.assertEqual(out["errors"], ["x"])
        self.assertEqual(out["version"], "1.2.3")

    def test_input_document_is_not_mutated(self):
        doc = self._semgrep(12, 30)
        filter_findings(doc, self.changed, "semgrep")
        self.assertEqual(len(doc["results"]), 2)

    def test_bandit_shape(self):
        doc = {"results": [
            {"filename": "src/app.py", "line_number": 13, "test_id": "B105"},
            {"filename": "src/app.py", "line_number": 99, "test_id": "B303"},
        ]}
        out, dropped = filter_findings(doc, self.changed, "bandit")
        self.assertEqual([f["test_id"] for f in out["results"]], ["B105"])
        self.assertEqual(dropped, 1)

    def test_bandit_line_range_straddling_the_hunk(self):
        doc = {"results": [{"filename": "src/app.py", "line_number": 10,
                            "line_range": [10, 11, 12]}]}
        out, _ = filter_findings(doc, self.changed, "bandit")
        self.assertEqual(len(out["results"]), 1)

    def test_gosec_shape_with_a_string_line_range(self):
        doc = {"Issues": [
            {"file": "src/app.py", "line": "44-46", "rule_id": "G101"},
            {"file": "src/app.py", "line": "7", "rule_id": "G404"},
        ]}
        out, dropped = filter_findings(doc, self.changed, "gosec")
        self.assertEqual([f["rule_id"] for f in out["Issues"]], ["G101"])
        self.assertEqual(dropped, 1)

    def test_unparseable_line_is_dropped_not_crashed(self):
        doc = {"Issues": [{"file": "src/app.py", "line": "unknown"}]}
        out, dropped = filter_findings(doc, self.changed, "gosec")
        self.assertEqual(out["Issues"], [])
        self.assertEqual(dropped, 1)

    def test_missing_findings_key_yields_an_empty_list(self):
        out, dropped = filter_findings({}, self.changed, "semgrep")
        self.assertEqual(out["results"], [])
        self.assertEqual(dropped, 0)

    def test_non_dict_entries_are_dropped(self):
        out, dropped = filter_findings({"results": ["junk"]}, self.changed, "semgrep")
        self.assertEqual(out["results"], [])
        self.assertEqual(dropped, 1)


class CliTest(unittest.TestCase):
    def _run(self, argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch("sys.stdin", io.StringIO(stdin)), \
             unittest.mock.patch("sys.stdout", out), \
             unittest.mock.patch("sys.stderr", err):
            rc = changed_lines.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_map_reads_the_diff_from_stdin(self):
        rc, out, _ = self._run(["map", "--diff", "-"], stdin=DIFF)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out), {"src/app.py": [11, 12, 44]})

    def test_filter_reports_the_drop_count_on_stderr(self):
        with unittest.mock.patch("builtins.open",
                                 unittest.mock.mock_open(read_data=DIFF)):
            doc = json.dumps({"results": [
                {"path": "src/app.py", "start": {"line": 11}, "end": {"line": 11}},
                {"path": "src/app.py", "start": {"line": 99}, "end": {"line": 99}},
            ]})
            rc, out, err = self._run(
                ["filter", "--diff", "/tmp/pr.diff", "--tool", "semgrep"], stdin=doc
            )
        self.assertEqual(rc, 0)
        self.assertEqual(len(json.loads(out)["results"]), 1)
        self.assertIn("dropped 1 finding", err)


if __name__ == "__main__":
    unittest.main()
