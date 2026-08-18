# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Milestone:** Catalog entry format + SHA-256 hash migration (in progress — see History for prior SHA).

- All existing JSON catalogs under `locales/`, `locales-ui/`, and `i18n-native/` use `{ "text", "source_sha256" }` leaves.
- `language_packs.py hash` recomputed US English hashes; matching keys in `de` / `es` / `fr` stamped when empty.
- **aic-server audit (after hash):** see `docs/language-pack-audit-aic-server.json`.
- **Known gap:** German SPA catalogs contain many keys not yet in US English packs (`en` SPA still smaller than `de`). Those keys are orphans until English source rows land. Other languages will be filled from the current `en` key set only — English is never pasted as a “translation.”
- Flags and Wave A–D pack fills are next.

## History

- `b6be41d` — manifest.json, glossary, Python tools + wrappers.
