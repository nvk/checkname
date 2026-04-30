#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_SKILL="$ROOT/claude-plugin/skills/checkname"
SOURCE_SCRIPT="$ROOT/claude-plugin/scripts/checkname.py"
CLAUDE_MANIFEST="$ROOT/claude-plugin/.claude-plugin/plugin.json"
TARGET_PLUGIN="$ROOT/plugins/checkname"
TARGET_SKILL="$TARGET_PLUGIN/skills/checkname"
TARGET_SCRIPT_DIR="$TARGET_PLUGIN/scripts"
TARGET_MANIFEST="$TARGET_PLUGIN/.codex-plugin/plugin.json"

mkdir -p "$TARGET_SKILL/references" "$TARGET_SKILL/agents" "$TARGET_SCRIPT_DIR"
cp "$SOURCE_SKILL/SKILL.md" "$TARGET_SKILL/SKILL.md"
cp "$SOURCE_SKILL/references/platforms.md" "$TARGET_SKILL/references/platforms.md"
cp "$SOURCE_SCRIPT" "$TARGET_SCRIPT_DIR/checkname.py"

python3 - "$CLAUDE_MANIFEST" "$TARGET_MANIFEST" <<'PY'
import json
import sys
from pathlib import Path

claude_manifest = Path(sys.argv[1])
target_manifest = Path(sys.argv[2])

claude = json.loads(claude_manifest.read_text())
target = json.loads(target_manifest.read_text())
target["version"] = claude["version"]
target_manifest.write_text(json.dumps(target, indent=2) + "\n")
PY

cat > "$TARGET_SKILL/agents/openai.yaml" <<'YAML'
interface:
  displayName: checkname
  shortDescription: Check domain and social namespace availability
  longDescription: Probe domain candidates via RDAP and social profile URLs, then compare candidate variants conservatively across platforms.
policy:
  tools:
    - Read
    - Bash
YAML

echo "Synced Codex plugin mirror."
