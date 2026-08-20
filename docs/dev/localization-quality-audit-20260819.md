# Localization quality audit (content, 2026-08-19)

**Scope:** Content quality of Tier 1 packs — whether a native speaker would
find the product credible. Structural correctness (key parity, sidecar
manifest, normalization, served-pack verification) is out of scope; a sibling
agent owns that pipeline.

**Honesty bar:** Live / Partial / Absent / BLOCKED. Key presence ≠ quality.
Agent drafts do not close localization work (`localization-work-queue.mdc`).
This audit is **not** a Met / certified / “product is localized” claim
(`compliance-claims-honesty.mdc`).

**Surfaces measured (read-only):**

| Tree | Role | Approx EN leaf strings |
| --- | --- | --- |
| `content/locales-ui/{tag}/` | Admin SPA catalogs | ~6,206 keys compared across Tier 1 |
| `content/locales/{tag}/` | Server catalogs (binder, training, messaging, …) | ~294 keys |

**Tags:** `en`, `en-GB`, `de`, `fr`, `es`, `zh-Hans`, `zh-TW`.

**Git baseline (do not touch sibling dirty trees):**

| Repo | Branch / tip | Note |
| --- | --- | --- |
| `pim-offline-server` | `local/reporting-integration` @ `5a4f2dbbc` | Large dirty tree (sibling) |
| `core-assets` | `main` @ `24123df` | Dirty: locales-ui packs + `localization-work/*` + many `_agent_*` scripts |

**Method:** Automated scan of all leaf `text` values (TEMP-only script; no pack
edits). Heuristics: German strong markers, ASCII-folded umlauts, English
function-word splice into non-English text, byte-identical-to-`en` share,
en-GB spelling vs identity, zh-Hans/zh-TW identity, `{{…}}` / `__PH0__`
integrity, short-chrome length ratios, core-term variant buckets.

---

## 1. Executive verdict

**The admin SPA packs are not “good.” Several are machine-derived sludge.**
The root cause stated by the operator is confirmed in the data: strings were
often **derived from German (or through German) rather than translated from
clean US English**. Evidence:

1. **`en` itself contains German** — chips and help bullets such as
   `gesund` / `ungesund` / `Verweigert`, and full sentences like
   *“Connect autorisiert a aufgezeichnete Session … and oeffnet dann the
   Desktop-Viewer.”*
2. **The same keys in `de` are clean German** (proper umlauts, Sie-register,
   coherent grammar) — e.g. *“Verbinden autorisiert eine aufgezeichnete
   Sitzung … und öffnet dann den Desktop-Viewer.”*
3. **`zh-TW` (and other packs) inherit the broken English/German mash** —
   *“將 autorisiert 連接到 aufgezeichnete 會話 (Sie bestaetigen the
   Aufzeichnung) …”*

Server `content/locales/*` catalogs are in **much better shape** (low
identical-gap and near-zero German contamination in this scan). Do not let
that greenwash the SPA.

**Customer-facing claim today:** do **not** tell customers the admin product
is professionally localized. Say catalogs exist; quality is **Partial** at
best for `de`, **BLOCKED** for credible Tier 1 on `en` source purity,
`en-GB`, `fr`, `es`, and both Chinese packs until retranslation and glossary
lock.

---

## 2. Per-tag scorecard (content quality)

Statuses describe **credibility of wording**, not key coverage.

