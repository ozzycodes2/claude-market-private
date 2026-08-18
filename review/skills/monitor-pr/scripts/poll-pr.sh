#!/usr/bin/env bash
# poll-pr.sh — read-only snapshot of a PR's CI + review state, emitted as one JSON
# object on stdout. Diagnostics go to stderr. Mutates NOTHING (no fixes, no thread
# resolution — that's the caller's job).
#
# Usage:
#   poll-pr.sh <pr-number> [--repo owner/name]
#   poll-pr.sh --help
#
# Env:
#   CLAUDE_BOT   substring identifying the Claude review-bot author login.
#                Default: "claude-code-action". Any author containing this, or
#                ending in "[bot]", is classified as a bot; everyone else human.
#
# Output JSON shape:
#   {
#     "pr": N, "repo": "owner/name", "state": "...",
#     "reviewDecision": "...", "mergeStateStatus": "...",
#     "checks": { "failing": [ {name,link} ], "pending": [ {name} ], "passing": K },
#     "threads": {
#       "bot":   [ {id,isResolved,isOutdated,author,path,line,body} ],
#       "human": [ {id,isResolved,isOutdated,author,path,line,body} ]
#     },
#     "issue_comments": [ {author,isBot,body} ]
#   }
# Requires: gh (authenticated), python3.

set -uo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

PR="${1:-}"
shift || true
REPO=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="${2:-}"; shift 2;;
    *) echo "poll-pr.sh: unknown arg: $1" >&2; exit 2;;
  esac
done

[[ -z "$PR" ]] && { echo "poll-pr.sh: missing <pr-number>" >&2; exit 2; }
command -v gh >/dev/null 2>&1 || { echo "poll-pr.sh: gh not found" >&2; exit 3; }
command -v python3 >/dev/null 2>&1 || { echo "poll-pr.sh: python3 not found" >&2; exit 3; }

BOT="${CLAUDE_BOT:-claude-code-action}"
REPO_ARGS=(); [[ -n "$REPO" ]] && REPO_ARGS=(--repo "$REPO")

# Resolve owner/name for the GraphQL call.
if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null)"
fi
OWNER="${REPO%%/*}"; NAME="${REPO##*/}"

# --- gather (each guarded; missing pieces degrade to empty) ------------------
CHECKS_JSON="$(gh pr checks "$PR" "${REPO_ARGS[@]}" --json name,state,bucket,link 2>/dev/null || echo '[]')"
VIEW_JSON="$(gh pr view "$PR" "${REPO_ARGS[@]}" \
  --json state,reviewDecision,mergeStateStatus,comments 2>/dev/null || echo '{}')"
THREADS_JSON="$(gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        nodes{
          id isResolved isOutdated
          comments(first:1){ nodes{ author{login} path line originalLine body } }
        }
      }
    }
  }
}' -F owner="$OWNER" -F repo="$NAME" -F pr="$PR" 2>/dev/null || echo '{}')"

export BOT PR REPO CHECKS_JSON VIEW_JSON THREADS_JSON
python3 <<'PY'
import json, os
bot = os.environ["BOT"].lower()
def is_bot(login):
    l = (login or "").lower()
    return bot in l or l.endswith("[bot]")

def loads(s, default):
    try: return json.loads(s) if s.strip() else default
    except Exception: return default

checks = loads(os.environ["CHECKS_JSON"], [])
view   = loads(os.environ["VIEW_JSON"], {})
threads_raw = loads(os.environ["THREADS_JSON"], {})

failing, pending, passing = [], [], 0
for c in checks:
    b = (c.get("bucket") or c.get("state") or "").lower()
    if b in ("fail", "failure", "error", "cancel", "cancelled", "timed_out", "action_required"):
        failing.append({"name": c.get("name"), "link": c.get("link")})
    elif b in ("pending", "queued", "in_progress", "waiting", "expected"):
        pending.append({"name": c.get("name")})
    else:
        passing += 1

bot_t, human_t = [], []
try:
    nodes = threads_raw["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
except Exception:
    nodes = []
for t in nodes:
    cn = (t.get("comments") or {}).get("nodes") or []
    c0 = cn[0] if cn else {}
    author = ((c0.get("author") or {}).get("login")) or ""
    entry = {
        "id": t.get("id"), "isResolved": t.get("isResolved"),
        "isOutdated": t.get("isOutdated"), "author": author,
        "path": c0.get("path"), "line": c0.get("line") or c0.get("originalLine"),
        "body": (c0.get("body") or "")[:500],
    }
    (bot_t if is_bot(author) else human_t).append(entry)

issue_comments = []
for c in (view.get("comments") or []):
    login = ((c.get("author") or {}).get("login")) or c.get("authorAssociation") or ""
    issue_comments.append({"author": login, "isBot": is_bot(login),
                           "body": (c.get("body") or "")[:500]})

print(json.dumps({
    "pr": int(os.environ["PR"]), "repo": os.environ["REPO"],
    "state": view.get("state"),
    "reviewDecision": view.get("reviewDecision"),
    "mergeStateStatus": view.get("mergeStateStatus"),
    "checks": {"failing": failing, "pending": pending, "passing": passing},
    "threads": {"bot": bot_t, "human": human_t},
    "issue_comments": issue_comments,
}, indent=2))
PY
