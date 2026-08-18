# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**core-assets SHA:** `e9d0bcd` (main)

**Done through Wave B** against current US English key set (`en_total` 536 for `aic-server`):

| Tag | missing | stale | Notes |
| --- | ---: | ---: | --- |
| de | 16 | 0 | Large orphan set vs thinner `en` SPA |
| fr | 0 | 0 | Wave A |
| es | 0 | 0 | Wave A |
| en-GB | 0 | 0 | Coverage complete; quality Partial (long strings often still US English) |
| zh-Hans | 0 | 0 | Wave B |
| zh-TW | 0 | 0 | Wave B; not converted from zh-Hans |

Also on disk: manifest, glossary, Python hash/audit tools, MIT flags (18 tags), developer standard, handbook updates.

**Not started:** Wave C (`ja`, `ko`, `pt-BR`, `it`, `he`) and Wave D (`pl`, `tr`, `nl`, `sv`, `fi`, `ar`) — no `content/locales/<tag>` folders yet.

## History

- `e9d0bcd` — thin EN stubs for Jump / DB Mgmt agents
- `7bd001c` / `417f904` — Wave B en-GB / zh-Hans / zh-TW
- `5f59b0d` — handbook, flags, developer standard
- `0f5d486` — Wave A fr/es
- `fd368bf` — entry format + hash migration
- `b6be41d` — manifest + language_packs.py
