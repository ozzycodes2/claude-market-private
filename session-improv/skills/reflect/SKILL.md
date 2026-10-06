---
name: reflect
description: Query Claude Code conversation history and session data using SQL. Use when analyzing past conversations, token usage, tool patterns, agent activity, or extracting insights from session logs. Triggers on requests about session history, conversation analysis, usage statistics, periodic reviews over a week/month/quarter, or cc-query.
context: fork
allowed-tools: Bash, Read
---

# Querying Session Data

Use `${CLAUDE_PLUGIN_ROOT}/bin/cc-query` to analyze Claude Code sessions with SQL (DuckDB).

## Reviewing a span of time — REQUIRED slots

Applies whenever the request names a period rather than one session: "the last
30 days", "this week", "this quarter".

**Read [period-review.md](period-review.md) before querying.** It carries the
tested queries, the per-finding schema, the guards, and the traps that have
produced wrong conclusions here before. The slots below are the index.

Four layers. Thirteen slots. Fill them all, or report a layer as *not
applicable* and say why.

**A — Measure** (transcripts, SQL)
A1 window and volume, date range first · A2 where the work went · A3 tool
patterns **with output chars**, ranked by cost not call count · A4 skill
utilization from `~/.claude.json` `skillUsage`, naming those **never invoked** ·
A5 plugin and MCP utilization against `enabledPlugins` · A6 navigation mix,
`LSP` vs. `Grep`/`Glob` vs. text search through Bash.

**B — Interpret** (causal; `Why` is mandatory in each)
B1 worked · B2 friction, including *what to try instead* · B3 learned ·
B4 corrections and interrupts, precise and upper-bound counts labeled
separately, recurring ones quoted verbatim.

**C — Audit the instruction surface** (files on disk, `git blame`)
C1 findings in `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, rule files, commands,
hooks — unenforced instructions, recency traps, contradictions, volatile
specifics, fossils. Each with `file:line` and quoted evidence. Never read
`settings*.json` or `.mcp.json` whole; they can hold secrets — `jq` named keys.

**D — Actions**
D1 prioritized actions, ordered by confidence, each with observation, why it
matters, confidence, action, and quantified cost only where the data supports
it · D2 measurement limits, stated **before** any recommendation rests on them.

Propose; never apply an edit to an instruction file without explicit consent.
An empty finding is a valid outcome. Check whether a recommendation is already
configured before making it.

## Query Planning (Read This First)

**Each bash call costs ~1-2 seconds** (DuckDB init + JSONL parsing). 20 separate queries wastes 20-40 seconds on overhead alone.

**Before running any query:**
1. List all questions you need answered
2. Combine into 1-2 heredoc batches
3. Store results mentally — never re-run the same query

**Standard pattern:**
```bash
cat << 'EOF' | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query
-- Query 1
SELECT ...;
-- Query 2
SELECT ...;
-- Query 3
SELECT ...;
EOF
```

## Quick Start

```bash
${CLAUDE_PLUGIN_ROOT}/bin/cc-query                    # All projects
${CLAUDE_PLUGIN_ROOT}/bin/cc-query ~/code/myproject   # Specific project
```

**IMPORTANT**: Always use heredoc (not echo). Enables batching:
```bash
cat << 'EOF' | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query
SELECT count(*) FROM messages;
EOF
```

## Use Cases

**Analyzing a specific session**: See [session-analysis.md](session-analysis.md) for templates and output format.

**Reviewing a span of time**: the REQUIRED slots are at the top of this file;
queries and traps in [period-review.md](period-review.md).

## Reference

**Schema details**: Run `echo '.schema' | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query` if you need the full schema.

**JSON queries**: See [json-queries.md](json-queries.md) for working with the `message` JSON field.

**Advanced patterns**: See [advanced-queries.md](advanced-queries.md) for complex analysis query ideas.

## Views

### Base Views

| View                 | Description                                    | Has `message` JSON |
| -------------------- | ---------------------------------------------- | ------------------ |
| `messages`           | All messages (user, assistant, system)         | ✓                  |
| `user_messages`      | User messages with tool results, todos         | ✓                  |
| `assistant_messages` | Assistant messages with API response data      | ✓                  |
| `system_messages`    | System messages (hooks, retries, tool output)  | ✗ (has `content`)  |
| `human_messages`     | Only human-typed messages (no tool results)    | ✗ (has `content`)  |
| `raw_messages`       | Raw JSON (uuid + full JSON string)             | ✗ (has `raw`)      |

### Convenience Views (pre-extracted, no JSON needed)

| View              | Key Fields                                      |
| ----------------- | ----------------------------------------------- |
| `tool_uses`       | `tool_name`, `tool_id`, `tool_input` (JSON)     |
| `tool_results`    | `tool_use_id`, `is_error`, `result_content`, `duration_ms` |
| `token_usage`     | `input_tokens`, `output_tokens`, `cache_read_tokens`, `model` |
| `bash_commands`   | `command`, `description`, `timeout`             |
| `file_operations` | `tool_name`, `file_path`, `pattern`             |

## Key Fields

**Common**: `uuid`, `timestamp`, `sessionId`, `message` (JSON), `type`, `cwd`, `version`

**Derived**: `isAgent`, `agentId`, `project`, `file`, `rownum`

**User-specific**: `toolUseResult`, `sourceToolAssistantUUID`, `todos`, `isMeta`

**human_messages only**: `content` (VARCHAR) — extracted text, not JSON

## Example Queries

### Recent human messages (what did we work on)
```sql
SELECT timestamp, left(content, 100) as message
FROM human_messages
ORDER BY timestamp DESC LIMIT 10;
```

### Recent sessions
```sql
SELECT sessionId, min(timestamp) as started, max(timestamp) as ended, count(*) as msgs
FROM messages
GROUP BY sessionId ORDER BY started DESC LIMIT 5;
```

### Message counts
```sql
SELECT type, count(*) as cnt FROM messages GROUP BY type ORDER BY cnt DESC;
```

### Token usage
```sql
-- Using convenience view (recommended)
SELECT sum(input_tokens) as input, sum(output_tokens) as output, sum(cache_read_tokens) as cached
FROM token_usage;

