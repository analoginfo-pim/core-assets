# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Consumer sync (`bd9378a`):** ran `scripts/sync-to-projects.ps1` on
Beavis2. Mirrored `content/i18n-native` →
`pim-app-config/crates/pim-app-config-i18n/bundles` (pushed as
`pim-app-config` `e1d579b`). `content/locales` + `locales-ui` already matched
`pim-offline-server/locales` (no consumer commit). Beavis2 disk overlay
(no Server UI rebuild): robocopy into
`C:\Program Files\AIC\PimServer\locales` and
`C:\ProgramData\AIC\PimServer\locales` (+ `ui/`). `aic-server-service`
left **Running**. Native configurator **binaries** still embed prior
packs until a separate non-UI rebuild; JSON-on-disk overlay does not
replace `include_str` bundles — **BLOCKED** for live Win32/Tauri string
match without that rebuild. Did not touch picker UI worker files; left
local dirty `gui/en/server_configurator.json` uncommitted.

**NEW configurator keys filled (post-97159ae):** the 125 keys that landed
in `en`+`de` only — Server `server_configurator.json` (40), Agent
`messages.json` (52), Jump CLI (5), DB Mgmt CLI (28) — are now present
for **fr, es, en-GB, zh-Hans, zh-TW, ja, ko, pt-BR, it, he, pl, tr, nl,
sv, fi, ar**. Deep-merge only; existing leaves untouched. Leaf shape
`{"text","source_sha256"}` matches `en`. Formal register; en-GB uses
Enrolment / programme / dialogue / serialise where distinct. KEEP chrome
kept for `AIC PIM/PAM`, field ids, and short `ok` / `fips_*` tokens.

**Native audit (these four files):** every tag **missing 0 / stale 0**
(same key counts as `en`: 335 / 164 / 8 / 31). Broader `audit --product
all` still reports unrelated gaps (e.g. `db_mgmt_configurator.json` Tauri
UI keys) outside this slice.

**en-GB UK quality finish** (prior): remaining intentional identical-to-
US leaves documented earlier; not reopened here.

Jump/DB MSI harvest (18 tags) remains as before.

Complete tags (installer harvest / SPA packs API — not every native
configurator key set):

`en`, `de`, `fr`, `es`, `en-GB`, `zh-Hans`, `zh-TW`, `ja`, `ko`, `pt-BR`,
`it`, `he`, `pl`, `tr`, `nl`, `sv`, `fi`, `ar`

## History

- *(this note)* — sync-to-projects + Beavis2 locale overlay from `bd9378a`
- `bd9378a` — fill NEW configurator keys for 16 tags
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
