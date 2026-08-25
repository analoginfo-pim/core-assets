#!/usr/bin/env python3
"""Size one key family's untranslated English so the repair can be planned.

Deciding whether to repair a page by hand or queue it for native review needs
two numbers the residue audit does not give: how many characters have to be
written, and whether any pack already translated the same key so the vocabulary
can be borrowed rather than invented. This prints both for a key prefix.

Usage: _size_namespace_residue.py <area> <namespace> <key-prefix> [min_packs]
Example: _size_namespace_residue.py locales-ui pages secureLaunch. 10
"""

import json
import pathlib
import sys

ROOT = pathlib.Path("content")
NEVER_EVIDENCE = {"en", "en-GB"}


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
            "usage: _size_namespace_residue.py <area> <namespace> <key-prefix> [min_packs]",
            file=sys.stderr,
        )
        return 2
    area, namespace, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    min_packs = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    base = ROOT / area
    english = load(base / "en" / f"{namespace}.json")
    tags = sorted(
        p.name for p in base.iterdir() if p.is_dir() and p.name not in NEVER_EVIDENCE
    )
    packs = {tag: load(base / tag / f"{namespace}.json") for tag in tags}

    rows = []
    for key, text in sorted(english.items()):
        if not key.startswith(prefix):
            continue
        same = [t for t in tags if packs[t].get(key) == text]
        if len(same) < min_packs:
            continue
        donors = [t for t in tags if key in packs[t] and packs[t][key] != text]
        rows.append((len(text), key, len(same), donors))

    rows.sort()
    chars = sum(row[0] for row in rows)
    with_donor = sum(1 for row in rows if row[3])
    print(f"{len(rows)} key(s) English in {min_packs}+ packs")
    print(f"{chars} English characters; {chars * 15} to write across 15 packs")
    print(f"{with_donor} of them already translated in at least one pack\n")
    for length, key, count, donors in rows:
        donor_note = ("donors: " + ",".join(donors)) if donors else "NO DONOR"
        print(f"{length:5}  [{count} packs English]  {key}   {donor_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
