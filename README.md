# AIC Core Assets

Centralized branding and icon assets for all Analog Information Systems PIM applications.

## Overview

This repository contains the official branding assets, logos, icons, and generation scripts used across all AIC PIM projects:

- **pim-offline-client** - Desktop application icons
- **pim-offline-server** - Web application favicons and PWA assets
- **pim-offline-legacy-client** - Legacy Python client icons
- **pim-ui-kit** - React component library branding
- **pim-orm** - Database/ORM library branding (if needed)

## Repository Structure

```
core-assets/
├── icons/
│   ├── desktop/          # Windows ICO, Linux/Mac icons
│   ├── web/              # SVG favicons, PNG icons for web
│   └── source/           # Source SVG files (editable)
├── logos/                # Full logos and variations
├── scripts/              # Icon generation and conversion scripts
└── docs/                 # Branding guidelines and usage docs
```

## Brand Identity

**Company**: Analog Information Systems  
**Product**: AIC PIM (Privileged Identity Management)  
**Logo**: "AIC" wordmark  

**Colors**:
- Primary: `#1a2332` (Dark Blue)
- Secondary: `#2d3e50` (Medium Blue)
- Accent: `#ffffff` (White for contrast)

**Typography**: Arial Bold, sans-serif

## Quick Start

### Using Icons in Your Project

#### Desktop Applications (Rust/C++)
```bash
# Copy Windows icon
cp icons/desktop/icon.ico ../your-project/assets/

# Reference in build script (Cargo.toml build-dependencies)
winresource = "0.1"
```

#### Web Applications
```bash
# Copy web assets
cp icons/web/* ../your-project/public/

# Reference in HTML
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

### Generating Icons

Use the provided scripts to generate icons from source SVGs:

```powershell
# Requires ImageMagick or Inkscape
.\scripts\generate-all-icons.ps1
```

## Asset Specifications

### Desktop Icons
- **Format**: ICO (Windows), PNG (Linux/Mac)
- **Sizes**: 16×16, 32×32, 48×48, 64×64, 128×128, 256×256
- **Color Depth**: 32-bit with alpha channel
- **Style**: Dark gradient background with white text

### Web Icons
- **Favicon**: SVG (modern) + ICO (legacy)
- **Apple Touch Icon**: 180×180 PNG (no transparency)
- **Android/PWA**: 192×192 and 512×512 PNG
- **Manifest**: JSON with theme colors

## Usage Guidelines

1. **Do not modify** production assets directly - edit source SVG files
2. **Regenerate** all formats after editing sources
3. **Test** icons in target applications before committing
4. **Version** significant branding changes

## License

These assets are proprietary to Analog Information Systems.  
© 2025 Analog Information Systems. All rights reserved.

---

## Contributing

When adding new assets:

1. Add source files to `icons/source/`
2. Generate production formats using scripts
3. Update this README with new asset locations
4. Commit source and generated files together
5. Tag release if branding changes significantly

## Support

For branding questions or asset requests, contact the development team.
