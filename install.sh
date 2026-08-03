#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE_DIR="$SCRIPT_DIR/skills/bang"
TARGET_ROOT="${AGENTS_SKILLS_HOME:-$HOME/.agents/skills}"
TARGET_DIR="$TARGET_ROOT/bang"

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "BANG skill source not found: $SOURCE_DIR" >&2
  exit 1
fi

if [ -e "$TARGET_DIR" ]; then
  echo "Refusing to overwrite existing skill: $TARGET_DIR" >&2
  echo "Move or remove it explicitly, then rerun this installer." >&2
  exit 2
fi

mkdir -p "$TARGET_ROOT"
cp -R "$SOURCE_DIR" "$TARGET_DIR"
chmod +x "$TARGET_DIR/scripts/"*.py

echo "Installed BANG to $TARGET_DIR"
echo "Next: configure the Yishan GEO MCP and your Feishu destination URL."
