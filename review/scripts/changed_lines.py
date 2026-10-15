#!/usr/bin/env python3
"""Filter a static analyzer's findings down to the lines a PR actually changed.

semgrep, bandit and gosec report per file, not per hunk, so a thirty-line change
to a two-thousand-line module returns findings on all two thousand lines. They
are real, they are not this PR's, and the author defers them round after round.

    gh pr diff "$PR_URL" > /tmp/pr.diff
    semgrep --config=auto --json ... \\
      | python3 changed_lines.py filter --diff /tmp/pr.diff --tool semgrep \\
      > semgrep-results.json

Reads the analyzer's JSON on stdin, writes the same shape on stdout, and prints
the drop count to stderr. `map` dumps the parsed diff instead, for debugging.

Changed means **added**: lines prefixed `+` in the unified diff. A hunk's
context lines are unchanged code the analyzer would have flagged on the base
branch too.
"""
import argparse
import json
import re
import sys

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_diff(text):
    """Map each file in a unified diff to the set of line numbers it adds.

    Line numbers are NEW-file, which is what every analyzer reports against.
    Deleted files are absent from the result: they add no lines, so nothing
    the analyzer says about them can be this PR's doing.
    """
    changed = {}
    path = None
    lineno = 0
    for line in text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].split("\t", 1)[0].strip()
            path = None if target == "/dev/null" else _strip_prefix(target)
            continue
        if line.startswith("@@"):
            m = _HUNK.match(line)
            lineno = int(m.group(1)) if m else 0
            continue
        if path is None or not lineno:
            continue
        if line.startswith("+"):
            changed.setdefault(path, set()).add(lineno)
            lineno += 1
        elif line.startswith("-") or line.startswith("\\"):
            pass  # removed line, or "\ No newline at end of file"
        else:
            lineno += 1
    return changed


def _strip_prefix(path):
    """Drop git's `b/` diff prefix and any `./`."""
    if path.startswith("b/"):
        path = path[2:]
    while path.startswith("./"):
        path = path[2:]
    return path


def lines_for(changed, path):
    """Resolve an analyzer's path against the diff's paths.

    Analyzers report relative to their own working directory, which may be a
    subdirectory of the repo root the diff is relative to, so fall back to a
    suffix match. Returns an empty set when the file is not in the diff.
    """
    path = _strip_prefix(path or "")
    if path in changed:
        return changed[path]
    for cand, lines in changed.items():
        if cand.endswith("/" + path) or path.endswith("/" + cand):
            return lines
    return set()


def _overlaps(changed, path, start, end):
    lines = lines_for(changed, path)
    if not lines:
        return False
    if start is None:
        return False
    return any(n in lines for n in range(start, (end or start) + 1))


def _as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _span_semgrep(f):
    return (
        f.get("path"),
        _as_int((f.get("start") or {}).get("line")),
        _as_int((f.get("end") or {}).get("line")),
    )


def _span_bandit(f):
    start = _as_int(f.get("line_number"))
    span = f.get("line_range") or []
    nums = [n for n in (_as_int(v) for v in span) if n is not None]
    return f.get("filename"), (min(nums) if nums else start), (max(nums) if nums else start)


def _span_gosec(f):
    raw = str(f.get("line") or "")
    parts = [_as_int(p) for p in raw.split("-", 1)]
    start = parts[0]
    end = parts[1] if len(parts) > 1 and parts[1] is not None else start
    return f.get("file"), start, end


# (findings key, span extractor). Each tool nests its findings under a
# different key and names its location fields differently; everything else
# about the document is passed through untouched.
TOOLS = {
    "semgrep": ("results", _span_semgrep),
    "bandit": ("results", _span_bandit),
    "gosec": ("Issues", _span_gosec),
}


def filter_findings(doc, changed, tool):
    key, span = TOOLS[tool]
    findings = doc.get(key) or []
    kept = [f for f in findings if isinstance(f, dict) and _overlaps(changed, *span(f))]
    out = dict(doc)
    out[key] = kept
    return out, len(findings) - len(kept)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("filter", help="drop findings outside the diff's added lines")
    f.add_argument("--diff", required=True, help="unified diff file, or - for stdin")
    f.add_argument("--tool", required=True, choices=sorted(TOOLS))

    m = sub.add_parser("map", help="dump the parsed diff as {path: [lines]}")
    m.add_argument("--diff", required=True)

    args = ap.parse_args(argv)
    text = sys.stdin.read() if args.diff == "-" else open(args.diff, encoding="utf-8").read()
    changed = parse_diff(text)

    if args.cmd == "map":
        json.dump({p: sorted(v) for p, v in sorted(changed.items())}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    doc = json.load(sys.stdin)
    out, dropped = filter_findings(doc, changed, args.tool)
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")
    print(f"{args.tool}: dropped {dropped} finding(s) outside the diff", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
