#!/usr/bin/env python3
"""Find leaves whose bytes were decoded with the wrong code page (mojibake).

Turkish `ot:gridStatusHelp` ships as
`Envanterden/ke┼ƒiften teslimat durumu (Canl─▒, K─▒smi veya ENGELLENM─░┼₧)`. Those
box-drawing glyphs are UTF-8 bytes for `ş`, `ı`, and `İŞ` that some tool read as
cp437 and then re-encoded as UTF-8. The pack is valid UTF-8 today, so no JSON or
encoding check catches it -- only a reader of that language notices, and no one
reads Turkish during an English review.

The test is a round trip, not a glyph blocklist: take the text, encode it back to
the suspected legacy code page, decode the result as UTF-8, and require that the
result differs and contains no replacement characters. A string that survives that
round trip was mojibake; ordinary text cannot be, because ordinary text either
fails to encode in the legacy page or fails to decode as UTF-8 afterwards.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"

# cp437 is the DOS OEM page PowerShell pipes still default to on this host; cp1252
# is the classic Windows-ANSI mis-read that yields "Ã©" for "é".
LEGACY_PAGES = ("cp437", "cp1252", "cp850")


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    if out is None:
        out = {}
    for k, v in (obj or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            out[key] = v["text"]
        elif isinstance(v, dict):
            flatten(v, key, out)
    return out


def repaired(text: str) -> tuple[str, str] | None:
    """Return (page, decoded) when `text` round-trips as mojibake, else None."""
    for page in LEGACY_PAGES:
        try:
            raw = text.encode(page)
        except UnicodeEncodeError:
            continue
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if decoded != text and "\ufffd" not in decoded:
            return page, decoded
    return None


def main() -> int:
    verbose = "--list" in sys.argv
    hits = 0
    for tag_dir in sorted(p for p in UI.iterdir() if p.is_dir()):
        for path in sorted(tag_dir.glob("*.json")):
            for key, text in flatten(json.loads(path.read_text(encoding="utf-8"))).items():
                # ASCII-only text can round-trip trivially; it is never mojibake.
                if text.isascii():
                    continue
                found = repaired(text)
                if not found:
                    continue
                page, decoded = found
                hits += 1
                print(f"{tag_dir.name}/{path.name}  {key}   [{page}]")
                if verbose:
                    print(f"    is:     {text!r}")
                    print(f"    should: {decoded!r}")
    print(f"\n{hits} leaf/leaves are wrong-code-page mojibake")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
