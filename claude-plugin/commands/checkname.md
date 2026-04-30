---
description: "Check domain and social-handle availability for a candidate name or explicit variants"
argument-hint: "\"<candidate name>\" [--variants a,b,c] [--tlds com,io,ai] [--platforms github,x,instagram,youtube,tiktok,bluesky,reddit,linkedin] [--trademark-uspto] [--markdown|--json]"
allowed-tools: Bash, Read
---

# /checkname

Use the bundled checker script to triage domain and social-handle availability.

## Workflow

1. Parse the candidate name and optional flags from `$ARGUMENTS`.
2. Run the bundled script:

```bash
python3 claude-plugin/scripts/checkname.py "<candidate>" --json
```

3. Pass through optional flags like `--variants`, `--tlds`, and `--platforms`.
4. If the user asks about federal trademarks, pass `--trademark-uspto`.
5. If the user asks for a readable report, use `--markdown`. Otherwise default
   to JSON and summarize it.
6. Interpret results conservatively:
   - `taken`: strong evidence the namespace exists
   - `available`: strong evidence it is unclaimed
   - `uncertain`: anti-bot, login wall, redirect ambiguity, or weak signal
   - `error`: transport or parsing failure
7. Recommend the best 2-3 variants with the cleanest cross-platform availability.
8. If USPTO triage is included, describe it as official search-query generation
   for manual review, not a trademark-clearance answer.

Always say:

- this is namespace triage, not trademark clearance
- final confirmation should happen in the registrar or signup flow
