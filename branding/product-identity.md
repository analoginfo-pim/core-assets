# Product identity (rename here)

This is the **single file** for the trademarked toolkit name and company
display names. Logos stay in `core-assets/branding/` (`aic-header.png`,
`aic-about.png`) and sync through `scripts/sync-to-projects.ps1`.

## How to rename the product

1. Edit `product-identity.json` (`product_name` and `product_name_mark`).
2. Run `scripts/sync-to-projects.ps1` (copies the JSON into AIC Server).
3. Copy the JSON onto the running host (no rebuild):
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File pim-offline-server\scripts\Apply-ProductIdentity.ps1 -Apply
   ```
   Deploy also copies:
   - install tree: `<INSTALL>\branding\product-identity.json`
   - overlay (wins): `%ProgramData%\AIC\PimServer\branding\product-identity.json`
4. Hard-refresh the admin SPA. Operator chrome reads the name from
   `GET /api/ui/branding`. No Cargo or Vite rebuild is required for a
   name-only change.

Operator sentences use the `{{productName}}` interpolation token. Do not
paste the trademarked name into locale catalogs or Rust honesty strings.

## Fields

| Key | Use |
| --- | --- |
| `product_name` | ASCII name (logs, filenames, identifiers) |
| `product_name_mark` | Operator chrome, including the trademark sign |
| `company_name` | Legal company name |
| `company_short` | Short mark (AIC) |
| `logo_header` | Default header logo path (customer override is Settings branding) |

Customer `UI_BRAND_NAME` / uploaded logos are a **tenant** overlay. They
do not replace this toolkit identity.

Honesty: the toolkit name is not a Cybersecurity Maturity Model
Certification of the organization and is not a Met stamp.