-- Or with raw JSON
SELECT sum(CAST(message->'usage'->>'input_tokens' AS BIGINT)) as input,
       sum(CAST(message->'usage'->>'output_tokens' AS BIGINT)) as output,
       sum(CAST(message->'usage'->>'cache_read_input_tokens' AS BIGINT)) as cache_hits
FROM assistant_messages;
```

### Most used tools
```sql
-- Using convenience view (recommended)
SELECT tool_name, count(*) as uses FROM tool_uses GROUP BY tool_name ORDER BY uses DESC LIMIT 10;

-- Or with raw JSON (json_extract_string required for mixed message types)
SELECT json_extract_string(message, '$.content[0].name') as tool, count(*) as uses
FROM messages WHERE type = 'assistant'
  AND json_extract_string(message, '$.content[0].type') = 'tool_use'
GROUP BY tool ORDER BY uses DESC LIMIT 10;
```

### Agent vs main session
```sql
SELECT isAgent, count(*) as messages, count(DISTINCT agentId) as agents
FROM messages
GROUP BY isAgent;
```

### Project comparison
```sql
SELECT project, count(*) as messages
FROM messages
GROUP BY project
ORDER BY messages DESC;
```

### Tool durations
```sql
-- Using convenience view (recommended)
SELECT tool_use_id, duration_ms, left(result_content, 50) as preview
FROM tool_results WHERE duration_ms IS NOT NULL ORDER BY duration_ms DESC LIMIT 10;

-- Or with raw JSON
SELECT CAST(toolUseResult->>'durationMs' AS INTEGER) as duration_ms,
       left(message->'content'->0->>'content', 50) as result_preview
FROM user_messages WHERE toolUseResult IS NOT NULL ORDER BY duration_ms DESC LIMIT 10;
```

## Critical Notes

**Use convenience views for tool analysis**: The `tool_uses`, `tool_results`, `bash_commands`, `file_operations`, and `token_usage` views pre-extract common fields so you don't need JSON functions:
```sql
SELECT tool_name, count(*) FROM tool_uses GROUP BY tool_name;  -- Simple!
```

**Column names are camelCase**: Use `sessionId`, `agentId`, `toolUseResult` (NOT `session_id`, `agent_id`)

**Arrow operators fail on mixed data**: On base views (`assistant_messages`, `messages`), arrow operators like `message->'content'->0->>'name'` cause "Conversion Error" because rows have different JSON structures. Use `json_extract_string()` or convenience views:
```sql
-- FAILS: message->'content'->0->>'name'
-- WORKS: json_extract_string(message, '$.content[0].name')
-- BEST:  SELECT tool_name FROM tool_uses
```

## JSON Access

- `json_extract_string(message, '$.field')` — **preferred**, handles mixed types
- `message->'field'` returns JSON (use only when all rows have same structure)
- `message->>'field'` returns string (same caveat)
- `message->'content'->0` array access (0-indexed)
- `UNNEST(CAST(json_array AS JSON[]))` expands arrays
- **Precedence gotcha**: Use parentheses with `IS NULL`: `(message->'usage') IS NOT NULL`

## Efficiency Guidelines

**Target: 1-2 tool calls per analysis.** Each bash call = ~1-2 seconds overhead.

| Calls | Overhead | Verdict |
|-------|----------|---------|
| 1-2   | 2-4s     | Good    |
| 5-10  | 10-20s   | Wasteful |
| 20+   | 40s+     | Unacceptable |

### Two-Call Pattern for Unknown Sessions

**Call 1: Discovery** — Find what you're looking for:
```bash
cat << 'EOF' | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query
-- Recent sessions
SELECT sessionId, project, min(timestamp) as started, max(timestamp) as ended, count(*) as msgs
FROM messages GROUP BY sessionId, project ORDER BY started DESC LIMIT 10;
EOF
```

**Call 2: Deep Analysis** — Query the specific session(s):
```bash
cat << 'EOF' | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query
-- Replace SESSION_ID with ID from Call 1
SELECT count(*) as msgs, count(DISTINCT agentId) as agents FROM messages WHERE sessionId = 'SESSION_ID';
SELECT tool_name, count(*) FROM tool_uses WHERE sessionId = 'SESSION_ID' GROUP BY tool_name ORDER BY count(*) DESC;
SELECT timestamp, left(content, 300) FROM human_messages WHERE sessionId = 'SESSION_ID' ORDER BY timestamp;
EOF
```

### Combine keyword searches with OR
```sql
-- BAD: 5 separate queries for each keyword
-- GOOD: One query with all patterns
SELECT timestamp, left(content, 300) FROM human_messages
WHERE lower(content) LIKE '%fix%'
   OR lower(content) LIKE '%wrong%'
   OR lower(content) LIKE '%instead%'
   OR lower(content) LIKE '%prefer%'
   OR lower(content) LIKE '%should%'
