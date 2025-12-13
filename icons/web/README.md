# Web Icon Assets

Favicons and web application icons for AIC PIM web applications.

## Files

- `favicon.svg` - Modern browser favicon (scalable)
- `logo.svg` - Full logo for in-app use
- `apple-touch-icon.svg` - iOS home screen icon source
- `manifest.json` - PWA manifest template

## Required Generated Files (not in repo)

Generate these using the scripts:

- `favicon.ico` - Legacy browser favicon (16, 32, 48px)
- `favicon-16.png`, `favicon-32.png` - PNG fallbacks
- `logo192.png` - Android Chrome (192×192)
- `logo512.png` - Android PWA splash (512×512)
- `apple-touch-icon.png` - iOS home screen (180×180)

## Usage

### Standard HTML Setup

```html
<!DOCTYPE html>
<html>
  <head>
    <!-- Modern browsers -->
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    
    <!-- Legacy browsers -->
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png" />
    
    <!-- iOS -->
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
    
    <!-- PWA -->
    <link rel="manifest" href="/manifest.json" />
    <meta name="theme-color" content="#1a2332" />
  </head>
</html>
```

### React (Vite)

Copy files to `public/` directory:
```bash
cp core-assets/icons/web/* your-app/public/
```

Reference in `index.html` as shown above.

## Generating PNG/ICO Files

Use the main generation script:
```powershell
cd ../../scripts
.\generate-icons.ps1
```

Or use online tools:
- https://cloudconvert.com/svg-to-ico
- https://cloudconvert.com/svg-to-png

## Manifest Configuration

Update `manifest.json` for your specific application:

```json
{
  "name": "Your App Name",
  "short_name": "App",
  "description": "Your app description",
  "theme_color": "#1a2332",
  "background_color": "#ffffff"
}
```
