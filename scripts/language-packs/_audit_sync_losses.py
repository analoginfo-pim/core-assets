#!/usr/bin/env python3
"""Report leaves a forward sync removed from the consumer tree, across every
namespace and tag, and say whether the UI code still calls them.

core-assets is the source of truth and the sync overwrites consumers wholesale,
so any key that exists only in the consumer tree is deleted the next time the
sync runs. That already happened once to three feature areas (80 keys, all
seven shipped SPA tags at once) and nothing caught it:

  - i18next falls back to the defaultValue in the code, so en still rendered
    correct English and no missing-string banner appeared.
  - The parity gate's Check 2 asserts en is a subset of each tag. When the key
    leaves en as well, the subset still holds.

The loss is the translation. A German operator reads English on those pages.

_recover_synced_away_leaves.py fixes that class of loss but is scoped to one
namespace. This runs the detection half over all of them, so the check happens
before the commit rather than after an operator notices.

Usage:
    python _audit_sync_losses.py [--ref HEAD] [--tree PATH]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
SERVER = CORE.parent / "pim-offline-server"
LOCALES = Path("ui/src/i18n/locales")
UI_SRC = SERVER / "ui" / "src"


def git_show(ref: str, rel: str, cwd: Path):
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"], cwd=cwd, capture_output=True
    )
    if proc.returncode != 0:
        return None
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(proc.stdout.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


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


def load_corpus() -> list[str]:
    corpus = []
    for path in sorted(UI_SRC.rglob("*.ts*")):
        if "i18n" in path.parts:
            continue
        corpus.append(path.read_text(encoding="utf-8", errors="replace"))
    return corpus


def main() -> int:
    argv = sys.argv[1:]
    ref = argv[argv.index("--ref") + 1] if "--ref" in argv else "HEAD"
    tree = Path(argv[argv.index("--tree") + 1]) if "--tree" in argv else SERVER

    root = tree / LOCALES
    if not root.is_dir():
        print(f"no locales at {root}", file=sys.stderr)
        return 2

    # tag -> namespace -> lost keys
    losses: dict[str, dict[str, list[str]]] = {}
    for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        tag = tag_dir.name
        for path in sorted(tag_dir.glob("*.json")):
            rel = (LOCALES / tag / path.name).as_posix()
            old = git_show(ref, rel, tree)
            if old is None:
                continue
            current = read_json(path)
            if current is None:
                print(f"{tag}/{path.name}: cannot read working tree", file=sys.stderr)
                continue
            lost = sorted(set(leaves(old)) - set(leaves(current)))
            if lost:
                losses.setdefault(tag, {})[path.stem] = lost

    if not losses:
        print(f"no leaves lost against {ref}")
        return 0

    total = sum(len(keys) for ns in losses.values() for keys in ns.values())
    print(f"{total} leaf/leaves lost against {ref}\n")

    per_tag = Counter(
        {tag: sum(len(keys) for keys in ns.values()) for tag, ns in losses.items()}
    )
    for tag, count in per_tag.most_common():
        detail = ", ".join(f"{ns}:{len(keys)}" for ns, keys in sorted(losses[tag].items()))
        print(f"  {count:5d}  {tag:8}  {detail}")

    # Liveness is the question that decides whether this is a regression or a
    # cleanup. Check the union once rather than per tag.
    distinct: set[tuple[str, str]] = {
        (ns, key) for ns_map in losses.values() for ns, keys in ns_map.items() for key in keys
    }
    corpus = load_corpus()
    live = []
    for ns, key in sorted(distinct):
        probe = re.sub(r"\[\d+\]$", "", key)
        if any(probe in text for text in corpus):
            live.append((ns, key))

    print(f"\n{len(distinct)} distinct key(s); {len(live)} still referenced by the UI code")
    if live:
        print("\nLIVE -- removing these ships a translation regression:")
        for ns, key in live[:40]:
            print(f"  {ns} :: {key}")
        if len(live) > 40:
            print(f"  ... +{len(live) - 40} more")
        print(
            "\nRecover from the pre-sync commit (git holds the reviewed translations;\n"
            "re-deriving from defaultValue would replace them with English) and\n"
            "back-port into core-assets so the next sync stops deleting them."
        )
    return 1 if live else 0


if __name__ == "__main__":
    raise SystemExit(main())
