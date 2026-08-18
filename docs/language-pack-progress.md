# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Tauri Appearance language combo (System + 18 PACK_TAGS):** Server Tauri,
Agent Tauri, Jump Config Tauri, and DB Mgmt Tauri now list the same language
choices as Win32 — System default plus every [`PACK_TAGS`] entry via
`locale_pref_choices_ui()` / `pack_display_label`. Cookie + `UI_LOCALE`
identity fallback; `en-GB` never aliases to `en`; `zh-TW` never aliases to
`zh-Hans`. `document.documentElement.dir` follows chrome `dir` (`rtl` for
he/ar). Shared `locale-browser.js` uses `canonicalizePackTag` aligned with
Rust. Jump/DB gained a minimal Appearance panel when none existed.

**Live Beavis2 restage (Tauri, debug):** Program Files copies —
`PimServer\pim-offline-server-configurator-tauri.exe`,
`PimAgent\pim-offline-client-configurator-tauri.exe` (+ agent-named twin),
`PimJumpServer\pim-jump-server-configurator-tauri.exe`,
`DbMgmtAgent\pim-db-mgmt-agent-configurator-tauri.exe`.
`aic-server-service` left **Running**.

**Appearance language combo (18 packs) — Win32 (prior):** Server and Agent
Win32 Appearance dialogs list **System default** plus every [`PACK_TAGS`]
entry. Saving writes `UI_LOCALE` and re-runs RTL layout for he/ar.

**Locale is a pack tag (no enum variants):** `pim-app-config-i18n`
`Locale` is now `{ tag: &'static str }` over [`PACK_TAGS`] (18 tags).
`parse_tag` / `canonicalize_pack_tag`: `en`/`en-US` → `en`; **`en-GB`
never aliases to `en`**; **`zh-TW` / `zh-Hant` never alias to `zh-Hans`**;
`he`/`ar` expose `dir() == "rtl"`. Disk maps preferred; chrome uses
`try_load_flat_catalog` (exact tag) then compiled `en`/`de`/`fr`.
Consumers updated off `Locale::En/De/Fr` matches. Admin SPA
LanguageSelector untouched.

**Prior:** Beavis2 INSTALLFOLDER native `locales\` staging (disk packs
on disk). Catalog fill `bd9378a` / prior bundle sync `e1d579b`.
Locale crate `pim-app-config` `5f249f5`.

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

- *(this note)* — Tauri Appearance: System + 18 PACK_TAGS (Server/Agent/Jump/DB)
- *(prior)* — Appearance combo lists System + 18 PACK_TAGS (he/ar RTL) Win32
- *(prior)* — Win32 GDI RTL (he/ar) on Server/Agent main + Help About
- *(prior)* — Beavis2 live debug restage (Agent/Jump/DB/Server + service)
- `69f73e0` — Locale tag string + PACK_TAGS; consumers off En/De/Fr enum
- `001b69e` — Beavis2 INSTALLFOLDER native `locales\` stage; skip include_str rebuild
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
