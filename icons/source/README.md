# Source Icon Files

Original SVG source files for all AIC branding assets.

## Files

- `aic-icon.svg` - Primary application icon (gradient background, white text)

## Editing Guidelines

1. **Use Vector Graphics Software**:
   - Adobe Illustrator
   - Inkscape (free)
   - Figma
   - Sketch

2. **Maintain Consistency**:
   - Font: Arial Bold
   - Text: "AIC"
   - Colors: 
     - Background gradient: #2d3e50 → #1a2332
     - Text: #ffffff

3. **Export Settings**:
   - Format: SVG 1.1
   - Decimal places: 2
   - Embed fonts or convert to paths
   - Optimize for web

4. **After Editing**:
   - Save source SVG
   - Regenerate all production formats using scripts
   - Test in target applications
   - Commit both source and generated files

## Creating New Variants

When creating logo variations:

1. **Copy base file**: `cp aic-icon.svg aic-icon-variant.svg`
2. **Make changes** preserving brand guidelines
3. **Save with descriptive name**: e.g., `aic-icon-monochrome.svg`
4. **Update generation scripts** to include new variant
5. **Document** the new variant in this README

## Quality Checklist

Before committing source changes:

- [ ] SVG validates (use https://validator.w3.org/)
- [ ] Text is legible at 16×16 pixels
- [ ] Colors match brand guidelines
- [ ] File size is reasonable (<50KB)
- [ ] No proprietary metadata (Adobe/Sketch IDs)
- [ ] Regenerated production formats successfully
- [ ] Tested in at least one target application
