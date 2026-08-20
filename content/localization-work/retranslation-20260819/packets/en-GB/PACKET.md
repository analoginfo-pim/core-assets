# Work packet — en-GB

**Status:** READY (standby) — **do not start** until parent signals ENGLISH_CLEAN_VERIFIED.

**Source:** Clean US English only (content/locales-ui/en, content/locales/en after Slice 1).
Never derive from de, zh-Hans, or any other pack.

## Register and plurals

Full UK English pack — spelling, legal, and idiomatic phrasing. NOT a spelling overlay of US English. Forbidden: aliasing to en; ~91% identical is FAIL.

**Plurals:** i18next one/other as needed; replace English-shaped "{{count}} session(s)" with proper plural keys.

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

- content/locales-ui/en-GB/binder.json
- content/locales-ui/en-GB/catalog.json
- content/locales-ui/en-GB/common.json
- content/locales-ui/en-GB/compliance.json
- content/locales-ui/en-GB/components.json
- content/locales-ui/en-GB/controls.json
- content/locales-ui/en-GB/dashboard.json
- content/locales-ui/en-GB/dialogs.json
- content/locales-ui/en-GB/docs.json
- content/locales-ui/en-GB/help.json
- content/locales-ui/en-GB/login.json
- content/locales-ui/en-GB/nav.json
- content/locales-ui/en-GB/ot.json
- content/locales-ui/en-GB/pages.json
- content/locales-ui/en-GB/reports.json
- content/locales-ui/en-GB/risks.json

### locales (server)

- content/locales/en-GB/binder.json
- content/locales/en-GB/cli.json
- content/locales/en-GB/disclosures.json
- content/locales/en-GB/messaging.json
- content/locales/en-GB/reports.json
- content/locales/en-GB/risks.json
- content/locales/en-GB/training.json

## Context

Per-key context (control type, length notes) is embedded in
english-source-corpus.json → keys[].context. Prefer that over guessing.
Buttons and column headers are high layout-risk for DE/FR expansion.

## Tag-specific acceptance extras

- Substantive UK phrasing rate well above spelling-only diffs
- Identical-to-clean-en share must not remain ~91% after pass
- No inherited German residue from old en

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
