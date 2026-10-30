#!/usr/bin/env python3
"""Adversarial cases for verify-gantt.py, both polarities.

Each mutation is a Gantt chart that still renders - the defect is in geometry
or labelling, which no other gate reads. The positive half matters as much: a
checker that fires on an honest plan gets widened or switched off.

Exit: 0 all pass, 1 any failure.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

verify = __import__("verify-gantt")

SHIPPED = sorted((ROOT / "assets").glob("example-gantt*.html"))
GOOD_TEXT = (ROOT / "assets/example-gantt.html").read_text(encoding="utf-8")
FAKE = Path("example-gantt-fixture.html")

WIRE = ('<rect x="389" y="192" width="126" height="24" rx="4" fill="rgba(77,77,77,0.15)" '
        'stroke="#4d4d4d" stroke-width="1" data-name="Wireframes" data-start="3" data-end="5"/>')
GROUP = '<g data-plot="gantt" data-domain="0 12" data-range="200 956">'
TODAY = ('<line x1="515" y1="60" x2="515" y2="416" stroke="#616161" stroke-width="1" '
         'stroke-dasharray="4,3" data-at="5" data-kind="today"/>')
WIRE_NAME = '>Wireframes</text>'

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
    result = subprocess.run([sys.executable, str(ROOT / "scripts/verify-gantt.py"), *args],
                            capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    # --- positive polarity ---------------------------------------------------
    check("shipped gantt examples exist (light, dark, full)", len(SHIPPED) == 3, str(SHIPPED))
    for path in SHIPPED:
        out = findings_for(path.read_text(encoding="utf-8"), path)
        check("shipped %s passes" % path.name, out == "", out)
    code, out = run_cli("--all")
    check("--all passes on the shipped set", code == 0 and "OK gantt: 3 file(s)" in out, out)
    check("a duration inside a bar is allowed",
          findings_for(GOOD_TEXT.replace(
              "</g>", '<text x="400" y="208">2 wk</text></g>', 1)) == "")

    # --- negative polarity ---------------------------------------------------
    must_fire("start lie: a bar drawn earlier than its start date",
              WIRE, WIRE.replace('x="389"', 'x="326"').replace('width="126"', 'width="189"'),
              "left edge is at x=326")
    must_fire("duration lie: a bar stretched past its end date",
              WIRE, WIRE.replace('width="126"', 'width="200"'), "right edge is at x=589")
    must_fire("task name printed again inside its bar",
              WIRE, WIRE + '<text x="400" y="208">Wireframes</text>', "printed 2 times")
    must_fire("other text inside a bar is not a duration",
              WIRE, WIRE + '<text x="400" y="208">GATE</text>', "in-bar text may carry only a duration")
    must_fire("task name missing from the left column",
              WIRE_NAME, ">Wireframe set</text>", "printed 0 times")
    must_fire("bar ends before it starts",
              'data-start="3" data-end="5"', 'data-start="5" data-end="3"', "not a forward span")
    must_fire("bar outside the plan domain",
              'data-start="3" data-end="5"', 'data-start="3" data-end="15"', "not a forward span")
    must_fire("duplicate task name",
              'data-name="Prototype"', 'data-name="Wireframes"', "two tasks are named")
    must_fire("task bar missing its dates",
              WIRE, WIRE.replace('data-start="3" ', ""), "a task bar needs data-name")
    must_fire("today line off the time scale",
              TODAY, TODAY.replace('x1="515"', 'x1="480"').replace('x2="515"', 'x2="480"'),
              "the today line")
    must_fire("today line that is not vertical",
              TODAY, TODAY.replace('x2="515"', 'x2="560"'), "the today line")
    must_fire("period line with a bad kind",
              'data-kind="period"', 'data-kind="week"', "a time line needs")
    must_fire("two today markers",
              TODAY, TODAY + TODAY, "2 today markers")
    must_fire("transform on a bound bar",
              WIRE, WIRE.replace("<rect ", '<rect transform="translate(40 0)" '), "carries transform")
    must_fire("transform on an ancestor group",
              GROUP, GROUP.replace("<g ", '<g style="translate: 40px 0" '), "an ancestor")
    must_fire("transform rule in a <style> block",
              "</style>", ".x { rotate: 4deg; } </style>", "a CSS `rotate` declaration")
    must_fire("rotated text",
              WIRE_NAME, WIRE_NAME.replace(">Wireframes", ' transform="rotate(-90 20 208)">Wireframes'),
              "rotated text")
    must_fire("plot group missing its range",
              ' data-range="200 956"', "", "numeric data-domain and data-range")
    must_fire("reversed range",
              'data-range="200 956"', 'data-range="956 200"', "empty or reversed")

    # density cap: 25 tasks
    extra = "".join(
        '<rect x="200" y="%d" width="63" height="4" data-name="T%d" data-start="0" data-end="1"/>'
        '<text x="20" y="%d">T%d</text>' % (420 + i * 4, i, 420 + i * 4, i) for i in range(18))
    many = GOOD_TEXT.replace("</g>", extra + "</g>", 1)
    check("density cap: 25 tasks is a finding",
          "exceeds the cap of 24" in findings_for(many), findings_for(many))

    # fail closed
    check("fail closed: a gantt example with no plot group",
          "exactly one" in findings_for("<svg><rect/></svg>"))
    check("fail closed: a plot with no task bars",
          "no verifiable task" in findings_for(
              GOOD_TEXT.replace("data-start=", "data-s=").replace("data-end=", "data-e=")))
    broken = GOOD_TEXT.replace(GROUP, '<g data-plot="gantt data-domain="0 12">')
    check("fail closed: an unclosed quote on the plot group",
          verify.check_source(FAKE, broken) != [])

    # --- scope, helpers and CLI ---------------------------------------------
    check("a bar chart is out of scope for the gantt checker",
          not verify.looks_like_gantt(Path("example-bar.html"),
                                      (ROOT / "assets/example-bar.html").read_text(encoding="utf-8")))
    check("number(): NaN and None are unreadable",
          verify.number("nan") is None and verify.number(None) is None)
    check("printed_number reads one token and refuses two",
          verify.printed_number("12 days")[0] == 12.0
          and verify.printed_number("1 of 2")[0] is None
          and verify.printed_number("none")[0] is None)

    code, out = run_cli()
    check("no arguments exits 2", code == 2, out)
    code, out = run_cli("/nonexistent/example-gantt.html")
    check("a missing file exits 2", code == 2, out)
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "example-gantt-bad.html"
        bad.write_text(GOOD_TEXT.replace(WIRE, WIRE + '<text x="400" y="208">Wireframes</text>'),
                       encoding="utf-8")
        code, out = run_cli(str(bad))
        check("a bad file exits 1 and is named", code == 1 and "printed 2 times" in out, out)
        other = Path(tmp) / "unrelated.html"
        other.write_text("<html><body>no chart</body></html>", encoding="utf-8")
        code, out = run_cli(str(other))
        check("an unrelated file is skipped, not passed off as verified",
              code == 0 and "no Gantt chart found" in out, out)
        undecodable = Path(tmp) / "example-gantt-bytes.html"
        undecodable.write_bytes(b"\xff\xfe\x00bad")
        code, out = run_cli(str(undecodable))
        check("an unreadable file exits 2", code == 2, out)

    print()
    if failures:
        print("%d of %d case(s) failed." % (failures, count))
        return 1
    print("OK gantt checker: %d case(s), both polarities" % count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