| Tag | Status | One-line judgment |
| --- | --- | --- |
| **en** | **BLOCKED** | Source catalog is contaminated: German chips, ASCII-folded DE, spliced “the/and/or” inside DE syntax. Cannot be the authority for translation until purged. |
| **en-GB** | **BLOCKED** | ~91% byte-identical to `en` (~5,663 / 6,206). Only ~126 spelling-only diffs. Not a UK pack — a US clone with light overlays. Also inherits DE residue (~46 strong markers). |
| **de** | **Partial** | Best of the set for operator chrome: Sie-register held in sampled Connect copy; terminology mostly coherent (`Sitzung`, `Zugangsdaten`, `Aufzeichnung`). Still: loanword drift (`Elevation` vs `Erhöhung`, `Enclave` vs `Enklave`, `Jump` vs `Sprunghost`), some English leftovers (~9% gap), sparse plurals. Needs glossary lock + human review — **not** Live. |
| **fr** | **BLOCKED** | ~25% genuine untranslated gap; ~66 DE contamination hits; ~202 splice artifacts; ~79 ASCII-fold hits; ~1,291 strings ≥30% longer than EN. Machine / cross-pack residue, not ANSSI-grade French. |
| **es** | **BLOCKED** | Same pattern as `fr` (~25% gap, ~70 DE hits, ~220 splices, ~108 ASCII folds). Diacritic folding (`sesion`, `grabacion`, `aprobacion`) is visible. Not neutral international Spanish suitable for audits. |
| **zh-Hans** | **BLOCKED** | Nav chrome often looks plausible, but pack still carries DE residue (~46), ASCII-fold (~68), EN splice into CJK (~63), and ~11% untranslated gap. No glossary lock; MLPS-facing credibility fails on contaminated bullets. |
| **zh-TW** | **BLOCKED** | Worst showcase of the pipeline: DE+EN+CJK mash on high-visibility My Workstations bullets; ~453 keys identical to `zh-Hans` (conversion / copy risk); mixes `會話` and `工作階段` for “session.” Must be retranslated from clean EN for Taiwan — never via Hans conversion of sludge. |

Server catalogs (`content/locales`): treat as **Partial** across Tier 1 for
this audit (much cleaner metrics; still need glossary + human sample review
before Live).

---

## 3. Quantified findings by dimension

Unless noted, numbers are **locales-ui**, keys compared ≈ 6,206.

### 3.1 Cross-language contamination

| Tag | Strong DE-marker hits | Share | Notes |
| --- | --- | --- | --- |
| en | **34** (dedicated residue scan) | — | Source poison |
| en-GB | 46 | 0.7% | Inherited from `en` / shared sludge keys |
| de | n/a (expected) | — | — |
| fr | 66 | 1.1% | e.g. `Domaene` still in `catalog.json` |
| es | 70 | 1.1% | same `Domaene` class |
| zh-Hans | 46 | 0.7% | |
| zh-TW | 35 | 0.6% | Low count, **high severity** (visible mash) |

**Representative examples (not exhaustive):**

| Pack | Example |
| --- | --- |
| `en` pages | `"gesund"` / `"ungesund"`; `"Verweigert"`; `"Zugangssperre, Benotung and regelbasierte Einschreibung sind not gebaut."` |
| `en` pages | `"Connect autorisiert a aufgezeichnete Session (Sie bestaetigen the Aufzeichnung) and oeffnet dann the Desktop-Viewer."` |
| `en` docs | `"Lassen Sie the Browser-Tab geoeffnet, waehrend the Session startet. Close Sie ihn erst nach the Trennen."` |
| `zh-TW` pages | `"將 autorisiert 連接到 aufgezeichnete 會話 (Sie bestaetigen the Aufzeichnung) 並連接到 Desktop-Viewer。"` |
| `zh-TW` pages | `"Session oeffnen erscheint nur, wenn Connect abgeschlossen wurde, the Viewer aber not navigiert hat."` |
| `fr`/`es` catalog | `"Domaene"` (German ASCII-fold, not Domäne / domaine / dominio) |

**Contrast (same key, `de` is fine):**
`Verbinden autorisiert eine aufgezeichnete Sitzung (Sie bestätigen die
Aufzeichnung) und öffnet dann den Desktop-Viewer.`

### 3.2 Untranslated leakage (byte-identical to `en`)

Heuristic splits “likely legitimate” (protocol names, control ids, short
acronyms) vs “gap.”

| Tag | Identical to en | Of which scored as gap | Gap share |
| --- | --- | --- | --- |
| en-GB | 5,663 | 5,072 | **81.7%** |
| fr | 1,943 | 1,557 | **25.1%** |
| es | 1,926 | 1,538 | **24.8%** |
| zh-Hans | 833 | 695 | **11.2%** |
| de | 718 | 561 | **9.0%** |
| zh-TW | 549 | 434 | **7.0%** |

