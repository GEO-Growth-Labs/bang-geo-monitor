# Contributing

## Scope

Keep BANG focused on one workflow: recent GEO report selection, keyword/source analysis, and verified Feishu monitoring output.

## Development

1. Fork the repository and create a focused branch.
2. Do not add real customer reports, names, task IDs, report URLs, MCP endpoints, credentials, or Feishu tokens, even as test fixtures.
3. Use synthetic fixtures whose labels are visibly generic.
4. Run `python3 -m unittest discover -s tests -v`.
5. Run `python3 tools/check_public_release.py`.
6. Run `python3 tools/validate_skill.py`.
7. Update the README only when user-facing setup or behavior changes.

Pull requests should describe the behavior changed, verification performed, and any compatibility risk to the MCP or report schemas.

To regenerate the synthetic README image, run `npm install` and `npm run render:demo`. Set `CHROME_PATH` only when Playwright cannot locate a browser. Review the image, then update `DEMO_SHA256` in `tools/check_public_release.py` to the new approved hash.
