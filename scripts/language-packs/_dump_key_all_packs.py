#!/usr/bin/env python3
"""Print one key across every pack, so a repair can match each pack's own wording.

Repairing a mistranslation is a chance to impose a translator's personal
preference on a pack that had already settled the terminology elsewhere. Reading
the same key in all seventeen packs first shows which packs got it right and what
convention they used, so the fix follows the pack rather than the fixer.

Usage: _dump_key_all_packs.py <namespace> <dotted.key> [--root ui|server]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}


def leaf(obj: dict, dotted: str) -> str | None:
    node = obj
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node.get("text") if isinstance(node, dict) else None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    namespace, key = args
    which = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--root=")), None)
    roots = [ROOTS[which]] if which else list(ROOTS.values())

    for root in roots:
        if not root.is_dir():
            continue
        tags = sorted(p.name for p in root.iterdir() if p.is_dir())
        found = False
        for tag in ["en"] + [t for t in tags if t != "en"]:
            path = root / tag / f"{namespace}.json"
            if not path.is_file():
                continue
            text = leaf(json.loads(path.read_text(encoding="utf-8")), key)
            if text is None:
                continue
            found = True
            print(f"{tag:9s} {text}")
        if found:
            print(f"\n^ {root.name}/{namespace}.json :: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