Server `locales`: gap share ≈ **0.7–1.7%** — not the primary fire.

Legitimate identical cases (keep allowlisted in gates): `SSH`, `RDP`, `VNC`,
`AIC`, `PAM`, `CMMC`, `AC-2`, SPDX-style ids, pure digits, product trademarks
the glossary marks “do not translate.”

### 3.3 Machine-translation artifacts

| Signal | en-GB | de | fr | es | zh-Hans | zh-TW |
| --- | --- | --- | --- | --- | --- | --- |
| ASCII-fold likely (`oeffnet`, `bestaetigen`, `Domaene`, …) | 19 | 8 | 79 | 108 | 68 | 39 |
| EN function-word splice heuristics | 0 | 23 | 202 | 220 | 63 | 44 |

Patterns confirmed by inspection:

- **ASCII-folded German** in non-DE packs and in `en`: `oeffnet`,
  `bestaetigen`, `geoeffnete`, `standardmaessig`, `Domaene`.
- **Spliced English** inside DE/CJK: `the`, `and`, `not`, `or`, `Close Sie`,
  `Connect autorisiert a …`.
- **Calques / mixed syntax** in zh-TW bullets (German verb + Chinese
  connective + English noun).
- **Spanish diacritic loss:** `sesion` vs `sesión`, `grabacion` vs
  `grabación` (terminology bucket scan).

### 3.4 Register consistency

| Tag | Expected | Observed |
| --- | --- | --- |
| de | formal **Sie** | Sampled Connect / docs paths use Sie; informal **du** heuristic ≈ 0 on SPA scan. **Partial** pass on register, fail on source EN. |
| fr | formal **vous** | Not deeply sampled sentence-by-sentence; contamination/splice dominate quality. Treat register as **unproven**. |
| es | formal **usted** | ~1 weak tú hit; same caveat as fr. |
| zh-TW | Taiwan Traditional | **Fail:** Hans-identical keys (~453); SC→TW conversion of bad source; term mix `會話`/`工作階段`. |
| en-GB | full UK pack | **Fail:** spelling overlay only (~126 spelling-only vs 5,663 identical). |

### 3.5 Terminology consistency (highest evaluator signal)

Core English terms mined against locales-ui; variant buckets (pattern hits):

| EN term | de (dominant / conflicts) | fr | es | zh notes |
| --- | --- | --- | --- | --- |
| session | **Sitzung(en)** strong | session(s) | sesión + **sesion** (fold) + leftover “session” | zh-TW: **會話** vs **工作階段** in same nav/common |
| credential | **Zugangsdaten** + Anmeldedaten | Identifiants / mot de passe / Credential leftovers | credencial(es) | 凭证 / 憑證 |
| vault | **Tresor** + Vault | coffre-fort + Vault | bóveda + Vault | 保险库 / 保險庫 |
| rotation | Rotation + Passwortrotation + many unmatched | rotation | rotación + fold | 轮换 |
| elevation | **Elevation** (loan) + Erhöhung | élévation + Elevation | elevación + Elevation | 提升 |
| endpoint | Endpunkt(e) | point(s) de terminaison + endpoint | punto final + endpoint | 端点 |
| enclave | **Enclave** vs **Enklave** split | enclave | enclave | needs glossary |
| attestation | Bestätigung vs Attestierung | attestation | sparse / weak | 证明 / 證明 — lock one |
| recording | Aufzeichnung vs Recording leftovers | enregistrement + recording | grabación vs registro vs fold | 录制 / 錄製; zh-TW also 錄製作業 |
| approval | Genehmigung(en) vs Freigabe | approbation | aprobación + fold | 审批 |
| jump host | **Jump** / Jump-Host dominate; Sprunghost rare | Jump left EN | Jump / host de salto rare | needs 跳板主机 vs keep Jump |
| workstation | Arbeitsplatz + Workstation leftovers | poste de travail + workstation | estación de trabajo + workstation | 工作站 (both) |

