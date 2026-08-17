#!/usr/bin/env python3
"""Inventory a repo's documentation surface for drift review.

Read-only. Emits one JSON object to stdout; diagnostics go to stderr. No
third-party dependencies (Python 3.9+ stdlib only), so it runs anywhere the
review does.

The output feeds the docs-drift skill: it enumerates the docs tree, parses ADR
files and the ADR index so they can be cross-checked, guesses source->rendered
artifact pairs, and reports CHANGELOG/README presence.

Usage:
  docs_inventory.py [--repo-root DIR] [--docs-dir REL] [--adrs-dir REL]

Options:
  --repo-root DIR   Repository root (default: current directory).
  --docs-dir REL    Docs dir relative to repo root (default: docs).
  --adrs-dir REL    ADR dir relative to docs dir (default: adrs).
  -h, --help        Show this help.

Exit codes:
  0  inventory produced (even if the docs dir is absent — see docs_dir_exists)
  2  bad arguments
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DOC_EXTS = {".md", ".rst", ".txt", ".yaml", ".yml", ".adoc"}
RENDERED_EXTS = {".html", ".htm"}

STATUS_RE = re.compile(r"^\s*(?:[-*]\s*)?\*{0,2}status\*{0,2}\s*:?\s*(.+?)\s*$", re.I)
SUPERSEDES_RE = re.compile(r"supersed(?:es|ed by)\s+(\d{3,4})", re.I)
AMENDED_RE = re.compile(r"amend(?:s|ed by)\s+(\d{3,4})", re.I)
ADR_FILE_RE = re.compile(r"^(\d{3,4})[-_].+\.md$", re.I)
# A markdown table row that starts with a link to an ADR file.
INDEX_ROW_RE = re.compile(r"\|\s*\[?(\d{3,4})\]?[^|]*\|(.+)$")


def warn(msg: str) -> None:
    print(f"docs_inventory: {msg}", file=sys.stderr)


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:  # unreadable file — report, keep going
        warn(f"cannot read {p}: {e}")
        return ""


def parse_adr_file(p: Path) -> dict:
    text = read_text(p)
    status = None
    supersedes, amends = [], []
    for line in text.splitlines()[:40]:  # status lives near the top
        m = STATUS_RE.match(line)
        if m and status is None:
            status = m.group(1).strip()
        supersedes += SUPERSEDES_RE.findall(line)
        amends += AMENDED_RE.findall(line)
    num = p.name[:4].lstrip("0") or "0"
    return {
        "file": p.name,
        "number": num,
        "status": status,
        "supersedes_or_superseded_by": sorted(set(supersedes)),
        "amends_or_amended_by": sorted(set(amends)),
    }


def parse_index(index_path: Path) -> list[dict]:
    rows = []
    for line in read_text(index_path).splitlines():
        m = INDEX_ROW_RE.search(line)
        if not m:
            continue
        rest = m.group(2)
        # Last non-empty pipe-separated cell is usually Status.
        cells = [c.strip() for c in rest.split("|") if c.strip()]
        rows.append({"number": m.group(1).lstrip("0") or "0",
                     "status_cell": cells[-1] if cells else None})
    return rows


def guess_rendered_pairs(docs_dir: Path, repo_root: Path) -> list[dict]:
    """Pair a likely source with a likely generated artifact.

    Heuristics, not proof: an OpenAPI spec next to an .html render, or a .md
    whose stem matches an .html in the same tree. The skill confirms.
    """
    pairs = []
    rendered = [p for p in docs_dir.rglob("*") if p.suffix.lower() in RENDERED_EXTS]
    for html in rendered:
        stem = html.stem.lower()
        source = None
        for cand in html.parent.rglob("*"):
            if cand.suffix.lower() in {".yaml", ".yml", ".json", ".md"} and (
                cand.stem.lower() in {stem, "openapi", "index"} or stem in cand.stem.lower()
            ):
                source = cand
                break
        pairs.append({
            "rendered": str(html.relative_to(repo_root)),
            "likely_source": str(source.relative_to(repo_root)) if source else None,
        })
    return pairs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True, description="Inventory docs for drift review.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--docs-dir", default="docs")
    ap.add_argument("--adrs-dir", default="adrs")
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        warn(f"--repo-root not a directory: {repo_root}")
        return 2

    docs_dir = repo_root / args.docs_dir
    adrs_dir = docs_dir / args.adrs_dir

    docs_files = []
    if docs_dir.is_dir():
        for p in sorted(docs_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in DOC_EXTS | RENDERED_EXTS:
                docs_files.append(str(p.relative_to(repo_root)))
    else:
        warn(f"docs dir absent: {docs_dir} (inventory will be sparse)")

    adr_files, adr_index = [], []
    if adrs_dir.is_dir():
        for p in sorted(adrs_dir.iterdir()):
            if p.is_file() and ADR_FILE_RE.match(p.name):
                adr_files.append(parse_adr_file(p))
        for idx_name in ("README.md", "index.md"):
            idx = adrs_dir / idx_name
            if idx.is_file():
                adr_index = parse_index(idx)
                break

    def has(*names: str) -> str | None:
        for n in names:
            for cand in (repo_root / n, docs_dir / n):
                if cand.is_file():
                    return str(cand.relative_to(repo_root))
        return None

    out = {
        "repo_root": str(repo_root),
        "docs_dir": args.docs_dir,
        "docs_dir_exists": docs_dir.is_dir(),
        "docs_files": docs_files,
        "adr_files": adr_files,
        "adr_index": adr_index,
        "rendered_pairs": guess_rendered_pairs(docs_dir, repo_root) if docs_dir.is_dir() else [],
        "changelog": has("CHANGELOG.md", "CHANGELOG"),
        "readme": has("README.md", "README"),
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    warn(f"{len(docs_files)} doc files, {len(adr_files)} ADRs, "
         f"{len(adr_index)} index rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
