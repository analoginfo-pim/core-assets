#!/usr/bin/env bash
# Generate WiX MSI banner + welcome/exit dialog bitmaps from the AIC brand.
#
# WiX (WixUI dialog sets) requires 24-bit BMP artwork at fixed sizes:
#   - WixUIBannerBmp : 493x58   (top strip on interior wizard pages)
#   - WixUIDialogBmp : 493x312  (Welcome / Exit dialog background)
#
# Layout follows WiX conventions so the theme's black title/body text stays
# legible: the banner keeps its left side blank (title text) with the AIC badge
# on the right; the dialog keeps a navy branding strip on the left third and a
# white field on the right where the welcome text is drawn.
#
# Brand palette (see ../docs/BRANDING.md):
#   navy gradient  #2d3e50 -> #1a2332
#   accent (server) #e86c00
#
# Requires ImageMagick 7 (`magick`) with Arial-Bold available. Run locally;
# commit the resulting BMPs under branding/installer/. Nothing here runs in a
# product's release pipeline -- the committed bitmaps are the deliverable.
set -euo pipefail

self_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(CDPATH= cd -- "${self_dir}/.." && pwd)"
out_dir="${repo_root}/branding/installer"
mkdir -p "${out_dir}"

navy_hi="#2d3e50"
navy_lo="#1a2332"
accent="#e86c00"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

# --- Banner: 493x58, white field, AIC badge on the right, accent baseline ----
magick -size 44x44 xc:none \
    -fill "${navy_lo}" -draw "roundrectangle 0,0 43,43 8,8" \
    -font Arial-Bold -fill white -gravity center -pointsize 18 -annotate +0+0 "AIC" \
    "${tmp}/badge.png"

magick -size 493x58 xc:white \
    "${tmp}/badge.png" -gravity East -geometry +12+0 -composite \
    -fill "${accent}" -draw "rectangle 0,54 492,57" \
    -background white -alpha remove -alpha off -type TrueColor \
    "BMP3:${out_dir}/aic-installer-banner.bmp"

# --- Dialog: 493x312, navy branding strip (left), white text field (right) ---
magick -size 164x312 "gradient:${navy_hi}-${navy_lo}" \
    -font Arial-Bold -fill white -gravity North \
    -pointsize 54 -annotate +0+96 "AIC" \
    -pointsize 18 -annotate +0+164 "PIM Server" \
    -fill "${accent}" -draw "rectangle 30,150 133,153" \
    "${tmp}/strip.png"

magick -size 493x312 xc:white \
    "${tmp}/strip.png" -gravity NorthWest -geometry +0+0 -composite \
    -fill "${accent}" -draw "rectangle 164,0 167,311" \
    -background white -alpha remove -alpha off -type TrueColor \
    "BMP3:${out_dir}/aic-installer-dialog.bmp"

echo "Wrote:"
magick identify "${out_dir}/aic-installer-banner.bmp" "${out_dir}/aic-installer-dialog.bmp"
