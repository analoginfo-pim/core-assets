# Retranslation prep pack (2026-08-19)

Standing kit for Tier 1 retranslation **after** clean US English is verified.

**Locale program:** `en` is the source. Packets under
`en-GB` / `de` / `fr` / `es` / `zh-Hans` / `zh-TW` are **equal-weight
derived packs**, not a Traditional Chinese–only program.

| File / dir | Role |
| --- | --- |
| `english-source-corpus.json` | Full EN key inventory + context + contamination flags |
| `english-source-corpus-SUMMARY.md` | Human counts |
| `en-contamination-quarantine.json` | Keys to recover in Slice 1 |
| `do-not-translate.md` | Literals that must stay Latin |
| `glossary-tier1-PROVISIONAL.md` | From audit §4 — lock before Live claims |
| `COORDINATION.md` | Ownership, commits, fan-out signal |
| `proposed-queue-items.md` | Queue IDs to apply when `queue.json` is free |
| `packets/en-recovery/` | **Slice 1 gate** |
| `packets/{en-GB,de,fr,es,zh-Hans,zh-TW}/` | Standby per-tag packets |
| `_build_prep_artifacts.py` | Regenerates corpus (read-only on locales) |

Plan narrative: `docs/dev/retranslation-plan-20260819.md`.
Audit: `docs/dev/localization-quality-audit-20260819.md`.
