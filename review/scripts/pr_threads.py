#!/usr/bin/env python3
"""Match the review threads on a PR back to the ledger findings that resolved them.

`/review:review` posts each finding as an inline review comment; `/review:fix`
resolves the findings. Closing the loop means answering the comment that asked,
which needs a mapping from finding to thread -- and GitHub hands back no such
mapping at post time.

Rebuilding it afterwards is possible because every comment the formatter posts
leads with a Conventional Comments marker (`**issue (blocking):** <title>`), so a
thread can be attributed to a review pass without knowing who posted it, and the
title in the header identifies which finding it was.

Matching is deliberate rather than best-effort: a pair needs the same file plus
either the same line or the finding's title in the body, and a thread that two
findings fit equally well is reported as ambiguous instead of guessed at. A wrong
match resolves a reviewer's question with an answer to a different question, which
is worse than leaving it open.

Reads the GraphQL response on stdin so it is testable without a network call; the
query that produces it is in `skills/fix/SKILL.md`.

    gh api graphql -f query='…' -F … | pr_threads.py match --ledger L --threads -
"""
import argparse
import json
import re
import sys

# The formatter's inline body starts `**<label> (<decoration>):** <subject>`,
# optionally wrapped in a `> [!CAUTION]` alert blockquote. Matching the marker
# rather than the author means a review posted by a human account, a bot, or a
# different session all attribute correctly.
_LABELS = ("praise", "nitpick", "suggestion", "issue", "thought", "question")
_MARKER = re.compile(
    r"^(?:>\s*)?\*\*(?P<label>" + "|".join(_LABELS) + r")"
    r"(?:\s*\((?P<decoration>[^)]*)\))?:\*\*\s*(?P<subject>.*)",
    re.MULTILINE,
)

# Actions, keyed by the ledger status that earns them.
#   committed -> the question was answered, so reply and resolve.
#   deferred  -> the question is still open and now has a stated decision to
#                make, so reply and leave it unresolved. Resolving here would
#                bury the one finding that most needs a human.
_ACTIONS = {"committed": "reply+resolve", "deferred": "reply"}

_PUNCT = re.compile(r"[^a-z0-9]+")


def _norm(text) -> str:
    """Lowercase, strip punctuation, collapse whitespace -- for title comparison."""
    return _PUNCT.sub(" ", str(text or "").lower()).strip()


