# Auditor text playbooks (packaged defaults)

Packaged source of truth for Assessment Binder **default section responses**.
English JSON in this folder is the outline. German (and later languages) ship
as locale catalogs under `locales/<tag>/binder.json` and as system playbook
rows with `locale = de`. Firms clone Generic (or import a firm JSON) and
customize verbiage without a product rebuild.

**Multilingual support is a tier-1 capability.** Every spec playbook in this
folder, and every locale catalog the product ships, must be in
`core-assets/content/` and in the AIC Server MSI. Omitting a spec pack or a
language from the installer is a defect.

## Install layout

| Location | Role |
| --- | --- |
| Common assets: `core-assets/content/auditor-playbooks/` | Canonical pack (syncs here) |
| Repo: `pim-offline-server/assets/auditor-playbooks/*.json` | Build / MSI source (synced copy) |
| Locales: `core-assets/content/locales/{en,de,es,fr}/` | Multilingual catalogs (tier 1) |
| Install: `%ProgramFiles%\AIC\PimServer\auditor-playbooks\` | Read-only product seed (MSI) |
| Install: `%ProgramFiles%\AIC\PimServer\locales\` | On-disk language packs (MSI) |
| Lab deploy copies the same trees next to the server exe | Dev parity with MSI |

On first boot / `ensure_schema` / lab seed, the server **imports** each file
into the playbook store when the slug is missing. System playbooks that operators
have not customized are refreshed only when `package_version` increases.
Operator clones and edited playbooks are **never** wiped on boot.

Current package series: **`package_version` = 8** (structured rich HTML section narratives — headings, short paragraphs, and lists — plus deep binder-instance wall refresh on ensure / admin API).

## Profile mapping (consume these in product)

| File slug | Binder `target_standard` | `target_level` | Catalog | Notes |
| --- | --- | --- | --- | --- |
| `generic` | `cmmc` | `2` | full | Legacy firm-neutral alias of CMMC L2 |
| `generic-cmmc-l1` | `cmmc` | `1` | full | FCI / 800-171 basic sections only |
| `generic-cmmc-l2` | `cmmc` | `2` | full | Preferred explicit CMMC L2 pack |
| `generic-cmmc-l3` | `cmmc` | `3` | full | Includes `enhanced_800_172` complete |
| `generic-nist-800-171-l1` | `nist_800_171` | `1` | full | Same L1 outline keys as CMMC L1 |
| `generic-nist-800-171-l2` | `nist_800_171` | `2` | full | Same L2 outline keys as CMMC L2 |
| `generic-nist-800-171-l3` | `nist_800_171` | `3` | full | No enhanced section (`includes_800_172=false`) |
| `generic-nist-800-172-l2` | `nist_800_172` | `2` | full | Includes `enhanced_800_172` |
| `generic-nist-800-172-l3` | `nist_800_172` | `3` | full | Includes `enhanced_800_172` |
| `generic-nist-800-53-moderate` | `nist_800_53` | `moderate` | full | Outline filter ≈ L2 (no enhanced) |
| `generic-nist-800-53-high` | `nist_800_53` | `high` | full | Outline filter ≈ L3 (+ enhanced) |
| `sample-audit-llp-cmmc-l2` | `cmmc` | `2` | full | Lab sample firm clone (`is_system=false`) |
| `scaffold-pci` | `pci` | _(empty)_ | **scaffold** | No binder section catalog yet |
| `scaffold-gdpr` | `gdpr` | _(empty)_ | **scaffold** | No binder section catalog yet |
| `scaffold-california` | `california` | _(empty)_ | **scaffold** | CCPA/CPRA — no binder catalog yet |
| `scaffold-spec-24` | `ata_spec_2400` | _(empty)_ | **scaffold** | Spec 24 / ATA Spec 2400 public-documentation alignment — **not a licensed standard**; mapping not guaranteed; not endorsed by licensors |
| `cmmc-agent-seed` | `cmmc` | `1` | **scaffold** | Existing Agent seed (always connected), elevation on the workstation, LibreOffice / Thunderbird / AIC Server desktop recipe. Points at CM-2, AC-6, CM-6, IA-5 short titles. Not Met. |

Section keys match `default_section_outline()` in `src/auditor_binder/defaults.rs`.
Level-specific packs include only keys the binder profile includes for that level
(see `BinderProfile::section_included` / `includes_800_172`).

## File format (`aic-auditor-playbook/v1`)

```json
{
  "format": "aic-auditor-playbook/v1",
  "package_version": 2,
  "slug": "generic-cmmc-l2",
  "title": "Generic (CMMC Level 2 / 171)",
  "description": "…",
  "company_name": "",
  "target_standard": "cmmc",
  "target_level": "2",
  "catalog_coverage": "full",
  "is_system": true,
  "locale": "en-US",
  "sections": [
    {
      "section_key": "architecture",
      "title": "Architecture & operating model",
      "field_kind": "section_narrative",
      "completeness": "complete",
      "ordinal": 1,
      "response_text": "Prepared by {auditor_name} ({company}) on {date}. …"
    }
  ]
}
```

### Fields

| Field | Notes |
| --- | --- |
| `format` | Must be `aic-auditor-playbook/v1` |
| `package_version` | Monotonic int; seed refreshes system playbooks when this increases |
| `slug` | Stable id (`generic-cmmc-l2`, `scaffold-pci`, …) |
| `target_standard` | `cmmc` \| `nist_800_171` \| `nist_800_172` \| `nist_800_53` \| `pci` \| `gdpr` \| `california` \| `ata_spec_2400` |
| `catalog_coverage` | `full` or `scaffold` (honest incomplete catalogs) |
| `locale` | Primary tag stored on the row (`en`, `de`, …). Uniqueness is `(slug, locale)`. English JSON packs stay the outline source; German system variants are seeded from `locales/de/binder.json` (titles + section HTML) without duplicating these files. |
| `sections[].section_key` | Must match binder outline keys |
| `sections[].response_text` | Plain text; tokens `{auditor_name}`, `{company}`, `{date}`, `{org_legal_name}`, `{system_enclave_name}`, `{assessment_date}` |

Scaffold files may carry a single `cover` stub with `completeness: operator_must_complete` —
the UI shows an honest “catalog incomplete” banner. **Do not claim PCI / GDPR /
California practice coverage until binder outline keys exist for those standards.**

## Operator workflow

1. **Clone** Generic (or `generic-cmmc-l2`) in the admin UI → firm playbook, or copy a JSON and edit offline.
2. **Export** from UI (`GET …/playbooks/{id}/export`) for offline editing.
3. **Reimport** via UI Import JSON or `POST …/playbooks/import` (refuses to overwrite system slugs — change `slug` first, or edit section texts in UI).
4. **Apply** to a binder (empty-only or overwrite; multi-select sections; fill-ins).

## Regenerating packs

Maintainer script (not shipped by MSI): `_gen_playbooks.py`. After editing
narratives or outline keys, re-run and bump `package_version` so lab/MSI hosts
refresh untouched system playbooks.

## Language packs

English packaged JSON in this folder remains the outline and English narrative
source. German (first additional language) is **catalog-driven**: on seed, the
server upserts a system playbook per English slug with `locale = de`, using
`locales/de/binder.json` for titles, descriptions, and section HTML.

To add another language:

1. Add `locales/<tag>/binder.json` (and `reports.json` / `risks.json` / `training.json`).
2. Register the file in `src/i18n_content.rs`.
3. Extend `Locale` in `pim-app-config-i18n` if the tag is new.
4. Optional: a parallel playbook JSON with `"locale": "<tag>"` still imports
   as `(slug, locale)` and will not overwrite the English row.

The playbook list API filters by `Accept-Language`: matching-locale rows plus
English rows whose slug has no localized twin.

## Honesty

Playbook text is OSA-side packaging only. It must not invent scan results or
assert Met / `resolved_verified`. Cite Current State Compliance evidence in the
binder; C3PAO assessor blocks stay blank in OSA tooling.
