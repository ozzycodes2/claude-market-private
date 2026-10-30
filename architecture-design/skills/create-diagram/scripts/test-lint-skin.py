#!/usr/bin/env python3
"""Tests for lint-skin.py's Tufte checks: rotated text, LEGEND heading, source line."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LINTER = ROOT / "scripts/lint-skin.py"

SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" role="img"
     aria-labelledby="{slug}-title {slug}-desc">
  <title id="{slug}-title">Fixture diagram</title>
  <desc id="{slug}-desc">Diagram showing a fixture connected to a result.</desc>
  {body}
</svg>
"""


def lint(directory: Path, name: str, body: str) -> subprocess.CompletedProcess[str]:
    path = directory / f"{name}.html"
    slug = name.removeprefix("example-")
    path.write_text(SVG.format(body=body, slug=slug), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(LINTER), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def expect_finding(directory: Path, name: str, body: str, category: str) -> None:
    result = lint(directory, name, body)
    assert result.returncode == 1, f"{name}: expected exit 1\n{result.stdout}"
    assert f"{category}:" in result.stdout, f"{name}: missing {category}\n{result.stdout}"
    print(f"OK: {name} rejected - {category}")


def expect_clean(directory: Path, name: str, body: str) -> None:
    result = lint(directory, name, body)
    assert result.returncode == 0, f"{name}: expected exit 0\n{result.stdout}"
    print(f"OK: {name} accepted")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        d = Path(raw)
        expect_finding(
            d,
            "rotated",
            '<text x="10" y="20" fill="#171717" transform="rotate(-90 10 20)">Story points</text>',
            "rotated-text",
        )
        expect_finding(
            d,
            "rotated-multiline",
            '<text x="10" y="20"\n      transform="translate(4 4) rotate(90)">Axis</text>',
            "rotated-text",
        )
        expect_clean(
            d,
            "horizontal-text",
            '<text x="10" y="20" fill="#171717" transform="translate(4 4)">Story points</text>',
        )
        expect_clean(
            d,
            "rotated-non-text",
            '<g transform="rotate(45)"><rect width="4" height="4"/></g>',
        )
        expect_finding(
            d,
            "legend-heading",
            '<text x="30" y="20" fill="#171717">LEGEND</text>',
            "legend-heading",
        )
        expect_finding(
            d,
            "legend-tspan",
            '<text x="30" y="20" fill="#171717"><tspan>LEGEND</tspan></text>',
            "legend-heading",
        )
        expect_clean(
            d,
            "legend-word-in-sentence",
            '<text x="30" y="20" fill="#171717">Legend keys</text>',
        )
        expect_clean(
            d,
            "legend-in-longer-text",
            '<text x="30" y="20" fill="#171717">LEGENDARY</text>',
        )

        def src(inner: str, attrs: str = 'data-role="source"') -> str:
            return f'<text {attrs} x="30" y="580" fill="#4d4d4d" font-size="8">{inner}</text>'

        good = "Source: team tracker, 8 sprints to Oct 2026. Story points."
        expect_clean(d, "example-bar", src(good))
        expect_clean(d, "example-bar-dark", src(good))
        expect_clean(d, "example-bar-full", src(good))
        expect_clean(
            d,
            "example-line-tspan",
            src(
                'Source: team tracker, 8 sprints<tspan x="30" dy="12"> to Oct 2026. Story points.</tspan>'
            ),
        )
        expect_clean(d, "example-bar-judged", src("Source: team judgement. Positions."))
        expect_clean(d, "example-barfoo", "")  # prefix boundary: not a chart type
        expect_clean(d, "example-architecture", "")  # non-chart: no source needed
        expect_finding(d, "example-bar-missing", "", "source-line")
        expect_finding(
            d, "example-bar-twice", src(good) + src(good), "source-line"
        )
        expect_finding(
            d, "example-bar-prefix", src("Data from tracker, 2026."), "source-line"
        )
        expect_finding(
            d,
            "example-bar-noperiod",
            src("Source: team tracker. Story points, 2026."),
            "source-line",
        )
        expect_finding(
            d,
            "example-bar-norole",
            src(good, attrs=""),
            "source-line",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
