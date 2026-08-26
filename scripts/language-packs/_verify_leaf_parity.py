#!/usr/bin/env python3
"""Compare the leaf key sets of two catalog JSON files.

A fix that rewrites a whole catalog file with json.dumps can produce a very
large line diff for a two-leaf change, because the original formatting is not
reproduced byte for byte. That diff size is harmless -- unless a leaf actually
went missing. This answers only that question: same keys before and after?

Usage:
    python _verify_leaf_parity.py <before.json> <after.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            yield prefix
            return
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{prefix}[{index}]")


def read(path: Path):
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise SystemExit(f"cannot decode {path}")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    before = set(leaves(read(Path(sys.argv[1]))))
    after = set(leaves(read(Path(sys.argv[2]))))
    print(f"before {len(before)} leaves, after {len(after)} leaves")
    lost = sorted(before - after)
    gained = sorted(after - before)
    if lost:
        print(f"LOST {len(lost)}:")
        for key in lost[:20]:
            print(f"  {key}")
    if gained:
        print(f"gained {len(gained)}:")
        for key in gained[:20]:
            print(f"  {key}")
    if not lost and not gained:
        print("identical key sets")
    return 1 if lost else 0


if __name__ == "__main__":
    raise SystemExit(main())
