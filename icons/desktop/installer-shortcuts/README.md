# MSI installer shortcut icons

Distinct multi-resolution Windows `.ico` files used by **WiX MSI installers** for
Add/Remove Programs product icons and per-shortcut desktop / Start Menu icons.
Canonical copies live only in this directory; consumer projects receive them via
`scripts/sync-to-projects.ps1` or at MSI build time through
`pim-installers/scripts/Stage-InstallerShortcutIcons.ps1`.

## Regeneration

From the `core-assets` repository root:

```powershell
pwsh ./scripts/generate-installer-shortcut-icons.ps1
```

### Toolchain

| Step | Primary tool | Fallback |
| ---- | ------------ | -------- |
| SVG → PNG rasterization | ImageMagick `magick convert` | Inkscape (`-UseInkscape`) |
| Compositing (accent band, badge, key) | ImageMagick `magick` | *(required)* |
| PNG frames → multi-size `.ico` | ImageMagick `magick convert` | *(required)* |

ImageMagick is **required** for ICO assembly. Install on Windows with:

```powershell
winget install --id ImageMagick.ImageMagick -e
```

Inkscape alone can render the base mark from `icons/source/aic-icon.svg`, but
cannot produce valid multi-resolution ICO files without ImageMagick.

Each output ICO embeds at least these sizes: **16, 32, 48, 256** pixels.

## Variants

All variants start from `icons/source/aic-icon.svg` (navy gradient + white
**AIC** wordmark). Differentiation is applied programmatically in
`scripts/generate-installer-shortcut-icons.ps1`.

| File | MSI use | Visual differentiation |
| ---- | ------- | ------------------------ |
| `aic-client-product.ico` | Agent MSI product icon (ARP) | Client palette — teal/cyan bottom accent band |
| `aic-client-admin-win32.ico` | Agent admin configurator (Win32) shortcut | Client palette + **W** badge (Win32) |
| `aic-client-admin-tauri.ico` | Agent admin configurator (Tauri) shortcut | Client palette + **T** badge (Tauri) |
| `aic-client-elevate-win32.ico` | Agent elevation UI (Win32) shortcut | Client palette + gold key motif + **W** |
| `aic-client-elevate-tauri.ico` | Agent elevation UI (Tauri) shortcut | Client palette + gold key motif + **T** |
| `aic-server-product.ico` | Server MSI product icon (ARP) | Server palette — orange bottom accent band |
| `aic-server-admin-win32.ico` | Server admin configurator (Win32) shortcut | Server palette + **W** badge |
| `aic-server-admin-tauri.ico` | Server admin configurator (Tauri) shortcut | Server palette + **T** badge |

**Client palette:** accent `#00aec7` (teal/cyan band).  
**Server palette:** accent `#e86c00` (orange band).

## MSI staging rename map

`pim-installers/scripts/Stage-InstallerShortcutIcons.ps1` copies from here into
per-build staging under `pim-installers/windows/staging/<product>/<version>/assets/`:

| Source (this directory) | Agent staging name | Server staging name |
| ------------------------- | ------------------ | ------------------- |
| `aic-client-product.ico` | `icon.ico` | — |
| `aic-server-product.ico` | — | `icon.ico` |
| `aic-client-admin-win32.ico` | `admin-gui-win32-shortcut.ico` | — |
| `aic-server-admin-win32.ico` | — | `admin-gui-win32-shortcut.ico` |
| `aic-client-admin-tauri.ico` | `admin-gui-tauri-shortcut.ico` | — |
| `aic-server-admin-tauri.ico` | — | `admin-gui-tauri-shortcut.ico` |
| `aic-client-elevate-win32.ico` | `elevate-win32-shortcut.ico` | — |
| `aic-client-elevate-tauri.ico` | `elevate-tauri-shortcut.ico` | — |

Do not edit staged copies by hand; regenerate here and re-run the MSI build.
