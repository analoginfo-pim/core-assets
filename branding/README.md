# In-app branding art

Bitmap branding artefacts displayed inside running AIC products (about
dialogs, headers, splash images). Anything that ships *inside* a product
window — as opposed to OS-level icons (taskbar, shortcut, ARP entry) — lives
here.

## Files

| File | Used by | Purpose |
| ---- | ------- | ------- |
| `aic-about.png` | `pim-offline-client/assets/aic-about.png` | "About" dialog hero image (Win32 admin GUI / agent). |
| `aic-header.png` | All Tauri configurators / elevation UIs (`pim-offline-client-configurator-tauri`, `pim-offline-client-elevate-tauri`, `pim-offline-server-configurator-tauri`). | Top-of-window header banner. |

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
