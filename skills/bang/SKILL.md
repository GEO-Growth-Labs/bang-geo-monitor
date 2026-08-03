---
name: bang
description: Run reusable GEO daily monitoring when the user invokes "BANG", "BANG 客户名", "BANG 客户名 最近N次", or asks for a customer's recent GEO monitoring sheet. Fetch the latest generated reports through the configured Yishan GEO MCP, calculate weak and small-advantage keywords, aggregate each AI platform's Top 20 source pool, and write a verified daily worksheet to the configured Feishu destination. Default to the latest 10 completed collections when N is omitted.
---

# BANG

Run one customer's GEO daily monitoring workflow and write the result to Feishu.

## Inputs

Accept:

- `BANG <客户名>`: use the latest 10 generated collections.
- `BANG <客户名> 最近N次`: use the latest N generated collections, where `N >= 1`.
- Natural-language requests with the same customer and optional count.

Ask only `请输入客户名字。` when the customer is missing. Do not ask for the count when it is missing; use `10` and state the default in the final summary.

Accept only a positive whole-number count. If an explicit count is zero, negative, decimal, or malformed, ask once for a positive whole number and do not start collection. If the requested count exceeds available generated tasks, use every available task and disclose the shortfall.

## Preflight

1. Run `python3 scripts/configure.py --show` from this skill directory.
2. Require a valid local config containing `mcp_server` and `feishu_parent_url`.
3. Confirm the configured MCP server exposes the tools in [references/mcp-contract.md](references/mcp-contract.md).
4. Confirm an authenticated Feishu writing tool can read the configured destination before downloading reports.
5. Stop with one concrete setup command when either dependency is unavailable. Never edit MCP credentials or guess a Feishu destination.

## Workflow

1. Resolve the customer with the configured GEO MCP. Prefer an exact non-test customer match. Ask one short clarification only when multiple plausible non-test customers remain.
2. List main tasks and repeat-history tasks, then flatten them into one timeline.
3. Keep only completed collections with generated reports, sort newest first, and select the latest `N` (`10` by default).
4. Skip incomplete or ungenerated newest tasks. Record every skipped task and date for the final summary.
5. Create a private temporary directory outside the repository with mode `0700`. Download the internal and external report for each selected task there when available. URL-encode non-ASCII OSS paths.
6. Use only the newest selected internal report for keyword analysis. Use every selected external report for source-pool aggregation.
7. Extract the required rows from the workbooks and run `scripts/analyze_reports.py` when local Python execution is available. See [references/report-schema.md](references/report-schema.md) for the exact workbook contract and failure rules.
8. Create or reuse a BANG-owned customer node and `<客户名>数据监测` sheet under `feishu_parent_url`. Verify the stored enterprise identifier before reuse. Build the worksheet from the specification; never copy another customer's sheet or token.
9. Write today's worksheet, apply styles, then perform readback verification according to [references/feishu-output-spec.md](references/feishu-output-spec.md).
10. Report links, task coverage, keyword counts, skipped tasks, and verification status.
11. Delete the private temporary directory after verification or failure. Do not retain downloaded workbooks or analysis JSON unless the user explicitly requests a local export outside the repository.

## Analysis Rules

Treat percentages as ratios in `[0, 1]` internally.

- For each keyword, average the customer `AI平台的可见占比` across its AI-platform rows.
- Average each `(核心竞品)` block across the same rows, then average those competitor-brand averages.
- Classify `customer < competitor average` as weak; sort by gap descending.
- Classify `customer > competitor average` as small advantage; sort by advantage ascending.
- Exclude exact ties.
- For source analysis, sum `AI平台的信源文章数` across all selected external reports after normalization.
- Rank Top 20 separately for `豆包`, `DeepSeek`, `元宝`, `千问`, and `Kimi`.
- Calculate share against that platform's total article count across all selected external reports, not only its Top 20.

Use [references/source-aliases.json](references/source-aliases.json) for common public-platform normalization. Preserve an unknown source name when no reliable mapping exists; do not invent a Chinese platform name.

## Reliability Rules

- Do not infer keyword results from external reports.
- Do not infer source weights from internal reports.
- Do not write partial output when both analyses are unavailable.
- Separate content, base style, source-color, sizing, freeze, and readback checkpoints.
- Retry only the failed checkpoint. Do not clear successful content to repair styles.
- Never claim success from intended writes; verify actual Feishu values and cell styles.
- Never expose MCP tokens, Feishu tokens, report download URLs, customer task IDs, or local config contents in the final answer.
- Never write reports, analysis JSON, or customer-derived files inside the installed Skill or its Git checkout.

## Final Summary

Include:

- Customer folder and monitoring-sheet links.
- Requested and actual selected task count, plus date range.
- Skipped newest tasks or dates.
- Internal report date used for keyword analysis.
- Weak-keyword and small-advantage counts.
- Whether content, styles, colors, and readback verification passed.
- Any reduced-scope result with the exact reason.

For tool contracts and error classification, read [references/mcp-contract.md](references/mcp-contract.md) and [references/troubleshooting.md](references/troubleshooting.md).
