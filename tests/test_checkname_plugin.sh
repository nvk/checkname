#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

test -f "$ROOT/claude-plugin/.claude-plugin/plugin.json"
test -f "$ROOT/claude-plugin/commands/checkname.md"
test -f "$ROOT/claude-plugin/skills/checkname/SKILL.md"
test -f "$ROOT/claude-plugin/skills/checkname/references/platforms.md"
test -f "$ROOT/claude-plugin/scripts/checkname.py"
test -f "$ROOT/plugins/checkname/.codex-plugin/plugin.json"
test -f "$ROOT/plugins/checkname/skills/checkname/SKILL.md"
test -f "$ROOT/plugins/checkname/skills/checkname/references/platforms.md"
test -f "$ROOT/plugins/checkname-opencode/skills/checkname/SKILL.md"
test -f "$ROOT/plugins/checkname-opencode/skills/checkname/references/platforms.md"
test -f "$ROOT/scripts/bootstrap-codex-plugin.sh"
test -f "$ROOT/scripts/verify-codex-plugin.sh"

bash -n "$ROOT/scripts/bootstrap-codex-plugin.sh"
bash -n "$ROOT/scripts/verify-codex-plugin.sh"

python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
source = json.loads((root / "claude-plugin/.claude-plugin/plugin.json").read_text())
codex = json.loads((root / "plugins/checkname/.codex-plugin/plugin.json").read_text())
assert source["version"] == codex["version"]
assert source["name"] == "checkname"
assert codex["name"] == "checkname"
PY

echo "plugin validate: ok"
