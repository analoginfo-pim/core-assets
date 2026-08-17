# Localization work queue

This folder is the durable to-do list for language-pack work. When product
Help, manuals, or other must-localize strings are added or changed, a work
item is recorded here so translators see new work instead of discovering it
by accident.

There is no separate localization GitHub repository. **`core-assets` is the
localization home.** Catalogs live under `content/locales/`,
`content/locales-ui/`, and `content/i18n-native/`. This queue tracks what
still needs professional localization.

## Files

| File | Role |
| --- | --- |
| `queue.json` | Source of truth. Agents and the recorder write this. |
| `queue.md` | Human list. Regenerated from `queue.json`. Do not hand-edit. |
| `surfaces.json` | English source files the recorder hashes on `record-all`. |

## Record new work

From the `core-assets` repo root (Python 3, no extra packages):

```text
python3 scripts/localization-work/localization_work.py add ^
  --id docs.example-chapter ^
  --title "Example chapter" ^
  --kind help-manual ^
  --source-repo pim-offline-server ^
  --source-path ui/src/pages/docs/example.ts ^
  --source-file ../pim-offline-server/ui/src/pages/docs/example.ts ^
  --product-route /docs/auditor#chapter-example ^
  --required-tags de fr es en-GB zh-Hans ^
  --notes "Why this is new work."
```

On Unix, use `\` instead of `^`.

When an already-queued English source changes:

```text
python3 scripts/localization-work/localization_work.py record ^
  --id docs.example-chapter ^
  --source-file ../pim-offline-server/ui/src/pages/docs/example.ts
```

If the SHA-256 changed, the item is **reopened**. `record-all` walks every
row in `surfaces.json`.

## Close an item

Set `"status": "closed"` in `queue.json` only when every `required_tags`
entry has a reviewed catalog. Agent draft strings do **not** close work.
Missing Tier 1 tags (`en-GB`, `zh-Hans` today) keep the item open.

Then run `render` so `queue.md` matches.

## Rules

- Do not invent a product environment variable for this queue.
- Do not add a git hook. Recording is an agent duty in the same change set.
- Queue notes stay in product language. No lab hostnames, lab accounts, or
  agent thinking.
- Closing is not a Met or certified claim.

See `docs/enterprise-localization.md` and the workspace rule
`localization-work-queue.mdc`.
