# Work packet — fr

**Status:** READY (standby) — **do not start** until parent signals ENGLISH_CLEAN_VERIFIED.

**Source:** Clean US English only (content/locales-ui/en, content/locales/en after Slice 1).
Never derive from de, zh-Hans, or any other pack.

## Register and plurals

Formal vous. ANSSI-appropriate cybersecurity terms. Anglicisms only when industry-required (session, audit).

**Plurals:** one/other. No English (s) patterns.

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

- content/locales-ui/fr/binder.json
- content/locales-ui/fr/catalog.json
- content/locales-ui/fr/common.json
- content/locales-ui/fr/compliance.json
- content/locales-ui/fr/components.json
- content/locales-ui/fr/controls.json
- content/locales-ui/fr/dashboard.json
- content/locales-ui/fr/dialogs.json
- content/locales-ui/fr/docs.json
- content/locales-ui/fr/help.json
- content/locales-ui/fr/login.json
- content/locales-ui/fr/nav.json
- content/locales-ui/fr/ot.json
- content/locales-ui/fr/pages.json
- content/locales-ui/fr/reports.json
- content/locales-ui/fr/risks.json

### locales (server)

- content/locales/fr/binder.json
- content/locales/fr/cli.json
- content/locales/fr/disclosures.json
- content/locales/fr/messaging.json
- content/locales/fr/reports.json
- content/locales/fr/risks.json
- content/locales/fr/training.json

## Context

Per-key context (control type, length notes) is embedded in
english-source-corpus.json → keys[].context. Prefer that over guessing.
Buttons and column headers are high layout-risk for DE/FR expansion.

## Tag-specific acceptance extras

- Full retranslation from clean EN; discard contaminated rows
- Zero German residue / ASCII-fold / EN splice
- Length risk: many strings expand — watch buttons/columns

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
