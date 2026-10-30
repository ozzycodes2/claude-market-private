#!/usr/bin/env python3
"""Verify that a bar chart's drawn bars match the values they are bound to.

A bar chart makes one claim: **bar length is proportional to value, measured
from zero, on one linear scale**. Break it and nothing errors - the figure
renders, every label is present, and the lie is in the geometry. `lint-skin.py`
reads colors and fonts, `verify-geometry.py` reads label masks, and neither
compares a drawn height against the number printed above it.

Invariants, each of which a bar chart has shipped broken:

1. ZERO BASELINE - the plot group declares `data-domain="lo hi"` and `lo` must
   be 0. A bar on a domain that starts above zero draws a small difference as
   a large one (Tufte's lie factor). The brief allows a drawn, stated axis
   break; this checker does not resolve one, so a broken axis is refused here
   rather than half-verified.

2. LENGTH PROPORTIONAL TO VALUE - every bar rect declares `data-value`; its
   height (vertical) or width (horizontal) must equal the shared scale applied
   to that value, and it must start on the declared baseline. The scale comes
   from the plot group: `data-baseline` is the pixel position of the domain
   floor and `data-top` the pixel position of the domain ceiling (the right
   edge, for `data-orient="horizontal"`). Data coordinates are rounded to whole
   pixels, so ROUND_TOLERANCE allows 0.75px, never a visible distortion.

3. PRINTED VALUE EQUALS BOUND VALUE - every bar has exactly one label bound to
   it by `data-for="<name>"`, and the whole numeric token it prints equals the
   bar's `data-value`. A label bound to no bar is reported, as is a bar with
   none: an unlabelled bar is a mark whose value the reader cannot check.

4. EACH VALUE ENCODED ONCE - with a printed value on every bar, a gridline, a
   value-axis line, or a tick-label scale draws the same number a second time.
   Any full-width rule other than the zero baseline and the declared reference
   line, and any run of numeric tick labels beside the bars, is refused. The
   zero baseline itself stays.

5. NO ROTATED TEXT, NO TRANSFORMS - a transform on a bound mark, its label, or
   an ancestor moves the rendered mark away from the raw coordinates checked
   here. All three carriers (attribute, inline style, <style> rule) are
   refused. Rotated text is refused anywhere: the axis title is horizontal.

6. REFERENCE LINE ON SCALE - a line declaring `data-reference="<value>"` must
   sit at that value on the same scale as the bars.

7. DENSITY - at most 16 bars. Past that, sorted horizontal bars or small
   multiples.

8. FAIL CLOSED - a file that presents as a bar chart but yields no parseable
   bars is a finding, never a pass.

Markup is read through html.parser.HTMLParser, never a regex, so a tag is
recognised exactly when a browser would recognise it (see verify-slopegraph.py
for the failure modes a regex tag matcher has).

WHAT THIS DOES NOT CHECK: absolute truth (a self-consistent figure with every
value wrong by one constant passes), negative values (the grammar is bars up
from zero), or stacked and grouped variants.

Usage:
    python3 scripts/verify-bar.py --all
    python3 scripts/verify-bar.py assets/example-bar.html

Exit: 0 clean, 1 findings, 2 usage.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

MAX_BARS = 16
ROUND_TOLERANCE = 0.75     # px, whole-pixel rounding of data coordinates
VALUE_TOLERANCE = 0.001    # printed label vs bound value
RULE_SHARE = 0.5           # a rule this share of the plot is a gridline or axis

CSS_MOVES_MARK_RE = re.compile(
    r"(?:^|[{;}\n])\s*(?:-(?:webkit|moz|ms|o)-)?"
    r"(?P<prop>transform|translate|rotate|scale|x1|y1|x2|y2|x|y"
    r"|offset(?:-(?:path|distance|position|anchor|rotate))?)\s*:",
    re.IGNORECASE,
)
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
NUMBER_RE = re.compile(
    r"[-+]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
)
DIGIT_RE = re.compile(r"\d")
NUMERIC_ONLY_RE = re.compile(r"[\d.,%+\-−]+")

GROUP_TAGS = ("g", "svg")
BODY_TAGS = ("text", "title", "desc", "style")
MARK_TAGS = ("rect", "line")


class Element:
    __slots__ = ("tag", "attrs", "line", "body", "ancestor")

    def __init__(self, tag, attrs, line, ancestor):
        self.tag, self.attrs, self.line = tag, attrs, line
        self.body = ""
        self.ancestor = ancestor


def first_wins(attrs) -> dict:
    """Attributes as the browser keeps them: on a repeat the FIRST wins."""
    seen = {}
    for name, value in attrs:
        seen.setdefault(name, "" if value is None else value)
    return seen


def css_moves_mark(css: str):
    """The first mark-moving declaration in CSS text, read past comments, or None."""
    stripped = CSS_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), css)
    return CSS_MOVES_MARK_RE.search(stripped)


def transform_carrier(attrs: dict):
    """How this element carries a transform, phrased for a finding, or None."""
    if "transform" in attrs:
        return "transform=%r" % attrs["transform"]
    style = attrs.get("style")
    if style is not None:
        found = css_moves_mark(style)
        if found is not None:
            return "style=%r (the %s property)" % (style, found.group("prop").lower())
    return None


class _Scanner(HTMLParser):
    """Collect rects, lines, texts, plot groups and style blocks with ancestry."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.marks: list = []      # rect and line elements
        self.texts: list = []
        self.styles: list = []
        self.named: list = []      # title and desc
        self.plots: list = []      # g elements declaring data-plot
        self.error = None
        self._groups: list = []
        self._open: list = []
        self._starts = [0]
        for index, char in enumerate(source):
            if char == "\n":
                self._starts.append(index + 1)
        try:
            self.feed(source)
            self.close()
        except Exception as exc:  # noqa: BLE001 - any parser failure fails closed
            self.error = "%s: %s" % (type(exc).__name__, exc)

    def _ancestor(self):
        for _tag, how in reversed(self._groups):
            if how is not None:
                return how
        return None

    def handle_starttag(self, tag, attrs):
        self._start(tag, first_wins(attrs), closes=False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, first_wins(attrs), closes=True)

    def _start(self, tag, attrs, closes):
        line = self.getpos()[0]
        if tag in GROUP_TAGS:
            if "data-plot" in attrs:
                self.plots.append(Element(tag, attrs, line, self._ancestor()))
            if not closes:
                how = None
                if "transform" in attrs:
                    how = "an ancestor <g>/<svg> transform"
                elif transform_carrier(attrs) is not None:
                    how = "an ancestor <g>/<svg> style transform"
                self._groups.append((tag, how))
            return
        if tag not in MARK_TAGS and tag not in BODY_TAGS:
            return
        element = Element(tag, attrs, line, self._ancestor())
        if tag in MARK_TAGS:
            self.marks.append(element)
            return
        {"text": self.texts, "style": self.styles}.get(tag, self.named).append(element)
        if not closes:
            self._open.append((tag, element))

    def handle_endtag(self, tag):
        stack = self._groups if tag in GROUP_TAGS else self._open if tag in BODY_TAGS else None
        if stack is None:
            return
        for index in range(len(stack) - 1, -1, -1):
            if stack[index][0] == tag:
                del stack[index:]
                return

    def handle_data(self, data):
        if self._open:
            self._open[-1][1].body += data


