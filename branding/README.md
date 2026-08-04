# In-app branding art

Bitmap branding artefacts displayed inside running AIC products (about
dialogs, headers, splash images). Anything that ships *inside* a product
window — as opposed to OS-level icons (taskbar, shortcut, ARP entry) — lives
here.

## Files

| File | Used by | Purpose |
| ---- | ------- | ------- |
| `aic-about.png` | `pim-offline-client/assets/aic-about.png` | "About" dialog hero image (Win32 admin GUI / agent). |
| `aic-header.png` | All Tauri configurators / elevation UIs (`pim-offline-client-configurator-tauri`, `pim-offline-client-elevate-tauri`, `pim-offline-server-configurator-tauri`); also `pim-offline-server/ui/public/aic-header.png` for the web login page and app chrome. | Top-of-window / login header banner. |
| `enterprise-atmosphere.svg` | `pim-offline-server/ui/public/enterprise-atmosphere.svg` | Subtle navy / steel-teal geometric wash for admin SPA login and shell canvas (decorative; not a logo). |
| `installer/aic-installer-banner.bmp` | `mix-server/wix/assets/` (WiX `WixUIBannerBmp`) | 493x58 24-bit top banner on interior MSI wizard pages. |
| `installer/aic-installer-dialog.bmp` | `mix-server/wix/assets/` (WiX `WixUIDialogBmp`) | 493x312 24-bit Welcome/Exit dialog background. |

## Installer wizard bitmaps (`installer/`)

WiX (WixUI dialog sets) requires 24-bit BMP artwork at fixed pixel sizes. These
are generated from the AIC brand by
[`../scripts/generate-installer-banners.sh`](../scripts/generate-installer-banners.sh)
(ImageMagick) and distributed via `../scripts/sync-to-projects.ps1`. The banner
keeps its left side blank for the theme's title text; the dialog keeps a navy
branding strip on the left and a white field on the right for the welcome text.
Regenerate with `bash ../scripts/generate-installer-banners.sh`, then re-sync.

## Adding new in-app art

1. Drop the new bitmap (or source SVG plus generated bitmap) here.
2. Add the consumer's destination path to
   `../scripts/sync-to-projects.ps1`.
3. Run `..\scripts\sync-to-projects.ps1` and commit the resulting copies in
   each consumer repo.

> Per the workspace agent rule
> (`c:\analog-pim\.cursor\rules\branding-assets.mdc`), no project may add a
> new in-app branding bitmap directly to its own `assets/` directory — it
> must enter the workspace through this folder first.
