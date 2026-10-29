"""Tests for technical-writing/skills/create-slides/scripts/check_deck.py.

The checker is imported by path so `check_html` can be driven with small HTML
fragments, and `main` is exercised in-process for coverage. Run with:

    python3 -I -m unittest discover -s technical-writing/tests -p 'test_check_deck.py'
"""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

_SKILL = Path(__file__).resolve().parents[1] / "skills" / "create-slides"
_SCRIPT = _SKILL / "scripts" / "check_deck.py"
_TEMPLATE = _SKILL / "assets" / "deck-template.html"

_spec = importlib.util.spec_from_file_location("check_deck", _SCRIPT)
check_deck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_deck)

ALLOWED = set(check_deck.BRAND_HEX)

DIAGRAM = (
    '<svg id="flow-root" viewBox="0 0 1104 520">'
    "<title>Request flow</title><desc>Client to API to store.</desc>"
    '<rect x="0" y="0" width="10" height="10" fill="#1A7A52"/>'
    "<text>many words inside the diagram do not count toward the slide budget at all "
    "because the diagram detail dial governs them instead of the slide rules</text>"
    "</svg>"
)


def content(body, eyebrow="CI", headline="Tests own most build time", extra=""):
    return (
        '<section class="slide s-content"><div class="slide-header">'
        f'<div class="eyebrow">{eyebrow}</div><h2>{headline}</h2></div>'
        f'<div class="body">{body}</div>{extra}</section>'
    )


def deck(*slides, head=""):
    return f"<!DOCTYPE html><html><head>{head}</head><body><div class=\"deck\">{''.join(slides)}</div></body></html>"


def rules(report):
    return [f["rule"] for f in report["findings"]]


class CleanDeckTest(unittest.TestCase):
    def test_shipped_template_passes(self):
        report = check_deck.check_html(_TEMPLATE.read_text(encoding="utf-8"), ALLOWED)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["slides"], 8)

    def test_diagram_slide_with_notes_passes(self):
        notes = '<aside class="notes"><p>Long prose is fine here, ' + "word " * 60 + "</p><ul><li>x</li></ul></aside>"
        report = check_deck.check_html(deck(content(f'<div class="visual dgm">{DIAGRAM}</div>', extra=notes)), ALLOWED)
        self.assertTrue(report["ok"], report)

    def test_title_slide_needs_no_visual(self):
        html = deck('<section class="slide s-title"><div class="eyebrow">Team</div><h1>Hello</h1><br><img src="x.png"></section>')
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"])

    def test_divider_numeral_and_separators_are_not_words(self):
        html = deck(
            '<section class="slide s-divider"><div class="eyebrow">Area · 01 · CI</div>'
            '<h2>Build</h2><div class="bg-n">' + "01 " * 40 + "</div></section>"
        )
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"])


class TextRuleTest(unittest.TestCase):
    def test_long_headline(self):
        html = deck(content('<div class="visual big-number">3×</div>', headline="one two three four five <strong>six seven eight</strong>"))
        report = check_deck.check_html(html, ALLOWED)
        self.assertEqual(rules(report), ["headline-words"])
        self.assertIn("8 words", report["findings"][0]["message"])

    def test_long_eyebrow(self):
        html = deck(content('<div class="visual big-number">3×</div>', eyebrow="Area 01 PR wall clock"))
        self.assertEqual(rules(check_deck.check_html(html, ALLOWED)), ["eyebrow-words"])

    def test_too_many_visible_words(self):
        labels = "".join(f'<div class="l">label {i}</div>' for i in range(12))
        html = deck(content(f'<div class="visual stat-strip">{labels}</div>'))
        report = check_deck.check_html(html, ALLOWED)
        self.assertEqual(rules(report), ["slide-words"])
        self.assertIn("30 visible words", report["findings"][0]["message"])

    def test_text_layers_reported_once_each(self):
        body = '<div class="sub">a</div><div class="visual statement"><p>a</p><p>b</p><ul><li>c</li></ul><ol><li>d</li></ol></div>'
        report = check_deck.check_html(deck(content(body)), ALLOWED)
        messages = [f["message"].split(" ")[0] for f in report["findings"]]
        self.assertEqual(rules(report), ["text-layer"] * 4)
        self.assertEqual(sorted(messages), sorted([".sub", "<p>", "<ul>", "<ol>"]))


class VisualRuleTest(unittest.TestCase):
    def test_content_slide_without_visual(self):
        report = check_deck.check_html(deck(content("<div>nothing</div>")), ALLOWED)
        self.assertEqual(rules(report), ["visual-count"])
        self.assertIn("expected 1", report["findings"][0]["message"])

    def test_two_visuals(self):
        body = '<div class="visual big-number">3×</div><div class="visual big-number">4×</div>'
        self.assertEqual(rules(check_deck.check_html(deck(content(body)), ALLOWED)), ["visual-count"])

    def test_statement_slide_without_visual(self):
        html = deck('<section class="slide s-statement"><div class="eyebrow">CI</div><div>Plain</div></section>')
        self.assertEqual(rules(check_deck.check_html(html, ALLOWED)), ["visual-count"])

    def test_title_slide_with_two_visuals(self):
        html = deck('<section class="slide s-title"><div class="visual">a</div><div class="visual">b</div></section>')
        report = check_deck.check_html(html, ALLOWED)
        self.assertIn("expected 0 or 1", report["findings"][0]["message"])


