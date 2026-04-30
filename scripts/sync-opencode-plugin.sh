#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_SKILL="$ROOT/claude-plugin/skills/checkname"
SOURCE_SCRIPT="$ROOT/claude-plugin/scripts/checkname.py"
TARGET_PLUGIN="$ROOT/plugins/checkname-opencode"
TARGET_SKILL="$TARGET_PLUGIN/skills/checkname"
TARGET_SCRIPT_DIR="$TARGET_PLUGIN/scripts"

mkdir -p "$TARGET_SKILL/references" "$TARGET_SCRIPT_DIR"
cp "$SOURCE_SKILL/SKILL.md" "$TARGET_SKILL/SKILL.md"
cp "$SOURCE_SKILL/references/platforms.md" "$TARGET_SKILL/references/platforms.md"
cp "$SOURCE_SCRIPT" "$TARGET_SCRIPT_DIR/checkname.py"

cat > "$TARGET_PLUGIN/README.md" <<'EOF'
# checkname for OpenCode

Load:

```text
plugins/checkname-opencode/skills/checkname/SKILL.md
```

The checker script lives at:

```text
plugins/checkname-opencode/scripts/checkname.py
```
EOF

echo "Synced OpenCode plugin mirror."
