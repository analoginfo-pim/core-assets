#!/usr/bin/env python3
"""Generate the AIC Enterprise desktop icons from the production mark.

Source: icons/source/aic-mark-512.png, the approved production icon (navy
"AIC" with the line under "AI", on white; see pam-platform-docs
website-and-ui README: "Use the plain AIC mark with the underline; do not
restore the old aqua-bar icon"). The old teal / aqua-bar set is retired.

Every icon is the mark on a white rounded tile. A bottom stripe says who
the program is for:

  - admin  -- amber stripe (--aic-amber #B45309): elevated operator tools,
              the server and agent configurators.
  - user   -- blue stripe (--aic-blue #2359D1): programs an end user runs,
              the elevation request dialogs.
  - none   -- services, agents and the default product icon.

Outputs (all under core-assets, then pushed by sync-to-projects.ps1):

  icons/desktop/installer-shortcuts/*.ico   per-shortcut ICOs
  icons/desktop/aic-icon.ico                default product ICO (no stripe)
  icons/desktop/aic-icon-preview.png        256 px preview (no stripe)
  icons/source/aic-icon-1024.png            1024 px master (no stripe)
  icons/source/aic-icon-admin-1024.png      1024 px master, admin stripe
  icons/source/aic-icon-user-1024.png       1024 px master, user stripe

The Tauri platform trees (icons/tauri for admin apps, icons/tauri-user for
the elevation dialog) are generated from the admin / user masters with
`tauri icon`; see icons/tauri/README.md.

Requires Pillow (pip install pillow).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "icons" / "desktop" / "installer-shortcuts"
MARK_PATH = REPO_ROOT / "icons" / "source" / "aic-mark-512.png"
SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)

NAVY = (0x0F, 0x21, 0x35)          # the mark's own navy
TILE = (0xFF, 0xFF, 0xFF)
BORDER = (0xDC, 0xE3, 0xEC)        # --aic-border
STRIPES = {
    "admin": (0xB4, 0x53, 0x09),   # --aic-amber
    "user": (0x23, 0x59, 0xD1),    # --aic-blue
}

_MARK: Image.Image | None = None


def _mark() -> Image.Image:
    """The mark as a navy glyph, alpha taken from its darkness, cropped tight."""
    global _MARK
    if _MARK is None:
        src = Image.open(MARK_PATH).convert("L")
        # The mark's navy has luminance ~30, so inverted luminance tops out
        # near 225; stretch it so the mark is fully opaque, not 88 percent.
        alpha = src.point(lambda v: min(255, (255 - v) * 255 // 222))
        bbox = alpha.point(lambda v: 255 if v > 24 else 0).getbbox()
        if bbox is None:
            raise SystemExit(f"error: no mark found in {MARK_PATH}")
        alpha = alpha.crop(bbox)
        glyph = Image.new("RGBA", alpha.size, NAVY + (0,))
        glyph.putalpha(alpha)
        _MARK = glyph
    return _MARK


def render(size: int, stripe: str | None) -> Image.Image:
    """One icon frame drawn at its own size, so small frames stay crisp."""
    scale = 4  # supersample the tile shape, then reduce
    big = size * scale
    radius = round(big * 0.1875)
    shape = Image.new("L", (big, big), 0)
    ImageDraw.Draw(shape).rounded_rectangle((0, 0, big - 1, big - 1), radius=radius, fill=255)

    tile = Image.new("RGBA", (big, big), TILE + (255,))
    draw = ImageDraw.Draw(tile)
    stripe_px = 0
    if stripe:
        stripe_px = max(2, round(size * 0.16))
        draw.rectangle((0, big - stripe_px * scale, big, big), fill=STRIPES[stripe] + (255,))
    if size >= 32:
        draw.rounded_rectangle(
            (0, 0, big - 1, big - 1), radius=radius, outline=BORDER + (255,), width=scale
        )
        if stripe:  # the stripe covers the border along the bottom
            draw.rectangle(
                (scale, big - stripe_px * scale, big - 1 - scale, big - 1 - scale),
                fill=STRIPES[stripe] + (255,),
            )
    tile.putalpha(shape)
    tile = tile.resize((size, size), Image.LANCZOS)

    width_ratio = 0.86 if size <= 24 else 0.78
    mark_src = _mark()
    mark_w = max(1, round(size * width_ratio))
    mark_h = max(1, round(mark_src.height * mark_w / mark_src.width))
    mark = mark_src.resize((mark_w, mark_h), Image.LANCZOS)
    field_h = size - stripe_px
    x = (size - mark_w) // 2
    y = max(0, (field_h - mark_h) // 2)
    tile.alpha_composite(mark, (x, y))
    return tile


def _add_save_entropy(img: Image.Image) -> Image.Image:
    """Deterministic micro-variation so PNG-in-ICO compression stays >= 1 KiB."""
    out = img.copy()
    px = out.load()
    w, h = out.size
    for yy in range(h):
        for xx in range(w):
            r, g, b, a = px[xx, yy]
            if a == 0:
                continue
            tweak = ((xx * 31 + yy * 17) ^ (xx >> 1) ^ (yy >> 1)) & 3
            px[xx, yy] = (
                min(255, max(0, r + tweak - 1)),
                min(255, max(0, g + ((tweak + 1) & 3) - 1)),
                min(255, max(0, b + ((tweak + 2) & 3) - 1)),
                a,
            )
    return out


def save_ico(path: Path, stripe: str | None) -> None:
    """Multi-resolution ICO; every frame is rendered at its own size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = [_add_save_entropy(render(sz, stripe)) for sz in SIZES]
    frames[-1].save(
        path,
        format="ICO",
        sizes=[(sz, sz) for sz in SIZES],
        append_images=frames[:-1],
    )


# Shortcut ICO -> stripe. Win32 and Tauri builds of one program look alike.
VARIANTS: list[tuple[str, str | None]] = [
    ("aic-client-product.ico", None),
    ("aic-client-admin-win32.ico", "admin"),
    ("aic-client-admin-tauri.ico", "admin"),
    ("aic-client-elevate-win32.ico", "user"),
    ("aic-client-elevate-tauri.ico", "user"),
    ("aic-server-product.ico", None),
    ("aic-server-admin-win32.ico", "admin"),
    ("aic-server-admin-tauri.ico", "admin"),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, stripe in VARIANTS:
        out = OUT_DIR / filename
        save_ico(out, stripe)
        if out.stat().st_size < 1024:
            print(f"error: {out} is smaller than 1 KiB ({out.stat().st_size} bytes)", file=sys.stderr)
            return 1
        print(f"  [ok] {out} ({out.stat().st_size} bytes)")

    default_ico = REPO_ROOT / "icons" / "desktop" / "aic-icon.ico"
    default_ico.write_bytes((OUT_DIR / "aic-client-product.ico").read_bytes())
    print(f"  [ok] {default_ico} (no stripe)")

    preview = REPO_ROOT / "icons" / "desktop" / "aic-icon-preview.png"
    render(256, None).save(preview, format="PNG")
    print(f"  [ok] {preview}")

    for name, stripe in (
        ("aic-icon-1024.png", None),
        ("aic-icon-admin-1024.png", "admin"),
        ("aic-icon-user-1024.png", "user"),
    ):
        path = REPO_ROOT / "icons" / "source" / name
        render(1024, stripe).save(path, format="PNG")
        print(f"  [ok] {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
