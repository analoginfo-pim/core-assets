# Generate Icon Files from SVG Sources
# This script converts SVG icons to PNG and ICO formats for use in applications
# Requires: ImageMagick (magick command) or Inkscape

param(
    [switch]$UseInkscape = $false
)

Write-Host "=== AIC Icon Generator ===" -ForegroundColor Cyan
Write-Host ""

# Check for required tools
$hasImageMagick = Get-Command magick -ErrorAction SilentlyContinue
$hasInkscape = Get-Command inkscape -ErrorAction SilentlyContinue

if (-not $hasImageMagick -and -not $hasInkscape) {
    Write-Host "ERROR: Neither ImageMagick nor Inkscape found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install one of the following:"
    Write-Host "  - ImageMagick: https://imagemagick.org/script/download.php"
    Write-Host "  - Inkscape: https://inkscape.org/release/"
    exit 1
}

$tool = if ($UseInkscape -and $hasInkscape) { "Inkscape" } 
        elseif ($hasImageMagick) { "ImageMagick" } 
        else { "Inkscape" }

Write-Host "Using: $tool" -ForegroundColor Green
Write-Host ""

# Function to convert SVG to PNG using ImageMagick
function ConvertTo-PngImageMagick {
    param($SvgPath, $PngPath, $Size)
    
    $result = & magick convert -background none -resize "${Size}x${Size}" $SvgPath $PngPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Generated $PngPath ($Size x $Size)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [FAIL] Failed to generate $PngPath" -ForegroundColor Red
        return $false
    }
}

# Function to convert SVG to PNG using Inkscape
function ConvertTo-PngInkscape {
    param($SvgPath, $PngPath, $Size)
    
    $result = & inkscape $SvgPath --export-filename=$PngPath --export-width=$Size --export-height=$Size 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Generated $PngPath ($Size x $Size)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [FAIL] Failed to generate $PngPath" -ForegroundColor Red
        return $false
    }
}

# Wrapper function
function ConvertTo-Png {
    param($SvgPath, $PngPath, $Size)
    
    if ($tool -eq "ImageMagick") {
        return ConvertTo-PngImageMagick -SvgPath $SvgPath -PngPath $PngPath -Size $Size
    } else {
        return ConvertTo-PngInkscape -SvgPath $SvgPath -PngPath $PngPath -Size $Size
    }
}

# ============================================
# Generate Client Application Icons
# ============================================
Write-Host "Generating Client Application Icons..." -ForegroundColor Yellow

$clientSvg = "pim-offline-client\assets\icon.svg"
$clientAssets = "pim-offline-client\assets"

if (Test-Path $clientSvg) {
    # Generate temporary PNG files for ICO creation
    $tempPngs = @()
    $sizes = @(16, 32, 48, 64, 128, 256)
    
    foreach ($size in $sizes) {
        $pngPath = Join-Path $clientAssets "icon-$size.png"
        if (ConvertTo-Png -SvgPath $clientSvg -PngPath $pngPath -Size $size) {
            $tempPngs += $pngPath
        }
    }
    
    # Create ICO file from PNGs
    if ($tempPngs.Count -gt 0) {
        Write-Host "  Creating icon.ico..." -ForegroundColor Cyan
        $icoPath = Join-Path $clientAssets "icon.ico"
        
        if ($tool -eq "ImageMagick") {
            & magick convert $tempPngs $icoPath 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Generated icon.ico" -ForegroundColor Green
            } else {
                Write-Host "  [FAIL] Failed to generate icon.ico" -ForegroundColor Red
            }
        } else {
            Write-Host "  [INFO] ICO creation requires ImageMagick. Keeping PNG files." -ForegroundColor Yellow
        }
        
        # Clean up temporary PNG files
        foreach ($png in $tempPngs) {
            Remove-Item $png -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "  [WARN] Client SVG not found: $clientSvg" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# Generate Web Application Icons
# ============================================
Write-Host "Generating Web Application Icons..." -ForegroundColor Yellow

$webPublic = "pim-offline-server\ui\public"
$faviconSvg = Join-Path $webPublic "favicon.svg"
$appleSvg = Join-Path $webPublic "apple-touch-icon.svg"

if (Test-Path $faviconSvg) {
    # Generate favicon.ico with multiple sizes
    Write-Host "  Creating favicon.ico..." -ForegroundColor Cyan
    
    $tempPngs = @()
    foreach ($size in @(16, 32, 48)) {
        $pngPath = Join-Path $webPublic "favicon-$size.png"
        if (ConvertTo-Png -SvgPath $faviconSvg -PngPath $pngPath -Size $size) {
            $tempPngs += $pngPath
        }
    }
    
    if ($tempPngs.Count -gt 0 -and $tool -eq "ImageMagick") {
        $icoPath = Join-Path $webPublic "favicon.ico"
        & magick convert $tempPngs $icoPath 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Generated favicon.ico" -ForegroundColor Green
        }
    }
    
    # Keep the PNG files for direct use
    # Remove-Item $tempPngs -ErrorAction SilentlyContinue
    
    # Generate PNG icons for Android/PWA
    ConvertTo-Png -SvgPath $faviconSvg -PngPath (Join-Path $webPublic "logo192.png") -Size 192
    ConvertTo-Png -SvgPath $faviconSvg -PngPath (Join-Path $webPublic "logo512.png") -Size 512
}

if (Test-Path $appleSvg) {
    # Generate Apple touch icon
    ConvertTo-Png -SvgPath $appleSvg -PngPath (Join-Path $webPublic "apple-touch-icon.png") -Size 180
}

Write-Host ""
Write-Host "=== Icon Generation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review generated icons in:"
Write-Host "     - pim-offline-client/assets/"
Write-Host "     - pim-offline-server/ui/public/"
Write-Host "  2. Commit the generated files to version control"
Write-Host "  3. Rebuild applications to use the new icons"
Write-Host ""
