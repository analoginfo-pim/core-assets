# Work packet — de

**Status:** READY (standby) — **do not start** until parent signals ENGLISH_CLEAN_VERIFIED.

**Source:** Clean US English only (content/locales-ui/en, content/locales/en after Slice 1).
Never derive from de, zh-Hans, or any other pack.

## Register and plurals

Formal Sie throughout. Correct compounds (Sitzung, Zugangsdaten, Aufzeichnung). No unjustified English loanwords when glossary has a German form.

**Plurals:** one/other (and few/many if used). No "(s)" hacks.

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

- content/locales-ui/de/binder.json
- content/locales-ui/de/catalog.json
- content/locales-ui/de/common.json
- content/locales-ui/de/compliance.json
- content/locales-ui/de/components.json
- content/locales-ui/de/controls.json
- content/locales-ui/de/dashboard.json
- content/locales-ui/de/dialogs.json
- content/locales-ui/de/docs.json
- content/locales-ui/de/help.json
- content/locales-ui/de/login.json
- content/locales-ui/de/nav.json
- content/locales-ui/de/ot.json
- content/locales-ui/de/pages.json
- content/locales-ui/de/reports.json
- content/locales-ui/de/risks.json

### locales (server)

- content/locales/de/binder.json
- content/locales/de/cli.json
- content/locales/de/disclosures.json
- content/locales/de/messaging.json
- content/locales/de/reports.json
- content/locales/de/risks.json
- content/locales/de/training.json

## Context

Per-key context (control type, length notes) is embedded in
english-source-corpus.json → keys[].context. Prefer that over guessing.
Buttons and column headers are high layout-risk for DE/FR expansion.

## Tag-specific acceptance extras

- Strategy is salvage + glossary normalize after clean EN — not full rewrite of already-good Sie chrome
- Glossary terms locked (Sitzung, Enklave, Rechteausweitung, …)
- English leftover gap targeted down from ~9%

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
