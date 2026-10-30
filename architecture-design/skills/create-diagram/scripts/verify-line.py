#!/usr/bin/env python3
"""Verify that a line chart's drawn geometry matches the values it declares.

A line chart's claim is that every vertex sits where one linear y scale puts
its value, at an x that is one linear index scale, and that each series is
named where it ends rather than in a key the eye has to travel to. All of it
can be broken without anything erroring: the figure renders, the labels are
present, and the lie is in the geometry or the layout. `lint-skin.py` reads
colours and fonts, `verify-geometry.py` reads masks against nodes, and neither
compares a drawn vertex against the value bound to it.

Eight invariants:

1. SHARED SCALES - every polyline declares `data-values`; vertex i of every
   series sits at one x for index i (evenly pitched), and every vertex's y
   sits where one linear y scale puts its value. The scale is fitted to the
   set (least squares) and every vertex is held to it, so one nudged vertex
   is a finding rather than a bend in the line.

2. BOUND TICKS AND A RANGE FRAME - y tick labels bind `data-tick="y"` and
   `data-value`, print exactly that number and sit where the scale puts it.
   The y axis rule spans the data minimum to the data maximum and the x axis
   rule spans the first to the last vertex; both ends carry a bound tick. An
   axis running past the data is ink that measures nothing.

3. EVERY SERIES NAMED AT ITS LAST POINT - one bound `data-role="name"` label
   per series, reading exactly the series name, to the right of the last
   vertex and on its row, nearer its own last vertex than any other series',
   and no two labels closer than 10px. Crowded end labels are data; the fix is
   fewer series or small multiples, never a moved vertex.

4. NO LEGEND ONCE EVERY SERIES IS LABELLED - a LEGEND heading, a
   `data-role="legend"` element, or a key line below the plot that repeats a
   series name duplicates a direct label.

5. A COMPARISON - at least one `<line data-ref=...>` carrying `data-value`,
   horizontal, at the y the scale puts that value, dashed `4,3`, with a bound
   `data-role="label"` text on its row.

6. NO FURNITURE - no rotated or vertical text, no `transform` anywhere, at
   most four gridlines and only at ink 0.08 or fainter, no filled area under
   a one-dimensional series (a polygon needs `data-area="cumulative"`), at
   most six series and at most one accent series, and no series stroke fainter
   than the 0.53 ink floor.

7. A SOURCE LINE - one `data-role="source"` text; when the y axis does not
   reach zero it says so.

8. FAIL CLOSED - a file that presents as a line chart but declares no
   parseable series is a finding, never a pass.

Scope treaty. This contract binds `data-line` on a `<polyline>`. It never
uses `data-series` (slopegraph, bump), `data-layer` (streamgraph),
`data-bins` (ridgeline), `data-size` (bubble) or `data-value` on a circle
(beeswarm), so no sibling checker claims a line file and this one claims none
of theirs. `--all` globs `example-line*.html` and still filters on the
detection rule, so a variant file is skipped even if named like one.

WHAT THIS DOES NOT CHECK, deliberately: absolute truth (a figure wrong by one
constant everywhere is self-consistent), banking angle (guidance, not a gate),
and prose in the source line beyond the zero statement.

Usage:
    python3 scripts/verify-line.py --all
    python3 scripts/verify-line.py assets/example-line.html

Exit: 0 clean, 1 findings, 2 usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
DECLARES_LINE_RE = re.compile(r"<polyline\b[^>]*\bdata-line\s*=", re.I | re.S)
NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)")
RGBA_RE = re.compile(r"rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)", re.I)
ACCENT = "#ef6306"
MAX_SERIES = 6
OPACITY_FLOOR = 0.53
GRID_ALPHA_CEILING = 0.08
GRID_CAP = 4
SCALE_TOL = 0.6      # data-scaled coordinates are rounded to 0.1-1px
AXIS_TOL = 1.0
LABEL_ROW_TOL = 6.0
LABEL_GAP = (8.0, 40.0)
LABEL_PITCH = 10.0
TICK_BASELINE = 3.0  # tick text baseline sits 3px under its mark
TICK_TOL = 2.0
LEGEND_Y = 470.0


class Element:
    def __init__(self, tag: str, attrs: dict, line: int):
        self.tag = tag
        self.attrs = attrs
        self.line = line
        self.body = ""


class _Scanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list = []
        self._open_text: list = []

    def _add(self, tag, attrs):
        d: dict = {}
        for key, value in attrs:
            d.setdefault(key.lower(), value if value is not None else "")
        el = Element(tag, d, self.getpos()[0])
        self.elements.append(el)
        return el

    def handle_starttag(self, tag, attrs):
        el = self._add(tag, attrs)
        if tag == "text":
            self._open_text.append(el)

    def handle_startendtag(self, tag, attrs):
        self._add(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "text" and self._open_text:
            self._open_text.pop()

    def handle_data(self, data):
        if self._open_text:
            self._open_text[-1].body += data


def parse_document(source: str) -> _Scanner:
    scanner = _Scanner()
    scanner.feed(HTML_COMMENT_RE.sub("", source))
    scanner.close()
    return scanner


def looks_like_line(path: Path, source: str) -> bool:
    """Does this file present itself as a line chart under THIS contract?

    The signal is `data-line` on a `<polyline>` or an `example-line` filename.
    Nothing here reads data-series, data-layer, data-bins, data-size or a
    circle's data-value, which is the treaty with the sibling checkers.
    """
    if path.name.startswith("example-line"):
        return True
    return DECLARES_LINE_RE.search(HTML_COMMENT_RE.sub("", source)) is not None


def num(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def printed_number(body: str):
    tokens = NUMBER_RE.findall(body)
    if len(tokens) != 1:
        return None
    return num(tokens[0].replace(",", ""))


def parse_points(text: str):
    pts = []
    for pair in text.replace(",", " ").split():
        pts.append(pair)
    nums = [num(p) for p in pts]
    if not nums or None in nums or len(nums) % 2:
        return None
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]


def fit(pairs):
    """Least-squares y = a + b*v over (v, y) pairs, or None if degenerate."""
    n = len(pairs)
    mv = sum(v for v, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    sxx = sum((v - mv) ** 2 for v, _ in pairs)
    if sxx == 0:
        return None
    b = sum((v - mv) * (y - my) for v, y in pairs) / sxx
    return my - b * mv, b


class Series:
    def __init__(self, name, values, points, el):
        self.name = name
        self.values = values
        self.points = points
        self.el = el


def parse_series(doc: _Scanner, findings: list, fname: str) -> list:
    out = []
    for el in doc.elements:
        if el.tag != "polyline" or "data-line" not in el.attrs:
            continue
        a = el.attrs
        name = a["data-line"].strip()
        where = "%s:%d" % (fname, el.line)
        if not name:
            findings.append("%s: polyline with an empty data-line name" % where)
            continue
        raw_vals = [num(t) for t in a.get("data-values", "").split(",")] if a.get("data-values") else []
        pts = parse_points(a.get("points", ""))
        if not raw_vals or None in raw_vals:
            findings.append("%s: series %r needs numeric data-values" % (where, name))
            continue
        if pts is None:
            findings.append("%s: series %r needs parseable points" % (where, name))
            continue
        if len(pts) != len(raw_vals):
            findings.append("%s: series %r declares %d values but draws %d vertices"
                            % (where, name, len(raw_vals), len(pts)))
            continue
        out.append(Series(name, raw_vals, pts, el))
    names = [s.name for s in out]
    for dup in sorted({n for n in names if names.count(n) > 1}):
        findings.append("%s: two polylines share the series name %r" % (fname, dup))
    return out


def check_scales(series: list, findings: list, fname: str):
    """(y_fit, xs) after holding every vertex to one x pitch and one y scale."""
    counts = {len(s.values) for s in series}
    if len(counts) != 1:
        findings.append("%s: series have different vertex counts %s; every series "
                        "shares one x grid" % (fname, sorted(counts)))
        return None, None
    n = counts.pop()
    if n < 2:
        findings.append("%s: a line needs at least two vertices per series" % fname)
        return None, None
    xs = [p[0] for p in series[0].points]
    pitch = (xs[-1] - xs[0]) / (n - 1)
    if pitch <= 0:
        findings.append("%s: x must increase left to right" % fname)
        return None, None
    for i, x in enumerate(xs):
        if abs(x - (xs[0] + i * pitch)) > SCALE_TOL:
            findings.append("%s: vertex %d of %r is at x=%g, off the even pitch "
                            "(expected %g)" % (fname, i, series[0].name, x,
                                               xs[0] + i * pitch))
    for s in series[1:]:
        for i, (x, _) in enumerate(s.points):
            if abs(x - xs[i]) > SCALE_TOL:
                findings.append("%s: vertex %d of %r is at x=%g but %r puts index "
                                "%d at x=%g; all series share one x grid"
                                % (fname, i, s.name, x, series[0].name, i, xs[i]))
    pairs = [(v, y) for s in series for v, (_, y) in zip(s.values, s.points)]
    y_fit = fit(pairs)
    if y_fit is None or y_fit[1] == 0:
        findings.append("%s: the declared values are all equal or the y scale is flat; "
                        "distinct values cannot share one position" % fname)
        return None, xs
    a, b = y_fit
    for s in series:
        for i, (v, (_, y)) in enumerate(zip(s.values, s.points)):
            if abs(y - (a + b * v)) > SCALE_TOL:
                findings.append(
                    "%s: %r vertex %d declares %g but is drawn at y=%g; the shared "
                    "scale puts it at y=%.1f" % (fname, s.name, i, v, y, a + b * v))
    return y_fit, xs


def hv(attrs):
    """(x1, y1, x2, y2) floats for a <line>, or None."""
    vals = [num(attrs.get(k)) for k in ("x1", "y1", "x2", "y2")]
    return None if None in vals else tuple(vals)


def check_axes_and_ticks(doc, series, y_fit, xs, findings, fname):
    a, b = y_fit
    scale = lambda v: a + b * v
    all_vals = [v for s in series for v in s.values]
    lo, hi = min(all_vals), max(all_vals)
    axes = {}
    for el in doc.elements:
        if el.tag == "line" and el.attrs.get("data-axis") in ("x", "y"):
            axes.setdefault(el.attrs["data-axis"], []).append(el)
    for kind in ("x", "y"):
        if len(axes.get(kind, [])) != 1:
            findings.append("%s: expected exactly one <line data-axis=\"%s\"> (the "
                            "range-frame rule), found %d" % (fname, kind, len(axes.get(kind, []))))
    if len(axes.get("y", [])) == 1:
        g = hv(axes["y"][0].attrs)
        if g is None or abs(g[0] - g[2]) > 0.01:
            findings.append("%s: the y axis rule must be vertical" % fname)
        else:
            ends = sorted([g[1], g[3]])
            want = sorted([scale(lo), scale(hi)])
            for got, exp, what in zip(ends, want, ("top", "bottom")):
                if abs(got - exp) > AXIS_TOL:
                    findings.append("%s: y axis %s is at y=%g but the data %s ends at "
                                    "y=%.1f; a range frame spans only min to max"
                                    % (fname, what, got, "maximum" if what == "top" else "minimum", exp))
    if len(axes.get("x", [])) == 1:
        g = hv(axes["x"][0].attrs)
        if g is None or abs(g[1] - g[3]) > 0.01:
            findings.append("%s: the x axis rule must be horizontal" % fname)
        else:
            if abs(min(g[0], g[2]) - xs[0]) > AXIS_TOL or abs(max(g[0], g[2]) - xs[-1]) > AXIS_TOL:
                findings.append("%s: x axis spans x=%g..%g but the data spans x=%g..%g; "
                                "a range frame spans only first to last point"
                                % (fname, min(g[0], g[2]), max(g[0], g[2]), xs[0], xs[-1]))
    ticks = [el for el in doc.elements
             if el.tag == "text" and el.attrs.get("data-tick") == "y"]
    seen = []
    for el in ticks:
        where = "%s:%d" % (fname, el.line)
        value = num(el.attrs.get("data-value"))
        printed = printed_number(el.body)
        ty = num(el.attrs.get("y"))
        if value is None or printed is None or ty is None:
            findings.append("%s: y tick needs a numeric data-value, one printed number and y" % where)
            continue
        seen.append(value)
        if abs(printed - value) > 1e-9:
            findings.append("%s: y tick prints %g but declares %g" % (where, printed, value))
        if abs(ty - (scale(value) + TICK_BASELINE)) > TICK_TOL:
            findings.append("%s: y tick %g is drawn at y=%g; the scale puts it at y=%.1f"
                            % (where, value, ty, scale(value) + TICK_BASELINE))
    if len(seen) < 2:
        findings.append("%s: bind at least two y ticks (data-tick=\"y\" data-value)" % fname)
    for want, what in ((lo, "minimum"), (hi, "maximum")):
        if seen and not any(abs(t - want) < 1e-9 for t in seen):
            findings.append("%s: no bound y tick at the data %s (%g); the range frame "
                            "labels its own ends" % (fname, what, want))
    return lo, hi


def check_labels(doc, series, findings, fname):
    labels = {}
    for el in doc.elements:
        if el.tag == "text" and el.attrs.get("data-role") == "name" and "data-line" in el.attrs:
            labels.setdefault(el.attrs["data-line"].strip(), []).append(el)
    for name in labels:
        if name not in {s.name for s in series}:
            findings.append("%s: label bound to unknown series %r" % (fname, name))
    placed = []
    last = {s.name: s.points[-1] for s in series}
    for s in series:
        els = labels.get(s.name, [])
        if len(els) != 1:
            findings.append("%s: series %r needs exactly one end label "
                            "(data-line + data-role=\"name\"), found %d"
                            % (fname, s.name, len(els)))
            continue
        el = els[0]
        where = "%s:%d" % (fname, el.line)
        x, y = num(el.attrs.get("x")), num(el.attrs.get("y"))
        if x is None or y is None:
            findings.append("%s: end label for %r needs numeric x and y" % (where, s.name))
            continue
        if el.body.strip() != s.name:
            findings.append("%s: end label reads %r but is bound to %r"
                            % (where, el.body.strip(), s.name))
        lx, ly = last[s.name]
        gap = x - lx
        if not LABEL_GAP[0] <= gap <= LABEL_GAP[1]:
            findings.append("%s: end label for %r is %.0fpx from its last vertex; it "
                            "belongs %g-%gpx to the right" % (where, s.name, gap, *LABEL_GAP))
        if abs(y - ly) > LABEL_ROW_TOL:
            findings.append("%s: end label for %r is %.0fpx off its last vertex's row"
                            % (where, s.name, abs(y - ly)))
        for other, (_, oy) in last.items():
            if other != s.name and abs(y - oy) < abs(y - ly):
                findings.append("%s: end label for %r sits nearer the last point of %r "
                                "than its own; a label on the wrong row renames the line"
                                % (where, s.name, other))
        placed.append((s.name, y))
    placed.sort(key=lambda p: p[1])
    for (n1, y1), (n2, y2) in zip(placed, placed[1:]):
        if y2 - y1 < LABEL_PITCH:
            findings.append("%s: end labels %r and %r are %.1fpx apart (minimum %g); too "
                            "many series for direct labels, split into small multiples"
                            % (fname, n1, n2, y2 - y1, LABEL_PITCH))


def check_legend(doc, series, findings, fname):
    names = [s.name.casefold() for s in series]
    for el in doc.elements:
        if el.attrs.get("data-role") == "legend" or "data-legend" in el.attrs:
            findings.append("%s:%d: a legend element is present although every series "
                            "is labelled at its end" % (fname, el.line))
        if el.tag != "text":
            continue
        body = el.body.strip().casefold()
        if body == "legend":
            findings.append("%s:%d: LEGEND heading; remove it, the series are labelled "
                            "in place" % (fname, el.line))
        y = num(el.attrs.get("y"))
        if (y is not None and y >= LEGEND_Y and "data-line" not in el.attrs
                and any(body.startswith(n) for n in names)):
            findings.append("%s:%d: key text %r repeats a direct label"
                            % (fname, el.line, el.body.strip()))


def check_reference(doc, y_fit, xs, findings, fname):
    a, b = y_fit
    refs = [el for el in doc.elements if el.tag == "line" and "data-ref" in el.attrs]
    if not refs:
        findings.append("%s: no comparison line; add <line data-ref data-value> (a "
                        "target, average or prior period)" % fname)
        return
    for el in refs:
        where = "%s:%d" % (fname, el.line)
        g, value = hv(el.attrs), num(el.attrs.get("data-value"))
        if g is None or value is None:
            findings.append("%s: reference line needs numeric x1/y1/x2/y2 and data-value" % where)
            continue
        if abs(g[1] - g[3]) > 0.01:
            findings.append("%s: reference line must be horizontal" % where)
        if abs(g[1] - (a + b * value)) > SCALE_TOL:
            findings.append("%s: reference line declares %g but is drawn at y=%g; the "
                            "scale puts it at y=%.1f" % (where, value, g[1], a + b * value))
        if re.sub(r"\s+", "", el.attrs.get("stroke-dasharray", "")) != "4,3":
            findings.append("%s: reference line must be dashed 4,3" % where)
        tag = el.attrs["data-ref"]
        labels = [t for t in doc.elements if t.tag == "text"
                  and t.attrs.get("data-ref") == tag and t.attrs.get("data-role") == "label"]
        if len(labels) != 1 or not labels[0].body.strip():
            findings.append("%s: reference %r needs one direct label (data-ref + "
                            "data-role=\"label\")" % (where, tag))
        else:
            ly = num(labels[0].attrs.get("y"))
            if ly is None or abs(ly - g[1]) > 12:
                findings.append("%s: the label for reference %r is not on its line"
                                % (where, tag))


def alpha(color: str):
    m = RGBA_RE.fullmatch(color.strip())
    return float(m.group(1)) if m else None


def check_furniture(doc, series, xs, findings, fname):
    for el in doc.elements:
        where = "%s:%d" % (fname, el.line)
        t = el.attrs.get("transform", "")
        if t:
            kind = "rotated text" if el.tag == "text" and "rotate" in t.lower() else "transform"
            findings.append("%s: %s on <%s>; text stays horizontal and the checker "
                            "reads raw coordinates" % (where, kind, el.tag))
        style = el.attrs.get("style", "").lower()
        if re.search(r"transform|rotate|translate|writing-mode", style):
            findings.append("%s: style moves or rotates <%s>" % (where, el.tag))
        if el.tag == "text" and re.search(r"vertical|sideways|^tb|^rl", el.attrs.get("writing-mode", "").lower()):
            findings.append("%s: vertical text" % where)
        if el.tag == "polygon" and el.attrs.get("data-area") != "cumulative":
            findings.append("%s: filled area under a one-dimensional series; area is for "
                            "cumulative quantities (data-area=\"cumulative\")" % where)
    grid = []
    span = (xs[-1] - xs[0]) * 0.5 if xs else 0
    for el in doc.elements:
        if el.tag != "line" or "data-axis" in el.attrs or "data-ref" in el.attrs:
            continue
        g = hv(el.attrs)
        if g and (abs(g[1] - g[3]) < 0.01 or abs(g[0] - g[2]) < 0.01) \
                and max(abs(g[2] - g[0]), abs(g[3] - g[1])) >= span:
            grid.append(el)
    if len(grid) > GRID_CAP:
        findings.append("%s: %d gridlines; at most %d" % (fname, len(grid), GRID_CAP))
    for el in grid:
        al = alpha(el.attrs.get("stroke", ""))
        if al is None or al > GRID_ALPHA_CEILING:
            findings.append("%s:%d: a gridline must be ink at %g or fainter"
                            % (fname, el.line, GRID_ALPHA_CEILING))
    if len(series) > MAX_SERIES:
        findings.append("%s: %d series; at most %d (limited by end-label collisions)"
                        % (fname, len(series), MAX_SERIES))
    accents = [s for s in series if s.el.attrs.get("stroke", "").lower() == ACCENT]
    if len(accents) > 1:
        findings.append("%s: %d accent series; one focal series only" % (fname, len(accents)))
    for s in series:
        al = alpha(s.el.attrs.get("stroke", ""))
        if al is not None and al < OPACITY_FLOOR:
            findings.append("%s: series %r stroke opacity %g is under the %g ink floor "
                            "(3:1 on light paper)" % (fname, s.name, al, OPACITY_FLOOR))
    for el in doc.elements:
        if el.tag == "text" and el.attrs.get("fill", "").lower() == ACCENT:
            findings.append("%s:%d: text painted in the accent" % (fname, el.line))


def check_source(doc, lo_axis_zero: bool, findings, fname):
    srcs = [el for el in doc.elements if el.tag == "text" and el.attrs.get("data-role") == "source"]
    if len(srcs) != 1:
        findings.append("%s: expected exactly one <text data-role=\"source\">, found %d"
                        % (fname, len(srcs)))
        return
    if not lo_axis_zero and not re.search(r"not from zero|not zero|break|truncat", srcs[0].body, re.I):
        findings.append("%s: the y axis does not reach zero and the source line does not "
                        "say so" % fname)


def check_source_text(path: Path, raw: str) -> list:
    fname = path.name
    findings: list = []
    doc = parse_document(raw)
    if not any(e.tag == "polyline" and "data-line" in e.attrs for e in doc.elements):
        findings.append("%s: presents as a line chart but declares no <polyline "
                        "data-line> series; refusing to report OK on a file this "
                        "checker could not read" % fname)
        return findings
    series = parse_series(doc, findings, fname)
    if not series:
        return findings
    y_fit, xs = check_scales(series, findings, fname)
    check_furniture(doc, series, xs, findings, fname)
    check_legend(doc, series, findings, fname)
    check_labels(doc, series, findings, fname)
    if y_fit is None:
        return findings
    lo, _ = check_axes_and_ticks(doc, series, y_fit, xs, findings, fname)
    check_reference(doc, y_fit, xs, findings, fname)
    check_source(doc, lo <= 0, findings, fname)
    return findings


def check(path: Path) -> list:
    raw = path.read_text(encoding="utf-8")
    if not looks_like_line(path, raw):
        return []
    return check_source_text(path, raw)


def targets(args: argparse.Namespace) -> list:
    if args.all:
        return sorted(ASSET_DIR.glob("example-line*.html"))
    return [Path(p) for p in args.paths]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify line chart vertices, end labels and reference lines "
                    "against the values they declare.")
    parser.add_argument("paths", nargs="*", help="HTML files to check")
    parser.add_argument("--all", action="store_true",
                        help="check every shipped example that presents as a line chart")
    args = parser.parse_args()
    if not args.all and not args.paths:
        parser.print_help()
        return 2
    findings: list = []
    checked = skipped = 0
    for path in targets(args):
        if not path.is_file():
            print("error: %s is not a readable file" % path, file=sys.stderr)
            return 2
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            print("error: cannot read %s: %s" % (path, error), file=sys.stderr)
            return 2
        if not looks_like_line(path, raw):
            skipped += 1
            continue
        findings.extend(check_source_text(path, raw))
        checked += 1
    for finding in findings:
        print(finding)
    tail = " (%d file(s) skipped as out of scope)" % skipped if skipped else ""
    if findings:
        print("\n%d line finding(s) across %d file(s).%s" % (len(findings), checked, tail))
        return 1
    if not checked:
        print("OK line: no line chart found to check%s" % tail)
        return 0
    print("OK line: %d file(s), one linear y scale and one x grid, range-frame axes, "
          "every series named at its last point, no legend, a labelled comparison "
          "line, and no rotated text%s" % (checked, tail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
