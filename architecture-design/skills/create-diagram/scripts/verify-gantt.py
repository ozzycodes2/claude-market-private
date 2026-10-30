#!/usr/bin/env python3
"""Verify that a Gantt chart's drawn bars match the dates they are bound to.

A Gantt chart makes one claim: **bar position and length are time, on one
linear scale**. Break it and nothing errors - the figure renders, every task is
present, and the lie is in the geometry. `lint-skin.py` reads colors and fonts,
`verify-geometry.py` reads label masks, and neither compares a drawn bar
against the dates it stands for.

Invariants:

1. ONE TIME SCALE - the plot group declares `data-domain="t0 t1"` (any unit,
   usually weeks from the plan start) and `data-range="x0 x1"`, the pixels that
   domain spans. Every task bar declares `data-start` and `data-end`, and its
   left edge and right edge must sit where the shared scale puts them
   (ROUND_TOLERANCE of 0.75px for whole-pixel data coordinates). A bar stretched
   "to fit its label" moves a deadline.

2. EACH TASK NAMED ONCE - a task name is printed exactly once in the figure
   (the left column), never again inside or beside its bar. Text inside a bar
   may carry only a duration. Printing the name twice is the same fact drawn
   twice.

3. DENSITY - at most 24 tasks. Past that, split into small multiples with the
   same time scale.

4. REFERENCE LINES ON SCALE - a vertical line declaring `data-at="<t>"` (the
   today marker, `data-kind="today"`, or a period boundary, `data-kind="period"`)
   must sit at t on the same scale, and at most one today marker is drawn.

5. NO TRANSFORMS - a transform on a bound mark or an ancestor moves the
   rendered bar away from the coordinates checked here. All three carriers
   (attribute, inline style, <style> rule) are refused; so is any rotated text.

6. FAIL CLOSED - a file that presents as a Gantt chart but yields no
   parseable task is a finding, never a pass.

Markup is read through html.parser.HTMLParser, never a regex (see
verify-slopegraph.py for why).

WHAT THIS DOES NOT CHECK: absolute truth (a self-consistent plan with every
date wrong by one constant passes), dependencies, or that the labels in the
left column sit on the right row.

Usage:
    python3 scripts/verify-gantt.py --all
    python3 scripts/verify-gantt.py assets/example-gantt.html

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

MAX_TASKS = 24
ROUND_TOLERANCE = 0.75     # px, whole-pixel rounding of data coordinates
DURATION_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:d|w|wk|wks|h|hr|hrs|mo|days?|weeks?|hours?|months?)", re.IGNORECASE)

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
    return re.search(r"""data-plot\s*=\s*["']?gantt\b""",
                     HTML_COMMENT_RE.sub("", source), re.IGNORECASE) is not None


def looks_like_gantt(path: Path, source: str) -> bool:
    return path.name.startswith("example-gantt") or declares_plot(source)



class Scale:
    __slots__ = ("t0", "t1", "x0", "x1")

    def x(self, t: float) -> float:
        return self.x0 + (t - self.t0) / (self.t1 - self.t0) * (self.x1 - self.x0)


def parse_scale(doc: _Scanner, findings: list, name: str):
    if len(doc.plots) != 1:
        findings.append(
            "%s: found %d data-plot groups; a Gantt chart declares exactly one "
            '<g data-plot="gantt" data-domain="t0 t1" data-range="x0 x1">'
            % (name, len(doc.plots)))
        return None
    attrs = doc.plots[0].attrs
    domain = [number(v) for v in attrs.get("data-domain", "").replace(",", " ").split()]
    pixels = [number(v) for v in attrs.get("data-range", "").replace(",", " ").split()]
    if len(domain) != 2 or len(pixels) != 2 or None in domain or None in pixels:
        findings.append(
            "%s: the plot group needs numeric data-domain and data-range (two values "
            "each), or no bar on it can be verified" % name)
        return None
    scale = Scale()
    scale.t0, scale.t1 = domain
    scale.x0, scale.x1 = pixels
    if scale.t1 <= scale.t0 or scale.x1 <= scale.x0:
        findings.append("%s: the time domain or pixel range is empty or reversed; no scale "
                        "can be derived" % name)
        return None
    return scale


