#!/usr/bin/env python3
"""Adversarial cases for verify-line.py, both polarities.

Every case is named for exactly what it asserts. The positive half matters as
much as the negative: a checker that fires on an honest line chart gets
widened or switched off, and then it guards nothing. Fixtures are strings
mutated from one clean figure; every mutation asserts that it changed the
text, so a stale replacement cannot silently turn a negative case into a
second positive one. Nothing is written to disk except the CLI cases, which
use a per-process temporary directory outside the repository.

Exit: 0 all pass, 1 any failure.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

verify = __import__("verify-line")

ASSETS = ROOT / "assets"
SHIPPED = [ASSETS / n for n in ("example-line.html", "example-line-dark.html",
                                "example-line-full.html")]
SCRIPT = ROOT / "scripts" / "verify-line.py"

MONO = "font-family=\"'SF Mono', monospace\""

# Scale: y = 420 - 4*v, x = 80 + 56*i. Series A 10..40, series B 5..15.
CLEAN = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>t</title></head><body>
<svg viewBox="0 0 1000 500" xmlns="http://www.w3.org/2000/svg" role="img">
  <title>t</title>
  <rect width="100%" height="100%" fill="#f8f8f8"/>
  <text x="64" y="60" fill="#4d4d4d" font-size="8" {M}>Signups per week</text>
  <line data-axis="y" x1="64" y1="260" x2="64" y2="400" stroke="#616161" stroke-width="1"/>
  <line data-axis="x" x1="80" y1="428" x2="248" y2="428" stroke="#616161" stroke-width="1"/>
  <text data-tick="y" data-value="40" x="56" y="263" fill="#4d4d4d" font-size="8" {M} text-anchor="end">40</text>
  <text data-tick="y" data-value="5" x="56" y="403" fill="#4d4d4d" font-size="8" {M} text-anchor="end">5</text>
  <line data-ref="target" data-value="25" x1="80" y1="320" x2="248" y2="320" stroke="#616161" stroke-width="1" stroke-dasharray="4,3"/>
  <text data-ref="target" data-role="label" x="264" y="316" fill="#4d4d4d" font-size="8" {M}>Target: 25</text>
  <polyline data-line="Alpha" data-values="10,20,30,40" points="80,380 136,340 192,300 248,260" fill="none" stroke="#ef6306" stroke-width="1.8"/>
  <polyline data-line="Beta" data-values="5,8,12,15" points="80,400 136,388 192,372 248,360" fill="none" stroke="#4d4d4d" stroke-width="1.2" stroke-dasharray="6,3"/>
  <text data-line="Alpha" data-role="name" x="264" y="264" fill="#171717" font-size="11" font-weight="600">Alpha</text>
  <text data-line="Beta" data-role="name" x="264" y="364" fill="#4d4d4d" font-size="11" font-weight="500">Beta</text>
  <text data-role="source" x="64" y="484" fill="#4d4d4d" font-size="8" {M}>Source: test. Y axis spans 5 to 40, not from zero.</text>
</svg></body></html>
""".replace("{M}", MONO)


def mut(src: str, old: str, new: str) -> str:
    assert old in src, "stale mutation: %r not in fixture" % old
    return src.replace(old, new, 1)


class Harness:
    def __init__(self) -> None:
        self.count = 0
        self.failures = 0
        self.dir = Path(tempfile.mkdtemp(prefix="verify-line-test-"))

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

    def flags(self, name: str, src: str, needle: str, fname: str = "fixture.html") -> None:
        got = self.findings(src, fname)
        self.check(name, any(needle in f for f in got),
                   "wanted %r in %s" % (needle, got))

    def write(self, name: str, text: str) -> Path:
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p