**Evaluator takeaway:** Even where German is “readable,” product vocabulary
is not locked. Romance packs mix translated and English loan forms. Chinese
packs disagree within themselves on “session.”

### 3.6 Locale-correct formatting (plurals, dates, numbers)

| Check | Result |
| --- | --- |
| i18next `_one` / `_other` (and friends) | Essentially **absent** as a system — ~2 plural-suffix keys in entire SPA tree per tag |
| `{{count}}` strings | Widespread **English-shaped** plurals: `"{{count}} session(s)"`, `"{{count}} workstation{{plural}}"` — not Chinese single-form strategy, not Romance plural rules |
| Display timezone | Product rule exists (`DISPLAY_TIMEZONE`); this audit did not re-verify every date format string — treat as **follow-on** once wording is clean |
| Server locales | No plural-suffix keys in scan |

**Verdict:** Pluralization is **Absent** as a designed localization feature.
Shipping `{{count}} … (s)` into Chinese/German is an evaluator tell.

### 3.7 Truncation / layout risk

German/French expansion is real:

| Tag | Strings ≥30% longer than EN |
| --- | --- |
| fr | **1,291** |
| es | **1,016** |
| de | **990** |
| en-GB | 37 |
| zh-* | low (different script width issues) |

Short-chrome examples (dialogs / common), DE vs EN:

| EN | DE | Risk |
| --- | --- | --- |
| Save failed | Speichern fehlgeschlagen | buttons/toasts |
| Not set up | Nicht eingerichtet | chips |
| Could not load issuances | Ausstellungen konnten nicht geladen werden | alerts |
| POA&M | Maßnahmenplan (POA&M) | nav |

Chinese: watch **fixed-width DataGrid columns** and nav labels with mixed
CJK+Latin (`会话 I/O 策略`). No full layout proof in this read-only audit
(would need rendered screenshots per `essential-ui-actions-must-be-visible.mdc`).

### 3.8 Placeholder and markup integrity

| Check | Result |
| --- | --- |
| `__PH0__` / replacement tokens | **0** in Tier 1 locales-ui scan |
| U+FFFD mojibake marker in values | **0** in scan |
| Missing `{{…}}` vs EN | Rare (2–3 keys flagged in de/fr/es/zh-TW) — fix in retranslation passes |

Placeholders are the **least broken** dimension. Do not mistake that for
quality.

---

## 4. Terminology glossary proposal (lock this first)

Propose **one approved rendering per tag**. Conflicts observed in current
packs are noted. Professional linguists may adjust; agents must not invent
a second synonym after lock.

| EN (source) | de | fr | es | zh-Hans | zh-TW | en-GB | Do not translate / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| session | Sitzung | session | sesión | 会话 | **工作階段** (prefer Taiwan IT) or lock 會話 — **pick one** | session | Conflict: zh-TW currently mixes both |
| credential / credentials | Zugangsdaten | identifiants | credenciales | 凭据 | 憑證 | credentials | Avoid Anmeldedaten unless login-specific |
| vault | Tresor | coffre-fort | bóveda | 保险库 | 保險庫 | vault | Keep “Vault” only in product name strings if branded |
| rotation | Rotation (Kennwortrotation when password-specific) | rotation | rotación | 轮换 | 輪替 | rotation | |
| elevation | Rechteausweitung *(prefer over bare Elevation)* | élévation de privilèges | elevación de privilegios | 提升 | 提升 | elevation | Conflict: DE/FR/ES still loan “Elevation” |
| endpoint | Endpunkt | point de terminaison | extremo / punto de conexión *(lock one)* | 端点 | 端點 | endpoint | “punto final” is weak for PAM |
| enclave | Enklave | enclave | enclave | 飞地 | 飛地 | enclave | Conflict: DE Enclave vs Enklave |
| attestation | Attestierung | attestation | atestación | 证明 | 證明 | attestation | Avoid soft Bestätigung for workforce attest |
| recording (session) | Aufzeichnung | enregistrement | grabación | 录制 | 錄製 | recording | Not “registro” for session replay |
| approval | Genehmigung | approbation | aprobación | 审批 | 核准 | approval | Conflict: Freigabe vs Genehmigung |
| jump host | Jump-Host *(or Sprunghost — lock one)* | hôte de rebond | host de salto | 跳板主机 | 跳板主機 | jump host | Conflict: bare “Jump” everywhere |
| workstation | Arbeitsplatz | poste de travail | estación de trabajo | 工作站 | 工作站 | workstation | |
| Connect (button) | Verbinden | Connexion / Connecter *(lock)* | Conectar | 连接 | 連線 | Connect | EN button currently polluted |
| Deny / Allow (decision) | Verweigert / Erlaubt | Refusé / Autorisé | Denegado / Permitido | 拒绝 / 允许 | 拒絕 / 允許 | Deny / Allow | EN must not keep German chips |
| healthy / unhealthy | ordnungsgemäß / gestört *(or gesund/ungesund if ops prefers — lock)* | sain / non sain | correcto / incorrecto | 正常 / 异常 | 正常 / 異常 | healthy / unhealthy | EN chips today are German |

