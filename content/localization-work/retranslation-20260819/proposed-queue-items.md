# Proposed localization-work queue items (retranslation 2026-08-19)

Per-tag ids (`quality.zh-TW-retranslation`, `quality.fr-retranslation`, …)
are **equal-weight derived packs from `en`**, not a Traditional Chinese
program.

**Do not close these on agent drafts.** Closing requires reviewed catalogs
per `localization-work-queue.mdc`.

`queue.json` was dirty under a sibling at prep time — **apply these when
safe** (do not collide with in-flight queue edits).

| ID | Title | Notes |
| --- | --- | --- |
| `quality.en-source-decontamination` | Purge German/MT sludge; reconstruct clean US English SPA source | **GATE** — Slice 1 |
| `quality.glossary-tier1-lock` | Approve and publish Tier 1 PAM glossary | After / with Slice 1 |
| `quality.en-GB-full-pack` | Real UK pack from clean EN (not spelling overlay) | After ENGLISH_CLEAN_VERIFIED |
| `quality.fr-retranslation` | Full FR retranslation + professional review | After gate |
| `quality.es-retranslation` | Full ES retranslation + professional review | After gate |
| `quality.zh-Hans-retranslation` | Full zh-Hans from clean EN | After gate |
| `quality.zh-TW-retranslation` | Full zh-TW from clean EN (no Hans conversion) | After gate |
| `quality.de-glossary-normalize` | DE salvage: glossary + human sample review | After gate |
| `quality.plural-forms-spa` | i18next plural forms for `{{count}}` strings | Parallel after glossary |
| `quality.gates-contamination-identical-glossary` | Automated quality gates (audit §6) | Hold the line |

Source path for enqueue tooling: point at
`docs/dev/retranslation-plan-20260819.md` and this folder.
