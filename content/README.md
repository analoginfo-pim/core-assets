# Common content packs (spec + multilingual)

This tree is the **common-assets** home for spec packages and language
catalogs. Branding and legal stay under `icons/`, `logos/`, and `legal/`.

**Multilingual support is a tier-1 capability.** Every spec pack and every
language catalog the product ships belongs here **and** in the product
installer. A file that exists only in a product repo has not shipped.

## Layout

| Path | What it is | Installer |
| --- | --- | --- |
| `auditor-playbooks/` | Every Assessment Binder playbook JSON (CMMC, NIST, PCI, GDPR, California, Spec 24 / Spec 2400) | AIC Server MSI → `INSTALLFOLDER\auditor-playbooks\` |
| `locales/{en,de,es,fr}/` | Server catalogs (binder, reports, risks, cli, messaging, disclosures, training) | AIC Server MSI → `INSTALLFOLDER\locales\` |
| `locales-ui/<tag>/` | Admin-SPA locale JSON (inspectable copy; also in the Vite bundle) | AIC Server MSI → `INSTALLFOLDER\locales\ui\` |
| `i18n-native/` | Native GUI / agent / recording catalogs (`pim-app-config-i18n` bundles) | Compiled into each product EXE |
| `localization-work/` | Open localization to-do list (`queue.json` / `queue.md`) | Not installed — translator / agent work queue |

Sync: `scripts/sync-to-projects.ps1` (`content/auditor-playbooks`,
`content/locales`, `content/i18n-native`).

## Languages

| Tag | Status |
| --- | --- |
| `en` | Required — US English source |
| `de` | Required — first additional language (tier 1) |
| `es`, `fr` | Partial — messaging / disclosures / CLI where catalogs exist |

Adding a language is a **data add**: new JSON under `locales/<tag>/` (and
native `bundles/gui/<tag>/`), register in `i18n_content.rs` /
`pim-app-config-i18n`, stage in the MSI. Do not rewrite product code per
language.

## Honesty

Spec 24 / Spec 2400 mapping is from **public documentation** and is **not
guaranteed correct**. It is **not** a licensed standard and is **not
endorsed** by Spec 24 licensors, Airlines for America, or the ATA
e-Business Program. Catalog and playbook text must not quote licensed
specification body text.
