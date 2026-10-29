#!/usr/bin/env python3
"""Check an HTML slide deck against the create-slides minimalism and brand rules.

Read-only. Prints a JSON report to stdout and exits 0 when the deck passes,
1 when it has findings, 2 when the deck or profile cannot be read.

Rules (references/minimalism.md):
  headline-words   h1/h2 longer than 7 words
  eyebrow-words    .eyebrow longer than 3 words
  slide-words      more than 25 visible words, excluding notes and diagram SVG
  text-layer       .sub, <p>, <ul>, or <ol> outside the speaker notes
  visual-count     content or statement slide without exactly one .visual,
                   or any slide with more than one
  diagram-source   inline <svg> missing create-diagram provenance: a root id
                   ending in -root, a non-empty first-child <title>, a <desc>
  xml-declaration  exported SVG pasted with its <?xml ...?> line
  off-brand-color  hex color outside the brand tokens and the diagram profile
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

MAX_HEADLINE_WORDS = 7
MAX_EYEBROW_WORDS = 3
MAX_SLIDE_WORDS = 25

DEFAULT_PROFILE = Path(__file__).resolve().parent.parent / "assets" / "machinify.diagram-profile.md"

BRAND_HEX = frozenset({
    "1F3539", "2B4A50", "4ECF99", "1A7A52", "FBAE40", "8A5A10", "CFE9BC",
    "BFD1DD", "171717", "F8F8F8", "EEEEEE", "081D27", "283B45", "5C6D76",
    "C3D0D9", "E2EAEF", "F7FBFD", "FFFFFF",
    "95E124", "B0DCFD", "005D97", "166F1C", "5546F6", "C71EC4", "855A2A",
})

# Slide types whose body must hold exactly one visual.
NEEDS_VISUAL = ("s-content", "s-statement")

VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "source", "track", "wbr",
})

# The guards skip entities (&#123;), url(#id) references, and id selectors
# such as #bad-root that happen to start with hex letters.
HEX_RE = re.compile(r"(?<![&\w(])#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![-\w])")
NON_COLOR_ATTRS = frozenset({"href", "xlink:href", "id", "class"})


def normalize_hex(raw: str) -> str:
    raw = raw.upper()
    if len(raw) == 3:
        return "".join(c * 2 for c in raw)
    return raw[:6]


def profile_hex(path: Path) -> set[str]:
    return {normalize_hex(m.group(1)) for m in HEX_RE.finditer(path.read_text(encoding="utf-8"))}


def word_count(text: str) -> int:
    """Count tokens with a letter or digit, so separators like "·" are free."""
    return sum(1 for token in text.split() if any(c.isalnum() for c in token))


class Slide:
    def __init__(self, number: int, classes: list[str]) -> None:
        self.number = number
        self.classes = classes
        self.visible: list[str] = []
        self.headlines: list[list[str]] = []
        self.eyebrows: list[list[str]] = []
        self.visuals = 0
        self.text_layers: list[str] = []
        self.svgs: list[dict] = []


class DeckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.slides: list[Slide] = []
        self.slide: Slide | None = None
        self.slide_depth = -1
        self.notes_depth = -1
        self.svg: dict | None = None
        self.svg_depth = -1
        self.colors: list[tuple[int, str]] = []
        self.xml_declarations: list[int] = []

    def _slide_number(self) -> int:
        return self.slide.number if self.slide else 0

    def _scan_colors(self, text: str) -> None:
        for match in HEX_RE.finditer(text):
            self.colors.append((self._slide_number(), match.group(0)))

    def _open(self, tag: str, attrs: list[tuple[str, str | None]], void: bool) -> None:
        attr = {k: v or "" for k, v in attrs}
        classes = set(attr.get("class", "").split())
        for name, value in attr.items():
            if name not in NON_COLOR_ATTRS:
                self._scan_colors(value)

        depth = len(self.stack)
        if tag == "section" and "slide" in classes and self.slide is None:
            self.slide = Slide(len(self.slides) + 1, sorted(classes))
            self.slides.append(self.slide)
            self.slide_depth = depth
        elif self.slide is not None:
            self._open_in_slide(tag, attr, classes, depth)

        if not void:
            self.stack.append((tag, classes))

    def _open_in_slide(self, tag: str, attr: dict, classes: set[str], depth: int) -> None:
        slide = self.slide
        assert slide is not None
        if self.svg is not None:
            if depth == self.svg_depth + 1:
                if self.svg["first_child"] is None:
                    self.svg["first_child"] = tag
                if tag == "desc":
                    self.svg["has_desc"] = True
            return
        if tag == "aside" and "notes" in classes:
            self.notes_depth = depth
            return
        if self.notes_depth >= 0:
            return
        if tag == "svg":
            self.svg = {"id": attr.get("id", ""), "first_child": None, "title": "", "has_desc": False}
            self.svg_depth = depth
            slide.svgs.append(self.svg)
        if "visual" in classes:
            slide.visuals += 1
        if "sub" in classes:
            slide.text_layers.append(".sub")
        if tag in ("p", "ul", "ol"):
            slide.text_layers.append(f"<{tag}>")
        if tag in ("h1", "h2"):
            slide.headlines.append([])
        if "eyebrow" in classes:
            slide.eyebrows.append([])

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, tag in VOID_TAGS)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, True)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                break
        else:
            return
        del self.stack[index:]
        if index <= self.svg_depth:
            self.svg, self.svg_depth = None, -1
        if index <= self.notes_depth:
            self.notes_depth = -1
        if index <= self.slide_depth:
            self.slide, self.slide_depth = None, -1

    def handle_pi(self, data: str) -> None:
        if data.lower().startswith("xml"):
            self.xml_declarations.append(self._slide_number())

    def handle_data(self, data: str) -> None:
        tags = [tag for tag, _ in self.stack]
        if "style" in tags:
            self._scan_colors(data)
            return
        if "script" in tags or self.slide is None or self.notes_depth >= 0:
            return
        if self.svg is not None:
            if tags[-1] == "title" and len(tags) - 1 == self.svg_depth + 1:
                self.svg["title"] += data
            return
        if any("bg-n" in classes for _, classes in self.stack):
            return
        self.slide.visible.append(data)
        in_headline = any(tag in ("h1", "h2") for tag in tags[self.slide_depth:])
        in_eyebrow = any("eyebrow" in classes for _, classes in self.stack[self.slide_depth:])
        if in_headline and self.slide.headlines:
            self.slide.headlines[-1].append(data)
        if in_eyebrow and self.slide.eyebrows:
            self.slide.eyebrows[-1].append(data)


def check_html(html: str, allowed_hex: set[str]) -> dict:
    parser = DeckParser()
    parser.feed(html)
    parser.close()
    findings: list[dict] = []

    def add(slide: int, rule: str, message: str) -> None:
        findings.append({"slide": slide, "rule": rule, "message": message})

    for slide in parser.slides:
        n = slide.number
        for parts in slide.headlines:
            text = " ".join("".join(parts).split())
            if word_count(text) > MAX_HEADLINE_WORDS:
                add(n, "headline-words", f"headline has {word_count(text)} words (max {MAX_HEADLINE_WORDS}): {text!r}")
        for parts in slide.eyebrows:
            text = " ".join("".join(parts).split())
            if word_count(text) > MAX_EYEBROW_WORDS:
                add(n, "eyebrow-words", f"eyebrow has {word_count(text)} words (max {MAX_EYEBROW_WORDS}): {text!r}")
        words = word_count(" ".join(slide.visible))
        if words > MAX_SLIDE_WORDS:
            add(n, "slide-words", f"{words} visible words (max {MAX_SLIDE_WORDS}); move prose to <aside class=\"notes\">")
        for layer in dict.fromkeys(slide.text_layers):
            add(n, "text-layer", f"{layer} outside the notes; drop it or move it to <aside class=\"notes\">")
        needs_one = any(kind in slide.classes for kind in NEEDS_VISUAL)
        if slide.visuals > 1 or (needs_one and slide.visuals != 1):
            add(n, "visual-count", f"{slide.visuals} elements with class \"visual\" (expected {'1' if needs_one else '0 or 1'})")
        for svg in slide.svgs:
            problems = []
            if not svg["id"].endswith("-root"):
                problems.append("root id does not end in -root")
            if svg["first_child"] != "title" or not svg["title"].strip():
                problems.append("first child is not a non-empty <title>")
            if not svg["has_desc"]:
                problems.append("no <desc>")
            if problems:
                add(n, "diagram-source", "inline <svg> was not exported by create-diagram: " + "; ".join(problems))

    for n in dict.fromkeys(parser.xml_declarations):
        add(n, "xml-declaration", "remove the <?xml ...?> line from the inlined SVG")

    seen: set[tuple[int, str]] = set()
    for n, raw in parser.colors:
        if normalize_hex(raw[1:]) in allowed_hex or (n, raw.upper()) in seen:
            continue
        seen.add((n, raw.upper()))
        add(n, "off-brand-color", f"{raw} is not a brand token or a Machinify diagram profile color")

    findings.sort(key=lambda f: (f["slide"], f["rule"]))
    return {"ok": not findings, "slides": len(parser.slides), "findings": findings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check an HTML deck against the create-slides minimalism and brand rules.",
        epilog="Exit 0 when clean, 1 with findings, 2 when a file cannot be read.",
    )
    parser.add_argument("deck", type=Path, help="deck .html file")
    parser.add_argument(
        "--profile",
        type=Path,
        default=DEFAULT_PROFILE,
        help="diagram profile whose colors are also allowed (default: the bundled Machinify profile)",
    )
    args = parser.parse_args(argv)

    try:
        html = args.deck.read_text(encoding="utf-8")
        allowed = BRAND_HEX | profile_hex(args.profile)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = check_html(html, set(allowed))
    report["deck"] = str(args.deck)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
