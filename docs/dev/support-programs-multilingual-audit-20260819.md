# Support programs multilingual audit (measured, 2026-08-19)

Read-only inventory of operator-facing **support programs** (elevation helpers,
configurators, launchers, agent-side operator UI, CLIs) versus the admin SPA’s
seven Tier 1 packs. **Not** a Met / certified claim. Vocabulary: Live / Partial /
Absent / BLOCKED.

Ground truth: `pim-app-config/crates/pim-app-config-i18n`,
`core-assets/content/i18n-native/`, per-binary sources, and
`pim-installers/scripts/Stage-NativeLanguagePacks.ps1` + MSI builders.

## Architecture (measured)

| Layer | What exists |
| --- | --- |
| Shared crate | `pim-app-config-i18n`: `resolve_locale`, `PACK_TAGS` (18 tags), `Locale::is_rtl` / `dir()` for `he`/`ar` |
| Common assets | `core-assets/content/i18n-native/{gui,apps,cli}/` mirrored into crate `bundles/` |
| Compile-time embed | Most catalogs `include_str!` only **`en` + `de`** (chrome / server_configurator / offline_client also **`fr`** in places). Other tags need **disk** packs |
| Disk loader | Prefer `INSTALLFOLDER\locales\<tag>\` (and overlays); then compiled fallback |
| MSI staging | `Stage-NativeLanguagePacks.ps1` used by **Agent, Recording, Jump, DB Mgmt** MSIs only. **Server MSI** stages SPA `locales` / `locales-ui`, **not** native `gui/server_configurator.json`. **WA MSI** does not call Stage-Native |

**Tier 1 bar for comparison:** `en`, `en-GB`, `de`, `fr`, `es`, `zh-Hans`, `zh-TW`.

Repo JSON for gui chrome / server_configurator / jump / db_mgmt and for
agent / jump / db / recording **apps** exists for all 18 `PACK_TAGS` (key counts
match `en`). That is **catalog presence**, not delivery.

## Matrix

| Binary / surface | Mechanism | Locales that actually work without extra disk | Approx coverage | In installer? | Status / gap |
| --- | --- | --- | --- | --- | --- |
| **Admin SPA** (reference, out of “support programs”) | react-i18next + `locales-ui` | Tier 1 packs staged by Server MSI | ~180 routes verified (operator claim) | Yes (`locales\ui\`) | **Live** (SPA only) |
| **pim-offline-server-configurator-win32** | Catalog: `chrome` + `server_configurator` (~1005 keys); `.rc` English rewritten at runtime | Compiled **en/de/fr**; other tags need disk gui packs **not** staged by Server MSI | High for dialogs/menus wired through `apply_dialog` / `t()`; long help still EN (doc note) | EXE in Server MSI; **native gui packs not staged** | **Partial** — Live for en/de/fr; Tier 1 zh/es/en-GB/zh-TW **BLOCKED** at install without manual locales |
| **pim-offline-server-configurator-tauri** | Same catalogs via `gui_i18n_chrome`; `document.dir` from `Locale::dir()` | Same as Win32 | Product map applied; few `data-i18n*` attrs (~10) — most strings via English-key map | Same as Win32 | **Partial** (same disk gap) |
| **pim-offline-client-elevate-win32** | Catalog via agent `messages.json` (`locale_ui::apply_main_dialog_strings`); `.rc` is EN template | Compiled agent messages **en/de**; Agent MSI stages **all** app tags + chrome | ~20 main controls catalog-driven; About/misc may stay EN | Elevate EXE + native packs in **Agent MSI** | **Partial** — mechanism Live for elevate chrome; RTL layout **not** applied in elevate-win32; full Tier 1 depends on staged agent packs |
| **pim-offline-client-elevate-tauri** | Agent `ui_message_catalog` + `data-i18n` (~45 attrs) | Front-end `supported: ["en","de","fr"]` hard-limit; lang attr only en/de/fr | Most form chrome catalog-driven; some JS banner strings still hardcoded EN | Agent MSI | **Partial** — not Tier 1–complete in UI picker; RTL **Absent** in elevate-tauri JS |
| **pim-offline-client-configurator-win32** | Agent `messages.json` + RTL (`SetProcessDefaultLayout`) | en/de compiled; disk via Agent MSI | Menus/title via `t()`; large dialog surface still mixed | Agent MSI packs | **Partial** |
| **pim-offline-client-configurator-tauri** | Agent catalog + `data-i18n` (menus etc.) | Depends on agent packs / DEFAULT_SUPPORTED | Substantial menu/chrome; no dedicated `client_configurator.json` in gui/ | Agent MSI | **Partial** |
| **pim-jump-server configurator (Tauri)** | Chrome from crate; product `src/locales/{en,de}/ui.json` | Chrome: disk/compiled; **product ui.json only en+de** in tree | Chrome + en/de product UI | Jump MSI stages apps + `jump_configurator.json` + chrome | **Partial** — Tier 1 product UI for es/zh/… **Absent** in Tauri `ui.json` (only en/de) |
| **pim-jump-server configurator (CLI/Win32)** | `disk_loader` + staged `jump_configurator.json` (~189 keys × 18 tags in repo) | Disk after Jump MSI | Product catalog when disk present | Yes (Jump MSI) | **Partial→Live** for tags on disk after install |
| **pim-db-mgmt-agent configurator (Tauri)** | Same pattern as Jump | Product ui.json **en+de** only | Same | DB Mgmt MSI stages packs | **Partial** |
| **pim-db-mgmt-agent configurator (CLI)** | disk + `db_mgmt_configurator.json` (~240 keys × 18) | Disk after MSI | Same | Yes | **Partial→Live** post-install disk |
| **pim-workstation-assurance configurator (Tauri)** | `chrome_for` only; local `locales/{en,de}/ui.json` | en/de chrome+ui | Chrome + thin ui.json | **No** Stage-Native in WA MSI | **Partial** / installer **Absent** for native packs |
| **recording-agent-configurator-tauri** | Chrome + recording `messages` catalog | Recording MSI stages app packs | Chrome + messages | Recording MSI | **Partial** |
| **pim-product-launcher-win32** | Local `locales/{en,de}/ui.json` (~20 strings) + locale resolve | **en/de only** | Small surface fully cataloged for en/de | Not via Stage-Native (embedded in launcher) | **Partial** — Tier 1 **Absent** |
| **pim-product-launcher-slint** | `chrome_for` + local en/de ui.json | en/de | Minimal | Same | **Partial** |
| **pim-app-config-cli / product CLI `--help`** | Clap `about` = **compile-time EN**; runtime about/before/after only **en+fr** bundles | en (Clap); fr runtime helpers only | Help banners mostly EN | CLI text files not Tier 1–complete; not MSI-harvested like SPA | **Absent** / **Partial** (fr only) |
| **pim-offline-agent CLI** | `cli.json` in agent packs (18 tags in repo; compile **en/de**) | en/de without disk; others with Agent MSI locales | Clap help keys in catalog | Agent MSI | **Partial** |
| **Agent service / WEL / syslog** | Intentionally US English (SIEM) | n/a | n/a | n/a | Out of scope (by design) |

## RTL / encoding (`he` / `ar`)

| Piece | Measured |
| --- | --- |
| Catalogs | `he` / `ar` JSON present under gui + apps (key parity with `en`) |
| Crate API | `Locale::is_rtl()` / `dir()` implemented and unit-tested |
| Server / Jump Tauri | Set `document.documentElement.dir` from chrome / locale |
| Client configurator Win32 | `LAYOUT_RTL` / `WS_EX_LAYOUTRTL` |
| Elevate Tauri | **No** RTL dir wiring; locale picker capped at en/de/fr |
| Elevate Win32 | Catalog apply only — **no** RTL layout helper |

Verdict: RTL is **Partial** (API + some shells) — **not** Live across support programs.

## Installer honesty

| MSI | Native `i18n-native` staged? |
| --- | --- |
| `Build-PimOfflineAgentMsi.ps1` | Yes (`pim-offline-agent` + chrome) — elevate + agent configurators ride this |
| `Build-PimOfflineRecordingAgentMsi.ps1` | Yes |
| `Build-PimJumpServerMsi.ps1` | Yes (+ `jump_configurator.json`) |
| `Build-PimDbMgmtAgentMsi.ps1` | Yes (+ `db_mgmt_configurator.json`) |
| `Build-PimOfflineServerMsi.ps1` | SPA + server `locales` only — **not** `gui/server_configurator.json` via Stage-Native |
| `Build-PimWorkstationAssuranceAgentMsi.ps1` | **No** Stage-Native |

Mechanism present ≠ delivery. Embedded `include_str!` covers a **narrow** locale set;
repo JSON for 18 tags is **not** the same as “ships and is selected in the UI.”

## Plain-language verdict

Support programs are **not** multilingual to the same degree as the admin SPA
(7 Tier 1 locales, crawl-verified).

- **Closest to Live:** AIC Server Configurator (Win32/Tauri) for **en/de/fr** with a large product catalog; Jump/DB Mgmt after MSI when disk packs are present; Agent elevate/configurator for **en/de** (and disk tags when Agent MSI is installed).
- **Partial everywhere else:** product Tauri `ui.json` trees are mostly **en+de**; elevate-tauri picker still **en/de/fr**; launchers **en+de**; CLI help largely **English**.
- **Largest gap:** Tier 1 parity (`en-GB`, `es`, `zh-Hans`, `zh-TW`) for support programs — catalogs often exist in `i18n-native`, but (1) compile-time embeds omit them, (2) Server/WA MSI paths do not stage native gui packs, (3) several Tauri front-ends only ship en/de `ui.json` and/or hard-limit supported tags. SPA multilingual is **not** inherited by elevation helpers / configurators / launchers / CLIs.

Overall support-program multilingual status: **Partial**. Not Absent (mechanism + packs exist). Not Live vs SPA Tier 1 bar.

## Evidence paths (primary)

- `pim-app-config/crates/pim-app-config-i18n/src/{locale,disk_loader,catalog/*}.rs`
- `core-assets/content/i18n-native/`
- `pim-installers/scripts/Stage-NativeLanguagePacks.ps1`
- `pim-offline-server-configurator-{win32,tauri}` `gui_i18n` / `i18n.rs`
- `pim-offline-client-elevate-{win32,tauri}` `locale_ui.rs` / `src/i18n.js`
- `pim-offline-client/src/i18n.rs` + `docs/dev/operator-cli-i18n.md`

Origin: 2026-08-19 operator read-only audit (no product code change, no deploy).
