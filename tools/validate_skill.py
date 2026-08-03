#!/usr/bin/env python3
"""Validate the public BANG skill without external Python packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "bang"


def main() -> int:
    errors: list[str] = []
    skill_md = SKILL / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        errors.append("SKILL.md has invalid YAML frontmatter boundaries")
    else:
        fields = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                errors.append(f"invalid frontmatter line: {line}")
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
        if set(fields) != {"name", "description"}:
            errors.append("frontmatter must contain only name and description")
        if fields.get("name") != "bang":
            errors.append("skill name must be bang")
        if len(fields.get("description", "")) < 80:
            errors.append("description is too short to define reliable triggers")

    if len(content.splitlines()) >= 500:
        errors.append("SKILL.md must stay below 500 lines")

    required = [
        SKILL / "agents" / "openai.yaml",
        SKILL / "scripts" / "configure.py",
        SKILL / "scripts" / "analyze_reports.py",
        SKILL / "references" / "mcp-contract.md",
        SKILL / "references" / "report-schema.md",
        SKILL / "references" / "feishu-output-spec.md",
        SKILL / "references" / "source-aliases.json",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if 'default_prompt: "' not in metadata or "$bang" not in metadata:
        errors.append("openai.yaml default_prompt must explicitly mention $bang")
    if 'value: "wanhu-admin"' not in metadata:
        errors.append("openai.yaml must declare the wanhu-admin MCP dependency")
    if 'url: "http://8.141.17.133:1024/mcp"' not in metadata:
        errors.append("openai.yaml must declare the approved wanhu-admin MCP URL")

    for link in re.findall(r"\[[^\]]+\]\((references/[^)]+)\)", content):
        if not (SKILL / link).is_file():
            errors.append(f"broken SKILL.md reference: {link}")

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
