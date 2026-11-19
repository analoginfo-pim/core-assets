# Source Icon Files

Master artwork for every AIC Enterprise desktop icon.

## Files

| File | What it is |
|---|---|
| `aic-mark-512.png` | The approved production icon: navy (`#0F2135`) "AIC" with the line under "AI", on white. Copied from `pam-platform-docs/docs/go-to-market/website-and-ui/images/aic-logo-black-512.png`. This is the only source the generator reads. |
| `aic-icon-1024.png` | 1024 px master, no stripe (services, agents, the default product icon). Generated. |
| `aic-icon-admin-1024.png` | 1024 px master with the admin stripe. Source for `../tauri/`. Generated. |
| `aic-icon-user-1024.png` | 1024 px master with the user stripe. Source for `../tauri-user/`. Generated. |
| `aic-icon.svg` | Retired teal-gradient artwork, kept for the agent build's SVG fallback. Do not use for new icons. |

The old teal / aqua-bar icons are retired. The website brand guide says:
use the plain AIC mark with the underline; do not restore the old aqua-bar
icon.

## Who gets which stripe

Every icon is the mark on a white rounded tile. A bottom stripe says who the
program is for:

| Stripe | Color | Programs |
|---|---|---|
| Admin | amber `#B45309` (`--aic-amber`) | Elevated operator tools: the server configurators, the agent configurators, DB Mgmt, Jump, Recording and WA configurators |
| User | blue `#2359D1` (`--aic-blue`) | Programs an end user runs: the elevation request dialogs |
| None | | Services, agents, CLIs and the default product icon |

The Win32 and Tauri builds of one program use the same icon.

## Regenerating

From the `core-assets` root (Pillow required):

```powershell
python scripts/generate_installer_shortcut_icons.py
# Tauri platform trees, from any Tauri project with @tauri-apps/cli:
npx tauri icon <core-assets>\icons\source\aic-icon-admin-1024.png --output <core-assets>\icons\tauri
npx tauri icon <core-assets>\icons\source\aic-icon-user-1024.png --output <core-assets>\icons\tauri-user
# Replace the generated icon.ico with the per-size ICOs (sharper small frames):
copy icons\desktop\installer-shortcuts\aic-server-admin-tauri.ico icons\tauri\icon.ico
copy icons\desktop\installer-shortcuts\aic-client-elevate-tauri.ico icons\tauri-user\icon.ico
```

Then push them with `scripts/sync-to-projects.ps1`.