class DiagramRuleTest(unittest.TestCase):
    def check_svg(self, svg):
        return check_deck.check_html(deck(content(f'<div class="visual dgm">{svg}</div>')), ALLOWED)

    def test_hand_drawn_svg(self):
        report = self.check_svg('<svg viewBox="0 0 10 10"><rect width="1" height="1"/></svg>')
        self.assertEqual(rules(report), ["diagram-source"])
        message = report["findings"][0]["message"]
        for problem in ("-root", "<title>", "<desc>"):
            self.assertIn(problem, message)

    def test_empty_title(self):
        report = self.check_svg('<svg id="a-root"><title> </title><desc>d</desc></svg>')
        self.assertEqual(rules(report), ["diagram-source"])

    def test_title_not_first_child(self):
        report = self.check_svg('<svg id="a-root"><desc>d</desc><title>t</title></svg>')
        self.assertIn("first child", report["findings"][0]["message"])

    def test_nested_title_and_desc_do_not_count(self):
        report = self.check_svg('<svg id="a-root"><g><title>t</title><desc>d</desc></g></svg>')
        self.assertIn("no <desc>", report["findings"][0]["message"])

    def test_svg_inside_notes_is_ignored(self):
        notes = '<aside class="notes"><svg><rect/></svg></aside>'
        html = deck(content('<div class="visual big-number">3×</div>', extra=notes))
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"])

    def test_xml_declaration(self):
        html = deck(content(f'<div class="visual dgm"><?xml version="1.0" encoding="UTF-8"?>{DIAGRAM}</div>'))
        self.assertEqual(rules(check_deck.check_html(html, ALLOWED)), ["xml-declaration"])

    def test_other_processing_instruction_is_ignored(self):
        html = deck(content(f'<div class="visual dgm"><?php echo 1 ?>{DIAGRAM}</div>'))
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"])


class ColorRuleTest(unittest.TestCase):
    def test_off_brand_in_head_style_reported_once(self):
        html = deck(head="<style>a{color:#5C7077} b{color:#5c7077} c{color:#fff}</style>")
        report = check_deck.check_html(html, ALLOWED)
        self.assertEqual(report["findings"], [{
            "slide": 0, "rule": "off-brand-color",
            "message": "#5C7077 is not a brand token or a Machinify diagram profile color",
        }])

    def test_off_brand_in_slide_attribute(self):
        body = '<div class="visual big-number" style="color:#B4473A">3×</div>'
        report = check_deck.check_html(deck(content(body)), ALLOWED)
        self.assertEqual([(f["slide"], f["rule"]) for f in report["findings"]], [(1, "off-brand-color")])

    def test_eight_digit_hex_compares_on_rgb(self):
        html = deck(head="<style>a{color:#1A7A52CC}</style>")
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"])

    def test_non_colors_are_ignored(self):
        html = deck(
            head="<style>#bad-root .n{fill:#1F3539} #nav{}</style>",
            *[content(
                '<div class="visual dgm"><svg id="bad-root"><title>t</title><desc>d</desc>'
                '<path fill="url(#abc)"/><a href="#abc">x</a></svg></div>',
                headline="Issue #123 &#123; fixed",
            )],
        )
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"], check_deck.check_html(html, ALLOWED))

    def test_script_text_is_not_scanned_or_counted(self):
        script = "<script>const a = '#123456 " + "word " * 40 + "';</script>"
        html = deck(content('<div class="visual big-number">3×</div>', extra=script))
        self.assertTrue(check_deck.check_html(html, ALLOWED)["ok"])

    def test_profile_hex_reads_and_normalizes(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        profile = tmp / "p.md"
        profile.write_text("| accent | `#abc` | `#12345678` |", encoding="utf-8")
        self.assertEqual(check_deck.profile_hex(profile), {"AABBCC", "123456"})

    def test_bundled_profile_colors_are_brand_colors(self):
        self.assertLessEqual(check_deck.profile_hex(check_deck.DEFAULT_PROFILE), set(check_deck.BRAND_HEX))


class ParserToleranceTest(unittest.TestCase):
    def test_stray_end_tag_and_unclosed_slide(self):
        html = '</div><section class="slide s-title"><h1>Hi</h1></span>'
        report = check_deck.check_html(html, ALLOWED)
        self.assertEqual(report, {"ok": True, "slides": 1, "findings": []})

    def test_nested_section_is_not_a_new_slide(self):
        html = deck('<section class="slide s-title"><section class="slide">x</section></section>')
        self.assertEqual(check_deck.check_html(html, ALLOWED)["slides"], 1)


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = check_deck.main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def test_clean_deck_exits_zero(self):
        code, out, err = self.run_main(_TEMPLATE)
        self.assertEqual((code, err), (0, ""))
        report = json.loads(out)
        self.assertTrue(report["ok"])
        self.assertEqual(report["deck"], str(_TEMPLATE))

    def test_findings_exit_one(self):
        path = self.tmp / "deck.html"
        path.write_text(deck(content("<p>x</p>")), encoding="utf-8")
        code, out, _ = self.run_main(path)
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["ok"])

    def test_custom_profile_extends_allowed_colors(self):
        path = self.tmp / "deck.html"
        path.write_text(deck(head="<style>a{color:#123456}</style>"), encoding="utf-8")
        profile = self.tmp / "p.md"
        profile.write_text("#123456", encoding="utf-8")
        self.assertEqual(self.run_main(path)[0], 1)
        self.assertEqual(self.run_main(path, "--profile", profile)[0], 0)

    def test_missing_deck_exits_two(self):
        code, out, err = self.run_main(self.tmp / "missing.html")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("error:", err)

    def test_missing_profile_exits_two(self):
        code, _, err = self.run_main(_TEMPLATE, "--profile", self.tmp / "missing.md")
        self.assertEqual(code, 2)
        self.assertIn("error:", err)


if __name__ == "__main__":
    unittest.main()
