# Work packet — Slice 1 English recovery (en)

**Status:** ACTIVE GATE — must complete before any target-language fan-out.

## Goal

Reconstruct a **clean US English** source catalog. The current en pack is
**BLOCKED** (German chips, ASCII-folded DE, DE↔EN splices). Translating from
it propagates poison into six languages.

## Forbidden recovery methods

- **Do NOT reverse-machine-translate from de into English.** That is how
  the corpus was poisoned.
- Do NOT copy from en-GB, r, es, or Chinese packs.
- Clean de on the same key is a **damage locator only**, never a pivot.

## Required recovery source mix (priority order)

1. **defaultValue in TSX call sites** (pim-offline-server/ui/src/**) —
   authored US English by construction; strongest recovery source.
2. **Git history** before recontamination. Known related commits in
   core-assets:
   - 606641d — en pack remove German leakage
   - 9cb573d / 22869a9 — German purge mirrors
   - Later fills (209270a, 6b71331, …) reintroduced sludge — prefer
     pre-fill clean values where history shows them.
3. **Author fresh** US English in product register where neither exists.

## Quarantine

Start from en-contamination-quarantine.json (heuristic). Expand with the
audit’s strong-marker scan until **zero** DE residue remains in en.

## Target paths

- content/locales-ui/en/*.json
- content/locales/en/*.json

(Coordinate with format sibling if sidecar source_sha256 migration is
in flight — do not fight their format; only restore 	ext values.)

## Acceptance for ENGLISH_CLEAN_VERIFIED

1. Quarantine list empty (or parent-waived named leftovers).
2. Automated DE-marker + ASCII-fold gates on en return zero hits.
3. Spot-check My Workstations / Connect / docs bullets read as native US English.
4. Corpus JSON regenerated; english_clean heuristic ≈ 100% for prior flags.
5. **Still not** a claim that all 6.6k strings are perfect prose — only that
   they are uncontaminated US English suitable as translation source.

## Honesty

This slice produces **clean source**, not “localization done.” Agent recovery
must be bilingual-reviewed for the worst namespaces (pages, docs, help).
