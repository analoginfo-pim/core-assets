#!/usr/bin/env python3
"""List leaves present in one catalog file but absent from another, and say
whether the UI source code still calls them.

A deletion pass that removes "dead" keys is only safe if the keys really are
dead. This re-checks that claim against the code for a specific before/after
pair, so a live key removed by mistake is named rather than discovered by an
operator seeing a missing string.

Usage:
    python _probe_lost_keys.py <namespace> <before.json> <after.json>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

UI_SRC = (
    Path(__file__).resolve().parents[3] / "pim-offline-server" / "ui" / "src"
)


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
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    namespace, before_path, after_path = sys.argv[1], sys.argv[2], sys.argv[3]
    before = set(leaves(read(Path(before_path))))
    after = set(leaves(read(Path(after_path))))
    lost = sorted(before - after)
    if not lost:
        print("nothing lost")
        return 0

    # One pass over the source, then substring tests per key. Keys are dotted
    # and distinctive enough that a plain containment test is reliable here.
    corpus: list[tuple[Path, str]] = []
    for path in sorted(UI_SRC.rglob("*.ts*")):
        if "i18n" in path.parts:
            continue
        corpus.append((path, path.read_text(encoding="utf-8", errors="replace")))

    live: list[tuple[str, str]] = []
    dead: list[str] = []
    for key in lost:
        # Strip a trailing array index; code references the array, not the item.
        probe = re.sub(r"\[\d+\]$", "", key)
        hit = next((p.name for p, text in corpus if probe in text), None)
        if hit:
            live.append((key, hit))
        else:
            dead.append(key)

    print(f"{len(lost)} leaves lost from {namespace}: {len(live)} LIVE, {len(dead)} dead")
    if live:
        print("\nLIVE (code still calls these -- removing them ships a missing string):")
        for key, where in live:
            print(f"  {key}   <- {where}")
    if dead:
        print(f"\ndead ({len(dead)}):")
        for key in dead:
            print(f"  {key}")
    return 1 if live else 0


if __name__ == "__main__":
    raise SystemExit(main())
