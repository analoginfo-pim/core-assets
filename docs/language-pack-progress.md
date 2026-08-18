# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**en-GB UK quality finish:** remaining identical-to-US leaves rewritten to
natural UK English where a distinct form exists (organisation/authorised
lexicon, Contents vs Table of contents, Loading the dashboard, Your
training is due soon, Look-back period, Notes for the export package,
formal UK agent/status/configurator chrome). Win32 `&` accelerators kept
where possible. Never appended "(UK)". Placeholders and `source_sha256`
preserved from `en`.

Honest identical-to-`en` recount (locales + locales-ui + native en-GB,
including Jump/DB Mgmt): **52** total — **3** long intentional
(`{organization_name}` banners + Copyright), KEEP chrome (OK / Cancel /
Apply / Close / Save / Error / Warning / Browse… / &Apply / &Save), plus
unavoidable variety-neutral short tokens and product proper nouns (CMMC,
POA&M, MSP-run IGA, Level 1–3, scaffold titles, Live/Partial/BLOCKED,
Yes/No, language names Deutsch/English/Français, AIC Jump Server / AIC
Database Management Agent product strings, PKCS#11, asset path tokens).
**Partial:** those remaining identical strings are intentional KEEP or
variety-neutral — not unfinished UK copy.

`aic-server` audit: en-GB **missing 0 / stale 0 / orphan 0 /
placeholder_broken 0** (present 536 / en_total 536).

**Configurator hardcoded extract (menus / dialogs / CLI):** Agent Win32
menu bar captions (`.rc` → pack keys + `apply_menu`), Server
settings/elevation/asymmetric dialog help and status strings, Jump and
DB Mgmt CLI About/Status/syslog-probe lines — all `en`+`de` in
`i18n-native`. Other tags may omit new keys. Follow-up: Server
install/uninstall confirm + Load/Save failed lines; DB password-mismatch
CLI. Beavis2 restaged PF/PD; packs API 18/18.

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

- `97159ae` — hardcoded extract: Agent menus, Server dialogs, Jump/DB CLI (en+de)
- `369b857` — en-GB quality finish; identical-to-en **52** (KEEP +
  variety-neutral + 3 long intentional); aic-server audit clean for en-GB
- `d967120` — stamp configurator help-keys SHA `30a1460`
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
