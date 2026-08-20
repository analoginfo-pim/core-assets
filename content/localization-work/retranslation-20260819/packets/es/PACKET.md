# Work packet — es

**Status:** READY (standby) — **do not start** until parent signals ENGLISH_CLEAN_VERIFIED.

**Source:** Clean US English only (content/locales-ui/en, content/locales/en after Slice 1).
Never derive from de, zh-Hans, or any other pack.

## Register and plurals

Neutral international Spanish; formal usted. No country idioms. Correct diacritics (sesión, grabación, aprobación).

**Plurals:** one/other. Preserve accents.

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

- content/locales-ui/es/binder.json
- content/locales-ui/es/catalog.json
- content/locales-ui/es/common.json
- content/locales-ui/es/compliance.json
- content/locales-ui/es/components.json
- content/locales-ui/es/controls.json
- content/locales-ui/es/dashboard.json
- content/locales-ui/es/dialogs.json
- content/locales-ui/es/docs.json
- content/locales-ui/es/help.json
- content/locales-ui/es/login.json
- content/locales-ui/es/nav.json
- content/locales-ui/es/ot.json
- content/locales-ui/es/pages.json
- content/locales-ui/es/reports.json
- content/locales-ui/es/risks.json

### locales (server)

- content/locales/es/binder.json
- content/locales/es/cli.json
- content/locales/es/disclosures.json
- content/locales/es/messaging.json
- content/locales/es/reports.json
- content/locales/es/risks.json
- content/locales/es/training.json

## Context

Per-key context (control type, length notes) is embedded in
english-source-corpus.json → keys[].context. Prefer that over guessing.
Buttons and column headers are high layout-risk for DE/FR expansion.

## Tag-specific acceptance extras

- Full retranslation from clean EN
- No diacritic folding
- Zero DE residue / splice

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
