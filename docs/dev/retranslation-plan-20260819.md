# Retranslation plan (preparation) — 2026-08-19

**Locale program:** US English (`en`) is the source of truth. Every derived
pack is required at equal weight: `en-GB`, `de`, `fr`, `es`, `zh-Hans`,
`zh-TW`, and any later shipped tag. zh-TW is one derived pack (and one
2026-08-19 banner example), not the product localization use case.

**Slice scope:** Preparation only. No locale JSON rewrites in this change set
except future Slice 1 ownership. No deploy.

**Git baseline**

| Repo | Tip / branch | Note |
| --- | --- | --- |
| `core-assets` | `main` @ `2a4eb94` (audit) | Dirty sibling `_agent_*` / packs — do not stage |
| `pim-offline-server` | `local/reporting-integration` @ `c61713e57` | Large dirty tree — not touched |

**Why packets live under**
`content/localization-work/retranslation-20260819/`:
translators already look under `localization-work/`; a dated subfolder keeps
this prep isolated from the sibling-dirty `queue.json` / `surfaces.json`
while remaining discoverable. The narrative plan stays in `docs/dev/` next
to the audit.

---

## Gate (read this first)

**US English is not clean enough to translate from.**

Per `docs/dev/localization-quality-audit-20260819.md` (SHA `2a4eb94`):

| Tag | Status |
| --- | --- |
| **en** | **BLOCKED** — German / reverse-MT poison |
| **en-GB** | **BLOCKED** — ~91% identical overlay, not a UK pack |
| **de** | **Partial** |
| **fr** / **es** / **zh-Hans** / **zh-TW** | **BLOCKED** |

**Consequence:** Six-way fan-out is **forbidden** until Slice 1 verifies clean
`en`. Packets below are **standing ready** for immediate fan-out after that
signal.

---

## Authoritative English corpus (inventory)

Extracted read-only from:

- `content/locales-ui/en/` (admin SPA)
- `content/locales/en/` (server catalogs)

| Metric | Count |
| --- | ---: |
| **Total keys** | **6,640** |
| locales-ui | 6,346 |
| locales (server) | 294 |
| Heuristic contamination flags | 68 (tip of iceberg; audit cites 34+ strong UI residues and broader sludge) |
| Heuristic “clean” | 6,572 — **not** a green light; heuristics miss subtle calques |

### Per-namespace breakdown

| Namespace | Keys |
| --- | ---: |
| `locales-ui/pages` | 3,470 |
| `locales-ui/help` | 976 |
| `locales-ui/docs` | 532 |
| `locales-ui/components` | 230 |
| `locales-ui/dialogs` | 227 |
| `locales-ui/dashboard` | 176 |
| `locales/binder` | 150 |
| `locales-ui/nav` | 135 |
| `locales-ui/common` | 120 |
| `locales-ui/ot` | 116 |
| `locales-ui/compliance` | 115 |
| `locales-ui/risks` | 83 |
| `locales-ui/catalog` | 55 |
| `locales-ui/login` | 40 |
| `locales-ui/controls` | 37 |
| `locales/reports` | 37 |
| `locales/training` | 34 |
| `locales-ui/binder` | 30 |
| `locales/risks` | 21 |
| `locales/cli` | 18 |
| `locales/messaging` | 18 |
| `locales/disclosures` | 16 |
| `locales-ui/reports` | 4 |

**Artifacts:**

- `content/localization-work/retranslation-20260819/english-source-corpus.json`
- `…/english-source-corpus-SUMMARY.md`
- `…/en-contamination-quarantine.json`

Server catalogs are cleaner (audit: Partial) — do **not** greenwash the SPA
(~6.2k+ keys).

---

## Operator sequencing update (2026-08-19 evening)

**Slice A (P0 credibility) — key completeness — SHIP FIRST.**
Every key in cleaned `en` exists in every pack with a real grammatical
string. Draft OK. Zero missing keys. See
`content/localization-work/retranslation-20260819/sliceA-parity-after.json`.

**Slice B — translation quality** — register, glossary, native review,
real `en-GB` identity pack, and de-conversion of any pack that was
derived via German or Hans conversion (including `zh-TW`). Still
**2–4 weeks / 2–4 months** per audit. Not claimed done by Slice A.

### Slice 1 — Reconstruct clean US English (GATE)

**Owner:** single English-recovery agent (packet:
`packets/en-recovery/PACKET.md`).

