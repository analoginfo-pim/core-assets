<#
.SYNOPSIS
  Pushes canonical branding/legal assets from this `core-assets` repo to every
  consumer project in the AIC PIM workspace.

.DESCRIPTION
  This is the source of truth for "which file goes where". Whenever a new
  product checks in a logo, favicon, EULA, etc., add an entry to the
  $assetMap below instead of letting the per-project copy drift.

  After running, every listed destination is byte-identical to its source in
  core-assets. The script is idempotent.

  See ../docs/BRANDING.md and the workspace rule at
  ../../.cursor/rules/branding-assets.mdc for the policy.

.PARAMETER WorkspaceRoot
  Workspace parent directory containing all the sibling repos. Defaults to
  the parent of this core-assets checkout (typically c:\analog-pim).

.PARAMETER WhatIf
  Show what would be copied without actually copying.

.EXAMPLE
  .\sync-to-projects.ps1
  .\sync-to-projects.ps1 -WhatIf
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string] $WorkspaceRoot
)

$ErrorActionPreference = "Stop"

$selfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $selfDir "..")).Path
if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $WorkspaceRoot = (Resolve-Path (Join-Path $repoRoot "..")).Path
}

# ---------------------------------------------------------------------------
# Asset map: <core-assets-relative-source>  ->  array of consumer paths
# (paths are relative to $WorkspaceRoot).
# ---------------------------------------------------------------------------
$assetMap = [ordered]@{

    # ----- Source vector / hi-res masters --------------------------------

    # Source SVG (editable) -- the offline-client keeps a copy because its
    # `build.rs` rasterizes from SVG when the .ico is missing.
    "icons/source/aic-icon.svg" = @(
        "pim-offline-client/assets/icon.svg"
    )

    # 1024x1024 source PNG used by `tauri icon` to generate the platform-icon
    # tree. Each Tauri project keeps a copy so `tauri icon` works locally,
    # but the canonical master lives here. The DERIVATIVE platform icons
    # (Square*.png, AppIcon-*.png, etc.) are generated INSIDE core-assets
    # under icons/tauri/ -- see ../icons/tauri/README.md -- and synced from
    # there by the per-tree entry below.
    "icons/source/aic-icon-1024.png" = @(
        "pim-offline-client-configurator-tauri/src-tauri/icons/icon.png",
        "pim-offline-client-elevate-tauri/src-tauri/icons/icon.png",
        "pim-offline-server-configurator-tauri/src-tauri/icons/icon.png"
    )

    # ----- Desktop / OS icons --------------------------------------------

    # Canonical Windows ICO -- every Win32 / Tauri / web project pulls from
    # here. Adding a project? Put its destination here.
    "icons/desktop/aic-icon.ico" = @(
        "pim-offline-client/assets/icon.ico",
        "pim-offline-client-configurator-win32/assets/aic-icon.ico",
        "pim-offline-client-elevate-win32/assets/aic-icon.ico",
        "pim-offline-server-configurator-win32/assets/aic-icon.ico",
        "pim-offline-server/assets/aic-icon.ico",
        "pim-offline-server/ui/public/favicon.ico",
        "pim-product-launcher-win32/assets/aic-icon.ico",
        "pim-app-config/crates/pim-app-config-cli/assets/aic-icon.ico",
        "pim-app-config/crates/pim-app-config-demo/assets/aic-icon.ico",
        "pim-offline-client-configurator-tauri/src/assets/aic-favicon.ico",
        "pim-offline-client-elevate-tauri/src/assets/aic-favicon.ico",
        "pim-offline-server-configurator-tauri/src/assets/aic-favicon.ico",
        "pim-ui-kit/packages/demo/public/favicon.ico",
        "pim-ui-kit/templates/app-template/public/favicon.ico"
    )

    # Static preview render of the icon (used in About/help screens).
    "icons/desktop/aic-icon-preview.png" = @(
        "pim-offline-client/assets/icon-preview.png"
    )

    # ----- Web ------------------------------------------------------------

    "icons/web/favicon.svg" = @(
        "pim-offline-server/ui/public/favicon.svg"
    )
    "icons/web/apple-touch-icon.svg" = @(
        "pim-offline-server/ui/public/apple-touch-icon.svg"
    )
    "icons/web/logo.svg" = @(
        "pim-offline-server/ui/public/logo.svg"
    )
    "icons/web/manifest.json" = @(
        "pim-offline-server/ui/public/manifest.json"
    )

    # ----- In-app branding bitmaps ---------------------------------------

    # About-dialog hero in the Win32 admin GUI / agent.
    "branding/aic-about.png" = @(
        "pim-offline-client/assets/aic-about.png"
    )

    # Top-of-window header banner used by every Tauri configurator and
    # elevation UI.
    "branding/aic-header.png" = @(
        "pim-offline-client-configurator-tauri/src/assets/aic-header.png",
        "pim-offline-client-elevate-tauri/src/assets/aic-header.png",
        "pim-offline-server-configurator-tauri/src/assets/aic-header.png"
    )

    # ----- Legal documents (shipped by every MSI installer) --------------

    "legal/EULA_AIC_Commercial.rtf" = @(
        "pim-installers/legal/EULA_AIC_Commercial.rtf"
    )
}

