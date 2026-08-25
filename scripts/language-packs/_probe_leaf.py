#!/usr/bin/env python3
"""Print one leaf across every pack, in both catalog trees, with hashes.

There are two catalog trees -- the core-assets source of truth and the copy
synced into the server UI -- and a defect can live in one but not the other.
Comparing them side by side, with the stored source_sha256 next to the hash of
the leaf's own text, shows at a glance whether a leaf is self-consistent
(authored) or carries someone else's hash (translated, and from what).

Usage:
    python _probe_leaf.py <namespace> <dotted.path>
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "content" / "locales-ui"
UI = Path(__file__).resolve().parents[3] / "pim-offline-server" / "ui" / "src" / "i18n" / "locales"


def digest(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def get(node, dotted: str):
    """Resolve a dotted path, tolerating [n] array indices."""
    for part in dotted.replace("[", ".").replace("]", "").split("."):
        if part == "":
            continue
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    namespace, dotted = sys.argv[1], sys.argv[2]

    for label, root in (("core-assets", CORE), ("ui/src/i18n", UI)):
        print(f"=== {label}  {namespace} :: {dotted}")
        if not root.is_dir():
            print("   (tree absent)")
            continue
        for pack in sorted(p for p in root.iterdir() if p.is_dir()):
            path = pack / f"{namespace}.json"
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"  {pack.name:8s} ! invalid json")
                continue
            leaf = get(data, dotted)
            if leaf is None:
                continue
            if isinstance(leaf, dict) and isinstance(leaf.get("text"), str):
                text = leaf["text"]
                stored = leaf.get("source_sha256") or ""
                own = digest(text)
                mark = "self" if stored == own else (stored[:8] if stored else "(no hash)")
                print(f"  {pack.name:8s} [{mark}] {text[:120]}")
            else:
                print(f"  {pack.name:8s} (not a leaf: {type(leaf).__name__})")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
