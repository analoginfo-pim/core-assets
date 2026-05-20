<#
.SYNOPSIS
  Generate differentiated installer shortcut icons for AIC Offline products.

.DESCRIPTION
  Produces multi-resolution .ico files under
  icons/desktop/installer-shortcuts/ for client vs server and Win32 vs Tauri
  (W / T badge). Also refreshes icons/desktop/aic-icon.ico and repairs the
  corrupted icons/source/aic-icon-1024.png raster master.

  Requires Python 3 with Pillow (`pip install pillow`).

.NOTES
  Per branding-assets.mdc, run this in core-assets, commit the outputs, then
  sync-to-projects.ps1 and rebuild MSIs.
#>
param()

$ErrorActionPreference = "Stop"
$selfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $selfDir "..")).Path
$pyScript = Join-Path $selfDir "generate_installer_shortcut_icons.py"

Write-Host "=== AIC installer shortcut icon generator ===" -ForegroundColor Cyan
Write-Host "Repo root: $repoRoot"

if (-not (Test-Path -LiteralPath $pyScript)) {
    throw "Missing Python generator: $pyScript"
}

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & py -3 $pyScript
}
else {
    & python $pyScript
}
if ($LASTEXITCODE -ne 0) {
    throw "Icon generation failed with exit code $LASTEXITCODE."
}

Write-Host ""
Write-Host "=== Installer shortcut icons complete ===" -ForegroundColor Green
Write-Host "Next: commit core-assets, run sync-to-projects.ps1, rebuild MSIs."
