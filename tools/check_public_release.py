#!/usr/bin/env python3
"""Fail when tracked release files appear to contain secrets or live customer endpoints."""

from __future__ import annotations

import re
import hashlib
import os
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {"", ".md", ".py", ".mjs", ".json", ".yaml", ".yml", ".toml", ".sh", ".txt"}
DEMO_ASSET = Path("docs/assets/bang-demo.png")
DEMO_SHA256 = "78251b6bf97b641cef2885c583ca8145d7a6688600a205ac02d2885afce9dd89"
RULES = {
    "GitHub token": re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Wanhu admin key": re.compile(r"\bagt_[A-Za-z0-9_-]{12,}\b"),
    "Bearer literal": re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._-]{16,}"),
    "live Feishu token URL": re.compile(
        r"https://(?!your-team\.)[A-Za-z0-9-]+\.(?:feishu\.cn|larksuite\.com)/(?:wiki|sheets)/[A-Za-z0-9]{12,}"
    ),
    "long numeric tenant identifier": re.compile(r"(?<!\d)\d{17,22}(?!\d)"),
    "bare Feishu object token": re.compile(r"\b(?:wikcn|shtcn|doccn|doxcn)[A-Za-z0-9]{8,}\b"),
    "opaque mixed-alphanumeric token": re.compile(
        r"\b(?=[A-Za-z0-9]{20,36}\b)(?=[A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*[a-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{20,36}\b"
    ),
    "UUID identifier": re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"),
    "labeled opaque identifier": re.compile(
        r"(?i)(?:task|mainTask|node|spreadsheet|sheet|wiki)[_-]?(?:id|token)\s*[:=]\s*[\"'`]?"
        r"(?!(?:YOUR|REPLACE|EXAMPLE|REDACTED))[A-Za-z0-9_-]{12,}"
    ),
    "unapproved live MCP endpoint": re.compile(
        r"https?://(?!8\.xxx\.xx\.133:1024/mcp\b)(?![^\s'\"]*\.example(?:/|\b))[^\s'\"]+/mcp\b"
    ),
    "private Wanhu endpoint exposure": re.compile(r"8\.141\.17\.133"),
    "report download URL": re.compile(r"https://[^\s'\"]+\.(?:xlsx|xls|csv)(?:\?[^\s'\"]*)?", re.I),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def validate_demo_asset(path: Path) -> list[str]:
    findings: list[str] = []
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != DEMO_SHA256:
        findings.append(f"{DEMO_ASSET}: demo PNG hash changed; regenerate from synthetic renderer and review")
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            return [f"{DEMO_ASSET}: invalid PNG signature"]
        while True:
            header = handle.read(8)
            if not header:
                break
            length, chunk_type = struct.unpack(">I4s", header)
            if chunk_type in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
                findings.append(f"{DEMO_ASSET}: embedded PNG metadata chunk {chunk_type.decode()}")
            handle.seek(length + 4, os.SEEK_CUR)
            if chunk_type == b"IEND":
                break
    return findings


def main() -> int:
    findings: list[str] = []
    paths = tracked_files()
    for path in paths:
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            findings.append(f"{relative}: symbolic links are not allowed in the public release")
            continue
        if not path.is_file():
            continue
        if relative == DEMO_ASSET:
            findings.extend(validate_demo_asset(path))
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            findings.append(f"{relative}: unreviewed binary file is not allowed")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{relative}: non-UTF-8 file is not allowed")
            continue
        for label, pattern in RULES.items():
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append(f"{relative}:{line}: {label}")
    if findings:
        print("Public release scan failed:", file=sys.stderr)
        print("\n".join(findings), file=sys.stderr)
        return 1
    print(f"Public release scan passed ({len(paths)} files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
