# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**core-assets SHA:** `d4fe15f` (en-GB UK quality)

**en-GB quality pass** (real UK register, not a US spelling overlay):

| Tag | product aic-server missing | stale | identical-to-en (all surfaces) | Notes |
| --- | ---: | ---: | ---: | --- |
| en-GB | 0 | 0 | 500 | Partial: remaining identical are mostly short shared chrome (OK/Cancel/Save) plus 3 long leaves that must stay (classification templates with `{organization_name}`, copyright). Placeholders intact; `source_sha256` unchanged. |

Wave A–D tags unchanged this run (not retouched).

## History

- `d4fe15f` — en-GB UK quality rewrite across locales / locales-ui / gui / agent / recording
- `fa05cb7` — Wave D pl/tr/nl/sv/fi/ar
- `2087c30` / `9a24427` — Wave C ja/ko/pt-BR/it/he
- `8b25375` — progress after Wave B
- `417f904` — Wave B en-GB / zh-Hans / zh-TW
- `5f59b0d` — handbook, flags, developer standard
- `0f5d486` — Wave A fr/es
- `fd368bf` — entry format + hash migration
- `b6be41d` — manifest + language_packs.py
