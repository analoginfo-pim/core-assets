# Language pack progress

Partner-readable status for Phil and Robert. Updated after each milestone push to `core-assets`.

## Latest

**core-assets SHA:** `7118aad` — en-GB UK quality

**en-GB quality pass** (real UK register from US English; not an alias of `en`):

| Tag | aic-server missing | stale | identical-to-en (all surfaces) | Notes |
| --- | ---: | ---: | ---: | --- |
| en-GB | 0 | 0 | 494 | **Partial:** ~512 leaves differ with UK register. Remaining identical: mostly short shared chrome (OK/Cancel/Save) and variety-neutral titles; **3 long** kept on purpose (classification templates with `{organization_name}`, copyright). Placeholders and `source_sha256` intact. |

Wave A–D other tags not retouched in this pass.

## History

- (this push) — en-GB UK quality follow-up lexical pass
- `d4fe15f` / `1941fae` — en-GB UK quality rewrite
- `fa05cb7` — Wave D pl/tr/nl/sv/fi/ar
- `9a24427` — Wave C ja/ko/pt-BR/it/he
- `417f904` — Wave B en-GB / zh-Hans / zh-TW
- `0f5d486` — Wave A fr/es
- `fd368bf` — entry format + hash migration
- `b6be41d` — manifest + language_packs.py
