# English source corpus summary

- Total keys: **6640**
- locales-ui: **6346**
- locales (server): **294**
- Contamination flagged (heuristic): **68**
- Heuristic clean: **6572**

## Per-namespace

| Namespace | Keys |
| --- | ---: |
| `locales-ui/pages` | 3470 |
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

## Gate

**English is BLOCKED** per `docs/dev/localization-quality-audit-20260819.md`. Contaminated keys must be recovered before any target-language fan-out.

Machine-readable corpus: `english-source-corpus.json`.
Quarantine list: `en-contamination-quarantine.json`.
