# checkname Protocol

Use this workflow when someone wants to know whether a brand, product, domain,
or social handle appears to be available.

## Scope

This protocol is for fast namespace triage:

- domain candidates
- social handles
- cross-platform consistency
- optional USPTO federal trademark-search triage

It is not:

- trademark clearance
- legal advice
- a substitute for checking the actual registrar or signup flow

## Primary Tool

Prefer the bundled checker script for deterministic probing:

```bash
python3 claude-plugin/scripts/checkname.py "Candidate Name" --json
```

Use comma-separated explicit variants when needed:

```bash
python3 claude-plugin/scripts/checkname.py "Candidate Name" \
  --variants candidate,candidate-name,getcandidate \
  --json
```

To include federal trademark triage:

```bash
python3 claude-plugin/scripts/checkname.py "Candidate Name" \
  --trademark-uspto \
  --json
```

If you are running from a generated mirror, use that mirror's `scripts/`
directory instead.

## Workflow

1. Normalize the proposed name into 2-5 reasonable variants.
2. Probe the variants across domains and selected platforms.
3. Treat `uncertain` as unresolved, not available.
4. Recommend the variants with the most consistent availability.
5. If USPTO triage is requested, treat it as manual trademark review support:
   - exact wording queries
   - broadened wording queries
   - live-result review in the official search system
6. Tell the user to confirm final availability manually at:
   - the registrar
   - the platform signup flow
   - trademark databases if the name matters commercially

## Status Meanings

- `taken`: strong evidence the domain/handle already exists
- `available`: strong evidence it is unclaimed
- `uncertain`: anti-bot, login wall, ambiguous redirect, or weak signal
- `error`: transport or parsing failure

## Good Output Shape

Return:

- a short summary
- the best 2-3 candidate variants
- domain results
- social results
- unresolved items

Always keep the final caveat:

`This is namespace triage, not trademark or legal clearance.`