def number(value):
    """A finite float from a complete numeric token, or None."""
    if value is None:
        return None
    try:
        parsed = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def printed_number(body: str):
    """(value, reason): a value only when the text holds exactly one numeric token."""
    match = NUMBER_RE.search(body)
    if match is None:
        return None, "prints no number"
    outside = body[:match.start()] + body[match.end():]
    if DIGIT_RE.search(outside):
        return None, "prints more than one numeric token"
    value = number(match.group())
    if value is None:
        return None, "prints a number this checker cannot read"
    return value, None


def declares_plot(source: str) -> bool:
    return re.search(r"""data-plot\s*=\s*["']?bar\b""",
                     HTML_COMMENT_RE.sub("", source), re.IGNORECASE) is not None


def looks_like_bar(path: Path, source: str) -> bool:
    return path.name.startswith("example-bar") or declares_plot(source)


class Plot:
    __slots__ = ("orient", "lo", "hi", "baseline", "top")

    def span(self) -> float:
        return self.top - self.baseline

    def position(self, value: float) -> float:
        """Pixel coordinate of a value: y for vertical bars, x for horizontal."""
        return self.baseline + (value - self.lo) / (self.hi - self.lo) * self.span()


def parse_plot(doc: _Scanner, findings: list, name: str):
    if len(doc.plots) != 1:
        findings.append(
            "%s: found %d data-plot groups; a bar chart declares exactly one "
            '<g data-plot="bar" data-domain="lo hi" data-baseline=".." data-top="..">'
            % (name, len(doc.plots))
        )
        return None
    attrs = doc.plots[0].attrs
    plot = Plot()
    plot.orient = attrs.get("data-orient", "vertical")
    if plot.orient not in ("vertical", "horizontal"):
        findings.append("%s: data-orient=%r is neither 'vertical' nor 'horizontal'"
                        % (name, plot.orient))
        return None
    domain = attrs.get("data-domain", "").replace(",", " ").split()
    bounds = [number(d) for d in domain]
    plot.baseline = number(attrs.get("data-baseline"))
    plot.top = number(attrs.get("data-top"))
    if len(bounds) != 2 or None in bounds or plot.baseline is None or plot.top is None:
        findings.append(
            "%s: the plot group needs a numeric data-domain (two values), data-baseline "
            "and data-top, or no bar on it can be verified" % name)
        return None
    plot.lo, plot.hi = bounds
    if plot.hi <= plot.lo or plot.top == plot.baseline:
        findings.append("%s: the domain or pixel span is empty; no scale can be derived" % name)
        return None
    if plot.lo != 0:
        findings.append(
            "%s: the value domain starts at %g, not 0 — bars encode value by length "
            "from a zero baseline, and a raised floor draws every difference larger "
            "than the data" % (name, plot.lo))
        return None
    return plot


