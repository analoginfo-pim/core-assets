#!/usr/bin/env python3
"""Print the full text of specific leaves, so a long paragraph can be repaired in place.

The batch applier replaces a whole leaf, not a substring. Repairing one wrong clause
inside a six-sentence paragraph therefore means resubmitting the entire paragraph,
and retyping it from a truncated audit line is how a targeted fix turns into an
accidental retranslation. This prints each requested leaf untruncated so the clause
can be edited against the real bytes.

Usage: _dump_leaves.py <tag>:<namespace>:<dotted.key> [...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")


def leaf(obj: dict, dotted: str) -> str | None:
    node = obj
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node.get("text") if isinstance(node, dict) else None


def main() -> int:
    specs = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not specs:
        print(__doc__)
        return 2
    for spec in specs:
        tag, namespace, key = spec.split(":", 2)
        for root in ROOTS:
            path = root / tag / f"{namespace}.json"
            if not path.is_file():
                continue
            text = leaf(json.loads(path.read_text(encoding="utf-8")), key)
            if text is None:
                continue
            print(f"\n===== {tag} :: {root.name}/{namespace}.json :: {key}")
            print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