def check_transforms(doc: _Scanner, findings: list, name: str) -> None:
    def report(element, what, how):
        findings.append(
            "%s:%d: %s carries %s — this checker validates raw coordinates, so a "
            "transform moves the rendered mark away from the dates it was checked "
            "against. Bake the offset into the coordinates instead"
            % (name, element.line, what, how))

    for element in doc.marks:
        if "data-start" in element.attrs or "data-at" in element.attrs:
            how = transform_carrier(element.attrs) or element.ancestor
            if how is not None:
                report(element, "a bound mark (%s)" % (
                    element.attrs.get("data-name") or element.attrs.get("data-at")), how)
    for element in doc.texts:
        how = transform_carrier(element.attrs)
        if how is not None and "rotate" in how.lower():
            findings.append("%s:%d: rotated text (%s) — labels read horizontally"
                            % (name, element.line, how))
    for element in doc.styles:
        found = css_moves_mark(element.body)
        if found:
            findings.append(
                "%s:%d: a CSS `%s` declaration — this checker cannot tell which marks it "
                "applies to. Remove it, or bake the offset into the coordinates"
                % (name, element.line + element.body.count("\n", 0, found.start("prop")),
                   found.group("prop").lower()))


class Task:
    __slots__ = ("name", "start", "end", "x", "y", "w", "h", "line")


def parse_tasks(doc: _Scanner, scale: Scale, findings: list, name: str) -> list:
    tasks, seen = [], set()
    for element in doc.marks:
        attrs = element.attrs
        if element.tag != "rect" or ("data-start" not in attrs and "data-end" not in attrs):
            continue
        task = Task()
        task.name = attrs.get("data-name", "")
        task.line = element.line
        task.start, task.end = number(attrs.get("data-start")), number(attrs.get("data-end"))
        coords = [number(attrs.get(k)) for k in ("x", "y", "width", "height")]
        if not task.name or task.start is None or task.end is None or None in coords:
            findings.append(
                "%s:%d: a task bar needs data-name, numeric data-start and data-end, and "
                "numeric x/y/width/height; this one has %r" % (name, element.line, dict(attrs)))
            continue
        if not scale.t0 <= task.start < task.end <= scale.t1:
            findings.append(
                "%s:%d: task %r runs %g to %g, which is not a forward span inside the "
                "plan's domain %g to %g"
                % (name, element.line, task.name, task.start, task.end, scale.t0, scale.t1))
            continue
        if task.name in seen:
            findings.append("%s:%d: two tasks are named %r — one task, one bar"
                            % (name, element.line, task.name))
            continue
        seen.add(task.name)
        task.x, task.y, task.w, task.h = coords
        tasks.append(task)
    return tasks


def check_scale(tasks: list, scale: Scale, findings: list, name: str) -> None:
    for task in tasks:
        left, right = scale.x(task.start), scale.x(task.end)
        if abs(task.x - left) > ROUND_TOLERANCE:
            findings.append(
                "%s:%d: task %r starts at t=%g but its left edge is at x=%g where the "
                "shared scale puts it at %.1f — a bar off the time scale moves the date"
                % (name, task.line, task.name, task.start, task.x, left))
        if abs(task.x + task.w - right) > ROUND_TOLERANCE:
            findings.append(
                "%s:%d: task %r ends at t=%g but its right edge is at x=%g where the "
                "shared scale puts it at %.1f — its duration is not proportional to its "
                "dates" % (name, task.line, task.name, task.end, task.x + task.w, right))


