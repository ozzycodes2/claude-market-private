#!/usr/bin/env python3
"""Tests for verify-cards.py: mark citation and number-pair membership."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFIER = ROOT / "scripts/verify-cards.py"

PAGE = """\
<html><body>
<svg viewBox="0 0 400 200" role="img">
  <rect data-value="12" x="10" y="10" width="20" height="40"/>
  <rect data-values="12,18,25" x="40" y="10" width="20" height="40"/>
  <text x="10" y="190">S4</text>
  <text x="50" y="190">Sprint <tspan>5</tspan></text>
  <text x="90" y="190">Velocity 30</text>
  <text x="90" y="10">x</text>
</svg>
<div class="card">
  <div class="card-header"><span class="card-dot"></span><h3>Sprint 4 slipped</h3></div>
  <p>{prose}</p>
</div>
</body></html>
"""


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args], capture_output=True, text=True, check=False
    )


def check(directory: Path, name: str, prose: str, ok: bool, needle: str = "") -> None:
    path = directory / f"{name}.html"
    path.write_text(PAGE.format(prose=prose), encoding="utf-8")
    result = run([str(path)])
    if ok:
        assert result.returncode == 0, f"{name}: expected pass\n{result.stdout}"
        assert result.stdout.startswith("PASS "), result.stdout
    else:
        assert result.returncode == 1, f"{name}: expected fail\n{result.stdout}"
        assert 'FAIL' in result.stdout and 'card "Sprint 4 slipped"' in result.stdout, result.stdout
        assert needle in result.stdout, f"{name}: missing {needle!r}\n{result.stdout}"
    print(f"OK: {name} {'passes' if ok else 'fails'}")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        d = Path(raw)
        # Mark citation. The h3 itself cites S4? No: "Sprint 4" is not a mark; S4 is.
        check(d, "mark-cited-in-prose", "Cause: S4 lost two days.", True)
        check(d, "mark-case-insensitive", "Cause: s4 lost two days.", True)
        check(d, "mark-from-tspan-text", "Cause: Sprint 5 caught up.", True)
        check(d, "mark-missing", "Cause: a holiday week.", False, "names no mark")
        check(d, "mark-single-char-ignored", "Cause: x marks the spot.", False, "names no mark")
        check(d, "mark-whole-word-only", "Cause: S45 was long.", False, "names no mark")
        check(d, "mark-cited-in-list", "</p><ul><li>S4 lost two days</li></ul><p>", True)
        check(d, "mark-missing-in-list", "</p><ul><li>A holiday week</li></ul><p>", False, "names no mark")
        check(d, "pair-checked-in-list", "</p><ul><li>S4: 12 → 99</li></ul><p>", False, "99")
        h2 = d / "h2-heading.html"
        h2.write_text(PAGE.replace("<h3>Sprint 4 slipped</h3>", "<h2>Holiday week</h2>").format(prose="No cause."), encoding="utf-8")
        result = run([str(h2)])
        assert result.returncode == 1 and 'card "Holiday week"' in result.stdout, result.stdout
        print("OK: h2 heading is the card title")
        # Number pairs.
        check(d, "pair-arrow-in-data", "S4: 12 → 18 points.", True)
        check(d, "pair-tight-arrow", "S4: 12→25 points.", True)
        check(d, "pair-to-form", "S4: from 12 to 18 points.", True)
        check(d, "pair-in-svg-text", "S4: 18 to 30 points.", True)
        check(d, "pair-arrow-missing", "S4: 12 → 99 points.", False, "99")
        check(d, "pair-to-missing", "S4: from 7 to 18 points.", False, "7")
        check(d, "pair-percent-exempt", "S4: 5% to 8% better.", True)
        check(d, "pair-thousands", "S4: 1,200 to 18 points.", False, "1,200")

        # --all: sweeps -full pages with cards only; others are ignored.
        result = run(["--all"])
        assert result.returncode in (0, 1)
        assert "Traceback" not in result.stderr, result.stderr
        print("OK: --all runs")

        result = run([])
        assert result.returncode == 2, "no args must be a usage error"
        print("OK: usage error without args")

        nocard = d / "nocard.html"
        nocard.write_text("<svg><text>S4</text></svg>", encoding="utf-8")
        result = run([str(nocard)])
        assert result.returncode == 0 and result.stdout.startswith("PASS"), result.stdout
        print("OK: page without cards passes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
