#!/usr/bin/env python3
"""Rewrite the worked examples from the shipped editorial skin to Mine Final.

The old skin reuses hexes across polarities — `#2d3142` is light `ink` and dark
`paper`, `#f5f5f5` is light `paper`, dark `ink` and `terminal-ink` — so a global
substitution corrupts every dark variant. Each file is classified from its own
`--color-paper` declaration and rewritten against the map for that polarity.

What this does not do: collapse the five-hue series palette, demote `link` to
ink at 1.2, move an accent off a `<text>`, or lift a traced mark from a hairline
to `soft`. Those are judgements about what a mark means, not substitutions.
Files needing them are reported under `structural` for a human or an agent to
finish.

Usage:
  reskin-assets.py [--dry-run] [--json] [ASSETS_DIR]

Exit status is 0 when every file was rewritten cleanly, 1 when a file could not
be classified.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent

# Old role -> new role, per polarity. Keys are lowercase #rrggbb.
LIGHT_HEX = {
    "#f5f5f5": "#f8f8f8",  # paper
    "#ececec": "#ffffff",  # paper-2
    "#2d3142": "#171717",  # ink
    "#111111": "#171717",  # ink-strong
    "#4f5d75": "#4d4d4d",  # muted
    "#5a6580": "#616161",  # soft
    "#bfc0c0": "#c6c6c6",  # rule-solid
    "#bf4520": "#ef6306",  # accent
    "#2e5aa8": "#171717",  # link -> ink; the caller must also set width 1.2
    # The gallery index ships its own warm paper, outside the role table. It is
    # a catalogue page rather than a diagram, so it joins the light polarity.
    "#f5f4ed": "#f8f8f8",
    "#efeee5": "#ffffff",
}

DARK_HEX = {
    "#2d3142": "#010102",  # paper
    "#393e53": "#0f1011",  # paper-2
    "#f5f5f5": "#f7f8f8",  # ink
    "#111111": "#171717",  # ink-strong
    "#bfc0c0": "#d0d6e0",  # muted
    "#949eb2": "#8a8f98",  # soft
    "#f08a59": "#ef6306",  # accent
    "#739fdf": "#f7f8f8",  # link -> ink
}

# rgba() washes are re-based onto the new role's triplet at the same opacity, so
# a 0.55 ink veil stays a 0.55 ink veil. lint-skin.py accepts an rgba() whose
# triplet matches a declared role, which is why re-basing is enough.
LIGHT_RGB = {
    (45, 49, 66): (23, 23, 23),  # ink
    (191, 69, 32): (239, 99, 6),  # accent
    (245, 245, 245): (248, 248, 248),  # paper
    (79, 93, 117): (77, 77, 77),  # muted
    (90, 101, 128): (97, 97, 97),  # soft
    (191, 192, 192): (198, 198, 198),  # rule-solid
}

DARK_RGB = {
    (245, 245, 245): (247, 248, 248),  # ink
    (240, 138, 89): (239, 99, 6),  # accent
    (45, 49, 66): (1, 1, 2),  # paper
    (191, 192, 192): (208, 214, 224),  # muted
    (148, 158, 178): (138, 143, 152),  # soft
}

# The series palette has no target: five hues is five chromas and this skin has
# one. Reported, never rewritten.
SERIES_HEX = {
    "#7c8f6f", "#5e7a9b", "#b8915a", "#9c6b50", "#6e6479",
    "#9caf8f", "#82a0c0", "#d3ad7a", "#b88670", "#8d8298",
}

# Terminal is an opt-in alternate skin that onboarding explicitly does not
# touch. Its palette is correct as shipped.
TERMINAL_PAPER = "#141414"

FONT_LINK = (
    "https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;1,400"
    "&family=Noto+Sans+KR:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;600&display=swap"
)
MONO_STACK = "'SF Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
RGBA_RE = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)")
# Two naming conventions ship side by side: the templates declare `--color-paper`
# and most examples declare a bare `--paper`.
PAPER_RE = re.compile(r"--(?:color-)?paper:\s*(#[0-9a-fA-F]{6})")
OLD_LIGHT_PAPER = "#f5f5f5"
GALLERY_PAPER = "#f5f4ed"
OLD_DARK_PAPER = {"#2d3142", "#393e53"}
NEW_PAPER = {"#f8f8f8": "light", "#010102": "dark", "#0f1011": "dark"}

# Values that mean the same role in both polarities, so they can be cleaned up
# without knowing which skin a file belongs to. A handful of assets were partly
# converted by an earlier pass and carry a light paper beside a dark accent;
# this is what catches the remainder.
RESIDUAL = {"#bf4520": "#ef6306", "#f08a59": "#ef6306"}
RESIDUAL_LINK = {"#2e5aa8", "#739fdf"}
RESIDUAL_RGB = {
    (191, 69, 32): (239, 99, 6),  # accent, light
    (240, 138, 89): (239, 99, 6),  # accent, dark
    (90, 101, 128): (97, 97, 97),  # soft, light — only ever appears light
}


def classify(text: str) -> str | None:
    """light, dark, terminal or done, read off the file's own paper declaration.

    `done` means the palette is already Mine Final and only the fonts are stale.
    A file with no paper declaration at all is classified from whichever old
    paper hex it carries, and is `done` when it carries none.
    """
    match = PAPER_RE.search(text)
    paper = match.group(1).lower() if match else None

    if paper == TERMINAL_PAPER:
        return "terminal"
    if paper in NEW_PAPER:
        return "done-" + NEW_PAPER[paper]
    if paper in {OLD_LIGHT_PAPER, GALLERY_PAPER}:
        return "light"
    if paper in OLD_DARK_PAPER:
        return "dark"
    if paper is not None:
        return None

    lowered = text.lower()
    if OLD_LIGHT_PAPER in lowered:
        return "light"
    if any(h in lowered for h in OLD_DARK_PAPER):
        return "dark"
    return "done"


SANS_STACK = "'Inter', system-ui, sans-serif"


def reskin_fonts(text: str) -> str:
    text = re.sub(r"https://fonts\.googleapis\.com/css2\?[^\"']+", FONT_LINK, text)
    text = re.sub(r"'Geist Mono',\s*ui-monospace,\s*monospace", MONO_STACK, text)
    text = text.replace("'Geist Mono'", "'SF Mono'")
    text = text.replace("'Geist'", "'Inter'")

    # The serif role is deleted, so the variable has no value left to resolve to
    # and every direct use of the face has to fall back to the sans.
    text = text.replace("var(--font-serif)", "var(--font-sans)").replace("var(--serif)", "var(--sans)")
    # Declarations appear minified on a shared line as well as on their own, and
    # under both the `--serif` and `--font-serif` names.
    text = re.sub(r"\s*--(?:font-)?serif:\s*'[^']*',\s*serif;?", "", text)
    text = re.sub(r"'Instrument Serif',\s*serif", SANS_STACK, text)
    # Noto's serif cuts went with the serif they backed.
    text = re.sub(r"'Noto Serif(?: KR| TC)?',\s*serif", SANS_STACK, text)

    # Unquoted stacks and the prose that names the retired faces. Mono first:
    # "Geist Mono" would otherwise be eaten by the "Geist" rule and leave
    # "Inter Mono", a family that does not exist.
    text = re.sub(r"Geist Mono,\s*monospace", MONO_STACK, text)
    text = re.sub(r"Geist,\s*sans-serif", "Inter, system-ui, sans-serif", text)
    text = text.replace("Geist Mono", "SF Mono").replace("Geist", "Inter")
    text = text.replace("Instrument Serif", "Inter")
    return text


def reskin_palette(text: str, polarity: str) -> str:
    hex_map = LIGHT_HEX if polarity == "light" else DARK_HEX
    rgb_map = LIGHT_RGB if polarity == "light" else DARK_RGB

    def sub_hex(match: re.Match[str]) -> str:
        return hex_map.get(match.group(0).lower(), match.group(0))

    def sub_rgba(match: re.Match[str]) -> str:
        triplet = tuple(int(match.group(i)) for i in (1, 2, 3))
        alpha = match.group(4)
        r, g, b = rgb_map.get(triplet, triplet)
        return f"rgba({r},{g},{b},{alpha})"

    return RGBA_RE.sub(sub_rgba, HEX_RE.sub(sub_hex, text))


def residual_cleanup(text: str, polarity: str) -> str:
    """Catch old accents and links in files an earlier pass left half-converted."""
    ink = "#171717" if polarity == "light" else "#f7f8f8"

    def sub_hex(match: re.Match[str]) -> str:
        value = match.group(0).lower()
        if value in RESIDUAL:
            return RESIDUAL[value]
        if value in RESIDUAL_LINK:
            return ink
        return match.group(0)

    def sub_rgba(match: re.Match[str]) -> str:
        triplet = tuple(int(match.group(i)) for i in (1, 2, 3))
        if triplet not in RESIDUAL_RGB:
            return match.group(0)
        r, g, b = RESIDUAL_RGB[triplet]
        return f"rgba({r},{g},{b},{match.group(4)})"

    return RGBA_RE.sub(sub_rgba, HEX_RE.sub(sub_hex, text))


def structural_findings(original: str, polarity: str) -> list[str]:
    """What substitution cannot fix, named so a human can finish it.

    Read against the *original*: substitution has already collapsed `link` into
    `ink` and the old accent into `#ef6306` by the time the file is written, so
    the evidence for both only exists before the rewrite.
    """
    lowered = original.lower()
    old_accent = "#bf4520" if polarity == "light" else "#f08a59"
    findings = []

    if any(h in lowered for h in SERIES_HEX):
        findings.append("series-palette")
    # An accent on a <text> is the override this skin exists to enforce. The
    # accent may arrive as a literal or through the token.
    for tag in re.findall(r"<text\b[^>]*>", lowered):
        if old_accent in tag or "var(--accent)" in tag or "var(--color-accent)" in tag:
            findings.append("accent-on-type")
            break
    if "#2e5aa8" in lowered or "#739fdf" in lowered or "var(--link)" in lowered:
        # Substitution gives these ink, but not the 1.2 weight that is the only
        # thing now separating an external call from an internal one.
        findings.append("link-weight")
    return sorted(set(findings))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite worked examples from the editorial skin to Mine Final.",
    )
    parser.add_argument("assets", nargs="?", default=str(SKILL_ROOT / "assets"),
                        help="directory of example HTML (default: the skill's assets/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change without writing")
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    args = parser.parse_args()

    assets = Path(args.assets)
    if not assets.is_dir():
        print(f"error: {assets} is not a directory", file=sys.stderr)
        return 1

    report: dict[str, object] = {"light": 0, "dark": 0, "terminal": 0, "done": 0,
                                 "unclassified": [], "structural": {}, "changed": 0}

    for path in sorted(assets.glob("*.html")):
        original = path.read_text(encoding="utf-8")
        polarity = classify(original)
        if polarity is None:
            report["unclassified"].append(path.name)  # type: ignore[union-attr]
            continue
        bucket = polarity if polarity in report else "done"
        report[bucket] = report[bucket] + 1  # type: ignore[operator]

        text = reskin_fonts(original)
        if polarity in {"light", "dark"}:
            text = reskin_palette(text, polarity)
        if polarity != "terminal":
            text = residual_cleanup(text, "dark" if polarity.endswith("dark") else "light")

        findings = structural_findings(original, "dark" if polarity.endswith("dark") else "light")
        if findings:
            report["structural"][path.name] = findings  # type: ignore[index]

        if text != original:
            report["changed"] = report["changed"] + 1  # type: ignore[operator]
            if not args.dry_run:
                path.write_text(text, encoding="utf-8")

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"light {report['light']}  dark {report['dark']}  terminal {report['terminal']}")
        print(f"rewritten: {report['changed']}")
        if report["structural"]:
            print(f"needs a judgement call: {len(report['structural'])} file(s)", file=sys.stderr)
            for name, findings in sorted(report["structural"].items()):  # type: ignore[union-attr]
                print(f"  {name}: {', '.join(findings)}", file=sys.stderr)
        if report["unclassified"]:
            print(f"unclassified: {report['unclassified']}", file=sys.stderr)

    return 1 if report["unclassified"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
