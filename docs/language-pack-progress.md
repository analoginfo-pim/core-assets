# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Configurator screens/help from pack keys:** `en` (+ `de`) expanded for
AIC Server (`server_configurator.json` help/status/dialog keys), Jump and
DB Mgmt (full Tauri `ui.json` key sets), and Agent About
(`config.about.*` in `pim-offline-agent` messages). Win32/Tauri loaders
resolve via `pim-app-config-i18n` disk `.text` packs. Other tags may omit
the new keys (incomplete product pack OK; do not claim selectable until
complete).

Jump/DB MSI harvest (18 tags) remains as before.

Complete tags (installer harvest / SPA packs API — not every native
configurator key set):

`en`, `de`, `fr`, `es`, `en-GB`, `zh-Hans`, `zh-TW`, `ja`, `ko`, `pt-BR`,
`it`, `he`, `pl`, `tr`, `nl`, `sv`, `fi`, `ar`

## History

- `30a1460` — configurator screen/help keys (Server/Agent/Jump/DB) en+de
- `bab36a4` — Jump/DB native catalogs for all 18 tags + configurator JSON
- `bf48f53` — sync locales-ui into server; product harvest / Beavis2 stage note
- `66ec69d` / `7118aad` — en-GB UK quality follow-up lexical pass
- `d4fe15f` / `1941fae` — en-GB UK quality rewrite
- `fa05cb7` — Wave D pl/tr/nl/sv/fi/ar
- `9a24427` — Wave C ja/ko/pt-BR/it/he
- `417f904` — Wave B en-GB / zh-Hans / zh-TW
- `0f5d486` — Wave A fr/es
- `fd368bf` — entry format + hash migration
- `b6be41d` — manifest + language_packs.py
