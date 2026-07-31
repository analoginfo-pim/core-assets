# AIC Core Assets

Centralized branding, icon, and legal assets for all Analog Informatics
Corporation (AIC) PIM applications.

> **Single source of truth.** This repository is the **only** authoritative
> location for AIC branding (icons, logos, splash art) and shared legal text
> (EULAs, license files) used by any product in the workspace. Other
> in-tree copies are build outputs, kept in sync by
> [`scripts/sync-to-projects.ps1`](scripts/sync-to-projects.ps1). The
> workspace-wide agent rule
> (`c:\analog-pim\.cursor\rules\branding-assets.mdc`) forbids editing
> branding files outside this repo.
>
> Adding a new branded artefact to a product? See the **Adding new branding
> to a project** section in
> `c:\analog-pim\.cursor\rules\branding-assets.mdc`.

## Overview

This repository contains the official branding assets, logos, icons, legal
text, and generation/sync scripts used across all AIC PIM projects:

- **pim-offline-client** - Desktop application icons
- **pim-offline-server** - Web application favicons and PWA assets
- **pim-offline-legacy-client** - Legacy Python client icons
- **pim-ui-kit** - React component library branding
- **pim-orm** - Database/ORM library branding (if needed)

## Repository Structure

```
core-assets/
├── certs/
│   └── localhost-dev/    # Dev / lab TLS bundle
├── geoip/                # MaxMind GeoLite2-Country.mmdb + product credentials
├── threat-intel/         # FireHOL / ET Open / AbuseIPDB offline lists
├── icons/
│   ├── desktop/          # Windows ICO, Linux/Mac icons
│   ├── web/              # SVG favicons, PNG icons for web, manifest.json
│   └── source/           # Source SVG files (editable)
├── legal/                # Shared legal text shipped with installers (EULAs)
├── logos/                # Full logos and variations
├── scripts/
│   ├── generate-icons.ps1
│   ├── sync-to-projects.ps1
│   ├── Update-MaxMindGeoLite.ps1
│   ├── Update-ThreatIntelLists.ps1
│   └── create-desktop-icon.ps1
└── docs/                 # Branding guidelines and usage docs
```

### GeoIP + threat intel (shared product seed)

`geoip/` and `threat-intel/` hold MaxMind GeoLite2-Country.mmdb (~9 MB),
product-default MaxMind credentials (`maxmind-constants.toml`), and offline
FireHOL / ET Open / AbuseIPDB blocklists for **firewall / IDS / access-control**
across AIC products (offline server first; Mix later).

- **Refresh:** `scripts/Update-MaxMindGeoLite.ps1` and
  `scripts/Update-ThreatIntelLists.ps1 -ConfirmDownload …`, then
  `scripts/sync-to-projects.ps1`.
- **MSI:** `Build-PimOfflineServerMsi.ps1` stages these into
  `%ProgramFiles%\AIC\OfflinePimServer\geoip\` and `\threat-intel\`.
- **First boot / reset:** the offline server copies missing files into
  ProgramData; on-demand Download/Update remains available.
- **License:** MaxMind GeoLite2 — ship only inside AIC product channels;
  rotate credentials if exposed. FireHOL / ET / AbuseIPDB — respect upstream
  ToS. See `geoip/README.md` and `threat-intel/README.md`.

### Localhost-dev certificates (new in May 2026)

`certs/localhost-dev/` is the canonical bundle of self-signed TLS certs
that `pim-offline-server` and `pim-offline-agent` use for localhost /
lab testing. Every MSI ships these exact bytes, every dev `cargo run`
picks them up via `pim-offline-server/scripts/Sync-DevCerts.ps1`, and
every CI smoke test can rely on a stable fingerprint. See
[`certs/localhost-dev/README.md`](certs/localhost-dev/README.md) for
the regeneration recipe, the `NeverOverwriteFile` install contract,
and the public-key safety guarantees.

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
Copyright 2026 Analog Informatics Corporation.

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
