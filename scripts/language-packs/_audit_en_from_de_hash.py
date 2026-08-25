#!/usr/bin/env python3
"""Prove which en / en-GB leaves were translated from German, not authored.

Every leaf carries source_sha256, the hash of the text it was translated from.
So provenance is checkable rather than guessable: if an en leaf's stored hash
equals the hash of the *German* pack's text for the same key, that leaf was
produced from German. English is supposed to be the source, so an en leaf whose
source is German is a pivot inversion -- the defect that shipped
"Getrennte / luftgekapte Hosts nutzen weiterhin lokale ... Konfiguratoren."
as the default-locale string.

The test is exact. It never compares words, spelling, or "does this look
German" -- only two hex digests. A hit is evidence.

Usage:
    python _audit_en_from_de_hash.py [--show-all] [--tag en-GB]
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"


def digest(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def leaves(node, prefix=""):
    """Yield (dotted-path, leaf-dict) for every {text, source_sha256} leaf."""
    if isinstance(node, dict):
        if "text" in node and isinstance(node.get("text"), str):
            yield prefix, node
            return
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{prefix}[{index}]")


def load(tag: str) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    directory = CATALOG / tag
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"  ! {tag}/{path.name}: {exc}", file=sys.stderr)
            continue
        for dotted, leaf in leaves(data):
            out[(path.stem, dotted)] = leaf
    return out


def main() -> int:
    argv = sys.argv[1:]
    show_all = "--show-all" in argv
    tag = "en"
    if "--tag" in argv:
        tag = argv[argv.index("--tag") + 1]

    german = load("de")
    target = load(tag)
    if not german:
        print("de pack not found", file=sys.stderr)
        return 1

    # Hash of the German text, keyed the same way, so a lookup is one step.
    de_hash = {key: digest(leaf["text"]) for key, leaf in german.items()}

    hits: list[tuple[str, str, str, str]] = []
    for key, leaf in target.items():
        stored = leaf.get("source_sha256") or ""
        if not stored or key not in de_hash:
            continue
        if stored == de_hash[key]:
            # Self-consistent English would hash to its own text.
            if stored == digest(leaf["text"]):
                continue
            hits.append((key[0], key[1], leaf["text"], german[key]["text"]))

    print(
        f"{len(hits)} {tag} leaf/leaves carry a source hash equal to the German text\n"
        f"({len(target)} leaves scanned against {len(german)} German leaves)"
    )
    if not hits:
        return 0

    by_ns = Counter(namespace for namespace, _, _, _ in hits)
    print("\nby namespace:")
    for namespace, count in by_ns.most_common():
        print(f"  {count:5d}  {namespace}")

    print()
    shown = hits if show_all else hits[:30]
    for namespace, dotted, text, de_text in shown:
        print(f"  {namespace} :: {dotted}")
        print(f"     {tag}: {text[:150]}")
        print(f"     de: {de_text[:150]}")
    if not show_all and len(hits) > len(shown):
        print(f"\n  ... {len(hits) - len(shown)} more (--show-all)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
