#!/usr/bin/env python3
"""Show existing sentences that carry the honesty phrase "not Met".

The 17 new section-landing descriptions all end in some form of "not Met and not
certified". That phrasing already ships elsewhere, so the new translations should
reuse the wording the packs settled on rather than inventing a second rendering of
the same disclaimer.
"""

from __future__ import annotations

import json
from pathlib import Path

UI = Path(__file__).resolve().parents[2] / "content" / "locales-ui"
TAGS = ("de", "fr", "es", "ja", "zh-Hans", "he")


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


def load(tag: str, namespace: str) -> dict:
    path = UI / tag / f"{namespace}.json"
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    shown = 0
    for path in sorted((UI / "en").glob("*.json")):
        for key, text in load("en", path.stem).items():
            low = text.lower()
            if "not met" not in low and "is not certified" not in low:
                continue
            if shown >= 6:
                return 0
            shown += 1
            print(f"\n=== {path.stem}:{key}\n  en       {text!r}")
            for tag in TAGS:
                print(f"  {tag:8s} {load(tag, path.stem).get(key)!r}")
    if shown == 0:
        print("no existing 'not Met' / 'is not certified' sentence in the en packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
