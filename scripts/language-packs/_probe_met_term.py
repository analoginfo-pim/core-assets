#!/usr/bin/env python3
"""Print how each pack already renders the compliance status words.

New strings that end in "not Met" must reuse whatever noun the packs already use
for that status, or the same concept appears under two names in one UI -- which
reads to an assessor as two different concepts.
"""

from __future__ import annotations

import json
from pathlib import Path

UI = Path(__file__).resolve().parents[2] / "content" / "locales-ui"
TAGS = (
    "en-GB", "de", "fr", "es", "it", "pt-BR", "nl", "sv", "fi",
    "pl", "tr", "ja", "ko", "zh-Hans", "zh-TW", "he", "ar",
)
WANTED = {"met", "not met", "partially met", "partial", "not applicable"}


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
    hits: dict[str, list[tuple[str, str]]] = {}
    for path in sorted((UI / "en").glob("*.json")):
        for key, text in load("en", path.stem).items():
            if text.strip().lower() in WANTED:
                hits.setdefault(text.strip(), []).append((path.stem, key))

    for english, places in sorted(hits.items()):
        namespace, key = places[0]
        print(f"\n=== {english!r}  ({len(places)} site(s), sampling {namespace}:{key})")
        for tag in TAGS:
            print(f"  {tag:8s} {load(tag, namespace).get(key)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
