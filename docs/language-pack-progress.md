# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Milestone:** Wave A — French (`fr`) and Spanish (`es`) complete for aic-server + matching native chrome (vous / usted; placeholders preserved).

- **aic-server audit** (`docs/language-pack-audit-aic-server.json`): `en_total` **536**; **fr** missing **0**, stale **0**; **es** missing **0**, stale **0** (orphans are extra `locales-ui/docs.json` keys not in current `en`).
- **Native** (gui chrome + server_configurator + agent + recording-agent): `en_total` **470**; **fr** / **es** missing **0**, stale **0**.
- Catalog leaf format remains `{ "text", "source_sha256" }` with hashes matching US English.
- German (`de`) untouched this wave. `en-GB` / `zh-Hans` not started.
- Tooling helpers under `scripts/language-packs/wave_a_*.py` support apply/fill; do not treat English as a translation.

## History

- `fd368bf` — Catalog entry format + SHA-256 hash migration.
- `b6be41d` — manifest.json, glossary, Python tools + wrappers.
