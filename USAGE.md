# Using Core Assets in Your Project

## Quick Reference

### Clone as Submodule (Recommended)

```bash
# In your project root
git submodule add https://github.com/analoginfo-pim/core-assets.git assets/core

# Update submodule
git submodule update --init --recursive
```

### Copy Assets Directly

```bash
# Desktop application
cp core-assets/icons/desktop/aic-icon.ico your-project/assets/

# Web application
cp core-assets/icons/web/* your-project/public/
```

### Update from Core Assets

```bash
# If using submodule
cd assets/core
git pull origin master

# If copying files, repeat copy commands
```

## Integration Examples

### Rust Desktop App

**Cargo.toml:**
```toml
[build-dependencies]
[target.'cfg(windows)'.build-dependencies]
winresource = "0.1"
```

**build.rs:**
```rust
#[cfg(windows)]
{
    if std::path::Path::new("assets/aic-icon.ico").exists() {
        let mut res = winresource::WindowsResource::new();
        res.set_icon("assets/aic-icon.ico");
        res.set("ProductName", "AIC PIM Application");
        res.set("CompanyName", "Analog Information Systems");
        res.compile()?;
    }
}
```

### React/Vite Web App

**Copy files:**
```bash
cp ../core-assets/icons/web/*.svg public/
cp ../core-assets/icons/web/manifest.json public/
```

**index.html:**
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#1a2332" />
```

## Repository Structure

```
core-assets/
├── icons/
│   ├── desktop/          # aic-icon.ico (Windows)
│   ├── web/              # favicon.svg, logo.svg, etc.
│   └── source/           # aic-icon.svg (editable)
├── scripts/              # Generation scripts
└── docs/                 # Guidelines and instructions
```

## Support

**Repository:** https://github.com/analoginfo-pim/core-assets  
**Issues:** https://github.com/analoginfo-pim/core-assets/issues
