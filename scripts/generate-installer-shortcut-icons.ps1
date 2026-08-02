<#
.SYNOPSIS
  Generate differentiated MSI installer shortcut .ico files from the AIC mark.

.DESCRIPTION
  Produces eight multi-resolution Windows .ico files under
  icons/desktop/installer-shortcuts/. Each variant layers palette accents,
  optional Win32/Tauri badges, and (for elevation shortcuts) a key motif on
  top of icons/source/aic-icon.svg.

  Per branding-assets.mdc, these artefacts live only in core-assets. MSI
  builds copy them via pim-installers/scripts/Stage-InstallerShortcutIcons.ps1.

.PARAMETER UseInkscape
  Force Inkscape for SVG rasterization when ImageMagick is also installed.

.NOTES
  Requires ImageMagick (`magick`) for ICO assembly and compositing.
  PNG rasterization can fall back to Inkscape when ImageMagick is absent.
  See icons/desktop/installer-shortcuts/README.md.
#>
param(
    [switch] $UseInkscape
)

$ErrorActionPreference = "Stop"

$selfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $selfDir "..")).Path

# ImageMagick installed via winget is not always on PATH in the same shell session.
$magickCandidates = @(
    (Get-Command magick -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
    (Get-ChildItem "${env:ProgramFiles}\ImageMagick*\magick.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName)
)
$magickExe = $magickCandidates | Where-Object { $_ } | Select-Object -First 1
if ($magickExe) {
    $magickDir = Split-Path -Parent $magickExe
    $env:PATH = "$magickDir;$env:PATH"
}

$hasImageMagick = [bool] $magickExe
$hasInkscape    = [bool] (Get-Command inkscape -ErrorAction SilentlyContinue)
if (-not $hasImageMagick -and -not $hasInkscape) {
    throw "Neither ImageMagick (`magick`) nor Inkscape found. Install ImageMagick to generate installer shortcut ICO files."
}

$renderTool = if ($UseInkscape -and $hasInkscape) { "Inkscape" }
              elseif ($hasImageMagick) { "ImageMagick" }
              else { "Inkscape" }

Write-Host "=== AIC installer shortcut icon generator ===" -ForegroundColor Cyan
Write-Host "Repo root: $repoRoot"
Write-Host "Raster backend: $renderTool" -ForegroundColor Green
if (-not $hasImageMagick) {
    throw "ICO assembly requires ImageMagick. Install ImageMagick (winget install ImageMagick.ImageMagick)."
}

function Invoke-Magick {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Args)
    & magick @Args
    if ($LASTEXITCODE -ne 0) {
        throw "magick failed: magick $($Args -join ' ')"
    }
}

function Convert-SvgToPng([string] $svgPath, [string] $pngPath, [int] $size) {
    if ($renderTool -eq "ImageMagick") {
        Invoke-Magick $svgPath -background none -resize "${size}x${size}" $pngPath
    }
    else {
        & inkscape $svgPath --export-filename=$pngPath --export-width=$size --export-height=$size 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Failed to render $svgPath -> $pngPath ($size px)" }
    }
    Write-Host ("  [ok] {0} ({1}x{1})" -f (Resolve-Path $pngPath).Path, $size) -ForegroundColor DarkGreen
}

function New-VariantPng {
    param(
        [string] $BasePng,
        [string] $OutPng,
        [string] $Palette,          # client | server
        [string] $Badge = "",       # W | T | ""
        [switch] $ElevationKey
    )

    $accent = if ($Palette -eq "client") { "#00aec7" } else { "#e86c00" }
    $badgeFill = if ($Palette -eq "client") { "#007a8c" } else { "#9a4500" }

    $args = @(
        $BasePng,
        "-alpha", "set",
        "-fill", $accent,
        "-draw", "rectangle 0,196 256,256",
        $OutPng
    )
    Invoke-Magick @args

    if ($ElevationKey) {
        $keyPng = Join-Path (Split-Path $OutPng) "key-overlay-temp.png"
        Invoke-Magick -size 256x256 xc:none `
            -fill "#f4d03f" -stroke "#b7950b" -strokewidth 4 `
            -draw "roundrectangle 168,168 238,238 12,12" `
            -fill "#b7950b" -draw "circle 203,203 203,188" `
            -draw "rectangle 218,198 248,208" `
            $keyPng
        Invoke-Magick $OutPng $keyPng -compose over -composite $OutPng
        Remove-Item -LiteralPath $keyPng -Force -ErrorAction SilentlyContinue
    }

    if ($Badge) {
        Invoke-Magick $OutPng `
            -fill white -stroke $badgeFill -strokewidth 5 `
            -draw "circle 208,48 208,72" `
            -font "Arial-Bold" -pointsize 34 -fill $badgeFill `
            -gravity NorthEast -annotate "+30+14" $Badge `
            $OutPng
    }
}

function Get-PngPixelSize {
    param([string] $PngPath)
    # PNG IHDR: bytes 16..23 are width/height big-endian uint32 (RFC 2083).
    $bytes = [System.IO.File]::ReadAllBytes($PngPath)
    if ($bytes.Length -lt 24 -or $bytes[0] -ne 0x89 -or $bytes[1] -ne 0x50) {
        throw "Not a PNG file: $PngPath"
    }
    $w = ([uint32]$bytes[16] -shl 24) -bor ([uint32]$bytes[17] -shl 16) -bor ([uint32]$bytes[18] -shl 8) -bor [uint32]$bytes[19]
    $h = ([uint32]$bytes[20] -shl 24) -bor ([uint32]$bytes[21] -shl 16) -bor ([uint32]$bytes[22] -shl 8) -bor [uint32]$bytes[23]
    return @{ Width = [int]$w; Height = [int]$h }
}

function New-PngCompressedIco {
    param(
        [Parameter(Mandatory = $true)][string[]] $PngPaths,
        [Parameter(Mandatory = $true)][string] $OutIco
    )
    # ImageMagick 7.1+ writes BMP/DIB frames into .ico by default. Windows
    # Explorer often paints those as multi-colored static. Store PNG payloads
    # in the ICO container instead (same shape as icons/desktop/aic-icon.ico).
    $frames = @()
    foreach ($p in $PngPaths) {
        $dim = Get-PngPixelSize -PngPath $p
        $frames += [pscustomobject]@{
            Path   = $p
            Width  = $dim.Width
            Height = $dim.Height
            Bytes  = [System.IO.File]::ReadAllBytes($p)
        }
    }
    $count = $frames.Count
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter $ms
    try {
        $bw.Write([uint16]0)       # reserved
        $bw.Write([uint16]1)       # type = icon
        $bw.Write([uint16]$count)
        $offset = 6 + (16 * $count)
        foreach ($f in $frames) {
            $wb = if ($f.Width -ge 256) { [byte]0 } else { [byte]$f.Width }
            $hb = if ($f.Height -ge 256) { [byte]0 } else { [byte]$f.Height }
            $bw.Write($wb)
            $bw.Write($hb)
            $bw.Write([byte]0)     # color palette
            $bw.Write([byte]0)     # reserved
            $bw.Write([uint16]1)   # color planes
            $bw.Write([uint16]32)  # bits per pixel (advisory for PNG frames)
            $bw.Write([uint32]$f.Bytes.Length)
            $bw.Write([uint32]$offset)
            $offset += $f.Bytes.Length
        }
        foreach ($f in $frames) {
            $bw.Write($f.Bytes)
        }
        $bw.Flush()
        [System.IO.File]::WriteAllBytes($OutIco, $ms.ToArray())
    }
    finally {
        $bw.Dispose()
        $ms.Dispose()
    }
    $written = [System.IO.File]::ReadAllBytes($OutIco)
    $pngSigs = 0
    for ($i = 0; $i -lt $written.Length - 3; $i++) {
        if ($written[$i] -eq 0x89 -and $written[$i + 1] -eq 0x50 -and
            $written[$i + 2] -eq 0x4E -and $written[$i + 3] -eq 0x47) {
            $pngSigs++
        }
    }
    if ($pngSigs -lt $count) {
        throw "PNG-compressed ICO validation failed for $OutIco (pngSigs=$pngSigs expected=$count)"
    }
}

function New-MultiResIco {
    param(
        [string] $VariantPng256,
        [string] $IcoPath
    )

    $tempDir = Join-Path $env:TEMP ("core-assets-shortcut-ico-{0}" -f [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    try {
        $pngs = @()
        foreach ($sz in @(16, 32, 48, 256)) {
            $p = Join-Path $tempDir "frame-$sz.png"
            if ($sz -eq 256) {
                # Force RGBA so every frame is TrueColorAlpha PNG (color-type 6).
                Invoke-Magick $VariantPng256 -alpha set -type TrueColorAlpha -define png:color-type=6 $p
            }
            else {
                Invoke-Magick $VariantPng256 -resize "${sz}x${sz}" -alpha set -type TrueColorAlpha -define png:color-type=6 $p
            }
            $pngs += $p
        }
        New-PngCompressedIco -PngPaths $pngs -OutIco $IcoPath
        Write-Host "  [ok] $IcoPath (PNG-compressed ICO)" -ForegroundColor Green
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$srcSvg = Join-Path $repoRoot "icons/source/aic-icon.svg"
if (-not (Test-Path -LiteralPath $srcSvg)) {
    throw "Missing source SVG at $srcSvg."
}

$outDir = Join-Path $repoRoot "icons/desktop/installer-shortcuts"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$buildDir = Join-Path $env:TEMP "core-assets-shortcut-build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

Write-Host ""
Write-Host "Rendering base mark at 256px..." -ForegroundColor Yellow
$base256 = Join-Path $buildDir "aic-base-256.png"
Convert-SvgToPng -svgPath $srcSvg -pngPath $base256 -size 256

$variants = @(
    @{ File = "aic-client-admin-win32.ico";   Palette = "client"; Badge = "W"; Key = $false }
    @{ File = "aic-client-admin-tauri.ico";   Palette = "client"; Badge = "T"; Key = $false }
    @{ File = "aic-client-elevate-win32.ico"; Palette = "client"; Badge = "W"; Key = $true }
    @{ File = "aic-client-elevate-tauri.ico"; Palette = "client"; Badge = "T"; Key = $true }
    @{ File = "aic-server-admin-win32.ico";   Palette = "server"; Badge = "W"; Key = $false }
    @{ File = "aic-server-admin-tauri.ico";   Palette = "server"; Badge = "T"; Key = $false }
    @{ File = "aic-server-product.ico";       Palette = "server"; Badge = "";  Key = $false }
    @{ File = "aic-client-product.ico";       Palette = "client"; Badge = "";  Key = $false }
)

Write-Host ""
Write-Host "Compositing variants and assembling ICO files..." -ForegroundColor Yellow
foreach ($v in $variants) {
    $variantPng = Join-Path $buildDir ($v.File -replace '\.ico$', '.png')
    New-VariantPng -BasePng $base256 -OutPng $variantPng -Palette $v.Palette -Badge $v.Badge -ElevationKey:($v.Key)
    $icoPath = Join-Path $outDir $v.File
    New-MultiResIco -VariantPng256 $variantPng -IcoPath $icoPath
}

Remove-Item -LiteralPath $buildDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Installer shortcut icon generation complete ===" -ForegroundColor Cyan
Write-Host "Outputs: $outDir"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Inspect icons/desktop/installer-shortcuts/*.ico in Explorer."
Write-Host "  2. Commit and push core-assets."
Write-Host "  3. Run scripts/sync-to-projects.ps1 (optional mirror under pim-installers)."
