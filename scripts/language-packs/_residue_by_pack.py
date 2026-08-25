#!/usr/bin/env python3
"""Count, per pack, how many keys in one family are still byte-identical to English.

The sizing script answers "how big is this family's residue" but its pack count is
a threshold, so repairing four packs out of fifteen leaves the headline number
unchanged and progress looks like nothing happened. This prints the per-pack
column instead, which is the number that actually moves when a batch lands.

Usage: _residue_by_pack.py <area> <namespace> <key-prefix>
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
            "usage: _residue_by_pack.py <area> <namespace> <key-prefix>",
            file=sys.stderr,
        )
        return 2
    area, namespace, prefix = sys.argv[1], sys.argv[2], sys.argv[3]

    base = ROOT / area
    english = load(base / "en" / f"{namespace}.json")
    family = sorted(k for k in english if k.startswith(prefix))
    tags = sorted(p.name for p in base.iterdir() if p.is_dir() and p.name != "en")

    print(f"{len(family)} key(s) in {area}/{namespace}:{prefix}*\n")
    rows = []
    for tag in tags:
        pack = load(base / tag / f"{namespace}.json")
        same = [k for k in family if pack.get(k) == english[k]]
        missing = [k for k in family if k not in pack]
        rows.append((len(same), len(missing), tag))

    rows.sort(reverse=True)
    for same, missing, tag in rows:
        note = f"  ({missing} absent)" if missing else ""
        bar = "#" * round(same / max(1, len(family)) * 40)
        print(f"  {tag:7} {same:3}/{len(family)} English  {bar}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
