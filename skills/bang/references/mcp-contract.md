# Yishan GEO MCP Contract

Use the locally configured MCP server name from `~/.config/bang/config.json`. The server name is configurable; the tool contract is not.

## Required tools

1. `geo.enterprise.search`
   - Input: customer-name search text.
   - Output: customer candidates with a stable enterprise identifier, display name, and test/formal status when available.
2. `geo.enterprise.tasks`
   - Input: selected enterprise identifier.
   - Output: main collection tasks with status, report status, timestamps, task identifier, and repeat-history metadata when applicable.
3. Repeat-history task listing
   - Use the repeat-history tool exposed by the server when a main task indicates recurring executions.
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

Use a direct Streamable HTTP MCP request only when the configured MCP URL and bearer-token environment variable already exist in Codex configuration. Never read a bearer value into chat, print it, store it in this repository, or add MCP configuration during a BANG run.

## Missing tools

- Connected server with no tools: report `MCP connected but exposed no tools`.
- Missing one required tool: name that tool and stop before report analysis.
- Authentication failure: classify HTTP 401/403 as bearer or permission failure; do not retry with guessed credentials.