def check_names(doc: _Scanner, tasks: list, findings: list, name: str) -> None:
    """Each task name is printed once; text inside a bar is only a duration."""
    printed = [(element, element.body.strip()) for element in doc.texts]
    for task in tasks:
        count = sum(1 for _e, body in printed if body == task.name)
        if count != 1:
            findings.append(
                "%s:%d: task %r is printed %d times — name each task exactly once, in the "
                "left column" % (name, task.line, task.name, count))
    for element, body in printed:
        x, y = number(element.attrs.get("x")), number(element.attrs.get("y"))
        if x is None or y is None:
            continue
        for task in tasks:
            inside = task.x <= x <= task.x + task.w and task.y <= y <= task.y + task.h + 1
            if inside and not DURATION_RE.fullmatch(body):
                findings.append(
                    "%s:%d: text %r sits inside task %r — in-bar text may carry only a "
                    "duration; the name belongs in the left column"
                    % (name, element.line, body[:24], task.name))


def check_lines(doc: _Scanner, scale: Scale, findings: list, name: str) -> None:
    today = 0
    for element in doc.marks:
        attrs = element.attrs
        if element.tag != "line" or "data-at" not in attrs:
            continue
        at = number(attrs["data-at"])
        kind = attrs.get("data-kind")
        coords = [number(attrs.get(k)) for k in ("x1", "x2")]
        if at is None or None in coords or kind not in ("today", "period"):
            findings.append(
                "%s:%d: a time line needs a numeric data-at, numeric x1/x2 and "
                "data-kind of 'today' or 'period'" % (name, element.line))
            continue
        today += kind == "today"
        expected = scale.x(at)
        if abs(coords[0] - coords[1]) > ROUND_TOLERANCE or abs(coords[0] - expected) > ROUND_TOLERANCE:
            findings.append(
                "%s:%d: the %s line for t=%g is drawn at x=%g where the shared scale puts "
                "it at %.1f" % (name, element.line, kind, at, coords[0], expected))
    if today > 1:
        findings.append("%s: %d today markers; a plan has one present" % (name, today))


def check_source(path: Path, raw: str) -> list:
    findings: list = []
    doc = _Scanner(raw)
    if doc.error is not None:
        return ["%s: presents as a Gantt chart but could not be parsed as HTML (%s) — "
                "refusing to report OK on a file this checker could not read"
                % (path.name, doc.error)]
    if declares_plot(raw) and not doc.plots:
        return ["%s: declares data-plot but no complete group could be parsed — an unclosed "
                "attribute quote swallows the tag; refusing to report OK" % path.name]
    scale = parse_scale(doc, findings, path.name)
    if scale is None:
        return findings
    tasks = parse_tasks(doc, scale, findings, path.name)
    if not tasks:
        findings.append(
            "%s: presents as a Gantt chart but declares no verifiable task — every bar rect "
            "needs data-name, data-start and data-end. Refusing to report OK on a file this "
            "checker could not read" % path.name)
        return findings
    if len(tasks) > MAX_TASKS:
        findings.append(
            "%s: %d tasks exceeds the cap of %d — split into small multiples on one time "
            "scale" % (path.name, len(tasks), MAX_TASKS))
    check_transforms(doc, findings, path.name)
    check_scale(tasks, scale, findings, path.name)
    check_names(doc, tasks, findings, path.name)
    check_lines(doc, scale, findings, path.name)
    return findings


def targets(args: argparse.Namespace) -> list:
    if args.all:
        return sorted(ASSET_DIR.glob("example-gantt*.html"))
    return [Path(p) for p in args.paths]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify Gantt bars against the dates they are bound to.")
    parser.add_argument("paths", nargs="*", help="HTML files to check")
    parser.add_argument("--all", action="store_true",
                        help="check every shipped example-gantt*.html")
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
        if not looks_like_gantt(path, raw):
            skipped += 1
            continue
        findings.extend(check_source(path, raw))
        checked += 1

    for finding in findings:
        print(finding)
    tail = " (%d file(s) skipped as out of scope)" % skipped if skipped else ""
    if findings:
        print("\n%d Gantt finding(s) across %d file(s).%s" % (len(findings), checked, tail))
        return 1
    if not checked:
        print("OK gantt: no Gantt chart found to check%s" % tail)
        return 0
    print("OK gantt: %d file(s), bars on one time scale, each task named once, at most %d "
          "tasks%s" % (checked, MAX_TASKS, tail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
