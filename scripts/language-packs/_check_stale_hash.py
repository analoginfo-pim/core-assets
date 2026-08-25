#!/usr/bin/env python3
"""Ask whether a leaf's stored source hash still matches today's English.

Every leaf records `source_sha256`, the hash of the English text it was translated
from. That is the drift alarm: when English is edited, the stored hash stops
matching and the translation is knowingly stale. But the alarm is only useful if
someone reads it, and a stale hash that nobody acts on is indistinguishable from
no alarm at all.

The distinction matters for triage. A stale hash means the translation was once
correct and English moved underneath it -- ordinary, expected, and the drift gate
already knows. A *current* hash on a wrong translation is worse: the pack is
asserting "this is a faithful rendering of exactly this English", and it is not.
Nothing downstream can detect that, which is why it needs a human.

Usage: _check_stale_hash.py <namespace>:<dotted.key> [...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from language_packs import source_sha256  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")


def node_for(obj: dict, dotted: str) -> dict | None:
    node = obj
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) and isinstance(node.get("text"), str) else None


def main() -> int:
    specs = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not specs:
        print(__doc__)
        return 2

    for spec in specs:
        namespace, key = spec.split(":", 1)
        for root in ROOTS:
            en_path = root / "en" / f"{namespace}.json"
            if not en_path.is_file():
                continue
            en_node = node_for(json.loads(en_path.read_text(encoding="utf-8")), key)
            if en_node is None:
                continue
            want = source_sha256(en_node["text"])
            print(f"\n===== {root.name}/{namespace}.json :: {key}")
            print(f"  english hash today: {want[:16]}")
            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                tag = tag_dir.name
                if tag == "en":
                    continue
                path = tag_dir / f"{namespace}.json"
                if not path.is_file():
                    continue
                node = node_for(json.loads(path.read_text(encoding="utf-8")), key)
                if node is None:
                    continue
                got = node.get("source_sha256") or ""
                verdict = "CURRENT (claims faithful)" if got == want else "stale"
                print(f"  {tag:9s} {got[:16] or '(none)':18s} {verdict}")
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
