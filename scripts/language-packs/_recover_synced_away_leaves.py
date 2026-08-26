#!/usr/bin/env python3
"""Recover catalog leaves a forward sync deleted, and back-port them to source.

core-assets is the source of truth and the sync overwrites the consumer tree
wholesale, so a key that lives only in the consumer is a key waiting to be
deleted. Three feature areas were authored straight into
pim-offline-server/ui/src/i18n/locales and never back-synced:

    enclaveRegularUsers.*                      51 leaves  EnclaveRegularUsersPage
    chrome.accessControl.classificationGov.*   18 leaves  ClassificationPanel
    chrome.operatingLevel.* (partial)          11 leaves  SettingsPage

All seven shipped SPA tags carried reviewed translations for them. The next sync
removed all seven at once. Nothing broke visibly: i18next falls back to the
defaultValue in the code, so en still rendered correct English and the parity
gate stayed green because Check 2 only asserts en is a subset of each tag -- when
the key leaves en as well, the subset still holds.

What was lost is the translation. A German operator now reads English on those
three pages, which is the residue class this work has been chasing.

Recovery reads the pre-sync commit rather than the code, because git holds the
real reviewed de / fr / es / zh-Hans / zh-TW text. Re-deriving from defaultValue
would replace six packs of reviewed translation with English and call it a fix.

Existing leaves are never overwritten -- the same sync that deleted these also
delivered a genuine German-leak fix, and that must survive.

Usage:
    python _recover_synced_away_leaves.py [--ref HEAD~1] [--fix]
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
SERVER = CORE.parent / "pim-offline-server"
CATALOG = CORE / "content" / "locales-ui"
SERVER_LOCALES = Path("ui/src/i18n/locales")

# The SPA gate's shipped set. Other core-assets packs never held these keys, so
# they are a queue item, not a recovery target.
SPA_TAGS = ["en", "en-GB", "de", "fr", "es", "zh-Hans", "zh-TW"]

NAMESPACE = "pages"


def git_show(ref: str, path: str) -> dict | None:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=SERVER,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(proc.stdout.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def leaf_paths(node, prefix=()):
    """Yield tuple paths to leaves. A leaf is a string, or {text, source_sha256}."""
    if isinstance(node, str):
        yield prefix
        return
    if isinstance(node, dict):
        keys = set(node)
        if "text" in keys and keys <= {"text", "source_sha256"}:
            yield prefix
            return
        for name, child in node.items():
            yield from leaf_paths(child, prefix + (name,))
        return
    if isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaf_paths(child, prefix + (index,))


def get_at(root, path: tuple):
    node = root
    for step in path:
        node = node[step]
    return node


def put_at(root, path: tuple, value) -> str | None:
    """Insert value at path, creating dicts. Returns a reason string on refusal."""
    node = root
    for depth, step in enumerate(path[:-1]):
        if isinstance(step, int):
            # Restoring into a list position the current tree does not have is
            # not a merge, it is a guess about ordering. Refuse.
            if not isinstance(node, list) or step >= len(node):
                return f"list index {step} absent at {'.'.join(map(str, path[:depth]))}"
            node = node[step]
            continue
        if not isinstance(node, dict):
            return f"non-dict at {'.'.join(map(str, path[:depth]))}"
        child = node.get(step)
        if child is None:
            child = {}
            node[step] = child
        elif isinstance(child, dict) and "text" in child and set(child) <= {
            "text",
            "source_sha256",
        }:
            return f"leaf blocks ancestor {'.'.join(map(str, path[: depth + 1]))}"
        node = child
    last = path[-1]
    if isinstance(last, int):
        return f"list tail index {last}"
    if not isinstance(node, dict):
        return "non-dict parent"
    if last in node:
        return "already present"
    node[last] = copy.deepcopy(value)
    return None


def main() -> int:
    argv = sys.argv[1:]
    write = "--fix" in argv
    ref = argv[argv.index("--ref") + 1] if "--ref" in argv else "HEAD~1"

    total_restored = 0
    refusals: list[str] = []
    recovered_keys: set[tuple] = set()

    for tag in SPA_TAGS:
        rel = (SERVER_LOCALES / tag / f"{NAMESPACE}.json").as_posix()
        old = git_show(ref, rel)
        if old is None:
            print(f"{tag:8} skip -- no {rel} at {ref}")
            continue
        server_path = SERVER / rel
        current = read_json(server_path)
        if current is None:
            print(f"{tag:8} skip -- cannot read working tree {rel}")
            continue

        old_paths = set(leaf_paths(old))
        new_paths = set(leaf_paths(current))
        lost = sorted(old_paths - new_paths, key=lambda p: tuple(map(str, p)))
        if not lost:
            print(f"{tag:8} nothing lost")
            continue

        placed = 0
        for path in lost:
            reason = put_at(current, path, get_at(old, path))
            if reason:
                refusals.append(f"{tag} {'.'.join(map(str, path))}: {reason}")
            else:
                placed += 1
                recovered_keys.add(path)

        print(f"{tag:8} {len(lost):3} lost, {placed:3} restorable")
        total_restored += placed

        if write and placed:
            server_path.write_text(
                json.dumps(current, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            # Back-port to core-assets so the next forward sync stops deleting
            # them. This is the half that was missing all along.
            core_path = CATALOG / tag / f"{NAMESPACE}.json"
            core = read_json(core_path)
            if core is None:
                refusals.append(f"{tag}: no core-assets {NAMESPACE}.json to back-port into")
                continue
            back = 0
            for path in lost:
                if put_at(core, path, get_at(old, path)) is None:
                    back += 1
            if back:
                core_path.write_text(
                    json.dumps(core, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(f"{'':8} back-ported {back} into core-assets/{tag}")

    print(f"\n{total_restored} leaf/leaves {'restored' if write else 'would be restored'}")
    if refusals:
        print(f"\n{len(refusals)} refusal(s):")
        for line in refusals[:40]:
            print(f"  {line}")
        if len(refusals) > 40:
            print(f"  ... +{len(refusals) - 40} more")

    if recovered_keys:
        groups: dict[str, int] = {}
        for path in recovered_keys:
            head = ".".join(map(str, path[:2]))
            groups[head] = groups.get(head, 0) + 1
        print("\nrecovered key groups (per tag):")
        for head, count in sorted(groups.items(), key=lambda kv: -kv[1]):
            print(f"  {count:4}  {head}")
        print(
            f"\n{len(recovered_keys)} distinct keys are absent from the 11 non-SPA "
            f"core-assets packs and need a localization-work row."
        )

    if not write:
        print("\n(report only; pass --fix to restore and back-port)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
