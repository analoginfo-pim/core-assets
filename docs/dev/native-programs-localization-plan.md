# Native support programs — Tier 1 localization plan

**Status:** Plan only (2026-08-19). No product code, catalog, embed, or deploy
work in this change set.

**Builds on:** [`support-programs-multilingual-audit-20260819.md`](support-programs-multilingual-audit-20260819.md)
(`core-assets` `44da8ac`). Do not re-audit; verify blockers before each slice.

**Home:** `core-assets/docs/dev/` (this file), not `pim-offline-server/docs/dev/`.
Native catalogs and the measured audit already live in `core-assets`; the work
spans elevate, agent, Jump, DB Mgmt, WA, launchers, and CLIs. Server docs would
imply a single-repo owner that does not exist.

**Vocabulary:** Live / Partial / Absent / BLOCKED
([`compliance-claims-honesty.mdc`](../../.cursor/rules/compliance-claims-honesty.mdc)).
Not Met / certified.

**Tier 1 tags:** `en`, `en-GB`, `de`, `fr`, `es`, `zh-Hans`, `zh-TW`
([`compliance-artifacts-must-localize.mdc`](../../.cursor/rules/compliance-artifacts-must-localize.mdc)).

**Sibling coordination (do not edit their trees in this plan’s slices):**

| Sibling | Relevance |
| --- | --- |
| MSI / `pim-installers` | Server + WA `Stage-NativeLanguagePacks` wiring is **in progress / present in tree** (confirm at slice start; do not duplicate) |
| WA crate docs | Product docs only — leave alone |
| Operator-manuals plan | Separate surface — leave alone |

---

## One-line git baseline (plan authoring)

| Repo | Baseline |
| --- | --- |
| `core-assets` | `main` @ `44da8ac` (audit); dirty SPA locale / localization-work trees from siblings — **stage only this plan path** |
| `pim-offline-server` | `local/reporting-integration` @ `194ba60c3` (SPA nav-crawl); unrelated dirty tree — **do not touch** |

---

## Honest overall status

| Claim | Status |
| --- | --- |
| Mechanism (`pim-app-config-i18n`, disk loader, `PACK_TAGS` = 18) | **Live** |
| Repo catalogs under `content/i18n-native/` for gui + agent apps | **Live** (key parity with `en` for gui chrome / agent messages — catalog presence) |
| Tier 1 **delivery** in elevate / configurators / launchers / CLIs | **Partial** — not near Live |
| RTL (`he` / `ar`) across elevate shells | **Absent** → **Partial** API only (Tier 2; not required to close Tier 1) |

Repo JSON ≠ ships ≠ selectable in UI. Three separate blockers below.

---

## 1. Three distinct blockers (do not conflate)

| Blocker | What fails | Fix class | Typical files |
| --- | --- | --- | --- |
| **A. Compile-time embeds** | Binary only `include_str!`s `en`/`de` (and sometimes `fr`). Without disk packs, other tags fall back to English or miss keys. | Expand embeds **or** guarantee disk always present for that binary’s install layout | `pim-app-config-i18n/src/catalog/*.rs`, `bundles/` sync from `content/i18n-native/` |
| **B. UI-level tag caps** | Pickers / `supported: ["en","de","fr"]` / product `locales/{en,de}/ui.json` hide tags even when disk+embed work | Remove caps; drive picker from `PACK_TAGS` or Tier 1 subset; add product `ui.json` per tag | `elevate-tauri/src/i18n.js`, `locale-browser.js`; Jump/DB/WA/launcher `src/locales/**/ui.json` |
| **C. Packaging** | MSI never stages native packs → disk loader empty after install | `Stage-NativeLanguagePacks.ps1` + WiX harvest + required-file asserts | `pim-installers/scripts/Build-Pim*.ps1` |

**Verified at plan time (delta vs audit `44da8ac`):**

- **Agent / Recording / Jump / DB Mgmt** — still stage native packs (audit correct).
- **Server MSI** — now calls `Stage-NativeLanguagePacks` with `-AppKey pim-offline-server -MergeOnly` and asserts `chrome.json` + `server_configurator.json` for sample Tier 1 tags including `zh-Hans` / `zh-TW`. Treat packaging for Server configurators as **sibling-owned; confirm Live in MSI evidence before re-work**.
- **WA MSI** — now stages GuiOnly chrome via Stage-Native; product `ui.json` embeds remain a **separate** compile-time / UI-cap slice.

