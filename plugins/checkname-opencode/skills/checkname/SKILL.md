---
name: checkname
description: Check domain and social namespace availability for candidate names and handles. Use when someone needs fast triage on whether a brand, product, or handle appears to be available across domains and common social platforms. Prefer the bundled checkname script and report uncertain cases honestly.
---

# checkname

## Codex Plugin Notes

Codex plugins do not register Claude-style slash commands. In Codex, the
canonical explicit invocation is:

```text
@checkname northstar
@checkname "North Star Labs" --trademark-uspto
```

If `@checkname` is present, treat it as an explicit request to use this skill.
Do not fall back to generic repo exploration unless the bundled checker itself
fails or the plugin is not installed/enabled in the current Codex session.

## Purpose

This skill helps an agent answer:

- Is `brandname.com` likely available?
- Is `@brandname` taken on GitHub, X, Instagram, or YouTube?
- Which spelling variant is the cleanest cross-platform option?

The goal is fast namespace triage, not legal clearance.

## Use the checker script

Run the bundled checker with structured output first:

```bash
python3 ../../scripts/checkname.py "Candidate Name" --json
```

You can narrow the scope:

```bash
python3 ../../scripts/checkname.py "Candidate Name" \
  --variants candidate,candidate-name,getcandidate \
  --tlds com,io,ai,org \
  --platforms github,x,instagram,youtube,tiktok,bluesky,reddit,linkedin \
  --json
```

If the user wants a human-readable report:

```bash
python3 ../../scripts/checkname.py "Candidate Name" --markdown
```

If the user wants federal trademark triage too:

```bash
python3 ../../scripts/checkname.py "Candidate Name" --trademark-uspto --json
```

That mode should be described as:

- official USPTO search-query generation
- manual review support
- not trademark clearance

## Interpretation rules

1. Prefer `taken` and `available` only when the signal is clear.
2. Treat `uncertain` as unresolved. Do not quietly convert it into `available`.
3. Favor variants that are consistent across:
   - primary domain
   - GitHub
   - X
   - Instagram
   - YouTube
4. If one platform blocks automated checks, tell the user exactly that.
5. Always state:
   - this is namespace triage
   - final confirmation should happen in the registrar or signup flow
   - this is not trademark clearance

## Recommended output

Return:

- a 1-2 sentence recommendation
- the best 2-3 candidate variants
- a compact domain table
- a compact platform table
- a short unresolved list

## Supported platforms

See [references/platforms.md](references/platforms.md).
