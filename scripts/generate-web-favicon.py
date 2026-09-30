"""Generate the public-website favicon set from the master AIC icon.

Writes, next to icons/web/favicon.svg:
  favicon.ico      16, 32, and 48 px frames, PNG-compressed (never BMP/DIB)
  favicon-32.png   32 x 32 fallback
  webclip-256.png  256 x 256 home-screen (webclip) icon

Usage: python scripts/generate-web-favicon.py
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "icons" / "source" / "aic-icon-1024.png"
OUT = ROOT / "icons" / "web"
PNG_MAGIC = b"\x89PNG"


def main() -> int:
    if not SOURCE.is_file():
        print(f"source icon missing: {SOURCE}", file=sys.stderr)
        return 1
    master = Image.open(SOURCE).convert("RGBA")

    ico_path = OUT / "favicon.ico"
    master.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    frames = ico_path.read_bytes().count(PNG_MAGIC)
    if frames < 3:
        print(f"favicon.ico has {frames} PNG frames; expected 3", file=sys.stderr)
        return 1

    master.resize((32, 32), Image.LANCZOS).save(OUT / "favicon-32.png", format="PNG")
    master.resize((256, 256), Image.LANCZOS).save(OUT / "webclip-256.png", format="PNG")

    for name in ("favicon.ico", "favicon-32.png", "webclip-256.png"):
        print(f"{name} {(OUT / name).stat().st_size} bytes")
    print(f"favicon.ico PNG frames: {frames}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