def check_transforms(doc: _Scanner, findings: list, name: str) -> None:
    def report(element, what, how):
        findings.append(
            "%s:%d: %s carries %s — this checker validates raw coordinates, so a "
            "transform moves the rendered mark away from the number it was checked "
            "against. Bake the offset into the coordinates instead"
            % (name, element.line, what, how))

    for element in doc.marks:
        if "data-value" in element.attrs or "data-reference" in element.attrs:
            how = transform_carrier(element.attrs) or element.ancestor
            if how is not None:
                report(element, "a bound mark (%s)" % (
                    element.attrs.get("data-name") or element.attrs.get("data-reference")), how)
    for element in doc.texts:
        how = transform_carrier(element.attrs)
        if how is not None and "rotate" in how.lower():
            findings.append(
                "%s:%d: rotated text (%s) — axis titles are horizontal, above the plot"
                % (name, element.line, how))
        elif "data-for" in element.attrs:
            how = how or element.ancestor
            if how is not None:
                report(element, "a bound label (%s)" % element.body.strip()[:20], how)
    for element in doc.styles:
        found = css_moves_mark(element.body)
        if found:
            findings.append(
                "%s:%d: a CSS `%s` declaration — this checker cannot tell which marks it "
                "applies to. Remove it, or bake the offset into the coordinates"
                % (name, element.line + element.body.count("\n", 0, found.start("prop")),
                   found.group("prop").lower()))


class Bar:
    __slots__ = ("name", "value", "x", "y", "w", "h", "line")


def parse_bars(doc: _Scanner, findings: list, name: str) -> list:
    bars, seen = [], set()
    for element in doc.marks:
        attrs = element.attrs
        if element.tag != "rect" or "data-value" not in attrs:
            continue
        bar = Bar()
        bar.name = attrs.get("data-name", "")
        bar.line = element.line
        bar.value = number(attrs.get("data-value"))
        coords = [number(attrs.get(k)) for k in ("x", "y", "width", "height")]
        if not bar.name or bar.value is None or None in coords:
            findings.append(
                "%s:%d: a bar needs data-name, a numeric data-value and numeric "
                "x/y/width/height; this one has %r" % (name, element.line, dict(attrs)))
            continue
        if bar.value < 0:
            findings.append(
                "%s:%d: bar %r has a negative value; this grammar draws bars up from zero"
                % (name, element.line, bar.name))
            continue
        if bar.name in seen:
            findings.append("%s:%d: two bars are named %r — one category, one bar"
                            % (name, element.line, bar.name))
            continue
        seen.add(bar.name)
        bar.x, bar.y, bar.w, bar.h = coords
        bars.append(bar)
    return bars


