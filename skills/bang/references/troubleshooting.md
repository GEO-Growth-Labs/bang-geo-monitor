# Troubleshooting

## Configuration

- `config not found`: run `python3 scripts/configure.py --mcp-server yishan-geo --feishu-parent-url '<URL>'`.
- `MCP server not configured`: add it in Codex, restart Codex, and rerun preflight.
- `invalid Feishu URL`: use a writable Feishu/Lark wiki or sheets URL, not a browser share redirect.

## MCP

- Connection refused, DNS failure, or timeout before authentication: MCP URL/network issue.
- HTTP 401/403: bearer or server permission issue.
- Upstream missing-key response: MCP upstream API-key issue.
- Connected with an empty tool list: server deployment/tool-exposure issue.
- Report metadata exists but file access fails: report-storage permission or expired URL issue; refresh metadata once before stopping.

## Feishu

- Destination read fails: identity or URL permission issue. Stop before analysis unless the user asks for a local-only result.
- Content write fails: retry the content checkpoint once.
- Style or color write fails after content succeeds: retry only the failed style/color ranges.
- Readback mismatch: report the exact range and do not mark verification as passed.

## Reports

- Missing internal report: do not derive keyword gaps from external files.
- Missing external reports: do not derive source counts from internal files.
- Unexpected headers: report the missing worksheet/header names; never guess column positions from customer data.
