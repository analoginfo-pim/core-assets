# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Native disk loader vs rebuild (Beavis2):** shipping Win32/Tauri/CLI
paths in `pim-app-config-i18n` already prefer `disk_loader` (INSTALLFOLDER
`locales\<tag>\*.json` next to the EXE) over compiled `include_str!`
fallbacks. Confirmed: Agent / Jump / DB Mgmt install dirs had **no**
`locales\`; Server `PimServer\locales` held server binder catalogs only
(no `server_configurator.json` / `chrome.json`). Staged 18-tag native
packs beside EXEs (no debug rebuild, no `--release`, no `cargo clean`):

| Install dir | Staging |
| --- | --- |
| `PimAgent\locales` | `Stage-NativeLanguagePacks` → `pim-offline-agent` |
| `PimJumpServer\locales` | same → `pim-jump-server` (+ gui chrome / jump_configurator) |
| `DbMgmtAgent\locales` | same → `pim-db-mgmt-agent` |
| `PimServer\locales` | **merge** gui `chrome.json` + `server_configurator.json` (kept binder/training) |
| `OfflinePimServer\locales` | same gui merge |

**Skipped rebuild** — disk loader wins at runtime when those files exist.
`aic-server-service` restored to **Running** after a transient Stopped
blip during staging. No picker SPA edits. Never rotated `phil`.

**BLOCKED (18-tag native UI selection):** `Locale` in
`pim-app-config-i18n` is still only **`en` / `de` / `fr`**. Tags such as
`ja` / `zh-Hans` / `en-GB` parse to `Locale::En`, so disk packs for those
tags are on disk but not selected through `chrome_for` /
`resolve_locale` until Locale (and match arms) expand. Git sync of
bundles remains `pim-app-config` `e1d579b` / catalogs `bd9378a`.

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

- *(this note)* — Beavis2 INSTALLFOLDER native `locales\` stage; skip rebuild (disk wins); Locale en/de/fr BLOCKED for other tags
- `13d0eac` — sync-to-projects + Beavis2 server locale overlay from `bd9378a`
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
