# checkname Development Guide

## Structure

- `claude-plugin/` is the source of truth.
- `plugins/checkname/` is the generated Codex mirror.
- `plugins/checkname-opencode/` is the generated OpenCode mirror.
- `AGENTS.md` is the portable fallback for any other coding agent.

Do not hand-edit generated plugin mirrors. Re-run:

```bash
./scripts/sync-codex-plugin.sh
./scripts/sync-opencode-plugin.sh
```

## Validation

Run before shipping changes:

```bash
python3 -m unittest tests/test_checkname.py
./tests/test_checkname_plugin.sh
```