**Process:** Land this table as `content/localization-work/glossary-tier1.md`
(or equivalent) **after** the sibling pipeline settles; bind CI drift checks
to it (see §6).

---

## 5. Remediation plan (sequenced, honest effort)

### Phase 0 — Stop the bleeding (days, engineering)

1. **Freeze** any further MT fill that targets contaminated `en` keys.
2. **Quarantine list:** all `en` values matching DE strong markers / splice
   patterns (scan found **34+** clear UI residues; pages/docs bullets are
   the tip).
3. Sibling structural gates continue (parity, manifest) — orthogonal.

### Phase 1 — Repair US English source (1–2 weeks, bilingual DE↔EN reviewer)

1. Rewrite every contaminated `en` string from **intent**, using clean `de`
   only as a *hint*, never as a pivot to reverse-MT.
2. Re-hash `source_sha256` after EN fixes (language-pack standard).
3. Until EN is clean, **do not** claim Tier 1 progress on other tags.

**Effort:** hundreds of keys in `pages.json` / `docs.json` alone; expect
**~3–8 professional reviewer days** plus engineering apply — not an
overnight agent pass.

### Phase 2 — Glossary lock (3–5 days)

1. Human security linguist (or bilingual PAM specialist) confirms §4 table.
2. Publish glossary; add automated **term-drift** check (see §6).

### Phase 3 — Pack strategy by tag

| Tag | Strategy | Effort order of magnitude |
| --- | --- | --- |
| **de** | Targeted repair + glossary normalize; human review of nav, PAM, Connect, binder chrome | **Medium** — salvageable; **not** full rewrite if EN fixed |
| **en-GB** | **Full UK authoring pass** from clean EN (legal/spelling/phrasing), not sed `ize→ise` | **Medium–large** — treat as real locale |
| **fr** | **Full retranslation from clean EN**; discard contaminated rows; professional review | **Large** |
| **es** | Same as fr | **Large** |
| **zh-Hans** | Full retranslation from clean EN; MLPS-aware terminology | **Large** |
| **zh-TW** | **Full retranslation from clean EN for Taiwan**; forbid Hans→Hant conversion of current files | **Large** (highest visible damage) |
| Server `locales` | Sample review + glossary align | **Small–medium** |

**Professional human translation is warranted** for fr, es, zh-Hans, zh-TW,
and en-GB product chrome before any customer “localized” statement.
Agent-drafted strings **do not close** queue items.

### Phase 4 — Plurals and chrome length (parallel after glossary)

1. Replace `(s)` / `{{plural}}` hacks with proper i18next plural keys per
   language rule (zh: single form; de/fr/es: one/other as needed).
2. Layout pass on DE/FR nav and primary buttons at 1024/1280 with visual
   proof.

### Phase 5 — Hold the line (§6)

---

## 6. How quality is held over time

### What automation **can** catch (add after sibling pipeline lands)

