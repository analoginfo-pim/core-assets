#!/usr/bin/env python3
"""Find leaves whose English contains a phrase, and print each pack's rendering.

Repairing or authoring a single string is a guess unless the pack has already
translated the same idea somewhere else. This finds those places by English
substring, then prints the translated text beside it, so the new string can
borrow the pack's own wording for "the password stays in the vault", "recorded
session", and "never shown on screen" instead of inventing three new phrasings.

Usage: _find_phrase_donors.py "<english substring>" [tag ...]
"""

import json
import pathlib
import sys

ROOT = pathlib.Path("content")
AREAS = ("locales-ui", "locales")


def flat(obj, prefix="", out=None):
    out = {} if out is None else out
    for key, value in (obj or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and isinstance(value.get("text"), str):
            out[path] = value["text"]
        elif isinstance(value, dict):
            flat(value, path, out)
    return out


def load(path):
    return flat(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    if len(sys.argv) < 2:
        print('usage: _find_phrase_donors.py "<english substring>" [tag ...]', file=sys.stderr)
        return 2
    needle = sys.argv[1].lower()
    only = set(sys.argv[2:])

    for area in AREAS:
        base = ROOT / area
        if not (base / "en").is_dir():
            continue
        tags = sorted(p.name for p in base.iterdir() if p.is_dir() and p.name != "en")
        if only:
            tags = [t for t in tags if t in only]
        for namespace_path in sorted((base / "en").glob("*.json")):
            namespace = namespace_path.stem
            english = load(namespace_path)
            matches = {k: v for k, v in english.items() if needle in v.lower()}
            if not matches:
                continue
            packs = {tag: load(base / tag / f"{namespace}.json") for tag in tags}
            for key, text in matches.items():
                print(f"\n{area}/{namespace}:{key}")
                print(f"   en     {text}")
                for tag in tags:
                    rendered = packs[tag].get(key)
                    if rendered:
                        print(f"   {tag:8} {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
