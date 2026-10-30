#!/usr/bin/env python3
"""Adversarial cases for verify-bar.py, both polarities.

Each mutation is a bar chart that still renders - the defect is in geometry,
labels or ink, which no other gate reads. The positive half matters as much:
a checker that fires on an honest chart, or on the other shipped example
types, gets widened or switched off.

Exit: 0 all pass, 1 any failure.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

verify = __import__("verify-bar")

SHIPPED = sorted((ROOT / "assets").glob("example-bar*.html"))
GOOD_TEXT = (ROOT / "assets/example-bar.html").read_text(encoding="utf-8")
FAKE = Path("example-bar-fixture.html")

S1_RECT = ('<rect x="99" y="192" width="72" height="228" fill="rgba(77,77,77,0.15)" '
           'stroke="#4d4d4d" stroke-width="1" data-name="S1" data-value="72"/>')
S1_LABEL = 'data-for="S1">72</text>'
GROUP = '<g data-plot="bar" data-orient="vertical" data-domain="0 120" data-baseline="420" data-top="40">'
REF = ('<line x1="80" y1="103.3" x2="960" y2="103.3" stroke="#616161" stroke-width="1" '
       'stroke-dasharray="4,3" data-reference="100"/>')

failures = 0
count = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global failures, count
    count += 1
    if ok:
        print("OK: " + name)
    else:
        failures += 1
        print("FAIL: " + name + (" -- " + detail if detail else ""))


def findings_for(text: str, path: Path = FAKE) -> str:
    return "\n".join(verify.check_source(path, text))


def must_fire(name: str, old: str, new: str, fragment: str) -> None:
    if old not in GOOD_TEXT:
        check(name, False, "fixture drift: mutation target not found")
        return
    out = findings_for(GOOD_TEXT.replace(old, new, 1))
    check(name, fragment in out, "wanted %r in:\n%s" % (fragment, out))


def run_cli(*args: str):
    result = subprocess.run([sys.executable, str(ROOT / "scripts/verify-bar.py"), *args],
                            capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    # --- positive polarity: the honest chart passes -------------------------
    check("shipped bar examples exist (light, dark, full)", len(SHIPPED) == 3, str(SHIPPED))
    for path in SHIPPED:
        out = findings_for(path.read_text(encoding="utf-8"), path)
        check("shipped %s passes" % path.name, out == "", out)
    code, out = run_cli("--all")
    check("--all passes on the shipped set", code == 0 and "OK bar: 3 file(s)" in out, out)

    # --- negative polarity: each lie is named --------------------------------
    must_fire("height lie: a bar drawn taller than its value",
              S1_RECT, S1_RECT.replace('y="192"', 'y="160"').replace('height="228"', 'height="260"'),
              "not proportional to its value")
    must_fire("baseline lie: a bar floating above the zero baseline",
              S1_RECT, S1_RECT.replace('y="192"', 'y="180"'), "not on the zero baseline")
    must_fire("label mismatch: the printed number differs from the bound value",
              S1_LABEL, 'data-for="S1">27</text>', "prints '27' but is bound to 72")
    must_fire("label missing: a bar with no bound label",
              S1_LABEL, 'data-for="S9">72</text>', "prints no value label")
    must_fire("orphan label: a label bound to no bar",
              S1_LABEL, 'data-for="S9">72</text>', "bound to 'S9', which no bar declares")
    must_fire("label with two numbers is ambiguous",
              S1_LABEL, 'data-for="S1">72 of 88</text>', "more than one numeric token")
    must_fire("label with no number",
              S1_LABEL, 'data-for="S1">many</text>', "prints no number")
    must_fire("two labels for one bar",
              S1_LABEL, S1_LABEL + '<text x="1" y="1" data-for="S1">72</text>', "2 value labels")
    must_fire("truncated axis: the domain floor is raised above zero",
              'data-domain="0 120"', 'data-domain="40 120"', "starts at 40, not 0")
    must_fire("gridline: a full-width rule repeats values every bar prints",
              REF, REF + '<line x1="80" y1="230" x2="960" y2="230" stroke="rgba(23,23,23,0.08)"/>',
              "draws the same number twice")
    must_fire("value-axis line beside the bars",
              REF, REF + '<line x1="80" y1="40" x2="80" y2="420" stroke="#616161"/>',
              "value-axis line")
    must_fire("tick labels beside the bars",
              REF, REF + '<text x="72" y="361" text-anchor="end">20</text>', "numeric tick label")
    must_fire("rotated axis title",
              '<text x="80" y="28"', '<text transform="rotate(-90 24 230)" x="80" y="28"',
              "rotated text")
    must_fire("transform on a bound bar",
              S1_RECT, S1_RECT.replace("<rect ", '<rect transform="translate(0 40)" '), "carries transform")
    must_fire("style transform on a bound label",
              S1_LABEL, 'style="translate: 0 40px" ' + S1_LABEL, "the translate property")
    must_fire("transform on an ancestor group",
              GROUP, GROUP.replace("<g ", '<g transform="translate(0 40)" '), "an ancestor")
    must_fire("transform rule in a <style> block",
              "</style>", ".x { transform: translateY(40px); } </style>", "a CSS `transform` declaration")
    must_fire("reference line drawn off the bars' scale",
              REF, REF.replace('y1="103.3"', 'y1="140"').replace('y2="103.3"', 'y2="140"'),
              "off the bars' scale")
    must_fire("reference line without coordinates",
              REF, REF.replace('x1="80"', 'x1="x"'), "needs a numeric data-reference")
    must_fire("duplicate bar name",
              'data-name="S2"', 'data-name="S1"', "two bars are named 'S1'")
    must_fire("negative value",
              'data-value="95"', 'data-value="-95"', "negative value")
    must_fire("bar without a name",
              'data-name="S3" ', "", "needs data-name")
    must_fire("plot group missing its pixel scale",
              ' data-baseline="420"', "", "numeric data-domain")
    must_fire("unknown orientation",
              'data-orient="vertical"', 'data-orient="diagonal"', "neither 'vertical' nor 'horizontal'")
    must_fire("empty domain",
              'data-domain="0 120"', 'data-domain="0 0"', "empty")

    # --- event markers -----------------------------------------------------------
    S4_EVENT = '<g data-event="S4" data-event-label="API shipped late">'
    S4_RULE = '<line x1="465" y1="40" x2="465" y2="152"'
    check("event markers: the shipped chart carries S4 and S5 markers",
          GOOD_TEXT.count("data-event=") == 2)
    must_fire("event marker drawn beside its bar, not on the centre",
              S4_RULE, S4_RULE.replace('x1="465"', 'x1="470"').replace('x2="465"', 'x2="470"'),
              "is drawn at 470 but bar 'S4' is centred at 465")
    check("event marker 0.4px off the centre is accepted",
          findings_for(GOOD_TEXT.replace(S4_RULE, S4_RULE.replace('x1="465"', 'x1="465.4"')
                                         .replace('x2="465"', 'x2="465.4"'), 1)) == "")
    must_fire("event marker naming an unknown category",
              S4_EVENT, S4_EVENT.replace('data-event="S4"', 'data-event="S9"'),
              "names a category no bar carries")
    must_fire("event marker without a rule inside",
              S4_RULE, '<rect x="1" y="1" width="1" height="1"', "needs a data-event category and a <line>")
    must_fire("event marker that is not a straight rule",
              S4_RULE, S4_RULE.replace('x2="465"', 'x2="500"'), "must be a straight rule")
    by_tick = GOOD_TEXT.replace('data-name="S4"', 'data-name="bar-4"').replace(
        'data-for="S4"', 'data-for="bar-4"')
    check("event marker resolves a tick label that differs from the bar's data-name",
          findings_for(by_tick) == "", findings_for(by_tick))
    check("event marker on a tick label with no bar under it fails",
          "names a category no bar carries" in findings_for(
              by_tick.replace('data-event="S4"', 'data-event="S5x"')))
    check("the event rule is not mistaken for a value-axis line",
          "value-axis line" not in findings_for(GOOD_TEXT))
    # density cap: 17 bars
    many = GOOD_TEXT.replace("</g>", "".join(
        '<rect x="%d" y="400" width="4" height="20" data-name="X%d" data-value="6.3"/>'
        '<text data-for="X%d">6.3</text>' % (i, i, i) for i in range(9)) + "</g>", 1)
    check("density cap: 17 bars is a finding",
          "exceeds the cap of 16" in findings_for(many), findings_for(many))

    # fail closed
    check("fail closed: a bar example with no plot group",
          "exactly one" in findings_for("<svg><rect/></svg>"))
    check("fail closed: a bar example whose bars carry no data-value",
          "no verifiable bar" in findings_for(GOOD_TEXT.replace("data-value=", "data-v=")))
    broken = GOOD_TEXT.replace(GROUP, '<g data-plot="bar data-orient="vertical">')
    check("fail closed: an unclosed quote on the plot group",
          verify.check_source(FAKE, broken) != [])

    # --- horizontal orientation ----------------------------------------------
    horizontal = (
        '<svg><g data-plot="bar" data-orient="horizontal" data-domain="0 100" '
        'data-baseline="200" data-top="600">'
        '<line x1="200" y1="40" x2="200" y2="200" stroke="#616161"/>'
        '<rect x="200" y="50" width="200" height="20" data-name="A" data-value="50"/>'
        '<text x="410" y="64" data-for="A">50</text>'
        '<rect x="200" y="90" width="400" height="20" data-name="B" data-value="100"/>'
        '<text x="610" y="104" data-for="B">100</text>'
        '<line x1="400" y1="40" x2="400" y2="200" data-reference="50"/>'
        '</g></svg>')
    check("horizontal bars on a shared scale pass",
          findings_for(horizontal) == "", findings_for(horizontal))
    check("horizontal: a short bar is a finding",
          "not proportional" in findings_for(horizontal.replace('width="400"', 'width="300"')))
    grid = horizontal.replace("</g>", '<line x1="300" y1="40" x2="300" y2="200"/></g>')
    check("horizontal: a vertical gridline is a finding",
          "draws the same number twice" in findings_for(grid), findings_for(grid))
    axis = horizontal.replace("</g>", '<line x1="200" y1="100" x2="600" y2="100"/></g>')
    check("horizontal: a value-axis rule across the bars is a finding",
          "value-axis line" in findings_for(axis), findings_for(axis))
    ticks = horizontal.replace("</g>", '<text x="300" y="220">50</text></g>')
    check("horizontal: tick labels under the bars are a finding",
          "numeric tick label" in findings_for(ticks), findings_for(ticks))
    check("horizontal: the zero baseline rule alone passes",
          findings_for(horizontal) == "")

    horizontal_event = horizontal.replace(
        "</g>", '<g data-event="B"><line x1="200" y1="100" x2="600" y2="100"/></g></g>')
    check("horizontal: an event rule at the bar centre passes",
          findings_for(horizontal_event) == "", findings_for(horizontal_event))
    check("horizontal: an event rule off the bar centre fails",
          "is drawn at 90" in findings_for(horizontal_event.replace(
              'y1="100" x2="600" y2="100"/></g></g>', 'y1="90" x2="600" y2="90"/></g></g>')))

    # --- scope and CLI ---------------------------------------------------------
    check("a waterfall is out of scope for the bar checker",
          not verify.looks_like_bar(Path("example-waterfall.html"),
                                    (ROOT / "assets/example-waterfall.html").read_text(encoding="utf-8")))
    check("number(): NaN and None are unreadable",
          verify.number("nan") is None and verify.number(None) is None and verify.number("1,000") == 1000.0)
    check("css_moves_mark sees a property behind a comment",
          verify.css_moves_mark("/**/transform: x") is not None
          and verify.css_moves_mark("text-transform: uppercase") is None)

    code, out = run_cli()
    check("no arguments exits 2", code == 2, out)
    code, out = run_cli("/nonexistent/example-bar.html")
    check("a missing file exits 2", code == 2, out)
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "example-bar-bad.html"
        bad.write_text(GOOD_TEXT.replace(S1_LABEL, 'data-for="S1">27</text>'), encoding="utf-8")
        code, out = run_cli(str(bad))
        check("a bad file exits 1 and is named", code == 1 and "bound to 72" in out, out)
        other = Path(tmp) / "unrelated.html"
        other.write_text("<html><body>no chart</body></html>", encoding="utf-8")
        code, out = run_cli(str(other))
        check("an unrelated file is skipped, not passed off as verified",
              code == 0 and "no bar chart found" in out, out)
        undecodable = Path(tmp) / "example-bar-bytes.html"
        undecodable.write_bytes(b"\xff\xfe\x00bad")
        code, out = run_cli(str(undecodable))
        check("an unreadable file exits 2", code == 2, out)

    print()
    if failures:
        print("%d of %d case(s) failed." % (failures, count))
        return 1
    print("OK bar checker: %d case(s), both polarities" % count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
