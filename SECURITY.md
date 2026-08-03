# Security Policy

## Supported version

Security fixes are applied to the latest `main` branch.

## Reporting

Use GitHub's private security-advisory flow for credential exposure, cross-customer data access, unsafe destination writes, or report URL leakage. Do not open a public issue containing secrets or customer data.

## Secret handling

- Keep MCP credentials in Codex configuration and environment-backed secret storage.
- Keep the Feishu destination in `~/.config/bang/config.json`; never commit it.
- Do not include customer workbooks in bug reports. Reproduce issues with synthetic data.
- Treat generated report URLs and task IDs as sensitive operational metadata.
