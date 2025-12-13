# Create AIC Icon for Windows Executables
Add-Type -AssemblyName System.Drawing

Write-Host "Creating AIC icon..." -ForegroundColor Cyan

$sizes = @(16, 32, 48, 64, 128)
$bitmaps = @()

# Create bitmaps for each size
foreach ($size in $sizes) {
    Write-Host "  Generating ${size}x${size}..." -ForegroundColor Gray
    
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    
    # Set high quality rendering
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    
    # Create gradient background
    $rect = New-Object System.Drawing.Rectangle(0, 0, $size, $size)
    $color1 = [System.Drawing.Color]::FromArgb(255, 45, 62, 80)  # #2d3e50
    $color2 = [System.Drawing.Color]::FromArgb(255, 26, 35, 50)  # #1a2332
    $bgBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, $color1, $color2, 45)
    $g.FillRectangle($bgBrush, $rect)
    
    # Draw AIC text
    $fontSize = [Math]::Max(6, [int]($size * 0.35))
    $font = New-Object System.Drawing.Font('Arial', $fontSize, [System.Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
    $text = 'AIC'
    
    # Center the text
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    
    $textRect = New-Object System.Drawing.RectangleF(0, 0, $size, $size)
    $g.DrawString($text, $font, $textBrush, $textRect, $sf)
    
    # Cleanup
    $g.Dispose()
    $font.Dispose()
    $textBrush.Dispose()
    $bgBrush.Dispose()
    
    $bitmaps += $bmp
}

# Save the 128x128 version as PNG for preview
$previewPath = Join-Path $PSScriptRoot "icon-preview.png"
$bitmaps[4].Save($previewPath, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Host "  Preview saved: icon-preview.png" -ForegroundColor Green

# Create ICO file manually
$icoPath = Join-Path $PSScriptRoot "icon.ico"
$fs = New-Object System.IO.FileStream($icoPath, [System.IO.FileMode]::Create)
$writer = New-Object System.IO.BinaryWriter($fs)

try {
    # ICO header
    $writer.Write([uint16]0)     # Reserved, must be 0
    $writer.Write([uint16]1)     # Type: 1 for ICO
    $writer.Write([uint16]$bitmaps.Count)  # Number of images
    
    # Calculate offset to first image data
    $offset = 6 + ($bitmaps.Count * 16)
    
    # Image directory entries
    $imageDatas = @()
    foreach ($bmp in $bitmaps) {
        $ms = New-Object System.IO.MemoryStream
        $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
        $imageData = $ms.ToArray()
        $ms.Dispose()
        $imageDatas += ,$imageData
        
        # Width (0 means 256)
        if ($bmp.Width -ge 256) {
            $writer.Write([byte]0)
        } else {
            $writer.Write([byte]$bmp.Width)
        }
        
        # Height (0 means 256)
        if ($bmp.Height -ge 256) {
            $writer.Write([byte]0)
        } else {
            $writer.Write([byte]$bmp.Height)
        }
        
        $writer.Write([byte]0)      # Color palette (0 = no palette)
        $writer.Write([byte]0)      # Reserved
        $writer.Write([uint16]1)    # Color planes
        $writer.Write([uint16]32)   # Bits per pixel
        $writer.Write([uint32]$imageData.Length)  # Size of image data
        $writer.Write([uint32]$offset)            # Offset to image data
        
        $offset += $imageData.Length
    }
    
    # Write image data
    foreach ($imageData in $imageDatas) {
        $writer.Write($imageData)
    }
    
    Write-Host "  ICO file created: icon.ico" -ForegroundColor Green
    
} finally {
    $writer.Close()
    $fs.Close()
    
    # Cleanup bitmaps
    foreach ($bmp in $bitmaps) {
        $bmp.Dispose()
    }
}

# Verify the file
if (Test-Path $icoPath) {
    $fileInfo = Get-Item $icoPath
    Write-Host ""
    Write-Host "Success! Icon file created:" -ForegroundColor Green
    Write-Host "  Path: $icoPath" -ForegroundColor White
    Write-Host "  Size: $($fileInfo.Length) bytes" -ForegroundColor White
    Write-Host ""
    Write-Host "The icon will be embedded in Windows executables on next build." -ForegroundColor Yellow
} else {
    Write-Host "Error: Icon file was not created" -ForegroundColor Red
    exit 1
}
