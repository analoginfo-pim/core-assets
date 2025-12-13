# Desktop Icon Assets

Windows, macOS, and Linux application icons for AIC PIM applications.

## Files

- `aic-icon.ico` - Windows multi-resolution icon (16-128px)
- `aic-icon-preview.png` - Preview/documentation image (128×128)

## Sizes Included in ICO

- 16×16 - Taskbar, small windows
- 32×32 - Standard window icon
- 48×48 - Large icons view
- 64×64 - High DPI displays
- 128×128 - Very high DPI / Retina displays

## Usage

### Rust Applications (with winresource)

Add to `Cargo.toml`:
```toml
[target.'cfg(windows)'.build-dependencies]
winresource = "0.1"
```

In `build.rs`:
```rust
#[cfg(windows)]
{
    let mut res = winresource::WindowsResource::new();
    res.set_icon("path/to/aic-icon.ico");
    res.set("ProductName", "Your App Name");
    res.set("CompanyName", "Analog Information Systems");
    res.compile()?;
}
```

### Electron Applications

```javascript
// In package.json build config
{
  "build": {
    "win": {
      "icon": "path/to/aic-icon.ico"
    }
  }
}
```

### .NET Applications

Add to `.csproj`:
```xml
<PropertyGroup>
  <ApplicationIcon>path\to\aic-icon.ico</ApplicationIcon>
</PropertyGroup>
```

## Regenerating

Use the script in `../../scripts/create-desktop-icon.ps1` to regenerate from source SVG.

```powershell
cd scripts
.\create-desktop-icon.ps1
```
