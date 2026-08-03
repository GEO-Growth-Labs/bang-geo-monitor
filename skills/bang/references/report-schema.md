# Report Schema

## Internal report

Require worksheet `关键词数据分析`.

Find a header row containing:

- `关键词名称`
- `AI平台名称`
- `AI平台的可见占比`

Use the row immediately above it as the grouped brand header. Require exactly one visibility column whose grouped header contains `(客户)` or `（客户）`, and one or more columns whose grouped headers contain `(核心竞品)` or `（核心竞品）`.

For each keyword:

1. Collect the customer visibility for every non-empty AI-platform row.
2. Average each competitor column across its non-empty platform rows.
3. Average the competitor-column averages.
4. Compare the two averages without rounding.
5. Round only the final displayed gap or advantage to four decimal places.

Treat numeric values from 0 through 1 as ratios. Treat numeric values over 1 through 100 as percentage points and divide by 100. Parse strings ending in `%` as percentage points. Reject values outside 0 through 100.

## External report

Require worksheet `AI平台的信源分析` and a header row containing:

- `信源平台名称`
- `AI平台名称`
- `AI平台的信源文章数`

Keep non-negative article counts. Ignore zero-count rows during ranking, but include no negative value. Sum duplicate normalized sources per AI platform across every selected external report.

## Missing data

- No usable internal report: block keyword analysis and state the newest attempted report date.
- No usable external report: block source-pool analysis and state the selected task dates.
- One side missing: write only the valid section when the Feishu destination is available, label the missing section `数据不可用`, and disclose reduced scope.
- Both sides missing: do not create or update a daily worksheet.
