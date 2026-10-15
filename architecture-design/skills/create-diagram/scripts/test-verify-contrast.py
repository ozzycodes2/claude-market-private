#!/usr/bin/env python3
"""Adversarial tests for verify-contrast.py - both polarities, both skins.

Per ADR 0005, a contract is a checker plus fixtures proving it fires when it
should and stays quiet when it shouldn't. The red half matters most here: the
palette this gate replaced (issue #161) shipped because nothing computed a
ratio, so the first cases below restore that palette and require the gate to
name every token that failed, on the skin it failed on.

Cases:
- the shipped style guide passes (green);
- the retired palette fails on exactly the four tokens that were under their
  bars: light accent and soft, dark soft and link (red);
- a translucent value is composited over paper before it is measured, so a
  token that passes opaque fails at low alpha (red), and an rgba() at alpha 1
  measures the same as its hex (green);
- a token used as text is held to 4.5:1 even when it would clear the 3:1
  non-text bar (red);
- `ink-strong` is measured on the accent fill it sits on, not on paper (red);
- an unknown role, a missing role, and an unparseable value fail closed (red).

Usage: python3 scripts/test-verify-contrast.py
Exit: 0 all pass, 1 a case failed.
"""

from __future__ import annotations

import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/verify-contrast.py"
STYLE_GUIDE = ROOT / "references/style-guide.md"

NS = runpy.run_path(str(CHECKER), run_name="verify_contrast_test")
CHECK = NS["check"]
CONTRAST = NS["contrast"]
COMPOSITE = NS["composite"]
PARSE_COLOR = NS["parse_color"]

SHIPPED = STYLE_GUIDE.read_text(encoding="utf-8")

ROWS = {
    "soft": "| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `#616161` | `#8a8f98` |",
    "accent": "| `accent` | Focal / 1–2 max per diagram — **never text** | `{colors.primary}` | `#ef6306` | `#ef6306` |",
    "accent-deep": "| `accent-deep` | Focus rings only | `{colors.primary-focus}` | `#d65905` | `#d65905` |",
    "ink-strong": "| `ink-strong` | Text on the accent fill | `{colors.on-primary}` | `#171717` | `#171717` |",
}

failures: list[str] = []


def ok(condition: bool, message: str) -> None:
    if condition:
        print(f"OK: {message}")
    else:
        failures.append(message)


def with_row(source: str, role: str, replacement: str) -> str:
    row = ROWS[role]
    if source.count(row) != 1:
        raise SystemExit(f"fixture drift: the shipped `{role}` row changed; update ROWS")
    return source.replace(row, replacement)


def findings_for(source: str) -> list[str]:
    return CHECK(source)[1]


def mentions(findings: list[str], skin: str, role: str) -> bool:
    return any(f.startswith(f"{skin}: `{role}`") for f in findings)


def test_shipped_palette_passes() -> None:
    rows, findings = CHECK(SHIPPED)
    ok(not findings, f"the shipped style guide has no contrast findings ({findings})")
    ok(len(rows) == 18, f"every text and non-text use is measured in both skins ({len(rows)} rows)")


def test_swapped_polarities_fail_on_each_token() -> None:
    """The two skins are not an inversion of each other.

    Carrying a value across the polarity line is the authoring mistake this
    gate exists for: `soft` reads 5.83:1 on light paper and 6.42:1 on dark, but
    each value lands at about 3.1 and 3.4 on the *other* ground, under the 4.5
    its own row asks for. The accent is the exception — one chroma serves both
    polarities, so swapping its columns is a no-op and must stay unreported.
    """
    source = with_row(SHIPPED, "soft",
                      "| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `#8a8f98` | `#616161` |")
    findings = findings_for(source)
    for skin in ("light", "dark"):
        ok(mentions(findings, skin, "soft"), f"swapped {skin} `soft` is reported")
    ok(not mentions(findings, "light", "accent"), "the shared accent is not reported")
    ok(any("light: `soft` as text is 3.06:1" in f for f in findings),
       "the swapped light soft fails the 4.5:1 text bar at 3.06:1")
    code = run_cli(source)
    ok(code == 1, "the CLI exits 1 on a swapped polarity")

    lifted = with_row(SHIPPED, "accent",
                      "| `accent` | Focal / 1–2 max per diagram — **never text** | `{colors.primary}` | `#f26a0a` | `#ef6306` |")
    ok(any("light: `accent` as non-text is 2.89:1" in f for f in findings_for(lifted)),
       "an accent one step lighter fails the 3:1 non-text bar at 2.89:1")


