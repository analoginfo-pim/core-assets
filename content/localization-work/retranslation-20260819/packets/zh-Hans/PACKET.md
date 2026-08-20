# Work packet — zh-Hans

**Status:** READY (standby) — **do not start** until parent signals ENGLISH_CLEAN_VERIFIED.

**Source:** Clean US English only (content/locales-ui/en, content/locales/en after Slice 1).
Never derive from de, zh-Hans, or any other pack.

## Register and plurals

Mainland Simplified; MLPS 2.0-aware vocabulary where relevant. Formal operator tone.

**Plurals:** Chinese typically uses a single form — do not ship English (s) plurals; use one form or explicit classifiers.

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

- content/locales-ui/zh-Hans/binder.json
- content/locales-ui/zh-Hans/catalog.json
- content/locales-ui/zh-Hans/common.json
- content/locales-ui/zh-Hans/compliance.json
- content/locales-ui/zh-Hans/components.json
- content/locales-ui/zh-Hans/controls.json
- content/locales-ui/zh-Hans/dashboard.json
- content/locales-ui/zh-Hans/dialogs.json
- content/locales-ui/zh-Hans/docs.json
- content/locales-ui/zh-Hans/help.json
- content/locales-ui/zh-Hans/login.json
- content/locales-ui/zh-Hans/nav.json
- content/locales-ui/zh-Hans/ot.json
- content/locales-ui/zh-Hans/pages.json
- content/locales-ui/zh-Hans/reports.json
- content/locales-ui/zh-Hans/risks.json

### locales (server)

- content/locales/zh-Hans/binder.json
- content/locales/zh-Hans/cli.json
- content/locales/zh-Hans/disclosures.json
- content/locales/zh-Hans/messaging.json
- content/locales/zh-Hans/reports.json
- content/locales/zh-Hans/risks.json
- content/locales/zh-Hans/training.json

## Context

Per-key context (control type, length notes) is embedded in
english-source-corpus.json → keys[].context. Prefer that over guessing.
Buttons and column headers are high layout-risk for DE/FR expansion.

## Tag-specific acceptance extras

- Full retranslation from clean EN
- No German/English mash in CJK strings
- Glossary: 会话 for session (Hans)

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
