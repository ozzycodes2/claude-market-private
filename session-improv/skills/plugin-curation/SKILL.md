---
name: plugin-curation
description: Use when the user wants to audit or prune their Claude Code setup — says "audit my plugins", "what am I actually using", "curate my Claude setup", "which plugins can I disable", "clean up my enabled plugins" — or runs a periodic (e.g. quarterly) review of installed plugins, skills, and MCP servers. Produces keep / consolidate / prune recommendations grounded in real usage counts.
---

# Plugin Curation

An audit pass over an installed Claude Code setup: pull real usage signals, cross-reference what's enabled, and produce keep / consolidate / prune recommendations. The output decides nothing on its own — it surfaces evidence so the user can prune with confidence.

**Core principle:** disable on evidence, not vibes — and read the evidence honestly. A low invocation count is a *question*, not a verdict: the count is blind to hooks, MCP servers, LSPs, subagents, and passive reference skills. **A favorited plugin is never an automatic cut.**

## When to use

- The user suspects their plugin/skill/MCP set has grown into bloat.
- A periodic checkpoint (quarterly fits the data window most setups retain).
- Before sharing a setup, or when context/startup feels heavier than the work justifies.

**Skip if:** the user just wants to toggle one known plugin — that's a `/plugin` action, not an audit.

## How to run

The work is: gather signals (steps 1–3), categorize (step 4), apply the caveat (step 5), then recommend (step 6). **This skill never edits `settings.json`** — it recommends; the user disables via `/plugin` or `update-config` afterward.

### 1. Read the primary signals — `~/.claude.json`

This file holds the authoritative all-time counters. Read three keys (ignore a fourth):

```bash
python3 - << 'PY'
import json, time, os
d = json.load(open(os.path.expanduser("~/.claude.json")))
now = time.time()
print("=== skillUsage: count | days_since_last | skill ===")
for k, v in sorted(d.get("skillUsage", {}).items(), key=lambda x: -x[1]["usageCount"]):
    age = round((now - v["lastUsedAt"]/1000)/86400, 1)
    print(f"{v['usageCount']:>3}  {age:>6}d  {k}")
print("=== favoritePlugins (explicit keeps) ===")
print("\n".join(d.get("favoritePlugins", [])))
print("=== mcpServers ===")
print(", ".join((d.get("mcpServers") or {}).keys()))
PY
```

- **`skillUsage`** — `usageCount` *and* `lastUsedAt`. Recency is half the signal: a high count that's 90 days stale means *abandoned*, not *valued* (the classic case is a skill you migrated away from but never disabled). Rank by count, but read the age column next to it.
- **`favoritePlugins`** — the user's explicit pins. Treat every entry as a keep. If usage data argues for cutting one, surface the conflict — don't override the pin.
- **`mcpServers`** — user-configured MCP servers. Their value lives in `mcp__*` calls (step 2), never in a Skill count.
- **`toolUsage`** — present but unreliable (typically near-empty). Don't base anything on it.

### 2. Fill the gaps — cc-query

`skillUsage` only covers skills. For MCP traffic and subagents — where whole plugins earn their place invisibly — run the batched supplement:

```bash
CCQ=$(ls ~/.claude/plugins/cache/cc-query-dev/cc-query/*/bin/cc-query | head -1)
"$CCQ" < <path-to>/queries.sql      # the queries.sql sitting next to this SKILL.md
```

