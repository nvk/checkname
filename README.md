# checkname

`checkname` is a small cross-agent checker for domain and social-handle
availability.

It is built for naming work:

- brand names
- product names
- app names
- launch handles

It does fast namespace triage across common domains and platforms, then compares
candidate variants conservatively.

It is not:

- trademark clearance
- legal advice
- a substitute for checking the registrar or signup flow yourself

It can also generate official USPTO federal trademark search queries for manual
review in the USPTO Trademark Search system.

## What It Checks

- domains via RDAP
- GitHub
- X
- Instagram
- TikTok
- YouTube
- Bluesky
- Reddit
- LinkedIn company slugs
- optional USPTO trademark-search queries for manual review

## Status Model

`checkname` returns four statuses:

- `taken`: strong evidence the domain or handle already exists
- `available`: strong evidence it is unclaimed
- `uncertain`: anti-bot response, login wall, weak signal, or ambiguous redirect
- `error`: transport or parsing failure

`uncertain` is important. A lot of social platforms deliberately make automated
checks noisy. `checkname` is designed to narrow options, not fake certainty.

USPTO support is intentionally conservative. `checkname` does not claim a mark
is safe or registrable. It generates official-style search queries and tells you
to review live federal results manually.

## Quick Start

Run the checker directly:

```bash
python3 claude-plugin/scripts/checkname.py "Acme Labs" --json
```

Check specific variants:

```bash
python3 claude-plugin/scripts/checkname.py "Acme Labs" \
  --variants acmelabs,acme-labs,getacme \
  --tlds com,io,ai,org \
  --platforms github,x,instagram,youtube,tiktok,bluesky,reddit,linkedin \
  --json
```

Render a readable report:

```bash
python3 claude-plugin/scripts/checkname.py "Acme Labs" --markdown
```

Include USPTO federal trademark triage:

```bash
python3 claude-plugin/scripts/checkname.py "Acme Labs" \
  --trademark-uspto \
  --json
```

That adds:

- exact wording queries using USPTO `CM:` syntax
- broadened wording queries based on the official USPTO search guidance
- the official search URL: `https://tmsearch.uspto.gov/`

It does not return a legal clearance answer.

## Agent Support

This repo ships the same workflow in multiple forms:

- `claude-plugin/`
  - source-of-truth Claude plugin
  - includes the `/checkname` command
- `plugins/checkname/`
  - generated Codex plugin mirror
- `plugins/checkname-opencode/`
  - generated OpenCode mirror
- `AGENTS.md`
  - portable fallback instructions for other coding agents

### Claude Code

Add the marketplace once:

```bash
claude plugin marketplace add nvk/checkname
```

Then install the plugin:

```bash
claude plugin install checkname@checkname
```

Primary command:

```text
/checkname "Acme Labs"
```

For federal trademark triage:

```text
/checkname "Acme Labs" --trademark-uspto
```

### Codex

Install from GitHub:

```bash
codex plugin marketplace add nvk/checkname
```

Or, if you are adding it from a local checkout:

```bash
codex plugin marketplace add /absolute/path/to/checkname/plugins/checkname
```

Then open `/plugins`, enable `checkname`, and use it.

Canonical explicit invocation in Codex:

```text
@checkname northstar
@checkname "North Star Labs" --trademark-uspto
```

If Codex starts exploring the current repo instead of using the plugin, the
usual causes are:

- the marketplace was added but the plugin was not enabled in `/plugins`
- the current session predates the install and needs a restart
- `@checkname` was typed in a client where the plugin is not installed

### OpenCode

Load:

```text
plugins/checkname-opencode/skills/checkname/SKILL.md
```

### Any Other Coding Agent

Use [AGENTS.md](AGENTS.md) as the portable instruction layer.

## Output Shape

The checker is designed to support:

- a short recommendation
- the best 2-3 candidate variants
- domain results
- platform results
- unresolved cases that need manual confirmation
- optional USPTO trademark-search queries for manual review

## Development

`claude-plugin/` is the source of truth.

After changing source files, resync the generated mirrors:

```bash
./scripts/sync-codex-plugin.sh
./scripts/sync-opencode-plugin.sh
```

Validate:

```bash
python3 -m unittest tests/test_checkname.py
./tests/test_checkname_plugin.sh
```

## Copyright and Warranty

Copyright (c) 2026 nvk.

`checkname` is released under the MIT License and is provided as-is, without
warranty of any kind. See [LICENSE](LICENSE).
