#!/usr/bin/env python3
"""Print the keys a pack DID translate in one key family, per pack.

When most of a page shipped in English, the safest source of vocabulary is the
part of that same page the pack already translated: it is the pack's own choice
of word for secret, credential, launch, and start settings, reviewed by whoever
wrote it. Translating the English half from scratch invents a second vocabulary
for the same page. This prints the translated half so the untranslated half can
borrow from it.

Usage: _dump_translated_siblings.py <area> <namespace> <key-prefix> [tag ...]
"""

import json
import pathlib
import sys

ROOT = pathlib.Path("content")


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
    if len(sys.argv) < 4:
        print(
            "usage: _dump_translated_siblings.py <area> <namespace> <key-prefix> [tag ...]",
            file=sys.stderr,
        )
        return 2
    area, namespace, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    only = set(sys.argv[4:])

    base = ROOT / area
    english = load(base / "en" / f"{namespace}.json")
    family = {k: v for k, v in english.items() if k.startswith(prefix)}
    tags = sorted(p.name for p in base.iterdir() if p.is_dir() and p.name != "en")
    if only:
        tags = [t for t in tags if t in only]

    for tag in tags:
        pack = load(base / tag / f"{namespace}.json")
        translated = {
            k: pack[k] for k in family if k in pack and pack[k] != family[k]
        }
        print(f"\n===== {tag}  ({len(translated)} translated) =====")
        for key in sorted(translated):
            print(f"  {key}")
            print(f"    en  {family[key]}")
            print(f"    {tag:6} {translated[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
