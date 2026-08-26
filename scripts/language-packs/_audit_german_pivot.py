#!/usr/bin/env python3
"""Find pack leaves that were translated from the German pack instead of English.

A leaf records `source_sha256`: the hash of the source text it was translated
from. When that hash equals the hash of the *German* text rather than the
English text, the leaf was built by pivoting through German. The evidence is
exact -- no heuristic, no word list.

Pivoting through German is not a cosmetic problem. Packs that pivoted did one
of three things, all of which a native reader spots immediately:

  copied     the German verbatim   (it/nl/pl/pt-BR/tr "Nur Herunterladen")
  transliterated it phonetically   (zh-Hans "努尔赫伦特拉登", ko "누르 헤룬터라덴")
  mistranslated a German homograph (compliance "Met" read as the verb "meet")

Leaves where German and English are identical are skipped: matching a shared
identifier such as "Server" or "Token" proves nothing about provenance.

Pivoting is provable; damage is not uniformly provable. A competent translator
working from German can still land correct target text (es "Solo descarga" is
right despite pivoting). So --classify splits the finding into what is provably
broken and what needs a native reader:

  verbatim    the pack ships the German string unchanged -- provably wrong
  review      pivoted, target text differs from the German -- needs a native

Transliteration hides inside "review": it cannot be proven mechanically, which
is exactly why those packs need a native reader rather than another script.

Usage:
  _audit_german_pivot.py [--namespace pages] [--verbose] [--classify]
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
PIVOT = "de"
SOURCE = "en"


def sha(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def leaves(node, prefix=""):
    """Yield (dotted.key, leaf_dict) for every {"text": ...} leaf."""
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            yield prefix, node
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def load(tag: str, namespace: str):
    path = CATALOG / tag / f"{namespace}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    argv = sys.argv[1:]
    verbose = "--verbose" in argv
    only = None
    if "--namespace" in argv:
        only = argv[argv.index("--namespace") + 1]

    namespaces = sorted(p.stem for p in (CATALOG / SOURCE).glob("*.json"))
    if only:
        namespaces = [n for n in namespaces if n == only]

    tags = sorted(
        p.name
        for p in CATALOG.iterdir()
        if p.is_dir() and p.name not in {SOURCE, PIVOT}
    )

    per_tag: Counter[str] = Counter()
    per_key: Counter[str] = Counter()
    findings: list[tuple[str, str, str, str, str]] = []

    for namespace in namespaces:
        en_data = load(SOURCE, namespace)
        de_data = load(PIVOT, namespace)
        if en_data is None or de_data is None:
            continue

        en_text = {key: leaf["text"] for key, leaf in leaves(en_data)}
        de_text = {key: leaf["text"] for key, leaf in leaves(de_data)}

        # Only keys where German actually diverges from English can prove a pivot.
        de_hash = {
            key: sha(text)
            for key, text in de_text.items()
            if en_text.get(key) is not None and text != en_text[key]
        }
        if not de_hash:
            continue

        for tag in tags:
            data = load(tag, namespace)
            if data is None:
                continue
            for key, leaf in leaves(data):
                want = de_hash.get(key)
                if want is None:
                    continue
                if leaf.get("source_sha256") != want:
                    continue
                per_tag[tag] += 1
                per_key[f"{namespace} :: {key}"] += 1
                findings.append((tag, namespace, key, de_text[key], leaf["text"]))

    if verbose:
        for tag, namespace, key, german, shipped in sorted(findings):
            print(f"  [{tag}] {namespace} :: {key}")
            print(f"      german   {german!r}")
            print(f"      shipped  {shipped!r}")

    if "--classify" in argv:
        verbatim: Counter[str] = Counter()
        review: Counter[str] = Counter()
        for tag, _ns, _key, german, shipped in findings:
            if shipped.casefold() == german.casefold():
                verbatim[tag] += 1
            else:
                review[tag] += 1
        print("\n  pack   verbatim-German   needs-native-review")
        for tag, _ in per_tag.most_common():
            print(f"  {tag:8s} {verbatim[tag]:>10d} {review[tag]:>20d}")
        print(f"\n{sum(verbatim.values())} leaf/leaves ship untranslated German (provably wrong)")
        print(f"{sum(review.values())} leaf/leaves pivoted but differ -- native review required")

    print("\nleaves translated from German, by pack:")
    for tag, count in per_tag.most_common():
        print(f"  {tag:8s} {count}")

    print("\nmost-pivoted keys:")
    for key, count in per_key.most_common(20):
        print(f"  {count:3d} packs  {key}")

    total = sum(per_tag.values())
    print(f"\n{total} leaf/leaves across {len(per_tag)} packs were built from German")
    print(f"{len(per_key)} distinct key(s) affected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
