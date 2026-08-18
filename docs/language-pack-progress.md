# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Milestone:** Handbook + flag assets (commit pending with this note after push).

- Developer standard: `docs/language-pack-developer-standard.md` (IDs, product tags, hash/audit, picker, no English leakage).
- Partner handbook updated: `docs/enterprise-localization.md` (`en-GB`, `zh-Hans`, `zh-TW`, `he` RTL, pack hash, picker).
- Compliance rule updated (workspace + `core-assets` mirror): `zh-TW`, Hebrew Tier 2, hash/picker notes.
- MIT lipis/flag-icons 4x3 SVGs under `content/language-packs/<tag>/flag.svg` (18 tags) + `LICENSE-flag-icons.txt`.

**Prior — Wave A (`0f5d486`):** French and Spanish match current US English key set for aic-server (`en_total` 536, fr/es missing 0 / stale 0) and native packs. German still has many orphan keys not yet in English source packs.

**Prior — Hash migration (`fd368bf`):** all existing catalogs use `{text, source_sha256}`.

**Prior — Tools (`b6be41d`):** manifest + Python tools + glossary.

## History

- `0f5d486` — Wave A fr/es complete vs en
- `fd368bf` — entry format + hash migration
- `b6be41d` — manifest + language_packs.py
