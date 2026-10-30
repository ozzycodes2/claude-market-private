#!/usr/bin/env python3
"""Adversarial cases for verify-scatter.py, both polarities.

Every case is named for exactly what it asserts. The positive half matters as
much as the negative: a checker that fires on an honest scatter plot, on a
bubble chart or on a beeswarm gets widened or switched off. Fixtures are
strings mutated from one clean figure whose trend endpoints are computed here
by an independent least squares, and every mutation asserts that it changed
the text. CLI cases write to a per-process temporary directory outside the
repository.

Exit: 0 all pass, 1 any failure.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

verify = __import__("verify-scatter")

ASSETS = ROOT / "assets"
SHIPPED = [ASSETS / n for n in ("example-scatter.html", "example-scatter-dark.html",
                                "example-scatter-full.html")]
SCRIPT = ROOT / "scripts" / "verify-scatter.py"
MONO = "font-family=\"'SF Mono', monospace\""

# Scale: cx = 80 + 20*x, cy = 420 - 10*y.
PTS = [(1, 2), (3, 5), (5, 4), (7, 8), (9, 9), (6, 6)]


def cx(x): return 80 + 20 * x
def cy(y): return 420 - 10 * y


def ols(points):
    n = len(points)
    mx = sum(x for x, _ in points) / n
    my = sum(y for _, y in points) / n
    b = sum((x - mx) * (y - my) for x, y in points) / sum((x - mx) ** 2 for x, _ in points)
    return my - b * mx, b


def build() -> str:
    a, b = ols(PTS)
    circles = []
    for i, (x, y) in enumerate(PTS):
        name = ' data-name="Gamma"' if (x, y) == (9, 9) else ""
        circles.append('<circle cx="%g" cy="%g" r="5" fill="#f8f8f8"/>' % (cx(x), cy(y)))
        circles.append('<circle data-x="%g" data-y="%g"%s cx="%g" cy="%g" r="5" fill="rgba(77,77,77,0.2)" '
                       'stroke="%s" stroke-width="1"/>'
                       % (x, y, name, cx(x), cy(y), "#ef6306" if name else "#4d4d4d"))
    ticks = []
    for v in (1, 9):
        ticks.append('<text data-tick="x" data-value="%d" x="%g" y="448" fill="#4d4d4d" font-size="8" %s '
                     'text-anchor="middle">%d</text>' % (v, cx(v), MONO, v))
    for v in (2, 9):
        ticks.append('<text data-tick="y" data-value="%d" x="136" y="%g" fill="#4d4d4d" font-size="8" %s '
                     'text-anchor="end">%d</text>' % (v, cy(v) + 3, MONO, v))
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>t</title></head><body>
<svg viewBox="0 0 1000 500" xmlns="http://www.w3.org/2000/svg" role="img">
  <title>t</title>
  <rect width="100%%" height="100%%" fill="#f8f8f8"/>
  <text x="124" y="84" fill="#4d4d4d" font-size="8" %(M)s>Lead time, days</text>
  <line data-axis="y" x1="124" y1="%(ay1)g" x2="124" y2="%(ay2)g" stroke="#616161" stroke-width="1"/>
  <line data-axis="x" x1="%(ax1)g" y1="432" x2="%(ax2)g" y2="432" stroke="#616161" stroke-width="1"/>
  %(ticks)s
  <line data-ref="median" data-value="5.5" x1="%(ax1)g" y1="%(my)g" x2="%(ax2)g" y2="%(my)g" stroke="#616161" stroke-width="1" stroke-dasharray="4,3"/>
  <text data-ref="median" data-role="label" x="%(ax1)g" y="%(myl)g" fill="#4d4d4d" font-size="8" %(M)s>Median: 5.5 days</text>
  <line data-trend="ols" x1="%(tx1)g" y1="%(ty1)g" x2="%(tx2)g" y2="%(ty2)g" stroke="#616161" stroke-width="1.2"/>
  <text data-trend="ols" data-role="label" x="150" y="300" fill="#4d4d4d" font-size="8" %(M)s>Least squares fit</text>
  %(circles)s
  <text data-name="Gamma" data-role="label" x="%(gx)g" y="%(gy)g" fill="#171717" font-size="8" %(M)s text-anchor="middle">Gamma</text>
  <text data-role="source" x="124" y="488" fill="#4d4d4d" font-size="8" %(M)s>Source: test. Solid line: least squares fit. Dashed line: median.</text>
</svg></body></html>
""" % {
        "M": MONO, "ay1": cy(9), "ay2": cy(2), "ax1": cx(1), "ax2": cx(9), "ticks": "\n  ".join(ticks),
        "my": cy(5.5), "myl": cy(5.5) - 8,
        "tx1": cx(1), "ty1": cy(a + b * 1), "tx2": cx(9), "ty2": cy(a + b * 9),
        "circles": "\n  ".join(circles), "gx": cx(9) - 20, "gy": cy(9) - 4,
    }