`queries.sql` (this skill's directory) returns MCP calls by server, subagent spawns by type (the spawn tool is `Agent`, not `Task`), and the data window. Note the earliest timestamp — it bounds every count.

### 3. Read what's enabled and what's orphaned

```bash
# Enabled (true) / disabled (false) — the source of truth for "what loads"
python3 -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));[print(('ON ' if v else 'OFF'),k) for k,v in sorted(d['enabledPlugins'].items())]"

# Dead cache orphans: installed but marked orphaned (don't load)
fd --hidden --max-depth 4 '^\.orphaned_at$' ~/.claude/plugins/cache -x dirname 2>/dev/null
```

A plugin cached but absent from `enabledPlugins` entirely is also dead weight — corroborates the `.orphaned_at` marker.

### 4. Categorize each enabled plugin

| Bucket | Signal | Action |
|---|---|---|
| Live core | count > 0 and recently used | Keep |
| Favorited | listed in `favoritePlugins` | Keep (flag if usage is low — user's call) |
| Abandoned | high count but weeks/months stale | Question: did you migrate away? Likely disable |
| Off-domain, zero use | no use AND irrelevant to the user's actual work | Prune candidate |
| Redundant cluster | several enabled plugins cover one job; user has a preferred one | Consolidate to the preferred; the rest are candidates |
| Dead cache orphan | `.orphaned_at` and/or absent from the enabled map | Already off; optional cache clear |
| Zero-use but defensible | count 0 but provides a hook / MCP / LSP / subagent / passive reference | Keep; flag for the user to confirm |

### 5. Apply the caveat — *before* recommending anything

A zero count does **not** mean unused. Re-check the right signal for each blind spot:

- **Hooks** fire on events (SessionStart, PreToolUse, Stop) and never appear as a tool call. Check `~/.claude/plugins/cache/<plugin>/*/hooks/` and the `hooks` block in settings.
- **MCP servers** surface only as `mcp__*` calls (step 2), never as a Skill.
- **LSP** plugins (e.g. a language server) are consumed silently by edit/diagnostic flows — they read as zero. Never prune an LSP on count.
- **Subagents** — a plugin may exist only to supply an agent type; cross-reference the `Agent` spawn counts.
- **Passive reference skills** shape behavior by being read into context, not invoked. Low count ≠ low value.
- **Output styles / status lines** have no invocation surface at all.

Rule of thumb: prune only the intersection of *(near-zero use) AND (not favorited) AND (no passive role) AND (off-domain or redundant)*. Anything in just one of those sets is a question for the user, not a deletion.

### 6. Produce recommendations

Group as **Keep / Consolidate / Prune**, each entry with its evidence (count, recency, favorite flag, or the passive role that defends it). Open with the data window. Close with a single recommended first move — usually the lowest-risk, highest-noise-reduction cut. Leave the actual `settings.json` edit to the user.

## Anti-patterns

| Don't | Why |
|---|---|
| Treat a zero count as "unused, prune it" | Blind to hooks, MCP, LSP, subagents, and passive reference skills. Zero is a question. |
| Recommend cutting a favorited plugin without flagging it | The pin is an explicit keep signal. Surface the count/favorite conflict; let the user decide. |
| Ignore recency | A 90-day-stale skill with a high count is abandoned, not valued. Cutting a freshly-used one is worse. |
| Prune an MCP-only or LSP-only plugin on a missing Skill call | Its value lives in `mcp__*` calls or silent language-server traffic. Check that signal instead. |
| Fire one cc-query call per metric | Per-invocation startup cost. Batch into the one `queries.sql` run. |
| Trust `toolUsage` from `~/.claude.json` | It's near-empty/unreliable. Use cc-query over transcripts for tool/MCP counts. |
| Report counts with no window | "Used 0 times" is meaningless without "…in N days, data back to <date>." |
| Edit `settings.json` from this skill | This is a recommendation pass. Auto-disabling on inference is how you lose a hook you needed. |
| Score the setup with a number ("health: 7/10") | Numbers feel rigorous and aren't. Specific keep/prune calls are the deliverable. |

## Example

```
User: audit my plugins, I think I have too many

You: [reads ~/.claude.json skillUsage + favoritePlugins; runs queries.sql; reads enabledPlugins]

     Data window: 2026-04-17 → today (~6 weeks, 14 projects). Counts under-represent
     anything older than that.

     Keep — live core
       ceej-skills (session-retro 27×/today, writing-commit-messages 7×/this week)
       codex (codex-rescue: 25 Agent spawns) · trivia (458 mcp__trivia__* calls)
       rust-analyzer-lsp — 0 Skill calls, but it's the language server. Silent, essential.

     Keep — favorited (your explicit pins)
       code-review, comprehensive-review, code-simplifier — pinned, but each used ≤2×
       and weeks stale. Still want them handy, or has your own review skill replaced them?

     Abandoned — high count, now stale
       superpowers:brainstorming 19×, writing-plans 14× — all 28–99d stale, plugin already
       disabled. Migration looks complete; nothing to do.

     Prune candidates — off-domain, zero use, not favorited
       observability-monitoring, database-migrations, backend-api-security — 0 use,
       no fit with your Rust work. Safe to disable.

     Recommended first move: disable the off-domain trio (zero risk, biggest noise cut).
     Re-run next quarter — the window deepens and the picture sharpens.
```
