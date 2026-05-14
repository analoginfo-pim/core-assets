# Tauri platform icons

This folder holds **derivative** icons generated from
`../source/aic-icon-1024.png` using the official Tauri CLI:

```powershell
# from the core-assets repo root, with `tauri-cli` >= 2.0 on PATH
tauri icon icons/source/aic-icon-1024.png --output icons/tauri
```

The output is committed to `core-assets` (NOT to per-project `src-tauri/icons/`
trees) and then synced into every consuming Tauri project by
`../scripts/sync-to-projects.ps1`.

## Why centralised

Before this change every Tauri project ran `tauri icon` against its own
`src-tauri/icons/icon.png` and committed an entire 30+-file derivative tree
into its own repo. Three projects shipping near-identical 567 kB source
PNGs and ~3 MB of generated artefacts was both wasteful and a drift trap:
one project regenerating with a slightly newer Tauri CLI could silently ship
a different favicon than its sibling. Centralising fixes both.

## When to regenerate

- The 1024 source PNG (`../source/aic-icon-1024.png`) has changed.
- The Tauri CLI's icon-generation output has changed in a way that affects
  PWA / Microsoft Store / Apple ecosystems we ship to.

After regenerating, commit the entire `icons/tauri/` tree in `core-assets`
and run `..\scripts\sync-to-projects.ps1` to push the change to consumers.

## Per-project `src-tauri/icons/`

The Tauri CLI hard-codes its expected layout
(`src-tauri/icons/icon.png`, `Square*.png`, `ios/AppIcon-*.png`,
`android/mipmap-*/ic_launcher*.png`, …). The sync script faithfully mirrors
that tree from here. **Do not edit those files in the Tauri projects** —
edit and regenerate here, then sync.
