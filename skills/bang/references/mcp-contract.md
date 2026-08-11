# Yishan GEO MCP Contract

Use the `wanhu-admin` Streamable HTTP MCP server configured in Codex. The public endpoint format is `http://8.xxx.xx.133:1024/mcp`; obtain the complete address from the Yishan team. Keep its Bearer Key in Codex credential configuration or an environment variable, never in this skill repository.

## Required tools

1. `geo.enterprise.search`
   - Input: customer-name search text.
   - Output: customer candidates with a stable enterprise identifier, display name, and test/formal status when available.
2. `geo.enterprise.tasks`
   - Input: selected enterprise identifier.
   - Output: main collection tasks with status, report status, timestamps, task identifier, and repeat-history metadata when applicable.
3. `geo.task.search`
   - Search repeat-task history when a main task indicates recurring executions.
   - Flatten repeat executions with main tasks before sorting.
4. `geo.task.reports`
   - Input: `{ "mainTaskId": "<task id>" }`.
   - Output: generated internal and external report metadata or download URLs.

## Selection invariants

- Exclude customer names marked as tests unless explicitly requested.
- Keep only completed collections whose report status is generated.
- Sort by collection-completed time, then update time, then create time, newest first.
- Use explicit task IDs in the user's order after verifying every report when task IDs are supplied.
- If fewer than N valid tasks exist, use all valid tasks and disclose the actual count.

## Safe fallback

Use a direct Streamable HTTP MCP request only when the configured URL and Bearer authentication already exist in Codex configuration. Never read a bearer value into chat, print it, or store it in this repository.

## Missing tools

- Connected server with no tools: report `MCP connected but exposed no tools`.
- Missing one required tool: name that tool and stop before report analysis.
- Authentication failure: classify HTTP 401/403 as bearer or permission failure; do not retry with guessed credentials.
