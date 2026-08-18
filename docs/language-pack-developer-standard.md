# Language pack developer standard

**Audience:** engineers adding or changing operator-visible strings in AIC
products. **Canonical home:** `core-assets/docs/language-pack-developer-standard.md`.

Partner quality and register rules remain in
[`enterprise-localization.md`](enterprise-localization.md). This document is the
**how-to** for unique IDs, product tags, hashes, and Win32 / Tauri / CLI packs.

---

## 1. Unique string IDs

Every phrase has one stable **string ID** (the JSON key path). That ID is
**identical** in every language folder for that product.

| Field | Role |
| --- | --- |
| **ID (key)** | Identity of the phrase. Same path in every pack. Never recycle for a new meaning. |
| **`text`** | Words in that language. |
| **`source_sha256`** | SHA-256 (hex lowercase) of UTF-8 **NFC** of the current US English `text`. Same value on a translated row when it is current. Not a second ID. |
| **`note`** (optional) | Translator context (Bitwarden-style). Recommended on ambiguous keys. |

Leaf shape:

```json
{
  "text": "Save",
  "source_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

Full identity in docs: `product` + namespace + key (for example
`aic-server-configurator` / `help` / `certificate_path`).

---

## 2. Product tags (catalog homes)

Catalogs stay in `core-assets`. Do **not** create a second localization git
repository. Manifest: `content/language-packs/manifest.json`.

| Product tag | Catalog home | Ships with |
| --- | --- | --- |
| `aic-server` | `content/locales/<tag>/`, `content/locales-ui/<tag>/` | AIC Server / admin SPA |
| `shared-gui-chrome` | `content/i18n-native/gui/<tag>/chrome.json` | Every Win32/Tauri configurator |
| `aic-server-configurator` | `content/i18n-native/gui/<tag>/server_configurator.json` (+ help/screens as added) | Server configurator |
| `aic-agent` | `content/i18n-native/apps/pim-offline-agent/<tag>/` | Endpoint agent |
| `aic-agent-configurator` | native under `i18n-native` (as added) | Agent configurator |
| `aic-jump-configurator` | native (as added) | Jump configurator |
| `aic-db-mgmt-configurator` | native (as added) | DB management configurator |
| `aic-recording-agent` | `content/i18n-native/apps/pim-offline-recording-agent/<tag>/` | Recording agent |

An installer loads **only** that product’s packs plus `shared-gui-chrome` for
GUI binaries.

---

## 3. Add or change US English

**Add a string**

1. Choose a stable key. Never recycle an ID for a new meaning.
2. Add the entry under the correct `en` tree. Run `hash` (below).
3. Call sites use the key plus a US English **comment**. Do not ship live
   English `defaultValue` on the render path when a pack exists.
4. Other packs stay **missing** until translated. Do not paste English into
   `de` / `fr` / `es` to “fill gaps.”
5. If German readiness already covers the page, add `de` in the same change set.

**Change English wording (same meaning)**

1. Edit `en` `text` only.
2. Run `hash` — `en.source_sha256` changes; other locales become **stale**.
3. Translators update `text` and copy the new `en` hash. Do not “fix” stale
   rows by copying English into another pack.

**Retire a string**

Delete from `en` first; `audit` reports orphans; delete orphans in the same
change set.

---

## 4. Hash and audit (all OS)

Python 3 **stdlib only**. No pip. No product environment variables.

```text
python3 scripts/language-packs/language_packs.py hash --root .
python3 scripts/language-packs/language_packs.py audit --root . --product aic-server
python3 scripts/language-packs/language_packs.py mark-stale --root .
```

On Windows: `py -3` or `python`, or
`.\scripts\language-packs\language_packs.ps1 hash`.
Thin `.sh` / `.ps1` wrappers only call the `.py`.

| Command | Job |
| --- | --- |
| `migrate` | Bare string → `{text, source_sha256}` |
| `hash` | Recompute `en` hashes; fill empty hashes on other tags from `en` |
| `mark-stale` | Exit 1 if any non-`en` hash mismatches `en` |
| `audit` | Missing / stale / orphan / placeholder-broken report |

---

## 5. Win32 / Tauri / CLI

Native screens, dialogs, hover text, and CLI help use the same entry format
under `content/i18n-native/`. Shared buttons (OK, Cancel, Save) live in
`shared-gui-chrome`. Product-specific strings live under that product’s tag.
Hover / tooltip copy is required in every pack — buttons without translated
tooltips are incomplete.

---

## 6. Language picker (flag + name + tag)

When two or more packs are installed, the picker shows, in order:

1. Country flag (MIT [lipis/flag-icons](https://github.com/lipis/flag-icons),
   SVG under `content/language-packs/<tag>/flag.svg`)
2. Display name (for example English (USA), 中文（台灣）)
3. Language tag (`en`, `en-GB`, `zh-TW`, …)

If only one pack is installed (almost always US English), set that language and
**do not show a flag**. Incomplete packs are not selectable in a released build.

`en-GB` is a full Tier 1 pack — not an alias of `en`. `zh-TW` is Taiwan
Traditional — never character-converted from `zh-Hans`. `he` and `ar` use
`dir=rtl` in the manifest.

---

## 7. English always installed — not mixed into the UI

- The US English pack is **always** installed and always in the picker as
  English (USA). Support can ask operators to switch to English for tickets.
- Source identifiers stay US English: string ID, Event ID, API `code`, log
  field names, control ids (`AC-1`).
- Diagnostics may optionally show string ID + current language + US English
  `text` for support. Off by default.
- **Forbidden:** CyberArk-style missing-key English fallback on a selected
  non-English pack. Missing keys are leakage; incomplete packs stay off the
  released picker. Exception fallback to the US English **pack** is only for
  install-tree / parse failure recovery — not for untranslated keys.

---

## 8. Troubleshooting

| Symptom | Check |
| --- | --- |
| `audit` missing counts high | Fill that tag from `en`; do not copy English as translation |
| `stale` after English edit | Re-translate and restamp `source_sha256` from current `en` |
| Orphans | Key in other pack but not `en` — delete or promote into `en` |
| Placeholder broken | Keep `{{tokens}}` / `{placeholders}` identical to English |
| Python missing | Install CPython 3; do not fall back to a Windows-only script |
| Wrong Chinese flag | `zh-Hans` → CN; `zh-TW` → TW — never swap |

---

## 9. Honesty

Filling catalogs is **not** a Met / certified / assessment-ready claim. Official
CMMC / NIST SP 800-53 bodies stay in the authority language. Do not translate
licensed ISO 27001 control text. Do not invent IGA strings.