# Tree-style sync targets: copy an entire core-assets directory recursively
# into each listed consumer directory. Used for Tauri's hard-coded
# `src-tauri/icons/<size>.png` + `Square*Logo.png` + `ios/AppIcon-*.png` +
# `android/mipmap-*/ic_launcher*.png` layout, which the Tauri CLI dictates
# and which we want generated in ONE place (core-assets) rather than three.
#
# Activate this entry once `tauri icon icons/source/aic-icon-1024.png
# --output icons/tauri` has populated `icons/tauri/`. Until then it is a
# no-op (the script tolerates an empty source).
$treeMap = [ordered]@{
    "icons/tauri" = @(
        "pim-offline-client-configurator-tauri/src-tauri/icons",
        "pim-offline-client-elevate-tauri/src-tauri/icons",
        "pim-offline-server-configurator-tauri/src-tauri/icons"
    )
}

# ---------------------------------------------------------------------------
# Drift detection: ensure $assetMap keys exist in core-assets first.
# ---------------------------------------------------------------------------
$missingSources = @()
foreach ($rel in $assetMap.Keys) {
    $src = Join-Path $repoRoot $rel
    if (-not (Test-Path -LiteralPath $src)) { $missingSources += $rel }
}
if ($missingSources.Count -gt 0) {
    throw "Sources missing from core-assets: $([string]::Join('; ', $missingSources))"
}

# ---------------------------------------------------------------------------
# Sync.
# ---------------------------------------------------------------------------
$copied = 0; $skipped = 0; $missingDestRoots = @()
foreach ($rel in $assetMap.Keys) {
    $src = Join-Path $repoRoot $rel
    $srcHash = (Get-FileHash $src -Algorithm SHA1).Hash
    foreach ($destRel in $assetMap[$rel]) {
        $dest = Join-Path $WorkspaceRoot $destRel
        $destDir = Split-Path -Parent $dest
        $destRepoRoot = ($destRel -split '[\\/]')[0]
        $destRepoFull = Join-Path $WorkspaceRoot $destRepoRoot
        if (-not (Test-Path -LiteralPath $destRepoFull)) {
            $missingDestRoots += $destRepoRoot
            continue
        }
        if (-not (Test-Path -LiteralPath $destDir)) {
            if ($PSCmdlet.ShouldProcess($destDir, "mkdir")) {
                New-Item -ItemType Directory -Force -Path $destDir | Out-Null
            }
        }
        $needCopy = $true
        if (Test-Path -LiteralPath $dest) {
            $destHash = (Get-FileHash $dest -Algorithm SHA1).Hash
            if ($destHash -eq $srcHash) {
                $needCopy = $false
                $skipped++
            }
        }
        if ($needCopy) {
            if ($PSCmdlet.ShouldProcess($dest, "copy from $rel")) {
                Copy-Item -LiteralPath $src -Destination $dest -Force
                $copied++
                Write-Host ("  copied  {0}  <-  {1}" -f $destRel, $rel) -ForegroundColor DarkGreen
            }
        }
    }
}

$missingDestRoots = $missingDestRoots | Select-Object -Unique
if ($missingDestRoots.Count -gt 0) {
    Write-Warning ("Skipped destinations because the consumer repo was not " +
                   "checked out under $WorkspaceRoot. Missing: " +
                   [string]::Join(', ', $missingDestRoots))
}

# ---------------------------------------------------------------------------
# Tree sync (Tauri platform icons etc.).
# ---------------------------------------------------------------------------
$treeCopied = 0; $treeSkipped = 0; $treeEmpty = 0
foreach ($srcRel in $treeMap.Keys) {
    $srcDir = Join-Path $repoRoot $srcRel
    if (-not (Test-Path -LiteralPath $srcDir)) {
        Write-Warning "Tree source $srcDir does not exist yet -- skipping."
        continue
    }
    $srcFiles = Get-ChildItem -LiteralPath $srcDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "README*" }
    if ($srcFiles.Count -eq 0) {
        # Treat an empty (or README-only) tree as "not yet generated"; do not
        # blow away the consumer's pre-existing tauri tree.
        $treeEmpty++
        Write-Host ("  (skip) $srcRel is empty -- run ``tauri icon`` first.") -ForegroundColor DarkYellow
        continue
    }
    foreach ($destRel in $treeMap[$srcRel]) {
        $destDir = Join-Path $WorkspaceRoot $destRel
        $destRepoRoot = ($destRel -split '[\\/]')[0]
        $destRepoFull = Join-Path $WorkspaceRoot $destRepoRoot
        if (-not (Test-Path -LiteralPath $destRepoFull)) { continue }
        foreach ($srcFile in $srcFiles) {
            $rel = $srcFile.FullName.Substring($srcDir.Length + 1)
            $dest = Join-Path $destDir $rel
            $destSubdir = Split-Path -Parent $dest
            if (-not (Test-Path -LiteralPath $destSubdir)) {
                if ($PSCmdlet.ShouldProcess($destSubdir, "mkdir")) {
                    New-Item -ItemType Directory -Force -Path $destSubdir | Out-Null
                }
            }
            $needCopy = $true
            if (Test-Path -LiteralPath $dest) {
                $sh = (Get-FileHash $srcFile.FullName -Algorithm SHA1).Hash
                $dh = (Get-FileHash $dest -Algorithm SHA1).Hash
                if ($sh -eq $dh) { $needCopy = $false; $treeSkipped++ }
            }
            if ($needCopy) {
                if ($PSCmdlet.ShouldProcess($dest, "copy from $srcRel/$rel")) {
                    Copy-Item -LiteralPath $srcFile.FullName -Destination $dest -Force
                    $treeCopied++
                }
            }
        }
    }
}

Write-Host ""
$summary = "Sync complete. Files: copied=$copied, already-in-sync=$skipped. " +
           "Trees: copied=$treeCopied, already-in-sync=$treeSkipped, empty=$treeEmpty."
Write-Host $summary -ForegroundColor Cyan
Write-Host "Workspace root: $WorkspaceRoot"
Write-Host "Source repo:    $repoRoot"
