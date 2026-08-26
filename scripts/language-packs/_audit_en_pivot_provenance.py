#!/usr/bin/env python3
"""Ask each en leaf where its text actually came from.

Every leaf carries source_sha256: the hash of the text it was translated
from. For the en catalog that hash should be the English source itself --
en is not translated from anything. When it is not, the hash names the
real parent, and comparing it against the German text is decisive rather
than stylistic: a hash match proves the English was produced from German.

That distinction matters because German-pivoted English does not look
German. It looks like fluent English with the wrong idiom -- "Article 12
Paragraph 3" for "Article 12(3)" (Absatz expanded), a capital letter after
a semicolon, "will be saved upon receipt" for "are stored at intake". A
word-list detector cannot see any of it; the hash can.

Buckets reported:

  self          source_sha256 == sha(own text). Normal for a source catalog.
  german-pivot  source_sha256 == sha(de text). Provably built from German.
  foreign       hash matches some other pack's text.
  orphan        hash matches nothing on disk -- the parent text is gone,
                usually because someone edited a catalog without rehashing.

Usage: _audit_en_pivot_provenance.py [--show-german] [--show-orphan]
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"


def sha(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            yield prefix, node
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def load(tag: str, namespace: str) -> dict[str, str]:
    path = CATALOG / tag / f"{namespace}.json"
    if not path.is_file():
        return {}
    return {k: v["text"] for k, v in leaves(json.loads(path.read_text(encoding="utf-8")))}


def main() -> int:
    show_german = "--show-german" in sys.argv[1:]
    show_orphan = "--show-orphan" in sys.argv[1:]

    tags = sorted(p.name for p in CATALOG.iterdir() if p.is_dir())
    buckets: Counter[str] = Counter()
    german_hits: list[tuple[str, str, str, str]] = []
    orphans: list[tuple[str, str, str]] = []
    foreign_by_tag: Counter[str] = Counter()

    for en_path in sorted((CATALOG / "en").glob("*.json")):
        namespace = en_path.stem
        # Index every text in every pack by hash so an unexplained parent can
        # still be named rather than shrugged at.
        by_hash: dict[str, list[tuple[str, str]]] = defaultdict(list)
        texts: dict[str, dict[str, str]] = {}
        for tag in tags:
            texts[tag] = load(tag, namespace)
            for key, text in texts[tag].items():
                by_hash[sha(text)].append((tag, key))

        german = texts.get("de", {})
        for key, leaf in leaves(json.loads(en_path.read_text(encoding="utf-8"))):
            text = leaf["text"]
            parent = leaf.get("source_sha256")
            if not parent:
                buckets["missing hash"] += 1
                continue
            if parent == sha(text):
                buckets["self"] += 1
                continue

            de_text = german.get(key)
            if de_text is not None and parent == sha(de_text):
                buckets["german-pivot"] += 1
                german_hits.append((namespace, key, de_text, text))
                continue

            owners = [t for t, k in by_hash.get(parent, []) if k == key]
            if owners:
                buckets["foreign"] += 1
                for owner in owners:
                    foreign_by_tag[owner] += 1
                continue

            buckets["orphan"] += 1
            orphans.append((namespace, key, text))

    for label, count in buckets.most_common():
        print(f"  {count:6d}  {label}")

    if foreign_by_tag:
        print("\nnon-en parents named by hash:")
        for tag, count in foreign_by_tag.most_common():
            print(f"  {count:6d}  {tag}")

    if show_german:
        print(f"\n{len(german_hits)} en leaf/leaves built from German:")
        for namespace, key, de_text, en_text in german_hits:
            print(f"  {namespace} :: {key}")
            print(f"      de  {de_text!r}")
            print(f"      en  {en_text!r}")

    if show_orphan:
        print(f"\n{len(orphans)} en leaf/leaves whose parent text is not on disk:")
        for namespace, key, text in orphans[:60]:
            print(f"  {namespace} :: {key}")
            print(f"      {text!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
