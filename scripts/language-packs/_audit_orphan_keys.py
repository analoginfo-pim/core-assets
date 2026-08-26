#!/usr/bin/env python3
"""Find catalog keys that exist in a translated pack but not in English.

en is the source catalog, so a key present in fr but absent from en is an
orphan: no English text was ever written for it. Two very different things
produce that shape, and they need opposite fixes, so guessing is not an
option.

  live    the code really does call t('ns:key'), and en is simply missing
          the entry. Deleting it would strip the translation and leave the
          operator on the code literal. The fix is to add it to en.

  dead    the code never calls it. Usually a key that moved namespace and
          left a copy behind -- common:technical.downloadOpenApi is one, a
          stale duplicate of docs:technical.downloadOpenApi that still
          shipped 'OpenAPI-JSON herunterladen' in the British pack, where
          nothing would ever render it and no reviewer would ever look.
          The fix is to delete it everywhere.

Dead keys are worse than they sound. They are unreachable, so no amount of
UI testing finds them, and they still count toward parity and still show up
in translation batches -- paying a vendor to translate strings the product
cannot display.

--fix deletes the dead ones. Live ones are only reported: adding English
text is an authoring decision, not something to synthesise here.

Usage: _audit_orphan_keys.py [--fix] [--show-live]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"
UI_SRC = ROOT.parent / "pim-offline-server" / "ui" / "src"

# Any t('...') / t("...") reference, with or without a defaultValue, because
# the question here is only "does the code ever ask for this key".
REF = re.compile(r"""\bt\(\s*(['"`])([^'"`\n]+?)\1""")
USE_NS = re.compile(r"""useTranslation\(\s*(['"])(?P<ns>[^'"]+)\1""")


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            yield prefix, node
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def code_keys() -> set[tuple[str, str]]:
    """(namespace, key) for every t() the UI performs."""
    seen: set[tuple[str, str]] = set()
    for path in sorted(UI_SRC.rglob("*.ts*")):
        if "i18n" in path.parts:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        if "t(" not in source:
            continue
        file_ns = USE_NS.search(source)
        fallback = file_ns.group("ns") if file_ns else None
        for _, raw in REF.findall(source):
            if "{" in raw or "$" in raw or " " in raw:
                continue
            if ":" in raw:
                namespace, key = raw.split(":", 1)
                seen.add((namespace, key))
            elif fallback:
                seen.add((fallback, raw))
    return seen


def drop(node, parts: list[str]) -> bool:
    """Delete a dotted path, pruning any dict left empty behind it."""
    head, rest = parts[0], parts[1:]
    if head not in node:
        return False
    if not rest:
        del node[head]
        return True
    child = node[head]
    if not isinstance(child, dict) or not drop(child, rest):
        return False
    if not child:
        del node[head]
    return True


def main() -> int:
    write = "--fix" in sys.argv[1:]
    show_live = "--show-live" in sys.argv[1:]

    if not UI_SRC.is_dir():
        print(f"no UI source at {UI_SRC}", file=sys.stderr)
        return 2

    used = code_keys()
    tags = sorted(p.name for p in CATALOG.iterdir() if p.is_dir() and p.name != "en")

    # namespace -> key -> tags carrying it without an en counterpart
    orphans: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for en_path in sorted((CATALOG / "en").glob("*.json")):
        namespace = en_path.stem
        english = {k for k, _ in leaves(json.loads(en_path.read_text(encoding="utf-8")))}
        for tag in tags:
            path = CATALOG / tag / f"{namespace}.json"
            if not path.is_file():
                continue
            for key, _ in leaves(json.loads(path.read_text(encoding="utf-8"))):
                if key not in english:
                    orphans[namespace][key].append(tag)

    live: list[tuple[str, str, int]] = []
    dead: list[tuple[str, str, int]] = []
    for namespace, keys in orphans.items():
        for key, carriers in keys.items():
            bucket = live if (namespace, key) in used else dead
            bucket.append((namespace, key, len(carriers)))

    removed = 0
    if write and dead:
        by_ns: dict[str, set[str]] = defaultdict(set)
        for namespace, key, _ in dead:
            by_ns[namespace].add(key)
        for tag in tags:
            for namespace, keys in by_ns.items():
                path = CATALOG / tag / f"{namespace}.json"
                if not path.is_file():
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                dirty = False
                for key in keys:
                    if drop(data, key.split(".")):
                        removed += 1
                        dirty = True
                if dirty:
                    path.write_text(
                        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

    print(f"{len(live)} orphan key(s) the code DOES call -- en needs the English text")
    if show_live:
        for namespace, key, count in sorted(live):
            print(f"  {namespace} :: {key}  ({count} pack(s) have a translation)")

    print(f"\n{len(dead)} orphan key(s) the code never calls -- unreachable")
    for namespace, key, count in sorted(dead)[:40]:
        print(f"  {namespace} :: {key}  ({count} pack(s))")
    if len(dead) > 40:
        print(f"  ... and {len(dead) - 40} more")

    if write:
        print(f"\n{removed} leaf/leaves deleted across {len(tags)} pack(s)")
    else:
        total = sum(count for _, _, count in dead)
        print(f"\n{total} leaf/leaves would be deleted (--fix to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
