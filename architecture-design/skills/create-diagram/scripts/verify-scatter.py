#!/usr/bin/env python3
"""Verify that a scatter plot's drawn geometry matches the values it declares.

A scatter plot claims that every point sits where two shared linear scales put
its (x, y), and, when it draws a trend, that the trend is a computed fit and
not a hand-drawn impression. Both can be broken without anything erroring: the
figure renders and the lie is in the geometry. `lint-skin.py` reads colours
and fonts, `verify-geometry.py` reads label masks, and neither compares a
drawn coordinate with the value bound to it.

Nine invariants:

1. SHARED SCALES - every data circle declares `data-x` and `data-y`; its cx
   sits where one linear x scale puts the value and its cy where one linear
   y scale does. Scales are fitted to the set (least squares) and every point
   is held to them, so a point nudged aside "to stop it overlapping" is a
   finding, not a different number.

2. BOUND TICKS AND A RANGE FRAME - ticks bind `data-tick` and `data-value`,
   print exactly that number, and sit where the scale puts it. Each axis rule
   (`data-axis`) spans only the data minimum to maximum, and both ends carry a
   bound tick.

3. THE TREND IS A FIT - a `<line data-trend="ols">` must equal the ordinary
   least squares line of the bound points at both of its ends, and must stay
   inside the data's x range. A diagonal line that is not a bound fit is a
   hand-drawn trend and is refused. The source line must name the method.

4. A COMPARISON - at least one horizontal or vertical `<line data-ref>` with
   `data-value`, dashed `4,3`, on its scale position, with a direct label. A
   `median` or `mean` reference must equal that statistic of the bound points.

5. DIRECT LABELS - a point with `data-name` has exactly one label bound to it,
   reading the name, within 48px of it and nearer to it than to any other
   named point; names are unique and non-empty. No LEGEND heading, no legend
   element, and no key repeating a direct label.

6. NO FURNITURE - no rotated or vertical text, no `transform`, no size
   encoding (`data-size` is the bubble contract), no full grid (horizontal
   and vertical rules together), at most four gridlines and only at ink 0.08
   or fainter.

7. THE CAP - 4 to 300 points. Past 300 the figure is a density estimate, not
   a scatter.

8. A SOURCE LINE - one `data-role="source"` text.

9. FAIL CLOSED - a file that presents as a scatter plot but yields fewer than
   four parseable points is a finding, never a pass.

Scope treaty. This contract binds `data-x` and `data-y` on a `<circle>` that
carries neither `data-size` (bubble) nor `data-value` (beeswarm), and the
`example-scatter` filename. It never uses `data-series`, `data-layer`,
`data-bins`, `data-ranks` or `data-line`, so no sibling checker claims a
scatter file and this one claims none of theirs; the bubble files bind the
same two attributes and are excluded by their `data-size`.

WHAT THIS DOES NOT CHECK, deliberately: absolute truth, whether a trend is
statistically meaningful, and optional rug marks, which carry no claim.

Usage:
    python3 scripts/verify-scatter.py --all
    python3 scripts/verify-scatter.py assets/example-scatter.html

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
CIRCLE_RE = re.compile(r"<circle\b(?P<attrs>[^>]*)>", re.I | re.S)
NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)")
RGBA_RE = re.compile(r"rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)", re.I)
METHOD_RE = re.compile(r"least[- ]squares|\bOLS\b", re.I)
ACCENT = "#ef6306"
MIN_POINTS = 4
MAX_POINTS = 300
SCALE_TOL = 0.6
AXIS_TOL = 1.0
TREND_TOL = 1.5
TICK_BASELINE = 3.0
TICK_TOL = 2.0
LABEL_REACH = 48.0
GRID_CAP = 4
GRID_ALPHA_CEILING = 0.08
LEGEND_Y = 470.0
STAT_TOL = 0.05


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


def declares_scatter_point(source: str) -> bool:
    """A circle binding data-x and data-y with no data-size and no data-value."""
    for match in CIRCLE_RE.finditer(HTML_COMMENT_RE.sub("", source)):
        attrs = match.group("attrs")
        if (re.search(r"\bdata-x\s*=", attrs) and re.search(r"\bdata-y\s*=", attrs)
                and not re.search(r"\bdata-size\s*=", attrs)
                and not re.search(r"\bdata-value\s*=", attrs)):
            return True
    return False


def looks_like_scatter(path: Path, source: str) -> bool:
    """Does this file present itself as a scatter plot under THIS contract?

    The filename or a bound plain point claims it. Bubble circles bind data-x
    and data-y too but always carry data-size, which keeps them out; the
    beeswarm binds data-value and is likewise out. Descriptions are not read:
    "scatter" appears in prose that belongs to other types.
    """
    return path.name.startswith("example-scatter") or declares_scatter_point(source)


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


def fit(pairs):
    """Least-squares p = a + b*v over (v, p) pairs, or None if degenerate."""
    n = len(pairs)
    mv = sum(v for v, _ in pairs) / n
    mp = sum(p for _, p in pairs) / n
    sxx = sum((v - mv) ** 2 for v, _ in pairs)
    if sxx == 0:
        return None
    b = sum((v - mv) * (p - mp) for v, p in pairs) / sxx
    return mp - b * mv, b


def median(values):
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def hv(attrs):
    vals = [num(attrs.get(k)) for k in ("x1", "y1", "x2", "y2")]
    return None if None in vals else tuple(vals)


def alpha(color: str):
    m = RGBA_RE.fullmatch(color.strip())
    return float(m.group(1)) if m else None


class Point:
    def __init__(self, x, y, cx, cy, name, el):
        self.x, self.y, self.cx, self.cy, self.name, self.el = x, y, cx, cy, name, el


def parse_points(doc, findings, fname):
    pts = []
    for el in doc.elements:
        if el.tag != "circle":
            continue
        a = el.attrs
        if "data-size" in a:
            findings.append("%s:%d: data-size on a scatter point; a size encoding is the "
                            "bubble contract (verify-bubble.py)" % (fname, el.line))
            continue
        if "data-x" not in a and "data-y" not in a:
            continue  # a paper underlay or a key swatch carries nothing
        vals = [num(a.get(k)) for k in ("data-x", "data-y", "cx", "cy")]
        if None in vals:
            findings.append("%s:%d: a data circle needs numeric data-x, data-y, cx and cy"
                            % (fname, el.line))
            continue
        pts.append(Point(*vals, a.get("data-name", None), el))
    return pts


def check_scales(pts, findings, fname):
    xf = fit([(p.x, p.cx) for p in pts])
    yf = fit([(p.y, p.cy) for p in pts])
    if xf is None or xf[1] == 0 or yf is None or yf[1] == 0:
        findings.append("%s: the declared x or y values are all equal, or the scale is "
                        "flat; distinct values cannot share one position" % fname)
        return None, None
    for p in pts:
        ex, ey = xf[0] + xf[1] * p.x, yf[0] + yf[1] * p.y
        if abs(p.cx - ex) > SCALE_TOL:
            findings.append("%s:%d: x=%g is drawn at cx=%g; the shared x scale puts it at "
                            "cx=%.1f" % (fname, p.el.line, p.x, p.cx, ex))
        if abs(p.cy - ey) > SCALE_TOL:
            findings.append("%s:%d: y=%g is drawn at cy=%g; the shared y scale puts it at "
                            "cy=%.1f" % (fname, p.el.line, p.y, p.cy, ey))
    return xf, yf


def check_axes_and_ticks(doc, pts, xf, yf, findings, fname):
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    rng = {"x": (min(xs), max(xs), xf), "y": (min(ys), max(ys), yf)}
    axes = {"x": [], "y": []}
    for el in doc.elements:
        if el.tag == "line" and el.attrs.get("data-axis") in axes:
            axes[el.attrs["data-axis"]].append(el)
    for kind in ("x", "y"):
        if len(axes[kind]) != 1:
            findings.append("%s: expected exactly one <line data-axis=\"%s\">, found %d"
                            % (fname, kind, len(axes[kind])))
            continue
        lo, hi, (a, b) = rng[kind]
        g = hv(axes[kind][0].attrs)
        if g is None:
            findings.append("%s: the %s axis rule needs numeric coordinates" % (fname, kind))
            continue
        flat = abs(g[0] - g[2]) if kind == "y" else abs(g[1] - g[3])
        if flat > 0.01:
            findings.append("%s: the %s axis rule must be %s" %
                            (fname, kind, "vertical" if kind == "y" else "horizontal"))
            continue
        ends = sorted([g[1], g[3]] if kind == "y" else [g[0], g[2]])
        want = sorted([a + b * lo, a + b * hi])
        if any(abs(e - w) > AXIS_TOL for e, w in zip(ends, want)):
            findings.append("%s: the %s axis spans %.1f..%.1f but the data spans %.1f..%.1f; "
                            "a range frame spans only min to max"
                            % (fname, kind, ends[0], ends[1], want[0], want[1]))
    seen = {"x": [], "y": []}
    for el in doc.elements:
        kind = el.attrs.get("data-tick")
        if el.tag != "text" or kind not in seen:
            continue
        where = "%s:%d" % (fname, el.line)
        value, printed = num(el.attrs.get("data-value")), printed_number(el.body)
        pos = num(el.attrs.get("x" if kind == "x" else "y"))
        if value is None or printed is None or pos is None:
            findings.append("%s: tick needs a numeric data-value, one printed number and "
                            "a position" % where)
            continue
        seen[kind].append(value)
        if abs(printed - value) > 1e-9:
            findings.append("%s: %s tick prints %g but declares %g" % (where, kind, printed, value))
        a, b = (xf if kind == "x" else yf)
        expect = a + b * value + (0 if kind == "x" else TICK_BASELINE)
        tol = AXIS_TOL if kind == "x" else TICK_TOL
        if abs(pos - expect) > tol:
            findings.append("%s: %s tick %g is drawn at %g; the scale puts it at %.1f"
                            % (where, kind, value, pos, expect))
    for kind in ("x", "y"):
        if len(seen[kind]) < 2:
            findings.append("%s: bind at least two %s ticks (data-tick data-value)" % (fname, kind))
        for want, what in ((rng[kind][0], "minimum"), (rng[kind][1], "maximum")):
            if seen[kind] and not any(abs(t - want) < 1e-9 for t in seen[kind]):
                findings.append("%s: no bound %s tick at the data %s (%g); the range frame "
                                "labels its own ends" % (fname, kind, what, want))


def check_trend(doc, pts, xf, yf, findings, fname):
    trends = [el for el in doc.elements if el.tag == "line" and "data-trend" in el.attrs]
    others = []
    for el in doc.elements:
        if el.tag != "line" or any(k in el.attrs for k in ("data-trend", "data-axis", "data-ref")):
            continue
        g = hv(el.attrs)
        if g and abs(g[0] - g[2]) > 0.5 and abs(g[1] - g[3]) > 0.5:
            others.append(el)
    for el in others:
        findings.append("%s:%d: a diagonal line that is not a bound fit; a trend is "
                        "<line data-trend=\"ols\"> computed from the points, never hand-drawn"
                        % (fname, el.line))
    if not trends:
        return False
    srcs = [e for e in doc.elements if e.tag == "text" and e.attrs.get("data-role") == "source"]
    if not any(METHOD_RE.search(s.body) for s in srcs):
        findings.append("%s: a trend line is drawn but the source line does not name the "
                        "method (least squares)" % fname)
    fit_xy = fit([(p.x, p.y) for p in pts])
    xmin, xmax = min(p.x for p in pts), max(p.x for p in pts)
    eps = 0.02 * (xmax - xmin)
    for el in trends:
        where = "%s:%d" % (fname, el.line)
        if el.attrs["data-trend"] != "ols":
            findings.append("%s: unsupported trend method %r; only ols is computed here"
                            % (where, el.attrs["data-trend"]))
            continue
        g = hv(el.attrs)
        if g is None or fit_xy is None:
            findings.append("%s: a trend needs numeric endpoints and points with varying x" % where)
            continue
        a0, b0 = fit_xy
        for px, py in ((g[0], g[1]), (g[2], g[3])):
            dx = (px - xf[0]) / xf[1]
            if dx < xmin - eps or dx > xmax + eps:
                findings.append("%s: the trend extends to x=%.2f outside the data range "
                                "%g..%g" % (where, dx, xmin, xmax))
            expect = yf[0] + yf[1] * (a0 + b0 * dx)
            if abs(py - expect) > TREND_TOL:
                findings.append("%s: the trend is drawn at y=%g where the least squares fit "
                                "puts it at y=%.1f (x=%.2f)" % (where, py, expect, dx))
        labels = [t for t in doc.elements if t.tag == "text"
                  and t.attrs.get("data-trend") and t.attrs.get("data-role") == "label"]
        if len(labels) != 1:
            findings.append("%s: the trend needs one direct label (data-trend + "
                            "data-role=\"label\")" % where)
    return True


def check_reference(doc, pts, xf, yf, findings, fname):
    refs = [el for el in doc.elements if el.tag == "line" and "data-ref" in el.attrs]
    if not refs:
        findings.append("%s: no comparison line; add <line data-ref data-value> (median, "
                        "average or target)" % fname)
        return
    for el in refs:
        where = "%s:%d" % (fname, el.line)
        g, value = hv(el.attrs), num(el.attrs.get("data-value"))
        if g is None or value is None:
            findings.append("%s: reference line needs numeric x1/y1/x2/y2 and data-value" % where)
            continue
        horizontal = abs(g[1] - g[3]) < 0.01
        vertical = abs(g[0] - g[2]) < 0.01
        if not (horizontal or vertical):
            findings.append("%s: reference line must be horizontal or vertical" % where)
            continue
        data = [p.y for p in pts] if horizontal else [p.x for p in pts]
        a, b = yf if horizontal else xf
        drawn = g[1] if horizontal else g[0]
        if abs(drawn - (a + b * value)) > SCALE_TOL:
            findings.append("%s: reference declares %g but is drawn at %g; the scale puts "
                            "it at %.1f" % (where, value, drawn, a + b * value))
        tag = el.attrs["data-ref"]
        stat = {"median": median(data), "mean": sum(data) / len(data),
                "average": sum(data) / len(data)}.get(tag)
        if stat is not None and abs(stat - value) > STAT_TOL:
            findings.append("%s: reference %r declares %g but the bound points give %g"
                            % (where, tag, value, stat))
        if re.sub(r"\s+", "", el.attrs.get("stroke-dasharray", "")) != "4,3":
            findings.append("%s: reference line must be dashed 4,3" % where)
        labels = [t for t in doc.elements if t.tag == "text"
                  and t.attrs.get("data-ref") == tag and t.attrs.get("data-role") == "label"]
        if len(labels) != 1 or not labels[0].body.strip():
            findings.append("%s: reference %r needs one direct label (data-ref + "
                            "data-role=\"label\")" % (where, tag))


def check_labels(doc, pts, findings, fname):
    named = [p for p in pts if p.name is not None]
    names = [p.name for p in named]
    for p in named:
        if not p.name.strip():
            findings.append("%s:%d: empty data-name" % (fname, p.el.line))
        elif names.count(p.name) > 1:
            findings.append("%s:%d: data-name %r is on more than one point"
                            % (fname, p.el.line, p.name))
    labels = {}
    for el in doc.elements:
        if (el.tag == "text" and el.attrs.get("data-role") == "label"
                and "data-name" in el.attrs):
            labels.setdefault(el.attrs["data-name"], []).append(el)
    for name in labels:
        if name not in names:
            findings.append("%s: label bound to unknown point %r" % (fname, name))
    for p in named:
        els = labels.get(p.name, [])
        if len(els) != 1:
            findings.append("%s: point %r needs exactly one direct label, found %d"
                            % (fname, p.name, len(els)))
            continue
        el = els[0]
        where = "%s:%d" % (fname, el.line)
        lx, ly = num(el.attrs.get("x")), num(el.attrs.get("y"))
        if lx is None or ly is None:
            findings.append("%s: label for %r needs numeric x and y" % (where, p.name))
            continue
        if el.body.strip() != p.name:
            findings.append("%s: label reads %r but is bound to %r" % (where, el.body.strip(), p.name))
        dist = ((lx - p.cx) ** 2 + (ly - p.cy) ** 2) ** 0.5
        if dist > LABEL_REACH:
            findings.append("%s: label for %r is %.0fpx from its point (max %g)"
                            % (where, p.name, dist, LABEL_REACH))
        for other in named:
            if other is not p and ((lx - other.cx) ** 2 + (ly - other.cy) ** 2) ** 0.5 < dist:
                findings.append("%s: label for %r sits nearer %r than its own point"
                                % (where, p.name, other.name))
    low = [n.casefold() for n in names if n.strip()]
    for el in doc.elements:
        if el.attrs.get("data-role") == "legend" or "data-legend" in el.attrs:
            findings.append("%s:%d: legend element; points are labelled in place" % (fname, el.line))
        if el.tag != "text":
            continue
        body = el.body.strip().casefold()
        if body == "legend":
            findings.append("%s:%d: LEGEND heading; remove it" % (fname, el.line))
        y = num(el.attrs.get("y"))
        if (y is not None and y >= LEGEND_Y and el.attrs.get("data-role") != "source"
                and any(body.startswith(n) for n in low)):
            findings.append("%s:%d: key text %r repeats a direct label"
                            % (fname, el.line, el.body.strip()))


def check_furniture(doc, pts, findings, fname):
    for el in doc.elements:
        where = "%s:%d" % (fname, el.line)
        t = el.attrs.get("transform", "")
        if t:
            kind = "rotated text" if el.tag == "text" and "rotate" in t.lower() else "transform"
            findings.append("%s: %s on <%s>; text stays horizontal and the checker reads "
                            "raw coordinates" % (where, kind, el.tag))
        if re.search(r"transform|rotate|translate|writing-mode", el.attrs.get("style", "").lower()):
            findings.append("%s: style moves or rotates <%s>" % (where, el.tag))
        if el.tag == "text" and re.search(r"vertical|sideways|^tb|^rl", el.attrs.get("writing-mode", "").lower()):
            findings.append("%s: vertical text" % where)
        if el.tag == "text" and el.attrs.get("fill", "").lower() == ACCENT:
            findings.append("%s: text painted in the accent" % where)
    if len(pts) > MAX_POINTS:
        findings.append("%s: %d points; at most %d (past that, bin or use small multiples)"
                        % (fname, len(pts), MAX_POINTS))
    if sum(1 for p in pts if p.el.attrs.get("stroke", "").lower() == ACCENT) > 1:
        findings.append("%s: more than one accent point; one focal point only" % fname)
    xs = [p.cx for p in pts]
    span = (max(xs) - min(xs)) * 0.5
    horiz, vert = [], []
    for el in doc.elements:
        if el.tag != "line" or any(k in el.attrs for k in ("data-axis", "data-ref", "data-trend")):
            continue
        g = hv(el.attrs)
        if not g:
            continue
        if abs(g[1] - g[3]) < 0.01 and abs(g[2] - g[0]) >= span:
            horiz.append(el)
        elif abs(g[0] - g[2]) < 0.01 and abs(g[3] - g[1]) >= span * 0.5:
            vert.append(el)
    grid = horiz + vert
    if horiz and vert:
        findings.append("%s: a full grid (horizontal and vertical rules); use range-frame "
                        "axes instead" % fname)
    if len(grid) > GRID_CAP:
        findings.append("%s: %d gridlines; at most %d" % (fname, len(grid), GRID_CAP))
    for el in grid:
        al = alpha(el.attrs.get("stroke", ""))
        if al is None or al > GRID_ALPHA_CEILING:
            findings.append("%s:%d: a gridline must be ink at %g or fainter"
                            % (fname, el.line, GRID_ALPHA_CEILING))
    srcs = [e for e in doc.elements if e.tag == "text" and e.attrs.get("data-role") == "source"]
    if len(srcs) != 1:
        findings.append("%s: expected exactly one <text data-role=\"source\">, found %d"
                        % (fname, len(srcs)))


def check_source_text(path: Path, raw: str) -> list:
    fname = path.name
    findings: list = []
    doc = parse_document(raw)
    pts = parse_points(doc, findings, fname)
    if len(pts) < MIN_POINTS:
        findings.append("%s: presents as a scatter plot but declares %d verifiable point(s); "
                        "each needs data-x, data-y, cx and cy, and the figure needs %d. "
                        "Refusing to report OK on a file this checker could not read"
                        % (fname, len(pts), MIN_POINTS))
        return findings
    check_furniture(doc, pts, findings, fname)
    xf, yf = check_scales(pts, findings, fname)
    check_labels(doc, pts, findings, fname)
    if xf is None:
        return findings
    check_axes_and_ticks(doc, pts, xf, yf, findings, fname)
    check_trend(doc, pts, xf, yf, findings, fname)
    check_reference(doc, pts, xf, yf, findings, fname)
    return findings


def check(path: Path) -> list:
    raw = path.read_text(encoding="utf-8")
    if not looks_like_scatter(path, raw):
        return []
    return check_source_text(path, raw)


def targets(args: argparse.Namespace) -> list:
    if args.all:
        return sorted(ASSET_DIR.glob("example-scatter*.html"))
    return [Path(p) for p in args.paths]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify scatter points, range frames, trend fit and reference "
                    "lines against the values they declare.")
    parser.add_argument("paths", nargs="*", help="HTML files to check")
    parser.add_argument("--all", action="store_true",
                        help="check every shipped example that presents as a scatter plot")
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
        if not looks_like_scatter(path, raw):
            skipped += 1
            continue
        findings.extend(check_source_text(path, raw))
        checked += 1
    for finding in findings:
        print(finding)
    tail = " (%d file(s) skipped as out of scope)" % skipped if skipped else ""
    if findings:
        print("\n%d scatter finding(s) across %d file(s).%s" % (len(findings), checked, tail))
        return 1
    if not checked:
        print("OK scatter: no scatter plot found to check%s" % tail)
        return 0
    print("OK scatter: %d file(s), shared x and y scales, range-frame axes, any trend "
          "equal to the least squares fit of its points, a labelled comparison line, "
          "at most %d points, and no rotated text%s" % (checked, MAX_POINTS, tail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