| Gate | Catches |
| --- | --- |
| DE strong-marker regex on non-`de` packs + on `en` | Cross-language contamination |
| ASCII-fold lexicon (`oeffnet`, `bestaetigen`, `Domaene`, …) | MT fold artifacts |
| Identical-to-`en` share with allowlist | Untranslated leakage |
| Glossary term map: one EN → allowed set per tag | Terminology drift |
| Require `_one`/`_other` (or documented single form) when EN has `{{count}}` | Plural-form presence |
| Forbid `__PH\d+__`, U+FFFD | Placeholder / mojibake |
| zh-TW ↔ zh-Hans identical-CJK rate ceiling | Hans→Hant lazy copy |
| en-GB identical share ceiling + minimum substantive diff rate | Spelling-overlay fake pack |

### What needs **human** review

- Register (Sie / vous / usted) across long prose
- Security-domain word choice (Attestierung vs Bestätigung, etc.)
- Naturalness and word order
- Legal / compliance chrome tone
- Screenshot layout credibility for long DE/FR strings

### Queue policy

Do not close `localization-work` items on agent MT. Closing requires
reviewed catalogs per required tags.

---

## 7. Proposed localization-work items (not enqueued)

**Not written to `content/localization-work/`** — that directory is dirty and
actively edited by a sibling (`queue.json` / `queue.md` / `surfaces.json`
modified; 42 open items). Enqueueing now would collide. Propose:

| ID | Title |
| --- | --- |
| `quality.en-source-decontamination` | Purge German/MT sludge from US English SPA source |
| `quality.glossary-tier1-lock` | Approve and publish Tier 1 PAM glossary (§4) |
| `quality.en-GB-full-pack` | Real UK pack from clean EN (not spelling overlay) |
| `quality.fr-retranslation` | Full FR retranslation + professional review |
| `quality.es-retranslation` | Full ES retranslation + professional review |
| `quality.zh-Hans-retranslation` | Full zh-Hans from clean EN |
| `quality.zh-TW-retranslation` | Full zh-TW from clean EN (no Hans conversion) |
| `quality.de-glossary-normalize` | DE salvage: glossary + human sample review |
| `quality.plural-forms-spa` | i18next plural forms for `{{count}}` strings |
| `quality.gates-contamination-identical-glossary` | Automated quality gates (§6) |

---

## 8. Three worst quality problems

1. **US English source is poisoned** — German chips and reverse-MT sentences
   in `en` (and thus every pack that copied them).
2. **zh-TW (and Romance) packs show DE+EN mash** — evaluator-visible on My
   Workstations / docs paths; destroys credibility instantly.
3. **No locked terminology + fake en-GB** — multiple renderings per concept
   and a 91% identical “UK” pack signal “machine completeness,” not
   localization.

---

## 9. Effort to reach *genuinely good* localization

| Band | What you get | Calendar (order of magnitude) |
| --- | --- | --- |
| Stop customer embarrassment | Clean `en` + quarantine contaminated bullets in all tags | **2–4 weeks** with focused bilingual help |
| Credible Tier 1 SPA chrome | Glossary + professional FR/ES/zh-Hans/zh-TW + en-GB + DE normalize | **2–4 months** (linguist capacity bound) |
| Live (held) | Gates in §6 + plural forms + layout proof + ongoing human spot audits | **Ongoing**; first “Live” claim only after sample native review sign-off |

**Rough cost signal:** treat Tier 1 SPA (~6k strings × 6 non-EN tags, with
heavy rewrite) as a **five-figure professional localization program**, not
an agent weekend. Server catalogs are a smaller add-on.

---

## 10. Related docs

- `docs/enterprise-localization.md` — register and accuracy rules
- `docs/dev/support-programs-multilingual-audit-20260819.md` — support-program
  *presence* (not SPA content quality)
- `.cursor/rules/localization-work-queue.mdc` — drafts do not close
- `.cursor/rules/compliance-claims-honesty.mdc` — no inflated grades

---

*Audit author: read-only quality pass 2026-08-19. No locale JSON or product
code modified. Scan artifacts lived only under `%TEMP%`.*