def test_alpha_is_composited_over_paper() -> None:
    translucent = with_row(SHIPPED, "soft",
                           "| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `rgba(97,97,97,0.5)` | `#8a8f98` |")
    ok(mentions(findings_for(translucent), "light", "soft"),
       "soft at 0.5 opacity fails although the opaque value passes")
    opaque = with_row(SHIPPED, "soft",
                      "| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `rgba(97,97,97,1)` | `#8a8f98` |")
    ok(not findings_for(opaque), "rgba() at alpha 1 measures the same as its hex")
    flat = COMPOSITE((0, 0, 0), 0.5, (255, 255, 255))
    ok(flat == (127.5, 127.5, 127.5), "compositing blends channels linearly by alpha")


def test_text_use_is_held_to_text_bar() -> None:
    # `soft` carries both an axis and a sublabel, so it is the role where the
    # two bars diverge: #8a8f98 on light paper is enough for a stroke and not
    # enough for a label.
    rgb, _ = PARSE_COLOR("`#8a8f98`")
    ratio = CONTRAST(rgb, (248, 248, 248))
    ok(3.0 <= ratio < 4.5, f"fixture soft sits between the bars ({ratio:.2f}:1)")
    source = with_row(SHIPPED, "soft",
                      "| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `#8a8f98` | `#8a8f98` |")
    findings = findings_for(source)
    ok(any("light: `soft` as text" in f for f in findings),
       "a soft that clears 3:1 still fails as text")
    ok(not any("light: `soft` as non-text" in f for f in findings),
       "the same soft is not reported as a non-text failure")


def test_ink_strong_is_measured_on_accent_fill() -> None:
    # #5a5a5a on paper is 6.49:1, but on the solid accent fill it is 2.12:1.
    source = with_row(SHIPPED, "ink-strong",
                      "| `ink-strong` | Text on the accent fill | `{colors.on-primary}` | `#5a5a5a` | `#171717` |")
    ok(mentions(findings_for(source), "light", "ink-strong"),
       "ink-strong that reads on paper but not on the accent fill is reported")


def test_fails_closed() -> None:
    unknown = SHIPPED.replace(ROWS["accent-deep"], ROWS["accent-deep"] + "\n| `halo` | Glow | derived | `#ffffff` | `#000000` |")
    ok(any("`halo` has no contrast classification" in f for f in findings_for(unknown)),
       "an unclassified role is a finding")
    missing = SHIPPED.replace(ROWS["accent-deep"] + "\n", "")
    ok(any("`accent-deep` is missing" in f for f in findings_for(missing)), "a missing role is a finding")
    garbled = with_row(SHIPPED, "soft", "| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `slate` | `#8a8f98` |")
    ok(any("light: `soft` no hex or rgba() color" in f for f in findings_for(garbled)),
       "an unparseable value is a finding")
    no_table = SHIPPED.replace("### Semantic roles", "### Roles")
    ok(bool(findings_for(no_table)), "a style guide without the table fails")


def run_cli(source: str) -> int:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "style-guide.md"
        path.write_text(source, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--style-guide", str(path), "--quiet"],
            capture_output=True, text=True, check=False,
        )
        return result.returncode


def main() -> int:
    test_shipped_palette_passes()
    test_swapped_polarities_fail_on_each_token()
    test_alpha_is_composited_over_paper()
    test_text_use_is_held_to_text_bar()
    test_ink_strong_is_measured_on_accent_fill()
    test_fails_closed()
    ok(run_cli(SHIPPED) == 0, "the CLI exits 0 on the shipped style guide")

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\n{len(failures)} case(s) failed.")
        return 1
    print("\nOK verify-contrast: both polarities behave, on both skins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
