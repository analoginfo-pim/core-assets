# AIC Legal Documents

Canonical legal-text assets shipped with AIC products.

## Files

| File | Purpose | Used by |
| ---- | ------- | ------- |
| `EULA_AIC_Commercial.rtf` | End-User License Agreement displayed by every Windows MSI installer (WiX `WixUI_Mondo` license dialog). | `pim-installers/scripts/Build-PimOfflineAgentMsi.ps1`, `pim-installers/scripts/Build-PimOfflineServerMsi.ps1`, and any future Windows installer. |

## Update procedure

1. Edit the document in this repository (`core-assets`).
2. Commit and tag (`legal-vYYYY.MM`) so installers can pin a known version.
3. Run `scripts/sync-to-projects.ps1` (in this repo) to refresh consumer copies.
4. Rebuild any in-flight MSIs so they bundle the new EULA.

## Policy

- **No project may ship a modified copy.** If a product needs a variant
  (e.g. a different language), add it here as a sibling file (`EULA_AIC_Commercial_de-DE.rtf`)
  and reference the variant from the consuming installer's WiX source.
- Old in-tree duplicates (e.g. `pim-offline-client/deployment/windows/License.rtf`,
  `pim-installers/staging/.../assets/EULA.rtf`) are now **build outputs**,
  not source. They are restaged from this directory by the build scripts.
