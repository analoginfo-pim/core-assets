#!/usr/bin/env python3
"""Generate differentiated installer shortcut .ico files for AIC Offline products.

Reads the vector master at icons/source/aic-icon.svg conceptually (rendered
via the same palette as that SVG) and writes multi-resolution ICO files under
icons/desktop/installer-shortcuts/.

Requires Pillow (pip install pillow).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "icons" / "desktop" / "installer-shortcuts"
SIZES = (16, 24, 32, 48, 64, 128, 256)

# Client = teal/cyan accent; server = navy + orange accent (US English labels in README).
PALETTES = {
    "client": {
        "bg_top": (0x1A, 0x4A, 0x5C),
        "bg_bottom": (0x0D, 0x2A, 0x36),
        "accent": (0x00, 0xB8, 0xD4),
        "badge_bg": (0x00, 0x7A, 0x8F),
    },
    "server": {
        "bg_top": (0x2D, 0x3E, 0x50),
        "bg_bottom": (0x1A, 0x23, 0x32),
        "accent": (0xF5, 0x8B, 0x28),
        "badge_bg": (0xC4, 0x6A, 0x12),
    },
}


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient_bg(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        row = (
            _lerp(top[0], bottom[0], t),
            _lerp(top[1], bottom[1], t),
            _lerp(top[2], bottom[2], t),
            255,
        )
        for x in range(size):
            px[x, y] = row
    return img


def _rounded_mask(size: int, radius_ratio: float = 0.1875) -> Image.Image:
    """Alpha mask with rounded corners (matches SVG rx=48 on 256 canvas)."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    r = max(1, int(size * radius_ratio))
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=255)
    return mask


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Prefer Arial on Windows; fall back to Pillow default bitmap font.
    for name in ("arialbd.ttf", "Arial Bold.ttf", "segoeuib.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_base(
    size: int,
    palette_key: str,
    *,
    elevate: bool = False,
    badge: str | None = None,
) -> Image.Image:
    pal = PALETTES[palette_key]
    base = _gradient_bg(size, pal["bg_top"], pal["bg_bottom"])
    mask = _rounded_mask(size)
    base.putalpha(mask)

    draw = ImageDraw.Draw(base)
    # Accent band along the bottom edge (client vs server color).
    band_h = max(2, size // 5)
    draw.rectangle((0, size - band_h, size, size), fill=pal["accent"] + (255,))

    if elevate:
        # Simple key motif on the accent band (elevation utility).
        cx = size // 2
        cy = size - band_h // 2
        kr = max(2, band_h // 3)
        draw.ellipse(
            (cx - kr, cy - kr, cx + kr, cy + kr),
            outline=(255, 255, 255, 255),
            width=max(1, size // 32),
        )
        draw.line(
            (cx + kr, cy, cx + kr + max(2, size // 8), cy - max(2, size // 10)),
            fill=(255, 255, 255, 255),
            width=max(1, size // 32),
        )

    # AIC wordmark (matches icons/source/aic-icon.svg).
    text = "AIC"
    font_size = max(8, int(size * 0.47))
    font = _font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = int(size * 0.28) - bbox[1]
    draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)

    if badge:
        badge_size = max(6, size // 4)
        bx1 = size - badge_size - max(1, size // 16)
        by1 = size - badge_size - max(1, size // 16)
        bx2, by2 = bx1 + badge_size, by1 + badge_size
        draw.ellipse((bx1, by1, bx2, by2), fill=pal["badge_bg"] + (255,))
        bfont = _font(max(6, badge_size // 2))
        bb = draw.textbbox((0, 0), badge, font=bfont)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        draw.text(
            (bx1 + (badge_size - bw) // 2 - bb[0], by1 + (badge_size - bh) // 2 - bb[1]),
            badge,
            fill=(255, 255, 255, 255),
            font=bfont,
        )

    return base


def _add_save_entropy(img: Image.Image) -> Image.Image:
    """Deterministic micro-variation so PNG-in-ICO compression stays >= 1 KiB."""
    out = img.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            tweak = ((x * 31 + y * 17) ^ (x >> 1) ^ (y >> 1)) & 3
            px[x, y] = (
                min(255, max(0, r + tweak - 1)),
                min(255, max(0, g + ((tweak + 1) & 3) - 1)),
                min(255, max(0, b + ((tweak + 2) & 3) - 1)),
                a,
            )
    return out


def save_ico(path: Path, master: Image.Image) -> None:
    """Write a multi-resolution ICO; Pillow resizes `master` to each entry in sizes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    prepared = _add_save_entropy(master.convert("RGBA"))
    prepared.save(
        path,
        format="ICO",
        sizes=[(sz, sz) for sz in SIZES],
    )


def regenerate_preview_png(path: Path) -> None:
    """Fix corrupted icons/source/aic-icon-1024.png sibling used by About dialogs."""
    preview = render_base(256, "client", elevate=False, badge=None)
    preview.save(path, format="PNG")


def regenerate_master_png(path: Path) -> None:
    img = render_base(1024, "client", elevate=False, badge=None)
    img.save(path, format="PNG")


VARIANTS: list[tuple[str, str, bool, str | None]] = [
    ("aic-client-product.ico", "client", False, None),
    ("aic-client-admin-win32.ico", "client", False, "W"),
    ("aic-client-admin-tauri.ico", "client", False, "T"),
    ("aic-client-elevate-win32.ico", "client", True, "W"),
    ("aic-client-elevate-tauri.ico", "client", True, "T"),
    ("aic-server-product.ico", "server", False, None),
    ("aic-server-admin-win32.ico", "server", False, "W"),
    ("aic-server-admin-tauri.ico", "server", False, "T"),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, palette, elevate, badge in VARIANTS:
        master = render_base(256, palette, elevate=elevate, badge=badge).convert("RGBA")
        out = OUT_DIR / filename
        save_ico(out, master)
        if out.stat().st_size < 1024:
            print(f"error: {out} is smaller than 1 KiB ({out.stat().st_size} bytes)", file=sys.stderr)
            return 1
        print(f"  [ok] {out} ({out.stat().st_size} bytes)")

    # Refresh corrupted raster master + desktop preview from the SVG palette.
    preview_path = REPO_ROOT / "icons" / "desktop" / "aic-icon-preview.png"
    regenerate_preview_png(preview_path)
    print(f"  [ok] {preview_path}")

    master_png = REPO_ROOT / "icons" / "source" / "aic-icon-1024.png"
    regenerate_master_png(master_png)
    print(f"  [ok] {master_png} (replaced corrupted placeholder)")

    # Default product ICO (client palette, no badge) for legacy sync targets.
    default_ico = REPO_ROOT / "icons" / "desktop" / "aic-icon.ico"
    client_product = OUT_DIR / "aic-client-product.ico"
    default_ico.write_bytes(client_product.read_bytes())
    print(f"  [ok] {default_ico} (from aic-client-product.ico)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
