#!/usr/bin/env python3
"""Replace one clause inside a leaf, proving nothing else moved.

The batch applier swaps a whole leaf. Fixing one wrong clause in a seven-paragraph
boilerplate would mean resubmitting the entire paragraph set, and hand-retyping
that much text to change six words is how a targeted repair silently becomes an
accidental retranslation of everything around it.

This edits the clause and nothing else. The old substring must appear exactly once
-- zero means the pack already changed and the caller's assumption is stale, more
than one means the caller cannot say which occurrence they meant, and both are
refusals rather than guesses. `source_sha256` is left alone because the English
source did not change; only the translation of it did.

Usage: _replace_clause.py <tag>:<namespace>:<dotted.key> <old> <new> [--apply]
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def node_for(obj: dict, dotted: str) -> dict | None:
    node = obj
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) and isinstance(node.get("text"), str) else None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    if len(args) != 3:
        print(__doc__)
        return 2
    spec, old, new = args
    tag, namespace, key = spec.split(":", 2)
    old, new = nfc(old), nfc(new)

    for root in ROOTS:
        path = root / tag / f"{namespace}.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        node = node_for(data, key)
        if node is None:
            continue
        text = nfc(node["text"])
        hits = text.count(old)
        if hits != 1:
            print(f"REFUSED {spec}: old clause occurs {hits}x, expected exactly 1")
            return 1
        updated = text.replace(old, new)
        if PLACEHOLDER.findall(text) != PLACEHOLDER.findall(updated):
            print(f"REFUSED {spec}: placeholder set would change")
            return 1
        print(f"{'APPLY ' if apply else 'DRY   '}{spec}")
        print(f"  -  {old}")
        print(f"  +  {new}")
        if apply:
            node["text"] = updated
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        return 0

    print(f"REFUSED {spec}: leaf not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