def check_geometry(bars: list, plot: Plot, findings: list, name: str) -> None:
    for bar in bars:
        expected_far = plot.position(bar.value)
        if plot.orient == "vertical":
            drawn_start, drawn_far = bar.y + bar.h, bar.y
            unit = "height"
        else:
            drawn_start, drawn_far = bar.x, bar.x + bar.w
            unit = "width"
        if abs(drawn_start - plot.baseline) > ROUND_TOLERANCE:
            findings.append(
                "%s:%d: bar %r starts at %g, not on the zero baseline at %g — a bar "
                "off the baseline no longer encodes its value by length"
                % (name, bar.line, bar.name, drawn_start, plot.baseline))
        if abs(drawn_far - expected_far) > ROUND_TOLERANCE:
            findings.append(
                "%s:%d: bar %r (%g) draws its far edge at %g where the shared scale puts "
                "%g at %.1f — its %s is not proportional to its value"
                % (name, bar.line, bar.name, bar.value, drawn_far, bar.value,
                   expected_far, unit))


def check_labels(doc: _Scanner, bars: list, findings: list, name: str) -> bool:
    """Every bar has exactly one bound label, and it prints the bound value."""
    bound: dict = {}
    for element in doc.texts:
        target = element.attrs.get("data-for")
        if target is None:
            continue
        bound.setdefault(target, []).append(element)
    names = {bar.name for bar in bars}
    complete = True
    for target, elements in bound.items():
        if target not in names:
            findings.append(
                "%s:%d: a label is bound to %r, which no bar declares — a label with no "
                "mark reads as data" % (name, elements[0].line, target))
    for bar in bars:
        elements = bound.get(bar.name, [])
        if not elements:
            findings.append(
                "%s:%d: bar %r prints no value label (data-for=%r) — an unlabelled bar "
                "asks the reader to take its length on trust" % (name, bar.line, bar.name, bar.name))
            complete = False
            continue
        if len(elements) > 1:
            findings.append(
                "%s:%d: bar %r has %d value labels — one mark, one label"
                % (name, elements[1].line, bar.name, len(elements)))
        shown, reason = printed_number(elements[0].body.strip())
        if shown is None:
            findings.append("%s:%d: the label for bar %r %s (%r)"
                            % (name, elements[0].line, bar.name, reason, elements[0].body.strip()[:28]))
        elif abs(shown - bar.value) > VALUE_TOLERANCE:
            findings.append(
                "%s:%d: bar %r prints %r but is bound to %g — the label and the geometry "
                "must state one number"
                % (name, elements[0].line, bar.name, elements[0].body.strip(), bar.value))
    return complete


def check_reference(doc: _Scanner, plot: Plot, findings: list, name: str) -> None:
    for element in doc.marks:
        declared = element.attrs.get("data-reference")
        if element.tag != "line" or declared is None:
            continue
        value = number(declared)
        coords = [number(element.attrs.get(k)) for k in ("x1", "y1", "x2", "y2")]
        if value is None or None in coords:
            findings.append("%s:%d: a reference line needs a numeric data-reference and "
                            "numeric x1/y1/x2/y2" % (name, element.line))
            continue
        drawn = coords[1] if plot.orient == "vertical" else coords[0]
        flat = abs(coords[1] - coords[3]) if plot.orient == "vertical" else abs(coords[0] - coords[2])
        expected = plot.position(value)
        if flat > ROUND_TOLERANCE or abs(drawn - expected) > ROUND_TOLERANCE:
            findings.append(
                "%s:%d: the reference line for %g is drawn at %g where the shared scale "
                "puts it at %.1f — a comparison line off the bars' scale compares nothing"
                % (name, element.line, value, drawn, expected))


