# Coordination protocol — Tier 1 retranslation

## Sequence (hard)

1. **Slice 1 — Clean US English** (single owner; gates everything).
2. **Verify English** (contamination gates pass; quarantine empty or
   waived with named keys).
3. **Six parallel per-tag agents** — only after step 2.

Do **not** start target-language rewrites while `en` is BLOCKED.

## File ownership

| Owner | May write | Must not touch |
| --- | --- | --- |
| English-recovery agent | `content/locales-ui/en/**`, `content/locales/en/**`, recovery notes under this folder | Any non-`en` tag; sibling format scripts |
| `en-GB` agent | `content/locales-ui/en-GB/**`, `content/locales/en-GB/**` | `en`, other tags |
| `de` agent | `…/de/**` only | `en`, other tags |
| `fr` agent | `…/fr/**` only | `en`, other tags |
| `es` agent | `…/es/**` only | `en`, other tags |
| `zh-Hans` agent | `…/zh-Hans/**` only | `en`, other tags; **must not read zh-TW as source** |
| `zh-TW` agent | `…/zh-TW/**` only | `en`, other tags; **must not copy from zh-Hans** |
| Format sibling | sidecar manifests, NFC/LF tooling | Translation wording |
| Audit sibling | audit / glossary docs | Pack JSON (unless asked) |

Shared working tree: never `git add -A`. Stage **explicit paths** only
(`shared-working-tree-is-not-yours.mdc`).

## Commit granularity

- **English recovery:** one commit per namespace batch when possible
  (`pages`, `docs`, `help`, …) or per contamination class; subject
  `fix(i18n): restore US English in <ns> (decontamination)`.
- **Per-tag retranslation:** one commit per tag per tree
  (`locales-ui` then `locales`), or smaller per-file if mid-flight with
  siblings. Never mix two tags in one commit.
- **No** force-push; no hook skip.

## Explicit bans

- No agent edits `en` after Slice 1 is verified, except documented EN
  source changes that re-open stale hashes for all tags.
- No agent touches another tag’s files “to keep them in sync.”
- No reverse-MT: `de` → `en`, `zh-Hans` → `zh-TW`, `en` → `en-GB` via
  spelling sed only.
- Agent drafts **do not** close `localization-work` queue items
  (`localization-work-queue.mdc`).

## Ready signal for fan-out

Parent posts: `ENGLISH_CLEAN_VERIFIED` with date, quarantine count = 0
(or explicit waived list), and path to updated corpus. Only then spawn
six tag agents with packet paths below.