ORDER BY timestamp DESC;
```

### Use CTEs for repeated filters
```sql
WITH clean_messages AS (
  SELECT * FROM human_messages
  WHERE content NOT LIKE '%<local-command%'
    AND content NOT LIKE '%<command-name%'
    AND length(content) > 20
)
SELECT timestamp, content FROM clean_messages
WHERE lower(content) LIKE '%error%';
```

### Never Re-Query
Once you have a result, remember it. Don't re-run the same query to "verify" or "check".

## Common Analysis Patterns

### Cross-Project Overview (Single Call)
```bash
cat << 'EOF' | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query
-- Project activity
SELECT project, count(*) as msgs, count(DISTINCT sessionId) as sessions,
       max(timestamp) as last_activity FROM messages GROUP BY project ORDER BY last_activity DESC LIMIT 10;
-- Tool patterns across all projects
SELECT tool_name, count(*) as uses FROM tool_uses GROUP BY tool_name ORDER BY uses DESC LIMIT 15;
-- Error-prone commands
SELECT left(command, 80) as cmd, count(*) as errors
FROM bash_commands bc JOIN tool_results tr ON bc.tool_id = tr.tool_use_id
WHERE tr.is_error GROUP BY cmd ORDER BY errors DESC LIMIT 10;
EOF
```

### Find user corrections/preferences (for CLAUDE.md insights)
```sql
SELECT timestamp, left(content, 400) as content
FROM human_messages
WHERE content NOT LIKE '%<local-command%'
  AND content NOT LIKE '%<command-name%'
  AND length(content) > 20
  AND (
    lower(content) LIKE '%instead%'
    OR lower(content) LIKE '%wrong%'
    OR lower(content) LIKE '%fix%'
    OR lower(content) LIKE '%prefer%'
    OR lower(content) LIKE '%should%'
    OR lower(content) LIKE '%don''t%'
    OR lower(content) LIKE '%please%'
  )
ORDER BY timestamp DESC;
```

### Weekly Summary (Single Call)

Date arithmetic is unavailable: the `-` operator is unbound for `DATE`,
`TIMESTAMP` and `TIMESTAMPTZ` in this build, so `now() - INTERVAL '7 days'`
and `current_date - 7` both fail with a binder error. Compute the cutoff in
the shell and interpolate it as a literal.

```bash
SINCE=$(date -v-7d +%F 2>/dev/null || date -d '7 days ago' +%F)
cat << EOF | ${CLAUDE_PLUGIN_ROOT}/bin/cc-query
-- Sessions this week
SELECT date_trunc('day', timestamp) as day, count(DISTINCT sessionId) as sessions, count(*) as msgs
FROM messages WHERE timestamp >= '$SINCE' GROUP BY day ORDER BY day;
-- What we worked on
SELECT left(content, 200) as topic FROM human_messages
WHERE timestamp >= '$SINCE' AND length(content) > 30
  AND content NOT LIKE '%<local-command%' ORDER BY timestamp DESC LIMIT 20;
-- Token consumption
SELECT sum(input_tokens) as input, sum(output_tokens) as output FROM token_usage WHERE timestamp >= '$SINCE';
EOF
```

Note the unquoted `EOF` — `<< 'EOF'` would pass `$SINCE` through literally.