def run_cases(h: Harness) -> int:
    # --- positive polarity -------------------------------------------------
    h.clean("a clean figure passes", CLEAN)
    for path in SHIPPED:
        got = verify.check(path)
        h.check("shipped %s passes" % path.name, not got, str(got))

    # --- shared scales -----------------------------------------------------
    h.flags("a vertex nudged off the y scale is caught",
            mut(CLEAN, "136,340 192,300", "136,340 192,310"), "shared scale")
    h.flags("a vertex off the shared x grid is caught",
            mut(CLEAN, "80,400 136,388 192,372", "80,400 140,388 192,372"), "share one x grid")
    h.flags("an uneven x pitch is caught",
            mut(mut(CLEAN, "192,300 248,260", "196,300 248,260"),
                "192,372 248,360", "196,372 248,360"), "even pitch")
    h.flags("a declared value that disagrees with the drawing is caught",
            mut(CLEAN, 'data-values="10,20,30,40"', 'data-values="10,20,35,40"'), "shared scale")
    h.flags("a flat y scale is refused",
            mut(mut(CLEAN, 'data-values="10,20,30,40"', 'data-values="10,10,10,10"'),
                'data-values="5,8,12,15"', 'data-values="10,10,10,10"'), "flat")
    h.flags("series with different vertex counts are refused",
            mut(mut(CLEAN, 'data-values="5,8,12,15"', 'data-values="5,8,12"'),
                "80,400 136,388 192,372 248,360", "80,400 136,388 192,372"), "different vertex counts")
    h.flags("values and vertices that disagree in count are refused",
            mut(CLEAN, 'data-values="5,8,12,15"', 'data-values="5,8,12"'), "draws 4 vertices")
    h.flags("non-numeric values are refused",
            mut(CLEAN, 'data-values="5,8,12,15"', 'data-values="5,x,12,15"'), "numeric data-values")
    h.flags("unparseable points are refused",
            mut(CLEAN, "80,400 136,388 192,372 248,360", "80,400 136,388 192"), "parseable points")
    h.flags("an empty series name is refused",
            mut(CLEAN, '<polyline data-line="Beta"', '<polyline data-line=" "'), "empty data-line")
    h.flags("two polylines with one name are refused",
            mut(CLEAN, '<polyline data-line="Beta"', '<polyline data-line="Alpha"'), "share the series name")
    h.flags("a single vertex per series is refused",
            mut(mut(mut(mut(CLEAN, 'data-values="10,20,30,40"', 'data-values="10"'),
                "80,380 136,340 192,300 248,260", "80,380"),
                'data-values="5,8,12,15"', 'data-values="5"'),
                "80,400 136,388 192,372 248,360", "80,400"), "at least two vertices")
    h.flags("a right-to-left x axis is refused",
            mut(mut(CLEAN, "80,380 136,340 192,300 248,260", "248,380 192,340 136,300 80,260"),
                "80,400 136,388 192,372 248,360", "248,400 192,388 136,372 80,360"),
            "increase left to right")

    # --- range frame and ticks --------------------------------------------
    h.flags("a y axis longer than the data is caught",
            mut(CLEAN, 'x2="64" y2="400"', 'x2="64" y2="420"'), "range frame spans only min to max")
    h.flags("a y axis shorter than the data is caught",
            mut(CLEAN, 'y1="260" x2="64"', 'y1="280" x2="64"'), "range frame spans only min to max")
    h.flags("a slanted y axis is refused",
            mut(CLEAN, 'x1="64" y1="260" x2="64"', 'x1="60" y1="260" x2="64"'), "must be vertical")
    h.flags("an x axis longer than the data is caught",
            mut(CLEAN, 'x1="80" y1="428" x2="248"', 'x1="80" y1="428" x2="300"'), "first to last point")
    h.flags("a slanted x axis is refused",
            mut(CLEAN, 'y1="428" x2="248" y2="428"', 'y1="428" x2="248" y2="430"'), "must be horizontal")
    h.flags("a missing y axis is refused",
            mut(CLEAN, 'data-axis="y"', 'data-x="y"'), 'data-axis="y"')
    h.flags("a tick printing a different number than it declares is caught",
            mut(CLEAN, ">40</text>", ">41</text>"), "prints 41")
    h.flags("a tick drawn off its scale position is caught",
            mut(CLEAN, 'y="263"', 'y="300"'), "scale puts it")
    h.flags("a tick with no numeric value is refused",
            mut(CLEAN, 'data-value="40" x="56"', 'data-value="" x="56"'), "numeric data-value")
    h.flags("fewer than two bound ticks is refused",
            mut(CLEAN, 'data-tick="y" data-value="5"', 'data-x="y" data-value="5"'), "at least two y ticks")
    h.flags("a missing tick at the data maximum is caught",
            mut(mut(CLEAN, 'data-value="40" x="56" y="263"', 'data-value="30" x="56" y="303"'),
                ">40</text>", ">30</text>"), "data maximum")

    # --- end labels --------------------------------------------------------
    h.flags("a missing end label is caught",
            mut(CLEAN, 'data-line="Beta" data-role="name"', 'data-x="Beta" data-role="name"'),
            "exactly one end label")
    h.flags("an end label whose text differs from its series is caught",
            mut(CLEAN, ">Beta</text>", ">Gamma</text>"), "reads 'Gamma'")
    h.flags("a label bound to an unknown series is caught",
            mut(CLEAN, 'data-line="Beta" data-role="name"', 'data-line="Zeta" data-role="name"'),
            "unknown series")
    h.flags("an end label left of its last vertex is caught",
            mut(CLEAN, 'data-line="Alpha" data-role="name" x="264"', 'data-line="Alpha" data-role="name" x="240"'),
            "to the right")
    h.flags("an end label far from its last vertex is caught",
            mut(CLEAN, 'data-line="Alpha" data-role="name" x="264"', 'data-line="Alpha" data-role="name" x="400"'),
            "to the right")
    h.flags("an end label off its row is caught",
            mut(CLEAN, 'y="264" fill="#171717"', 'y="290" fill="#171717"'), "off its last vertex's row")
    h.flags("labels swapped between rows are caught",
            mut(mut(CLEAN, 'data-line="Alpha" data-role="name" x="264" y="264"',
                    'data-line="Alpha" data-role="name" x="264" y="3640"'),
                'data-line="Beta" data-role="name" x="264" y="364"',
                'data-line="Beta" data-role="name" x="264" y="264"'), "nearer the last point")
    h.flags("an end label with no coordinates is refused",
            mut(CLEAN, 'data-line="Beta" data-role="name" x="264" y="364"', 'data-line="Beta" data-role="name" x="264"'),
            "numeric x and y")
    crowded = mut(mut(CLEAN, 'data-values="5,8,12,15"', 'data-values="10,20,30,38"'),
                  "80,400 136,388 192,372 248,360", "80,380 136,340 192,300 248,268")
    crowded = mut(crowded, 'y="364" fill="#4d4d4d" font-size="11"', 'y="272" fill="#4d4d4d" font-size="11"')
    h.flags("end labels closer than 10px are caught", crowded, "too many series")

    # --- legend ------------------------------------------------------------
    h.flags("a LEGEND heading is caught",
            mut(CLEAN, "</svg>", '<text x="40" y="478" font-size="8">Legend</text></svg>'), "LEGEND heading")
    h.flags("a legend element is caught",
            mut(CLEAN, "</svg>", '<g data-role="legend"></g></svg>'), "legend element")
    h.flags("a key repeating a direct label is caught",
            mut(CLEAN, "</svg>", '<text x="72" y="496" font-size="8">Beta</text></svg>'), "repeats a direct label")

    # --- comparison line ---------------------------------------------------
    h.flags("a missing comparison line is caught",
            mut(CLEAN, '<line data-ref="target"', '<line data-xx="target"'), "no comparison line")
    h.flags("a reference line off its scale position is caught",
            mut(CLEAN, 'y1="320" x2="248" y2="320"', 'y1="330" x2="248" y2="330"'), "scale puts it")
    h.flags("a slanted reference line is caught",
            mut(CLEAN, 'y1="320" x2="248" y2="320"', 'y1="320" x2="248" y2="324"'), "must be horizontal")
    h.flags("a reference line that is not dashed 4,3 is caught",
            mut(CLEAN, 'stroke-dasharray="4,3"', 'stroke-dasharray="2,3"'), "dashed 4,3")
    h.flags("a reference line without a label is caught",
            mut(CLEAN, 'data-ref="target" data-role="label"', 'data-ref="target" data-role="note"'), "direct label")
    h.flags("a reference label away from its line is caught",
            mut(CLEAN, 'x="264" y="316"', 'x="264" y="360"'), "not on its line")
    h.flags("a reference line with no numeric value is refused",
            mut(CLEAN, 'data-value="25"', 'data-value=""'), "numeric x1/y1/x2/y2 and data-value")

    # --- furniture ---------------------------------------------------------
    h.flags("rotated text is caught",
            mut(CLEAN, '<text x="64" y="60"', '<text transform="rotate(-90 64 60)" x="64" y="60"'), "rotated text")
    h.flags("any transform is caught",
            mut(CLEAN, '<polyline data-line="Beta"', '<polyline transform="translate(0 9)" data-line="Beta"'),
            "transform on <polyline>")
    h.flags("a style that rotates is caught",
            mut(CLEAN, '<text x="64" y="60"', '<text style="transform: rotate(9deg)" x="64" y="60"'), "style moves")
    h.flags("vertical writing mode is caught",
            mut(CLEAN, '<text x="64" y="60"', '<text writing-mode="vertical-rl" x="64" y="60"'), "vertical text")
    h.flags("an area fill under a one-dimensional series is caught",
            mut(CLEAN, "</svg>", '<polygon points="80,380 248,260 248,420 80,420" fill="rgba(239,99,6,0.06)"/></svg>'),
            "filled area")
    h.clean("a cumulative area is allowed when declared",
            mut(CLEAN, "</svg>", '<polygon data-area="cumulative" points="80,380 248,260 248,420 80,420" fill="rgba(23,23,23,0.06)"/></svg>'))
    grid = '<line x1="80" y1="%d" x2="248" y2="%d" stroke="rgba(23,23,23,0.08)" stroke-width="0.8"/>'
    four = "".join(grid % (y, y) for y in (300, 340, 360, 380))
    h.clean("up to four faint gridlines are allowed", mut(CLEAN, "</svg>", four + "</svg>"))
    h.flags("a fifth gridline is caught",
            mut(CLEAN, "</svg>", four + grid % (390, 390) + "</svg>"), "5 gridlines")
    h.flags("a strong gridline is caught",
            mut(CLEAN, "</svg>", '<line x1="80" y1="340" x2="248" y2="340" stroke="#616161"/></svg>'),
            "ink at 0.08 or fainter")
    h.flags("a series fainter than the ink floor is caught",
            mut(CLEAN, 'stroke="#4d4d4d" stroke-width="1.2"', 'stroke="rgba(23,23,23,0.4)" stroke-width="1.2"'),
            "ink floor")
    h.clean("a series at the ink floor is allowed",
            mut(CLEAN, 'stroke="#4d4d4d" stroke-width="1.2"', 'stroke="rgba(23,23,23,0.53)" stroke-width="1.2"'))
    h.flags("two accent series are caught",
            mut(CLEAN, 'stroke="#4d4d4d" stroke-width="1.2"', 'stroke="#ef6306" stroke-width="1.2"'),
            "accent series")
    h.flags("text painted in the accent is caught",
            mut(CLEAN, 'fill="#171717" font-size="11"', 'fill="#ef6306" font-size="11"'), "accent")
    seven = CLEAN
    for i in range(5):
        seven = mut(seven, "</svg>",
                    '<polyline data-line="S%d" data-values="5,8,12,15" points="80,400 136,388 192,372 248,360" fill="none" stroke="#4d4d4d"/></svg>' % i)
    h.flags("more than six series are caught", seven, "at most 6")

    # --- source line -------------------------------------------------------
    h.flags("a missing source line is caught",
            mut(CLEAN, 'data-role="source"', 'data-role="note"'), "one <text data-role=\"source\">")
    h.flags("a truncated axis with a silent source line is caught",
            mut(CLEAN, " Y axis spans 5 to 40, not from zero.", ""), "does not reach zero")
    zero = mut(mut(mut(CLEAN, 'data-values="5,8,12,15"', 'data-values="0,8,12,15"'),
                   "80,400 136,388", "80,420 136,388"),
               "5</text>", "0</text>")
    zero = mut(zero, 'data-value="5"', 'data-value="0"')
    zero = mut(zero, 'y="403"', 'y="423"')
    zero = mut(zero, 'x2="64" y2="400"', 'x2="64" y2="420"')
    zero = mut(zero, " Y axis spans 5 to 40, not from zero.", "")
    h.clean("a zero-based axis needs no truncation statement", zero)

    # --- fail closed and scope --------------------------------------------
    h.flags("a line chart with no parseable series is refused",
            "<html><body><svg></svg></body></html>", "refusing to report OK", "example-line-x.html")
    h.check("the slopegraph contract is out of scope",
            not verify.looks_like_line(Path("a.html"),
                                       '<line data-series="A" data-from="1" data-to="2" x1="1"/>'))
    h.check("a streamgraph layer is out of scope",
            not verify.looks_like_line(Path("a.html"), '<path data-layer="A" data-values="1,2"/>'))
    h.check("a polyline data-line claims the file",
            verify.looks_like_line(Path("a.html"), '<polyline data-line="A" data-values="1,2"/>'))
    h.check("a commented-out series claims nothing",
            not verify.looks_like_line(Path("a.html"), '<!-- <polyline data-line="A"/> -->'))
    h.check("the example-line filename claims the file",
            verify.looks_like_line(Path("example-line-z.html"), ""))
    for path in sorted(ASSETS.glob("*.html")):
        if path.name.startswith("example-line"):
            continue
        raw = path.read_text(encoding="utf-8")
        if verify.looks_like_line(path, raw):
            h.check("sibling file %s is not claimed" % path.name, False, "claimed by verify-line")
    h.check("--all globs only example-line files",
            all(p.name.startswith("example-line") for p in verify.targets(
                type("A", (), {"all": True, "paths": []})())))

    # --- CLI ---------------------------------------------------------------
    def cli(*args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args],
                              capture_output=True, text=True)

    good = h.write("example-line-good.html", CLEAN)
    bad = h.write("example-line-bad.html", mut(CLEAN, 'y="263"', 'y="300"'))
    other = h.write("notes.html", "<html><body>nothing here</body></html>")
    r = cli(str(good))
    h.check("CLI exits 0 on a clean file", r.returncode == 0 and r.stdout.startswith("OK line"), r.stdout)
    r = cli(str(bad))
    h.check("CLI exits 1 on a finding", r.returncode == 1 and "finding(s)" in r.stdout, r.stdout)
    r = cli(str(other))
    h.check("CLI reports an out-of-scope file honestly",
            r.returncode == 0 and "no line chart found" in r.stdout, r.stdout)
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
    print("OK line checker: %d case(s), both polarities" % h.count)
    return 0


def main() -> int:
    h = Harness()
    try:
        return run_cases(h)
    finally:
        h.close()


if __name__ == "__main__":
    raise SystemExit(main())