Elevate already rides **Agent MSI** packaging (C largely OK for elevate). Elevate’s remaining Tier 1 gaps are primarily **B** (Tauri picker) and **A** (compiled agent `messages` only `en`/`de` when disk missing) plus plain-language / RTL follow-ons.

---

## 2. Recommended slice ordering (justified)

Operator emphasis: **elevate is end-user-facing** on the local machine, often under time pressure. Ordering maximizes that audience first, then reuses the same agent catalogs / MSI, then admin configurators, then thin shells, then CLIs.

| Order | Surface | Why this order | Effort (Tier 1 to Live*) |
| --- | --- | --- | --- |
| **0** | Policy + verification harness design | Register rule clarification + automated check prevents silent rot | S |
| **1** | Elevate Win32 + Elevate Tauri | Highest end-user value; ~20–45 chrome keys already catalog-driven; Agent MSI already stages packs | M |
| **2** | Agent configurator (Win32 + Tauri) | Same `messages.json` / Agent MSI as elevate; operator surface next to elevate on endpoints | M |
| **3** | Server configurator (Win32 + Tauri) | Large catalog (~1000 keys) already Partial for en/de/fr; packaging sibling may already close C — focus B + long-help + verify disk | L |
| **4** | Jump / DB Mgmt configurators | Disk catalogs Live post-MSI; product Tauri `ui.json` still **en+de only** (blocker B) | M each |
| **5** | WA configurator | Chrome staging sibling in flight; thin product `ui.json` + no dedicated product JSON — smaller but Incomplete | M |
| **6** | Product launchers (Win32 / Slint) | Small string set; currently en/de only — fast once pattern proven | S |
| **7** | Operator CLIs (`--help`) | Lowest interactive urgency; Clap compile-time EN is structural — last | L |

\*Live = Tier 1 tags selectable, strings from catalogs (disk or embed), missing-key fail closed, verified by harness — not “JSON exists in git.”

**Rejected alternate:** Server configurator first — wrong audience vs operator directive. **Rejected:** expand all 18 tags in elevate UI before Tier 1 works — Tier 1 first; Tier 2/3 later.

---

## 3. Embed versus disk — recommendation

**Recommendation: both, with disk overriding compile-time embeds** (already the designed shape in `disk_loader.rs` + catalog modules). Do **not** choose compile-only or disk-only.