CLEAN = build()


def mut(src: str, old: str, new: str) -> str:
    assert old in src, "stale mutation: %r not in fixture" % old
    return src.replace(old, new, 1)


class Harness:
    def __init__(self) -> None:
        self.count = 0
        self.failures = 0
        self.dir = Path(tempfile.mkdtemp(prefix="verify-scatter-test-"))

    def close(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.count += 1
        if not ok:
            self.failures += 1
            print("FAIL %s%s" % (name, (": " + detail) if detail else ""))

    def findings(self, src: str, name: str = "fixture.html") -> list:
        return verify.check_source_text(Path(name), src)

    def clean(self, name: str, src: str) -> None:
        got = self.findings(src)
        self.check(name, not got, "unexpected findings: %s" % got)

    def flags(self, name: str, src: str, needle: str) -> None:
        got = self.findings(src)
        self.check(name, any(needle in f for f in got), "wanted %r in %s" % (needle, got))

    def write(self, name: str, text: str) -> Path:
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p


def add(src: str, extra: str) -> str:
    return mut(src, "</svg>", extra + "</svg>")


def run_cases(h: Harness) -> int:
    h.clean("a clean figure passes", CLEAN)
    for path in SHIPPED:
        got = verify.check(path)
        h.check("shipped %s passes" % path.name, not got, str(got))

    # --- shared scales -----------------------------------------------------
    h.flags("a point nudged along x is caught",
            mut(CLEAN, 'cx="180" cy="380" r="5" fill="rgba', 'cx="192" cy="380" r="5" fill="rgba'),
            "shared x scale")
    h.flags("a point nudged along y is caught",
            mut(CLEAN, 'cx="180" cy="380" r="5" fill="rgba', 'cx="180" cy="392" r="5" fill="rgba'),
            "shared y scale")
    h.flags("all points sharing one x is refused",
            CLEAN.replace('data-x="1"', 'data-x="9"').replace('data-x="3"', 'data-x="9"')
            .replace('data-x="5"', 'data-x="9"').replace('data-x="7"', 'data-x="9"')
            .replace('data-x="6"', 'data-x="9"'), "flat")
    h.flags("a data circle with a non-numeric value is refused",
            mut(CLEAN, 'data-x="3"', 'data-x="three"'), "numeric data-x")
    h.flags("a size encoding on a plain scatter is refused",
            mut(CLEAN, 'data-x="3"', 'data-size="4" data-x="3"'), "bubble contract")
    h.flags("fewer than four points is refused",
            "<html><body><svg><circle data-x=\"1\" data-y=\"1\" cx=\"1\" cy=\"1\" r=\"1\"/></svg></body></html>",
            "Refusing to report OK")

    # --- range frame and ticks --------------------------------------------
    h.flags("a y axis longer than the data is caught",
            mut(CLEAN, 'y2="400"', 'y2="420"'), "range frame spans only min to max")
    h.flags("an x axis longer than the data is caught",
            mut(CLEAN, 'x1="100" y1="432" x2="260"', 'x1="100" y1="432" x2="300"'),
            "range frame spans only min to max")
    h.flags("a slanted y axis is refused",
            mut(CLEAN, 'x1="124" y1="330" x2="124"', 'x1="120" y1="330" x2="124"'), "must be vertical")
    h.flags("a slanted x axis is refused",
            mut(CLEAN, 'y1="432" x2="260" y2="432"', 'y1="432" x2="260" y2="436"'), "must be horizontal")
    h.flags("a missing axis is refused",
            mut(CLEAN, 'data-axis="x"', 'data-no="x"'), 'data-axis="x"')
    h.flags("an axis with no coordinates is refused",
            mut(CLEAN, 'data-axis="x" x1="100"', 'data-axis="x" xx="100"'), "numeric coordinates")
    h.flags("a tick printing a different number is caught",
            mut(CLEAN, ">9</text>\n  <text data-tick=\"y\" data-value=\"2\"", ">8</text>\n  <text data-tick=\"y\" data-value=\"2\""),
            "prints 8")
    h.flags("a tick drawn off its scale position is caught",
            mut(CLEAN, 'data-value="1" x="100"', 'data-value="1" x="130"'), "scale puts it")
    h.flags("a tick with no value is refused",
            mut(CLEAN, 'data-value="1" x="100"', 'data-value="" x="100"'), "numeric data-value")
    h.flags("fewer than two ticks on an axis is refused",
            mut(CLEAN, 'data-tick="x" data-value="1"', 'data-no="x" data-value="1"'), "at least two x ticks")
    h.flags("a missing tick at the data maximum is caught",
            mut(mut(CLEAN, 'data-value="9" x="136" y="333"', 'data-value="5" x="136" y="373"'), 'text-anchor="end">9<', 'text-anchor="end">5<'),
            "data maximum")

    # --- trend -------------------------------------------------------------
    a, b = ols(PTS)
    h.flags("a hand-drawn trend that is off the fit is caught",
            mut(CLEAN, 'y2="%g"' % cy(a + b * 9), 'y2="%g"' % (cy(a + b * 9) + 12)), "least squares fit")
    h.flags("a trend running past the data range is caught",
            mut(CLEAN, 'x2="260" y2="%g"' % cy(a + b * 9), 'x2="320" y2="%g"' % cy(a + b * 12)),
            "outside the data range")
    h.flags("an unbound diagonal line is refused as a hand-drawn trend",
            add(CLEAN, '<line x1="100" y1="400" x2="260" y2="330" stroke="#616161" stroke-dasharray="4,3"/>'),
            "not a bound fit")
    h.flags("a trend method other than ols is refused",
            mut(CLEAN, 'data-trend="ols" x1', 'data-trend="eyeball" x1'), "unsupported trend method")
    h.flags("a trend without a method in the source line is caught",
            mut(CLEAN, "Solid line: least squares fit. ", ""), "does not name the method")
    h.flags("a trend without a direct label is caught",
            mut(CLEAN, '<text data-trend="ols" data-role="label"', '<text data-trend="ols" data-role="note"'),
            "direct label")
    h.flags("a trend with non-numeric endpoints is refused",
            mut(CLEAN, 'data-trend="ols" x1="100"', 'data-trend="ols" x1="a"'), "numeric endpoints")
    no_trend = re.sub(r'<line data-trend="ols"[^>]*/>', "", CLEAN)
    no_trend = mut(no_trend, "Solid line: least squares fit. ", "")
    no_trend = re.sub(r'<text data-trend="ols"[^>]*>[^<]*</text>', "", no_trend)
    h.clean("a figure with no trend line passes", no_trend)

    # --- comparison --------------------------------------------------------
    h.flags("a missing comparison line is caught",
            mut(CLEAN, 'data-ref="median" data-value', 'data-no="median" data-value'), "no comparison line")
    h.flags("a median that is not the median is caught",
            mut(CLEAN, 'data-value="5.5"', 'data-value="6.5"'), "bound points give 5.5")
    h.flags("a reference drawn off its scale position is caught",
            mut(CLEAN, 'y1="365" x2="260" y2="365"', 'y1="375" x2="260" y2="375"'), "scale puts it")
    h.flags("a diagonal reference is refused",
            mut(CLEAN, 'y1="365" x2="260" y2="365"', 'y1="365" x2="260" y2="375"'), "horizontal or vertical")
    h.flags("a reference that is not dashed 4,3 is caught",
            mut(CLEAN, 'stroke-dasharray="4,3"', 'stroke-dasharray="1,1"'), "dashed 4,3")
    h.flags("a reference without a label is caught",
            mut(CLEAN, 'data-ref="median" data-role="label"', 'data-ref="median" data-role="note"'), "direct label")
    h.flags("a reference with no value is refused",
            mut(CLEAN, 'data-value="5.5"', 'data-value=""'), "numeric x1/y1/x2/y2 and data-value")
    h.clean("a vertical target reference on the x scale passes",
            add(CLEAN, '<line data-ref="target" data-value="5" x1="180" y1="330" x2="180" y2="400" stroke="#616161" stroke-dasharray="4,3"/>'
                '<text data-ref="target" data-role="label" x="184" y="326" font-size="8">Target</text>'))

    # --- labels ------------------------------------------------------------
    h.flags("a named point with no label is caught",
            mut(CLEAN, '<text data-name="Gamma" data-role="label"', '<text data-name="Gamma" data-role="note"'),
            "exactly one direct label")
    h.flags("a label whose text differs from the name is caught",
            mut(CLEAN, ">Gamma</text>", ">Delta</text>"), "reads 'Delta'")
    h.flags("a label bound to an unknown point is caught",
            add(CLEAN, '<text data-name="Zed" data-role="label" x="1" y="1">Zed</text>'), "unknown point")
    h.flags("a label far from its point is caught",
            mut(CLEAN, 'x="240" y="326"', 'x="240" y="220"'), "from its point")
    h.flags("a label with no coordinates is refused",
            mut(CLEAN, 'data-name="Gamma" data-role="label" x="240" y="326"', 'data-name="Gamma" data-role="label"'),
            "numeric x and y")
    two = mut(CLEAN, 'data-x="7" data-y="8"', 'data-x="7" data-y="8" data-name="Beta"')
    two = add(two, '<text data-name="Beta" data-role="label" x="250" y="336" font-size="8">Beta</text>')
    h.flags("a label nearer another named point is caught", two, "nearer")
    h.flags("two points sharing a name are caught",
            mut(CLEAN, 'data-x="7" data-y="8"', 'data-x="7" data-y="8" data-name="Gamma"'), "more than one point")
    h.flags("an empty name is caught",
            mut(CLEAN, 'data-x="7" data-y="8"', 'data-x="7" data-y="8" data-name=" "'), "empty data-name")
    h.flags("a LEGEND heading is caught", add(CLEAN, '<text x="40" y="478" font-size="8">Legend</text>'), "LEGEND heading")
    h.flags("a legend element is caught", add(CLEAN, '<g data-role="legend"></g>'), "legend element")
    h.flags("a key repeating a direct label is caught",
            add(CLEAN, '<text x="72" y="496" font-size="8">Gamma team</text>'), "repeats a direct label")

    # --- furniture and caps ------------------------------------------------
    h.flags("rotated text is caught",
            mut(CLEAN, '<text x="124" y="84"', '<text transform="rotate(-90 124 84)" x="124" y="84"'), "rotated text")
    h.flags("a transform on a point is caught",
            mut(CLEAN, '<circle data-x="3"', '<circle transform="translate(0 3)" data-x="3"'), "transform on <circle>")
    h.flags("a style that rotates is caught",
            mut(CLEAN, '<text x="124" y="84"', '<text style="rotate: 9deg" x="124" y="84"'), "style moves")
    h.flags("vertical writing mode is caught",
            mut(CLEAN, '<text x="124" y="84"', '<text writing-mode="vertical-rl" x="124" y="84"'), "vertical text")
    h.flags("accent text is caught",
            mut(CLEAN, 'fill="#171717" font-size="8"', 'fill="#ef6306" font-size="8"'), "accent")
    h.flags("a second accent point is caught",
            mut(CLEAN, 'r="5" fill="rgba(77,77,77,0.2)" stroke="#4d4d4d"', 'r="5" fill="rgba(77,77,77,0.2)" stroke="#ef6306"'),
            "more than one accent point")
    h_line = '<line x1="100" y1="%d" x2="260" y2="%d" stroke="rgba(23,23,23,0.08)"/>'
    v_line = '<line x1="%d" y1="330" x2="%d" y2="420" stroke="rgba(23,23,23,0.08)"/>'
    h.clean("a few faint horizontal gridlines are allowed",
            add(CLEAN, h_line % (350, 350) + h_line % (370, 370)))
    h.flags("a full grid is caught",
            add(CLEAN, h_line % (350, 350) + v_line % (140, 140)), "full grid")
    h.flags("a fifth gridline is caught",
            add(CLEAN, "".join(h_line % (y, y) for y in (340, 350, 360, 370, 390))), "5 gridlines")
    h.flags("a strong gridline is caught",
            add(CLEAN, '<line x1="100" y1="350" x2="260" y2="350" stroke="#616161"/>'), "ink at 0.08 or fainter")
    def capped(extra_count: int) -> list:
        extra = "".join('<circle data-x="%d" data-y="%d" cx="%d" cy="%d" r="2"/>'
                        % (1 + i % 9, 2 + i % 7, cx(1 + i % 9), cy(2 + i % 7))
                        for i in range(extra_count))
        doc = verify.parse_document(add(CLEAN, extra))
        out: list = []
        pts = verify.parse_points(doc, out, "f.html")
        verify.check_furniture(doc, pts, out, "f.html")
        return out

    h.check("more than 300 points is caught",
            any("at most 300" in f for f in capped(295)), str(capped(295)))
    h.check("exactly 300 points passes the cap",
            not any("at most 300" in f for f in capped(294)), str(capped(294)))
    h.flags("a missing source line is caught",
            mut(CLEAN, 'data-role="source"', 'data-role="note"'), "source")

    # --- scope treaty ------------------------------------------------------
    h.check("a bubble circle is out of scope",
            not verify.looks_like_scatter(Path("a.html"), '<circle data-x="1" data-y="2" data-size="3" cx="1"/>'))
    h.check("a beeswarm dot is out of scope",
            not verify.looks_like_scatter(Path("a.html"), '<circle data-value="1" data-x="1" data-y="2"/>'))
    h.check("a plain bound point claims the file",
            verify.looks_like_scatter(Path("a.html"), '<circle data-x="1" data-y="2" cx="1"/>'))
    h.check("a commented-out point claims nothing",
            not verify.looks_like_scatter(Path("a.html"), '<!-- <circle data-x="1" data-y="2"/> -->'))
    h.check("the example-scatter filename claims the file",
            verify.looks_like_scatter(Path("example-scatter-q.html"), ""))
    for path in sorted(ASSETS.glob("*.html")):
        if path.name.startswith("example-scatter"):
            continue
        if verify.looks_like_scatter(path, path.read_text(encoding="utf-8")):
            h.check("sibling file %s is not claimed" % path.name, False, "claimed by verify-scatter")
    h.check("--all globs only example-scatter files",
            all(p.name.startswith("example-scatter") for p in verify.targets(
                type("A", (), {"all": True, "paths": []})())))
    h.check("median of an odd count is the middle value", verify.median([3, 1, 2]) == 2)
    h.check("median of an even count is the mean of the middle pair", verify.median([4, 1, 2, 3]) == 2.5)

    # --- CLI ---------------------------------------------------------------
    def cli(*args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True)

    good = h.write("example-scatter-good.html", CLEAN)
    bad = h.write("example-scatter-bad.html", mut(CLEAN, 'data-value="5.5"', 'data-value="6.5"'))
    other = h.write("notes.html", "<html><body>nothing</body></html>")
    r = cli(str(good))
    h.check("CLI exits 0 on a clean file", r.returncode == 0 and r.stdout.startswith("OK scatter"), r.stdout)
    r = cli(str(bad))
    h.check("CLI exits 1 on a finding", r.returncode == 1 and "finding(s)" in r.stdout, r.stdout)
    r = cli(str(other))
    h.check("CLI reports an out-of-scope file honestly",
            r.returncode == 0 and "no scatter plot found" in r.stdout, r.stdout)
    r = cli()
    h.check("CLI exits 2 with no arguments", r.returncode == 2, str(r.returncode))
    r = cli(str(h.dir / "missing.html"))
    h.check("CLI exits 2 on an unreadable path", r.returncode == 2, str(r.returncode))
    r = cli("--all")
    h.check("CLI --all passes on the shipped examples", r.returncode == 0, r.stdout)
    binary = h.dir / "binary.html"
    binary.write_bytes(b"\xff\xfe\x00")
    r = cli(str(binary))
    h.check("CLI exits 2 on an undecodable file", r.returncode == 2, str(r.returncode))
    h.check("fixtures are written outside the repository",
            not str(h.dir).startswith(str(ROOT)), "fixture dir %s" % h.dir)

    print()
    if h.failures:
        print("%d of %d case(s) failed." % (h.failures, h.count))
        return 1
    print("OK scatter checker: %d case(s), both polarities" % h.count)
    return 0


def main() -> int:
    h = Harness()
    try:
        return run_cases(h)
    finally:
        h.close()


if __name__ == "__main__":
    raise SystemExit(main())
