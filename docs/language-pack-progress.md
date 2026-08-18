# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**Product integration (Beavis2):** Wave A–D packs synced and staged; AIC Server
packs API lists all 18 complete tags (`en` required). MSI harvest in
`pim-installers` includes Server / Agent / Recording Features for every tag.
Sync map now copies `content/locales-ui` → `pim-offline-server/locales/ui`.

**core-assets catalog SHAs:** Wave C `9a24427`, Wave D `fa05cb7`, progress
`c6053d8`; later en-GB UK quality on `main` (`7118aad` / `66ec69d`).

Complete selectable tags:

`en`, `de`, `fr`, `es`, `en-GB`, `zh-Hans`, `zh-TW`, `ja`, `ko`, `pt-BR`,
`it`, `he`, `pl`, `tr`, `nl`, `sv`, `fi`, `ar`

## History

- (this push) — sync locales-ui into server; product harvest / Beavis2 stage note
- `66ec69d` / `7118aad` — en-GB UK quality follow-up lexical pass
- `d4fe15f` / `1941fae` — en-GB UK quality rewrite
- `fa05cb7` — Wave D pl/tr/nl/sv/fi/ar
- `9a24427` — Wave C ja/ko/pt-BR/it/he
- `417f904` — Wave B en-GB / zh-Hans / zh-TW
- `0f5d486` — Wave A fr/es
- `fd368bf` — entry format + hash migration
- `b6be41d` — manifest + language_packs.py
