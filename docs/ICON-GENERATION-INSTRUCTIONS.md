# AIC Icon Generation Instructions

Since ImageMagick/Inkscape are not installed, you can generate the required PNG and ICO files using online tools or install one of these tools:

## Option 1: Install ImageMagick (Recommended)
```powershell
# Using Chocolatey
choco install imagemagick

# Or download from: https://imagemagick.org/script/download.php
```

After installation, run:
```powershell
.\generate-icons.ps1
```

## Option 2: Online Conversion Tools

### For Desktop Application (pim-offline-client):
1. Open `pim-offline-client/assets/icon.svg` in a browser
2. Go to https://cloudconvert.com/svg-to-ico
3. Upload icon.svg
4. Set output to ICO with sizes: 16, 32, 48, 64, 128, 256
5. Download and save as `pim-offline-client/assets/icon.ico`

### For Web Application (pim-offline-server):
1. Open `pim-offline-server/ui/public/favicon.svg`
2. Convert to:
   - `favicon.ico` (sizes: 16, 32, 48) - https://cloudconvert.com/svg-to-ico
   - `logo192.png` (192x192) - https://cloudconvert.com/svg-to-png
   - `logo512.png` (512x512) - https://cloudconvert.com/svg-to-png
3. Open `pim-offline-server/ui/public/apple-touch-icon.svg`
4. Convert to `apple-touch-icon.png` (180x180)

## Current Status

✅ SVG source files created
✅ Build scripts updated to use icons
✅ Web application configured with SVG favicons (works in modern browsers)
⏳ PNG/ICO conversion pending (optional - SVG works for web, ICO needed for exe icon)

The web application will work with just the SVG files in modern browsers. The ICO files are primarily needed for:
- Windows executable icon embedding
- Legacy browser favicon support (optional)