def check_encoded_once(doc: _Scanner, bars: list, plot: Plot, findings: list, name: str) -> None:
    """With a value printed on every bar, gridlines and a tick scale repeat it."""
    if not bars:
        return
    if plot.orient == "vertical":
        extent = max(b.x + b.w for b in bars) - min(b.x for b in bars)
        depth = abs(plot.span())
    else:
        extent = max(b.y + b.h for b in bars) - min(b.y for b in bars)
        depth = abs(plot.span())
    for element in doc.marks:
        attrs = element.attrs
        if element.tag != "line" or "data-reference" in attrs:
            continue
        x1, y1, x2, y2 = [number(attrs.get(k)) for k in ("x1", "y1", "x2", "y2")]
        if None in (x1, y1, x2, y2):
            continue
        along_x = abs(y1 - y2) <= ROUND_TOLERANCE      # a horizontal rule
        along_y = abs(x1 - x2) <= ROUND_TOLERANCE      # a vertical rule
        if plot.orient == "vertical":
            value_rule = along_x and abs(x2 - x1) >= RULE_SHARE * extent
            on_baseline = abs(y1 - plot.baseline) <= ROUND_TOLERANCE
            axis_rule = along_y and abs(y2 - y1) >= RULE_SHARE * depth
        else:
            value_rule = along_y and abs(y2 - y1) >= RULE_SHARE * extent
            on_baseline = abs(x1 - plot.baseline) <= ROUND_TOLERANCE
            axis_rule = along_x and abs(x2 - x1) >= RULE_SHARE * depth
        if value_rule and not on_baseline:
            findings.append(
                "%s:%d: a full-width rule across the plot that is not the zero baseline — "
                "every bar prints its value, so a gridline draws the same number twice"
                % (name, element.line))
        elif axis_rule:
            findings.append(
                "%s:%d: a value-axis line beside the bars — every bar prints its value, so "
                "the axis repeats it. Keep the zero baseline only" % (name, element.line))
    left = min(b.x for b in bars)
    bottom = max(b.y + b.h for b in bars)
    for element in doc.texts:
        attrs = element.attrs
        body = element.body.strip()
        if "data-for" in attrs or not NUMERIC_ONLY_RE.fullmatch(body):
            continue
        x, y = number(attrs.get("x")), number(attrs.get("y"))
        if x is None or y is None:
            continue
        beside = plot.orient == "vertical" and attrs.get("text-anchor") == "end" and x < left
        below = plot.orient == "horizontal" and y >= bottom + 4
        if beside or below:
            findings.append(
                "%s:%d: a numeric tick label %r on the value axis — every bar prints its "
                "value, so a tick scale repeats it" % (name, element.line, body))


def check_source(path: Path, raw: str) -> list:
    findings: list = []
    doc = _Scanner(raw)
    if doc.error is not None:
        return ["%s: presents as a bar chart but could not be parsed as HTML (%s) — refusing "
                "to report OK on a file this checker could not read" % (path.name, doc.error)]
    if declares_plot(raw) and not doc.plots:
        return ["%s: declares data-plot but no complete group could be parsed — an unclosed "
                "attribute quote swallows the tag; refusing to report OK" % path.name]
    plot = parse_plot(doc, findings, path.name)
    if plot is None:
        return findings
    bars = parse_bars(doc, findings, path.name)
    if not bars:
        findings.append(
            "%s: presents as a bar chart but declares no verifiable bar — every bar rect "
            "needs data-name and data-value. Refusing to report OK on a file this checker "
            "could not read" % path.name)
        return findings
    if len(bars) > MAX_BARS:
        findings.append(
            "%s: %d bars exceeds the cap of %d — past it, sort and draw horizontal bars or "
            "split into small multiples" % (path.name, len(bars), MAX_BARS))
    check_transforms(doc, findings, path.name)
    check_geometry(bars, plot, findings, path.name)
    labelled = check_labels(doc, bars, findings, path.name)
    check_reference(doc, plot, findings, path.name)
    if labelled:
        check_encoded_once(doc, bars, plot, findings, path.name)
    return findings


def targets(args: argparse.Namespace) -> list:
    if args.all:
        return sorted(ASSET_DIR.glob("example-bar*.html"))
    return [Path(p) for p in args.paths]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify bar lengths against the values they are bound to.")
    parser.add_argument("paths", nargs="*", help="HTML files to check")
    parser.add_argument("--all", action="store_true",
                        help="check every shipped example-bar*.html")
    args = parser.parse_args(argv)
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
        if not looks_like_bar(path, raw):
            skipped += 1
            continue
        findings.extend(check_source(path, raw))
        checked += 1

    for finding in findings:
        print(finding)
    tail = " (%d file(s) skipped as out of scope)" % skipped if skipped else ""
    if findings:
        print("\n%d bar finding(s) across %d file(s).%s" % (len(findings), checked, tail))
        return 1
    if not checked:
        print("OK bar: no bar chart found to check%s" % tail)
        return 0
    print("OK bar: %d file(s), length proportional to value from a zero baseline, every "
          "printed label equal to its bound value, each value encoded once%s" % (checked, tail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
