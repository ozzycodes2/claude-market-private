-- plugin-curation: cc-query supplement
--
-- skillUsage in ~/.claude.json already covers skill invocation counts + recency.
-- These queries cover what that counter does NOT: MCP traffic by server, subagent
-- spawns by type, and the actual data window. Run the whole file in one shot —
-- cc-query has per-invocation startup cost, so batch rather than firing one query
-- per metric:
--
--   CCQ=$(ls ~/.claude/plugins/cache/cc-query-dev/cc-query/*/bin/cc-query | head -1)
--   "$CCQ" < <this file>
--
-- Views are DuckDB over the JSONL transcripts; columns are camelCase
-- (timestamp, isAgent, agentId, project, tool_name, tool_input).

-- 1. MCP calls grouped by server. A plugin's whole value may be its MCP server
--    (trivia, github), which never shows up as a Skill invocation. The regex is
--    approximate — server names contain underscores (claude_ai_Mermaid_Chart,
--    plugin_github_github) — so eyeball the raw tool_name list if grouping looks off.
SELECT regexp_extract(tool_name, '^mcp__(.+?)__', 1) AS mcp_server,
       count(*)        AS uses,
       max(timestamp)  AS last_used
FROM tool_uses
WHERE tool_name LIKE 'mcp__%'
GROUP BY mcp_server
ORDER BY uses DESC;

-- 2. Subagent spawns by type. The spawn tool is 'Agent' (NOT 'Task' — the Task*
--    tools are the todo list). A plugin may exist only to supply a subagent type,
--    which the Skill counter misses entirely. Custom agent types appear as
--    namespace:name (e.g. codex:codex-rescue).
SELECT coalesce(json_extract_string(tool_input, '$.subagent_type'), '(builtin)') AS agent_type,
       count(*) AS spawns
FROM tool_uses
WHERE tool_name = 'Agent'
GROUP BY agent_type
ORDER BY spawns DESC;

-- 3. Data window. Every count above is meaningless without "…over what span?".
--    State the earliest timestamp in the report; if it's shorter than the review
--    cadence, say the counts under-represent reality.
SELECT min(timestamp) AS earliest,
       max(timestamp) AS latest,
       count(DISTINCT project) AS projects
FROM messages;
