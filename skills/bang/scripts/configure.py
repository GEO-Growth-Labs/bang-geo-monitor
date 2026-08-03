#!/usr/bin/env python3
"""Create or inspect BANG's local, untracked configuration."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_CONFIG = Path.home() / ".config" / "bang" / "config.json"
ALLOWED_HOST_SUFFIXES = (".feishu.cn", ".larksuite.com")
REQUIRED_MCP_SERVER = "yishan-geo"


def validate_config(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    server = str(data.get("mcp_server") or "").strip()
    destination = str(data.get("feishu_parent_url") or "").strip()
    if server != REQUIRED_MCP_SERVER:
        errors.append(f"mcp_server must be {REQUIRED_MCP_SERVER}")
    if not destination:
        errors.append("feishu_parent_url is required")
        return errors

    parsed = urlparse(destination)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not any(host.endswith(suffix) for suffix in ALLOWED_HOST_SUFFIXES):
        errors.append("feishu_parent_url must be an HTTPS Feishu or Lark URL")
    if not any(part in parsed.path for part in ("/wiki/", "/sheets/")):
        errors.append("feishu_parent_url must point to a wiki or sheets node")
    return errors


def load_config(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be a JSON object")
    return data


def redact_url(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.hostname:
        return "<invalid>"
    kind = "wiki" if "/wiki/" in parsed.path else "sheets"
    return f"https://***/{kind}/***"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-server")
    parser.add_argument("--feishu-parent-url")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--show", action="store_true", help="validate and show redacted configuration")
    args = parser.parse_args()
    path = args.config.expanduser()

    if args.show:
        try:
            data = load_config(path)
        except FileNotFoundError:
            print("BANG config not found. Run configure.py with both required options.", file=sys.stderr)
            return 2
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print("Cannot read BANG config. Check JSON syntax and file permissions.", file=sys.stderr)
            return 2
        errors = validate_config(data)
        if errors:
            print("Invalid BANG config: " + "; ".join(errors), file=sys.stderr)
            return 2
        print(json.dumps({
            "config": "~/.config/bang/config.json" if path == DEFAULT_CONFIG else "<custom config path>",
            "mcp_server": data["mcp_server"],
            "feishu_parent_url": redact_url(str(data["feishu_parent_url"])),
            "valid": True,
        }, ensure_ascii=False, indent=2))
        return 0

    if not args.mcp_server or not args.feishu_parent_url:
        parser.error("--mcp-server and --feishu-parent-url are required unless --show is used")

    data = {
        "mcp_server": args.mcp_server.strip(),
        "feishu_parent_url": args.feishu_parent_url.strip(),
    }
    errors = validate_config(data)
    if errors:
        print("Invalid BANG config: " + "; ".join(errors), file=sys.stderr)
        return 2

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".bang-config-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"BANG config written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