| Concern | Implication |
| --- | --- |
| Offline endpoints / no server | Elevate and agent GUIs must not call the server for catalogs. Disk next to install + compiled fallback covers this. |
| MSI upgrade | Disk packs refresh without rewriting every `include_str!`. Matches the SPA lesson: locale JSON on disk → fast fix loop. |
| Broken / missing install tree | Compiled `en` (and preferably `de`/`fr`) keep a usable English/German dialog if `locales\` is deleted. |
| Binary size | Embedding all 18 × large catalogs into every binary is costly; Tier 1 expand-on-demand is enough for elevate’s small `messages` surface if desired. |

**Concrete policy for this program:**

1. **Keep** disk-first load from `INSTALLFOLDER\locales\<tag>\` (and documented ProgramData overlay if already present).
2. **Keep** compiled fallback for at least `en` (+ current `de`/`fr` where already embedded).
3. **For elevate / agent endpoint binaries:** guarantee Agent MSI always stages **all Tier 1** agent app packs + chrome (already intended). Optionally expand `include_str!` for agent `messages.json` to **all Tier 1** so a copy of elevate EXE alone (side-by-side without full MSI tree) still speaks Tier 1 — nice-to-have in Slice 1b, not a substitute for packaging.
4. **Do not** invent product env vars for catalog paths ([`no-environment-variables.mdc`](../../.cursor/rules/no-environment-variables.mdc)).

---

## 4. Endpoint language selection (including offline)

**Authoritative chain for native endpoint GUIs** (matches `pim-app-config-i18n::resolve_locale` / agent `i18n.rs` today):

1. **Explicit in-process preference** — `UI_LOCALE` from AppConfig / agent `settings.json` (and elevators that `boot_from_settings_json`).
2. **OS UI language** — Win32 / browser / Tauri locale APIs (not `$env:LANG` as AIC config).
3. **`en`**.

**Elevate-specific rules:**

| Source | Role |
| --- | --- |
| Person record `ui_locale` / preferred language on AIC Server | **Not** required at elevate show time. May be **synced later by the agent** into local `UI_LOCALE` when online — additive, never the sole path. |
| Elevate Tauri cookie / URL lang / picker | Must offer **Tier 1** tags (remove `en/de/fr` hard cap). Persisting picker choice must write `UI_LOCALE` (or the existing cookie + settings bridge), not an env var. |
| Offline / agent down | OS → `en`; catalogs from disk/embed only. |

No product environment variables. CLI `--locale` remains an operator override where CLIs already support it.

---

## 5. RTL (`he` / `ar`) — honesty

Tier 1 **does not** include Hebrew or Arabic. Closing Tier 1 does **not** require full RTL.

| Piece | Today | Cost to Live |
| --- | --- | --- |
| `Locale::is_rtl()` / `dir()` | Live in crate | — |
| Client configurator Win32 | `SetProcessDefaultLayout` + `WS_EX_LAYOUTRTL` | Pattern to copy |
| Server / Jump Tauri | `document.dir` from locale | Pattern to copy |
| Elevate Win32 | Catalog apply only — **no** RTL layout | **M** — copy client-configurator helper onto elevate dialog |
| Elevate Tauri | **No** `dir` wiring; picker capped | **S–M** after picker uncapped |

**Plan stance:** Defer full RTL to a **Tier 2 slice after Tier 1 Live**. Document as BLOCKED for `he`/`ar` until then. Do not greenwash Tier 1 as “RTL ready.”

---

## 6. Register — which voice per binary

| Binary class | Register | Authority |
| --- | --- | --- |
| **Elevate (Win32 + Tauri)** | Plain, jargon-free, short sentences; sixth-grade *spirit* (employee under pressure). Prefer “Ask for more access” over “Submit elevation request” where product meaning allows. | Closer to [`training-materials-plain-language-and-images.mdc`](../../.cursor/rules/training-materials-plain-language-and-images.mdc) than to operator formal tone — **even though that rule formally governs training docs**. |
| Agent / server / Jump / DB / WA **configurators** | Formal operator/admin | [`enterprise-localization.mdc`](../../.cursor/rules/enterprise-localization.mdc) |
| Launchers | Short operator labels | `enterprise-localization` |
| CLIs `--help` | Operator/admin technical | `enterprise-localization` |
| WEL / syslog / SIEM | US English (by design) | Out of scope |

### Rule clarification (warranted — not landed in this plan commit)

[`native-operator-gui-i18n.mdc`](../../.cursor/rules/native-operator-gui-i18n.mdc) correctly covers locale resolution and shared chrome, but it frames all native GUIs as **operator** surfaces. Elevate is **end-user**. Recommend a short amendment (implementation slice 0) that:

1. Names elevate helpers as **end-user** native GUIs.
2. Requires plain-language US English source for elevate catalogs (`elevate.*` keys).
3. Keeps configurators on enterprise register.
4. Does **not** lower FIPS / auth / audit floors.

Until that amendment lands, treat this plan section as the binding product decision for sequencing work.

---

## 7. Verification (SPA nav-crawl does not cover native)

Without automation, native packs will rot the same way SPA packs did.

**Minimum harness (Slice 0 / 1 acceptance):**

| Check | How | Pass bar |
| --- | --- | --- |
| Catalog parity | Script: for each Tier 1 tag, every `elevate.*` / chrome key in `en` exists in tag JSON with non-empty `text` | Exit non-zero on miss |
| Runtime string bind | Launch elevate (or dialog unit harness) with `UI_LOCALE=<tag>` via AppConfig fixture / settings file — **not** env vars; assert Win32 control text / Tauri `data-i18n` nodes match catalog | Per-tag |
| Screenshot matrix | One PNG per Tier 1 tag at fixed size; agent or reviewer inspects | Evidence under `docs/dev/evidence/native-i18n-<date>/` |
| Picker / supported list | Tauri: supported list ⊇ Tier 1; Win32: Appearance combo if present | Assert |
| Missing-key | Force unknown key → visible fail / log per product policy — never silent English hide in a non-`en` pack | Align with SPA missing-string honesty |

**Not sufficient:** “Agent MSI built,” “JSON committed,” “German looks fine once.”

Optional later: headless UI automation (FlaUI / WinAppDriver / Tauri WebDriver). Start with catalog parity + screenshot matrix — cheaper and catches the SPA-class rot.

---

## 8. Installer delivery + localization-work queue

| Requirement | Plan action |
| --- | --- |
| [`multilingual-tier-1-installer.mdc`](../../.cursor/rules/multilingual-tier-1-installer.mdc) | Confirm sibling Server/WA Stage-Native harvest is Live; Agent MSI remains the elevate vehicle. Do not invent a second staging script. |
| [`localization-work-queue.mdc`](../../.cursor/rules/localization-work-queue.mdc) | Any **new or rewritten** US English elevate / chrome source strings → `localization_work.py add|record` in `core-assets` in the **same** change set as the English edit. Closing requires reviewed Tier 1 catalogs — agent MT drafts do not close. |
| Sync | `content/i18n-native/` → crate `bundles/` via existing sync; MSI stages from `core-assets`, not from ad-hoc copies. |

---

## 9. Per-binary honesty (Tier 1)

| Surface | Catalogs in repo | Embed | UI cap | MSI native stage | Tier 1 status |
| --- | --- | --- | --- | --- | --- |
| Elevate Win32 | agent `messages` 18 tags | en/de messages | n/a (OS/`UI_LOCALE`) | Agent MSI **Yes** | **Partial** |
| Elevate Tauri | same + `data-i18n` | same | **en/de/fr** hard cap | Agent MSI **Yes** | **Partial** (B dominant) |
| Agent configurators | same | en/de | mixed | Agent MSI **Yes** | **Partial** |
| Server configurators | gui + `server_configurator` 18 | en/de/fr | mostly catalog-driven | Server MSI **confirm sibling Live** | **Partial** → near Live for disk tags after confirm |
| Jump / DB Tauri product UI | gui product JSON 18; **ui.json en+de** | chrome limited | **en+de ui.json** | Jump/DB **Yes** | **Partial** (B on product UI) |
| WA configurator | chrome 18; thin ui.json en+de | en/de | en+de | WA **confirm sibling Live** (chrome) | **Partial** |
| Launchers | local en/de ui.json | en/de | en/de | Not Stage-Native | **Partial** / Tier 1 **Absent** in UI |
| CLIs | sparse; Clap EN | en(+fr notices) | n/a | uneven | **Absent** / **Partial** |

---

## Sequenced slices (smallest useful first)

### Slice 0 — Register note + verification scaffold

| | |
| --- | --- |
| **Goal** | Bind elevate plain-language decision; add catalog-parity script skeleton + evidence folder contract |
| **Touches** | `core-assets/.cursor/rules/native-operator-gui-i18n.mdc` (amendment) + mirror workspace rule; `core-assets/scripts/…` parity checker; short note in this plan’s status table |
| **Does not** | Change product strings yet |
| **Acceptance** | Rule merged; `python`/`pwsh` parity check runs on `elevate.*` keys for Tier 1 and fails on a deliberate missing key |

### Slice 1 — Elevate Tier 1 delivery (priority)

| | |
| --- | --- |
| **Goal** | Elevate Win32 + Tauri: all Tier 1 tags selectable and rendered from catalogs offline |
| **Touches** | `pim-offline-client-elevate-tauri/src/i18n.js`, `locale-browser.js` (remove supported cap → Tier 1 or `PACK_TAGS`); elevate Win32 only if picker/settings path gaps; optional Tier 1 `include_str!` expand in `offline_client` messages; plain-language pass on `content/i18n-native/apps/pim-offline-agent/*/messages.json` `elevate.*` keys; localization-work queue rows for rewritten EN |
| **Does not** | Full RTL; CLI help; server configurator |
| **Acceptance** | Parity script green for Tier 1; screenshots × 7 tags; Tauri picker lists Tier 1; offline (agent settings only, no server) shows non-English when `UI_LOCALE`/`OS` set; Agent MSI still stages packs (smoke list `locales\zh-TW\messages.json`) |

### Slice 1b — Elevate RTL (deferred; Tier 2)

Copy client-configurator Win32 RTL helpers; set `document.dir` in elevate-tauri. Acceptance: `he`/`ar` layout mirrored. **Not** on Tier 1 critical path.

### Slice 2 — Agent configurator Tier 1

Uncap any supported lists; wire remaining English dialog literals through `t()`; same Agent MSI. Acceptance: parity + screenshot for main dialogs × Tier 1 sample (`en`, `de`, `zh-TW`).

### Slice 3 — Server configurator verify + gaps

Confirm sibling packaging Live (disk `server_configurator.json` for Tier 1). Close remaining EN long-help / uncapped pickers. Acceptance: install-tree or staged-dir proof + screenshot; do not re-implement Stage-Native.

### Slice 4 — Jump + DB Mgmt product `ui.json`

Add Tier 1 `ui.json` (or migrate product strings into staged gui JSON and delete dual trees). Remove en/de-only assumptions. Acceptance: Tauri UI shows Tier 1 without English chrome holes.

### Slice 5 — WA configurator

After sibling chrome staging confirmed: Tier 1 product UI strings (chrome-only is not enough for operator sentences in local `ui.json`). Acceptance: parity + screenshot.

### Slice 6 — Launchers

Expand `locales/<tier1>/ui.json` or move to `pim-app-config-i18n` chrome keys; sync into installers if needed. Acceptance: launcher UI × Tier 1.

### Slice 7 — CLIs

Clap `about`/help from catalogs at runtime where feasible; document residual compile-time EN honestly as Partial if Clap cannot fully localize. Acceptance: `--help` sample per Tier 1 or documented BLOCKED with reason.

---

## Effort estimate (Tier 1 Live across support programs)

| Band | Scope | Calendar (single focused track) |
| --- | --- | --- |
| **S** | Slice 0 | ~0.5–1 day |
| **M** | Slice 1 elevate | ~2–4 days (includes plain-language EN rewrite + 6 translations + harness + evidence) |
| **M** | Slice 2 agent configurator | ~2–3 days |
| **L** | Slice 3 server configurator residual | ~3–5 days (catalog already large) |
| **M×2** | Slice 4 Jump + DB | ~2–3 days each |
| **M** | Slice 5 WA | ~1–2 days after packaging confirm |
| **S** | Slice 6 launchers | ~1 day |
| **L** | Slice 7 CLIs | ~3–5 days (Clap constraints) |
| **Total Tier 1** | Slices 0–6 (CLI optional) | **~3–5 engineer-weeks** wall time if serialized; less with parallel Jump/DB after elevate pattern exists |
| **RTL Tier 2** | Slice 1b + other shells | **+1–2 weeks** honest — layout bugs dominate |

This is **not** “almost done.” Catalog presence + Partial delivery ≠ Tier 1 Live.

---

## Return summary (for parent / operator)

| Question | Answer |
| --- | --- |
| Slice order | 0 policy/harness → **1 elevate** → 2 agent cfg → 3 server cfg → 4 Jump/DB → 5 WA → 6 launchers → 7 CLIs; RTL after Tier 1 |
| Embed vs disk | **Both; disk overrides**; keep narrow compiled fallback; Agent MSI must stage Tier 1; optional Tier 1 message embeds for elevate resilience |
| Offline language | `UI_LOCALE` → OS UI language → `en`; server person preferred language is sync-only, never required for elevate |
| Register | Elevate = plain end-user; configurators/CLIs = enterprise-localization; **rule amendment warranted** |
| Verification | Catalog parity script + per-locale screenshots + picker asserts; not SPA nav-crawl |
| Effort | ~3–5 engineer-weeks to Tier 1 Live (ex-CLI); CLI extra; RTL extra |
| Plan path | `core-assets/docs/dev/native-programs-localization-plan.md` |

---

## Origin

2026-08-19 — operator: elevate and other support programs must be fully
localized for local-machine users; plan from measured audit `44da8ac`; three
blockers separated; installer sibling owns packaging deltas already in flight.
