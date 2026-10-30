#!/usr/bin/env python3
"""Check that summary cards in a chart page are tied to the diagram.

For each element with class ``card`` (its heading, ``<h2>`` to ``<h4>``, plus all other text in it:
``<p>``, ``<li>``, and the rest):

1. Mark citation: the card text names at least one mark visible in the
   diagram, meaning a string equal (case-insensitive, trimmed) to the full text
   of some SVG ``<text>`` element, at least 2 characters long (a tick label,
   a node name, a series end label). Matching is on whole words.
2. Number-pair membership: every pair written ``X -> Y``, ``X→Y``, ``X to Y``
   or ``from X to Y`` (X and Y plain numbers, not percentages) has both X and
   Y in the file's bound data (``data-value``, ``data-values``, ``data-x``,
   ``data-y``, ``data-size``, ``data-start``, ``data-end``, ``data-domain``)
   or in the text of an SVG ``<text>``.

Not checked: derived numbers (percent change, averages) are not verified
against the data. Their arithmetic and their stated span ("+75% over 8
weeks") are a review item (SKILL.md section 9), not a machine check, and so is
the "at most one 'What the chart doesn't show' card" rule.

Usage: verify-cards.py FILE... | --all
``--all`` sweeps every assets/example-*-full.html that has ``.card`` elements.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

DATA_ATTRS = (
    "data-value", "data-values", "data-x", "data-y", "data-size",
    "data-start", "data-end", "data-domain",
)
HEADINGS = {"h2", "h3", "h4"}
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "wbr"}

NUMBER = r"\d+(?:,\d{3})*(?:\.\d+)?"
PAIR_RE = re.compile(
    rf"(?<![\w.,])({NUMBER})(?![\d%,]|\.\d)\s*(?:→|->|\s+to\s+)\s*({NUMBER})(?![\d%]|\.\d)"
)
NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.svg_depth = 0
        self.svg_texts: list[str] = []
        self.numbers: set[float] = set()
        self.cards: list[dict] = []
        self._text_open = None  # (depth, pieces)
        self._card_depths: list[int] = []  # depth at which each open card started
        self._in_h3 = False

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        attr_map = {k.casefold(): (v or "") for k, v in attrs}
        for name in DATA_ATTRS:
            if name in attr_map:
                self.numbers.update(
                    float(n) for n in NUMBER_RE.findall(attr_map[name])
                )
        void = tag in VOID_TAGS
        if not void:
            self.depth += 1
        if tag == "svg":
            self.svg_depth += 1
        if tag == "text" and self.svg_depth and self._text_open is None:
            self._text_open = (self.depth, [])
        if "card" in attr_map.get("class", "").split():
            self.cards.append({"h3": [], "p": []})
            self._card_depths.append(self.depth)
        if self._card_depths and not self.svg_depth:
            if tag in HEADINGS:
                self._in_h3 = True
                self.cards[-1]["h3"].append("")
            elif tag in ("p", "li"):
                self.cards[-1]["p"].append("")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.casefold() not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.casefold()
        if tag in VOID_TAGS:
            return
        if self._text_open is not None and tag == "text" and self._text_open[0] == self.depth:
            content = re.sub(r"\s+", " ", " ".join(self._text_open[1])).strip()
            self._text_open = None
            if content:
                self.svg_texts.append(content)
                self.numbers.update(
                    float(n.replace(",", ""))
                    for n in re.findall(NUMBER, content)
                )
        if tag == "svg" and self.svg_depth:
            self.svg_depth -= 1
        if tag in HEADINGS:
            self._in_h3 = False
        if self._card_depths and self._card_depths[-1] == self.depth:
            self._card_depths.pop()
        self.depth -= 1

    def handle_data(self, data):
        if self._text_open is not None:
            self._text_open[1].append(data)
        if self._card_depths and not self.svg_depth:
            bucket = self.cards[-1]["h3" if self._in_h3 else "p"]
            if not bucket:
                bucket.append("")
            bucket[-1] += data


def card_title(card):
    return re.sub(r"\s+", " ", " ".join(card["h3"])).strip()


def card_text(card):
    return re.sub(r"\s+", " ", " ".join(card["h3"] + card["p"])).strip()


def names_a_mark(text, marks):
    lowered = text.casefold()
    for mark in marks:
        pattern = rf"(?<!\w){re.escape(mark.casefold())}(?!\w)"
        if re.search(pattern, lowered):
            return True
    return False


def check_page(html):
    """Return (card_count, [(card_title, reason), ...])."""
    parser = PageParser()
    parser.feed(html)
    parser.close()
    marks = {t for t in parser.svg_texts if len(t) >= 2}
    failures = []
    for card in parser.cards:
        text = card_text(card)
        title = card_title(card)
        if not names_a_mark(text, marks):
            failures.append((title, "names no mark visible in the diagram"))
        for match in PAIR_RE.finditer(text):
            for group in (1, 2):
                raw = match.group(group)
                if float(raw.replace(",", "")) not in parser.numbers:
                    failures.append(
                        (title, f"number {raw} in \"{match.group(0)}\" is not in the chart data")
                    )
    return len(parser.cards), failures


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--all", action="store_true", help="sweep assets/example-*-full.html with cards")
    args = ap.parse_args()
    if args.all == bool(args.files):
        ap.error("provide either file arguments or --all")

    paths = sorted(ASSET_DIR.glob("example-*-full.html")) if args.all else args.files
    failed = False
    for path in paths:
        try:
            count, failures = check_page(path.read_text(encoding="utf-8"))
        except OSError as error:
            print(f"FAIL {path}: {error}")
            failed = True
            continue
        if args.all and count == 0:
            continue
        shown = path.name if args.all else str(path)
        if failures:
            failed = True
            for title, reason in failures:
                print(f'FAIL {shown}: card "{title}": {reason}')
        else:
            print(f"PASS {shown}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
