# AIC Branding Assets

This directory contains the branding and icon assets for all Analog Information Systems PIM applications.

## Brand Identity

**Logo**: "AIC" (Analog Informatics Corporation)
**Colors**: 
- Primary: #1a2332 (Dark Blue)
- Secondary: #2d3e50 (Medium Blue)
- Accent: #ffffff (White for contrast)

**Typography**: Arial Bold, sans-serif

## Asset Locations

### Desktop Application (pim-offline-client)
- **Location**: `pim-offline-client/assets/`
- **Files**:
  - `icon.svg` - Source SVG (256x256, editable)
  - `icon.ico` - Windows application icon (generated)
- **Usage**: Embedded in Windows executables via `build.rs`

### Web Application (pim-offline-server)
- **Location**: `pim-offline-server/ui/public/`
- **Files**:
  - `favicon.svg` - Modern browser favicon (scalable)
  - `favicon.ico` - Legacy browser favicon (multi-size)
  - `logo.svg` - Full logo for in-app use
  - `apple-touch-icon.png` - iOS home screen icon (180x180)
  - `logo192.png` - Android/PWA icon (192x192)
  - `logo512.png` - Android/PWA splash icon (512x512)
  - `manifest.json` - PWA manifest with icon references
- **Usage**: Referenced in `index.html` and served by Vite/Axum

### Legacy Client (pim-offline-legacy-client)
- Uses Python/Tkinter - can reference SVG or PNG versions
- Copy icons from client assets directory as needed

## Generating Icons

### Automated Script (Recommended)
```powershell
# From the analog-pim root directory
.\generate-icons.ps1
```

This PowerShell script automatically generates all required PNG and ICO files from the SVG sources.

**Requirements**:
- ImageMagick (recommended): https://imagemagick.org/script/download.php
- OR Inkscape: https://inkscape.org/release/

### Manual Generation

#### Using ImageMagick:
```bash
# Generate Windows ICO for desktop app
cd pim-offline-client/assets
magick convert -background none icon.svg -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico

# Generate web icons
cd ../../pim-offline-server/ui/public
magick convert -background none favicon.svg -define icon:auto-resize=48,32,16 favicon.ico
magick convert -background none -resize 192x192 favicon.svg logo192.png
magick convert -background none -resize 512x512 favicon.svg logo512.png
magick convert -background none -resize 180x180 apple-touch-icon.svg apple-touch-icon.png
```

#### Using Inkscape:
```bash
# Desktop app
inkscape pim-offline-client/assets/icon.svg --export-filename=icon-256.png -w 256 -h 256
# ... repeat for other sizes (128, 64, 48, 32, 16)
# Then combine with ImageMagick: magick convert icon-*.png icon.ico

# Web app
inkscape pim-offline-server/ui/public/favicon.svg --export-filename=logo192.png -w 192 -h 192
inkscape pim-offline-server/ui/public/favicon.svg --export-filename=logo512.png -w 512 -h 512
inkscape pim-offline-server/ui/public/apple-touch-icon.svg --export-filename=apple-touch-icon.png -w 180 -h 180
```

## Icon Specifications

### Desktop Application (Windows)
- **Format**: ICO (multi-resolution)
- **Sizes**: 16×16, 32×32, 48×48, 64×64, 128×128, 256×256
- **Color**: 32-bit with transparency
- **Style**: Dark background with white text for task bar visibility

### Web Application
- **Favicon**: 
  - Modern: SVG (any size, scalable)
  - Legacy: ICO (16×16, 32×32, 48×48)
- **Apple Touch Icon**: PNG 180×180 (no transparency, solid background)
- **Android/PWA**: PNG 192×192 and 512×512
- **Manifest**: JSON with icon references and theme colors

## Updating Icons

1. **Edit Source SVG**: Modify `icon.svg` files using a vector graphics editor
2. **Regenerate**: Run `generate-icons.ps1` to create all formats
3. **Test**: Build and run applications to verify icon appearance
4. **Commit**: Add both SVG sources and generated files to git

## Browser Support

The web application uses a progressive enhancement strategy:

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />          <!-- Modern browsers -->
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" /> <!-- Legacy browsers -->
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />          <!-- iOS -->
<link rel="manifest" href="/manifest.json" />                         <!-- PWA/Android -->
```

## License & Usage

These assets are proprietary to Analog Information Systems and should only be used in official AIC PIM applications.

**Copyright © 2025 Analog Information Systems. All rights reserved.**
