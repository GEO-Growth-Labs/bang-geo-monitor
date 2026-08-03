# Feishu Output Specification

Use the configured parent URL as the only destination root. Never embed a tenant domain, space ID, node token, spreadsheet token, or template token in the skill.

## Destination hierarchy

1. Read the configured parent node.
2. Resolve the selected customer's stable enterprise identifier from MCP before choosing a destination.
3. Calculate `enterprise_hash` as lowercase SHA-256 of the canonical enterprise identifier. Reuse only a customer node of the expected type whose single BANG monitoring-workbook child has matching `_BANG_META` values. Treat that verified workbook as the node ownership marker.
4. When an exact-name node exists without a matching marker, do not write to it. Create a new node named `<客户名>（BANG）` or ask for clarification if that name is also ambiguous.
5. Reuse a spreadsheet named `<客户名>数据监测` only when its hidden `_BANG_META` worksheet contains `A1=owner`, `B1=BANG`, `A2=schema_version`, `B2=1`, `A3=enterprise_hash`, and `B3=<matching hash>`. Otherwise create a new spreadsheet.
6. Create and read back those exact `_BANG_META` cells on new workbooks, then hide the worksheet when supported. Store the hash, never the raw enterprise identifier. Never place credentials, report URLs, task IDs, or customer report data there.
7. Reuse today's worksheet named `M月D日`, or create a blank worksheet with that title.
8. Never inspect or copy another customer's workbook as a template.

## Grid

Use columns `A:Q`.

| Range | Meaning |
|---|---|
| `A:B` | Keyword gap section |
| `C:E` | 豆包 |
| `F:H` | DeepSeek |
| `I:K` | 元宝 |
| `L:N` | 千问 |
| `O:Q` | Kimi |

### Header rows

- Merge `A1:B1`; set `薄弱关键词`.
- Merge `C1:Q1`; set `信源池`.
- Set `A2=关键词`, `B2=差值`.
- Merge platform headers in row 2: `C2:E2`, `F2:H2`, `I2:K2`, `L2:N2`, `O2:Q2`.
- In row 3, repeat `信源平台`, `引用数`, `平台占比` under each AI platform.
- Start weak-keyword data at `A3:B`.

### Keyword rows

1. Write weak keywords by descending gap.
2. Format column B as `0.00%`.
3. Add one blank row.
4. Add `高于竞品但优势较小的词` and `高出`.
5. Write strict small-advantage keywords by ascending advantage.

### Source rows

- Write Top 20 sources in rows `4:23`.
- Store article counts as numbers with format `#,##0`.
- Store shares as ratios with format `0.00%`.
- Leave unused Top 20 rows blank.

## Styles

- Freeze the first three rows and first two columns when supported.
- Bold rows 1 through 3 and the small-advantage section header.
- Use `#D9F3F0` for `A1:B1` and `#EAF2FF` for `C1:Q1`.
- Use neutral `#F6F7F9` for secondary headers and thin `#E5E7EB` borders.
- Set keyword text columns wide enough for full questions; wrap long text.
- Right-align counts and percentages.

Color only source-name cells based on how many AI-platform Top 20 lists contain the normalized source:

| Appearances | Fill |
|---:|---|
| 5 | `#FCE2E2` |
| 4 | `#FCE8D6` |
| 3 | `#EADCF8` |
| 2 | `#DDEBFF` |
| 1 | `#DDF2E3` |

Do not color adjacent count or share cells.

## Checkpoints

1. Clear the current worksheet's stale range only after the destination and analysis results are both ready.
2. Write content.
3. Apply merges and base styles.
4. Apply source-name colors.
5. Apply widths, wrapping, number formats, and freeze settings.
6. Read back `A1:Q8`.
7. Read back the weak-to-advantage transition.
8. Read one representative source-name cell from every non-empty color bucket and its two adjacent cells.

Pass verification only when values match, expected fills are present, and adjacent count/share cells have no source color fill.
