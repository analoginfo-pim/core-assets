#!/usr/bin/env python3
"""Assert core-assets holds every leaf the consumer catalog holds.

The sync copies core-assets over the consumer wholesale, so the sync is only
non-destructive while that containment holds. When it does not, the sync is a
silent deletion: i18next falls back to the code's defaultValue, so English
still renders and no missing-string banner appears -- but every translated pack
lost the key, and a German operator reads English on that page.

The parity gate cannot see this. Check 2 asserts en is a subset of each tag; a
key that leaves en *and* every tag together keeps that subset intact.

Run this before any forward sync. A non-empty report means back-port first.

Usage:
    python _audit_core_superset.py [--tree PATH] [--show-all]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
CATALOG = CORE / "content" / "locales-ui"
SERVER = CORE.parent / "pim-offline-server"
LOCALES = Path("ui/src/i18n/locales")


def read_json(path: Path):
    if not path.is_file():
        return None
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def leaves(node, prefix=""):
    """A leaf is a bare string, or {text} / {text, source_sha256}."""
    if isinstance(node, str):
        yield prefix
        return
    if isinstance(node, dict):
        if isinstance(node.get("text"), str) and set(node) <= {"text", "source_sha256"}:
            yield prefix
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
        return
    if isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def main() -> int:
    argv = sys.argv[1:]
    tree = Path(argv[argv.index("--tree") + 1]) if "--tree" in argv else SERVER
    show_all = "--show-all" in argv

    root = tree / LOCALES
    if not root.is_dir():
        print(f"no consumer locales at {root}", file=sys.stderr)
        return 2

    # tag -> namespace -> keys the consumer has and core-assets does not
    gaps: dict[str, dict[str, list[str]]] = {}
    missing_files: list[str] = []

    for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        tag = tag_dir.name
        for path in sorted(tag_dir.glob("*.json")):
            consumer = read_json(path)
            if consumer is None:
                print(f"{tag}/{path.name}: cannot read", file=sys.stderr)
                continue
            core = read_json(CATALOG / tag / path.name)
            if core is None:
                missing_files.append(f"{tag}/{path.name}")
                continue
            extra = sorted(set(leaves(consumer)) - set(leaves(core)))
            if extra:
                gaps.setdefault(tag, {})[path.stem] = extra

    if missing_files:
        print(f"{len(missing_files)} consumer file(s) have no core-assets counterpart:")
        for name in missing_files:
            print(f"  {name}")
        print()

    if not gaps:
        print("core-assets is a superset of the consumer catalog; the sync is safe")
        return 0 if not missing_files else 1

    total = sum(len(keys) for ns in gaps.values() for keys in ns.values())
    print(f"{total} consumer leaf/leaves are absent from core-assets -- the next sync deletes them\n")

    per_tag = Counter(
        {tag: sum(len(keys) for keys in ns.values()) for tag, ns in gaps.items()}
    )
    for tag, count in per_tag.most_common():
        detail = ", ".join(f"{ns}:{len(keys)}" for ns, keys in sorted(gaps[tag].items()))
        print(f"  {count:5d}  {tag:8}  {detail}")

    distinct = sorted(
        {(ns, key) for ns_map in gaps.values() for ns, keys in ns_map.items() for key in keys}
    )
    print(f"\n{len(distinct)} distinct key(s)")
    shown = distinct if show_all else distinct[:30]
    for ns, key in shown:
        print(f"  {ns} :: {key}")
    if not show_all and len(distinct) > len(shown):
        print(f"  ... +{len(distinct) - len(shown)} more (--show-all)")
    print("\nBack-port with _recover_synced_away_leaves.py before syncing.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