**Recovery source mix (priority order) — never reverse-MT from `de`:**

1. **`defaultValue` in TSX** (`pim-offline-server/ui/src/**`) — authored US
   English by construction (strongest).
2. **Git history** before recontamination — e.g. `606641d`, `9cb573d`,
   `22869a9` purged German; later fills (`209270a`, `6b71331`, …)
   reintroduced sludge. Prefer pre-fill clean values.
3. **Author fresh** US English in product register where neither exists.

Clean `de` on the same key = **damage locator only**, not a translation
pivot.

**Exit:** parent posts `ENGLISH_CLEAN_VERIFIED` (quarantine cleared;
DE-marker gates on `en` = 0; spot-check Connect / My Workstations / docs).

### Slice 1b — Glossary lock (short, human)

Promote `glossary-tier1-PROVISIONAL.md` → Locked after linguist review
(audit §4 table).

### Slice 2 — Six parallel per-tag agents (only after Slice 1)

| Agent | Packet |
| --- | --- |
| en-GB | `packets/en-GB/PACKET.md` — genuine UK pack, not overlay |
| de | `packets/de/PACKET.md` — salvage + glossary normalize |
| fr | `packets/fr/PACKET.md` — full retranslation from clean EN |
| es | `packets/es/PACKET.md` — full retranslation from clean EN |
| zh-Hans | `packets/zh-Hans/PACKET.md` — full from clean EN |
| zh-TW | `packets/zh-TW/PACKET.md` — full from clean EN; **forbid Hans conversion**; assert no byte-identical prose vs zh-Hans |

Recommended fan-out: **six parallel agents, one per tag**, after
`ENGLISH_CLEAN_VERIFIED`.

---

## Supporting deliverables (this prep slice)

| Artifact | Path |
| --- | --- |
| Do-not-translate | `…/do-not-translate.md` |
| Glossary (provisional) | `…/glossary-tier1-PROVISIONAL.md` |
| Coordination | `…/COORDINATION.md` |
| Per-tag packets | `…/packets/<tag>/PACKET.md` |
| EN recovery packet | `…/packets/en-recovery/PACKET.md` |
| Proposed queue IDs | `…/proposed-queue-items.md` |

Context for translators is embedded per key in the corpus JSON
(`keys[].context`: control type, length notes). Buttons / column headers
flag DE/FR layout risk.

---

## Effort estimate (verbatim from audit §9)

| Band | What you get | Calendar (order of magnitude) |
| --- | --- | --- |
| Stop customer embarrassment | Clean `en` + quarantine contaminated bullets in all tags | **2–4 weeks** with focused bilingual help |
| Credible Tier 1 SPA chrome | Glossary + professional FR/ES/zh-Hans/zh-TW + en-GB + DE normalize | **2–4 months** (linguist capacity bound) |
| Live (held) | Automated quality gates + plural forms + layout proof + ongoing human spot audits | **Ongoing**; first “Live” claim only after sample native review sign-off |

**Rough cost signal (audit):** treat Tier 1 SPA (~6k strings × 6 non-EN tags,
with heavy rewrite) as a **five-figure professional localization program**,
not an agent weekend.

---

## Honesty — what an agent pass can and cannot deliver

**Can:** remove German contamination from `en`; fill gaps; apply glossary
consistently; produce **reviewable drafts** for six tags; run mechanical
gates (identical-to-en, DE markers, zh-Hans↔zh-TW identity).

**Cannot:** produce native-quality French, Spanish, Chinese, or real UK
legal/idiomatic English; close `localization-work` queue items; claim Live /
professionally localized / Met.

Agent-drafted translations **do not** close localization work
(`localization-work-queue.mdc`). Human review is required before any quality
claim. Do not promise native-quality output from an agent pass.

---

## Proposed localization-work enqueue

`queue.json` is sibling-dirty — this prep **does not mutate** it. Apply
`proposed-queue-items.md` when the queue owner is free (IDs match audit §7
plus English-recovery explicit).

---

## Sibling coordination

- **Format sibling:** sidecar `source_sha256`, NFC/LF — wait for stable
  format before mass rewrites; Slice 1 may restore `text` only if agreed.
- **Audit sibling:** glossary + quality — landed at `2a4eb94`; this plan
  binds to it.

---

*Prep author: 2026-08-19. Locale JSON not modified. Packs not deployed.*