def parse_threads(payload) -> list:
    """Flatten a `reviewThreads` GraphQL response into one dict per thread."""
    try:
        nodes = payload["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    except (KeyError, TypeError):
        nodes = payload.get("nodes") if isinstance(payload, dict) else None
        if nodes is None:
            return []

    out = []
    for t in nodes or []:
        comments = ((t.get("comments") or {}).get("nodes")) or []
        first = comments[0] if comments else {}
        body = first.get("body") or ""
        marker = _MARKER.search(body)
        out.append(
            {
                "thread_id": t.get("id"),
                "is_resolved": bool(t.get("isResolved")),
                "is_outdated": bool(t.get("isOutdated")),
                "author": ((first.get("author") or {}).get("login")) or "",
                "comment_id": first.get("databaseId"),
                "path": first.get("path"),
                "line": first.get("line"),
                "original_line": first.get("originalLine"),
                "body": body,
                "from_review": bool(marker),
                "label": marker.group("label") if marker else None,
                "subject": (marker.group("subject").strip() if marker else ""),
            }
        )
    return out


def score(finding: dict, thread: dict):
    """Rank one finding/thread pair, or return None when they cannot be the same.

    Returns `(score, why)`. A same-file pair still needs a line or a title to
    agree -- file alone would happily match two unrelated findings in a long
    file.
    """
    if not thread.get("from_review") or thread.get("is_resolved"):
        return None
    f_path, t_path = finding.get("path"), thread.get("path")
    if not f_path or not t_path or f_path != t_path:
        return None

    points, why = 0, []
    f_line = finding.get("line")
    if f_line and f_line in (thread.get("line"), thread.get("original_line")):
        points += 2
        why.append("line")

    f_title = _norm(finding.get("title"))
    subject, body = _norm(thread.get("subject")), _norm(thread.get("body"))
    if f_title and (f_title == subject or (len(f_title) > 12 and f_title in body)):
        points += 2
        why.append("title")
    elif f_title and subject and (f_title in subject or subject in f_title):
        points += 1
        why.append("title~")

    if not points:
        return None
    # An outdated thread points at code that has since moved. Still answerable --
    # the reviewer asked a real question -- but rank it below a live match.
    if thread.get("is_outdated"):
        points -= 1
    return points, "+".join(why)


def match(ledger: dict, threads: list, statuses=("committed", "deferred")) -> dict:
    """Assign at most one thread per finding, best-scoring pair first."""
    wanted = set(statuses)
    findings = [
        f for f in ledger.get("findings") or [] if f.get("status") in wanted
    ]

    pairs = []
    for f in findings:
        for t in threads:
            s = score(f, t)
            if s:
                pairs.append((s[0], s[1], f, t))
    pairs.sort(key=lambda p: (-p[0], str(p[2].get("id"))))

    matched, used_f, used_t, ambiguous = [], set(), set(), []
    for points, why, f, t in pairs:
        fid, tid = f.get("id"), t.get("thread_id")
        if fid in used_f or tid in used_t:
            continue
        # A tie on the same thread means the evidence does not distinguish the
        # findings. Acting would answer the wrong question; report instead.
        rivals = [
            o for pts, _, o, ot in pairs
            if ot.get("thread_id") == tid and pts == points and o.get("id") != fid
            and o.get("id") not in used_f
        ]
        if rivals:
            ambiguous.append(
                {
                    "thread_id": tid,
                    "path": t.get("path"),
                    "candidates": sorted([fid] + [o.get("id") for o in rivals]),
                    "reason": f"{len(rivals) + 1} findings match equally well ({why})",
                }
            )
            used_t.add(tid)
            continue

        prior = {a.get("thread_id") for a in f.get("acknowledged") or []}
        if tid in prior:
            # Already answered on a previous run. Re-replying would spam the
            # thread, so this is a skip and not a failure.
            used_f.add(fid)
            used_t.add(tid)
            continue

        matched.append(
            {
                "finding_id": fid,
                "status": f.get("status"),
                "action": _ACTIONS.get(f.get("status"), "skip"),
                "thread_id": tid,
                "path": t.get("path"),
                "line": t.get("line") or t.get("original_line"),
                "is_outdated": t.get("is_outdated"),
                "title": f.get("title"),
                "resolved_by_sha": f.get("resolved_by_sha"),
                "decision_needed": (f.get("deferral") or {}).get("decision_needed"),
                "matched_on": why,
                "confidence": "high" if points >= 3 else "low",
            }
        )
        used_f.add(fid)
        used_t.add(tid)

    unmatched_findings = []
    for f in findings:
        if f.get("id") in used_f:
            continue
        if f.get("acknowledged"):
            continue
        unmatched_findings.append(
            {
                "finding_id": f.get("id"),
                "status": f.get("status"),
                "path": f.get("path"),
                "title": f.get("title"),
                # No path is the common case, not a defect: CI failures and
                # architectural findings never had an inline comment to answer.
                "reason": "no-path" if not f.get("path") else "no-matching-thread",
            }
        )

    unmatched_threads = [
        {
            "thread_id": t.get("thread_id"),
            "path": t.get("path"),
            "line": t.get("line") or t.get("original_line"),
            "subject": t.get("subject") or (t.get("body") or "")[:80],
            "from_review": t.get("from_review"),
        }
        for t in threads
        if t.get("thread_id") not in used_t and not t.get("is_resolved")
    ]

    return {
        "matched": matched,
        "ambiguous": ambiguous,
        "unmatched_findings": unmatched_findings,
        "unmatched_threads": unmatched_threads,
    }


def _load(spec):
    if spec in ("-", None):
        return json.load(sys.stdin)
    with open(spec, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _cmd_match(args):
    ledger = _load(args.ledger)
    threads = parse_threads(_load(args.threads))
    statuses = tuple(s.strip() for s in args.status.split(",") if s.strip())
    result = match(ledger, threads, statuses=statuses)

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    for m in result["matched"]:
        sha = (m.get("resolved_by_sha") or "-")[:12]
        flags = []
        if m["confidence"] == "low":
            flags.append("low-confidence")
        if m.get("is_outdated"):
            flags.append("outdated")
        suffix = f"  [{', '.join(flags)}]" if flags else ""
        print(f"{m['finding_id']}\t{m['action']:14}\t{m['thread_id']}\t{sha}\t{m['title']}{suffix}")
    for a in result["ambiguous"]:
        print(f"AMBIGUOUS\t{a['thread_id']}\t{a['path']}\t{a['reason']}: {', '.join(a['candidates'])}")
    for u in result["unmatched_findings"]:
        print(f"{u['finding_id']}\tno-thread\t{u['reason']}\t{u['title']}")
    if not any(result[k] for k in ("matched", "ambiguous", "unmatched_findings")):
        print("nothing to acknowledge")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="pr_threads.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("match", help="map ledger findings to the review threads that raised them")
    m.add_argument("--ledger", required=True)
    m.add_argument("--threads", default="-", help="reviewThreads GraphQL response, or - for stdin")
    m.add_argument("--status", default="committed,deferred")
    m.add_argument("--json", action="store_true")
    m.set_defaults(fn=_cmd_match)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
