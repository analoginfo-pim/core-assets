# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Milestone:** Plan 1 plumbing — manifest + Python tools (not yet hashed catalogs).

- Added `content/language-packs/manifest.json` (products, tags, tiers, flags, RTL).
- Added `scripts/language-packs/language_packs.py` (`migrate`, `hash`, `mark-stale`, `audit`) — Python 3 stdlib only; thin `.sh` / `.ps1` wrappers.
- Added `content/language-packs/glossary.en.json` (elevation, vault, rotation, checkout, session, enclave).
- Catalogs still use legacy bare-string JSON until the next milestone runs `hash`.
- Existing tags on disk: `en`, `de`, `es`, `fr` (partial). Planned tags not yet filled: `en-GB`, `zh-Hans`, `zh-TW`, Tier 2/3.
- **SHA:** (set on push)

## History

(See git log on `main` for prior localization commits.)
