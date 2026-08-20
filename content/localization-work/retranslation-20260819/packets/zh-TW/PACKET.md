# Work packet — zh-TW

**Status:** READY (standby) — **do not start** until parent signals ENGLISH_CLEAN_VERIFIED.

**Source:** Clean US English only (content/locales-ui/en, content/locales/en after Slice 1).
Never derive from de, zh-Hans, or any other pack.

## Register and plurals

Taiwan Traditional. Translate from US English only. NEVER convert from zh-Hans. Country/flag TW.

**Plurals:** Single-form strategy; no English (s).

## Inputs (read-only)

- Corpus: ../english-source-corpus.json (+ SUMMARY)
- Quarantine (must be empty / waived before start): ../en-contamination-quarantine.json
- Do-not-translate: ../do-not-translate.md
- Glossary: ../glossary-tier1-PROVISIONAL.md (or Locked successor)
- Coordination: ../COORDINATION.md
- Plan: ../../../docs/dev/retranslation-plan-20260819.md
- Audit: ../../../docs/dev/localization-quality-audit-20260819.md

## Target paths (this tag only)

### locales-ui

- content/locales-ui/zh-TW/binder.json
- content/locales-ui/zh-TW/catalog.json
- content/locales-ui/zh-TW/common.json
- content/locales-ui/zh-TW/compliance.json
- content/locales-ui/zh-TW/components.json
- content/locales-ui/zh-TW/controls.json
- content/locales-ui/zh-TW/dashboard.json
- content/locales-ui/zh-TW/dialogs.json
- content/locales-ui/zh-TW/docs.json
- content/locales-ui/zh-TW/help.json
- content/locales-ui/zh-TW/login.json
- content/locales-ui/zh-TW/nav.json
- content/locales-ui/zh-TW/ot.json
- content/locales-ui/zh-TW/pages.json
- content/locales-ui/zh-TW/reports.json
- content/locales-ui/zh-TW/risks.json

### locales (server)

- content/locales/zh-TW/binder.json
- content/locales/zh-TW/cli.json
- content/locales/zh-TW/disclosures.json
- content/locales/zh-TW/messaging.json
- content/locales/zh-TW/reports.json
- content/locales/zh-TW/risks.json
- content/locales/zh-TW/training.json

## Context

Per-key context (control type, length notes) is embedded in
english-source-corpus.json → keys[].context. Prefer that over guessing.
Buttons and column headers are high layout-risk for DE/FR expansion.

## Tag-specific acceptance extras

- ZERO keys byte-identical to zh-Hans for translated prose (allowlist only DNT literals)
- Lock 工作階段 (or glossary pick) — no mix with 會話
- Full retranslation from clean EN

## Acceptance criteria ("done" for this packet)

Agent drafts are **reviewable drafts only**. They do **not** close localization-work queue items. Human review is required before any Live / quality claim.

1. **Full key parity** with clean en for every file listed in Target paths.
2. **Placeholders preserved** exactly ({{…}}).
3. **Glossary terms** used consistently (see glossary-tier1-PROVISIONAL.md until Locked).
4. **Correct plural strategy** for this language (see Register).
5. **No English left** except do-not-translate entries.
6. **No content from any language other than the target** (no DE residue, no cross-tag copy).
7. Source for every string is **clean US English** — never another translation.


## Ownership

You may modify **only** the target paths above. Do not edit en or any other tag.
Commit with explicit path staging. Push only your tag paths.
