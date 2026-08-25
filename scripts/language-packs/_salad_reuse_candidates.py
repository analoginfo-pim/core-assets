#!/usr/bin/env python3
"""Find salad leaves repairable by reusing a clean translation of the same English.

A drafted translation is an agent's opinion and cannot close a localization-work
item. A translation already shipping in the same pack for the byte-identical
English source is not an opinion -- it is that pack's own settled wording, so
copying it onto a salad leaf is a provable repair and keeps terminology
consistent by construction.

For every salad leaf this looks for another leaf in the same pack whose English
source is identical (NFC) and whose translation is clean, then reports how much of
the 1247 can be closed that way. Where several clean donors disagree, the leaf is
reported as ambiguous rather than guessed at.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"

GERMANIC = {"nl", "sv", "fi", "en-GB"}
SKIP = {"en", "de"}
WORD = re.compile(r"[^\W\d_]{3,}", re.UNICODE)
THRESHOLD = 0.34


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def tokens(text: str) -> set[str]:
    return {nfc(m.group(0)).casefold() for m in WORD.finditer(text)}


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    if out is None:
        out = {}
    for k, v in (obj or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            out[key] = v["text"]
        elif isinstance(v, dict):
            flatten(v, key, out)
    return out


def load(tag: str, namespace: str) -> dict:
    path = UI / tag / f"{namespace}.json"
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    tags = sorted(p.name for p in UI.iterdir() if p.is_dir())
    namespaces = sorted(p.stem for p in (UI / "en").glob("*.json"))

    en_all: dict[str, dict[str, str]] = {n: load("en", n) for n in namespaces}
    de_all: dict[str, dict[str, str]] = {n: load("de", n) for n in namespaces}
    pack_all: dict[str, dict[str, dict[str, str]]] = {
        t: {n: load(t, n) for n in namespaces} for t in tags if t not in SKIP
    }

    # Which (namespace, key) leaves are salad, per tag.
    salad: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for namespace in namespaces:
        en, de = en_all[namespace], de_all[namespace]
        for key, en_text in en.items():
            de_text = de.get(key)
            if not de_text:
                continue
            german_only = tokens(de_text) - tokens(en_text)
            if len(german_only) < 3:
                continue
            for tag, packs in pack_all.items():
                if tag in GERMANIC:
                    continue
                text = packs[namespace].get(key)
                if not text or nfc(text) == nfc(de_text):
                    continue
                words = tokens(text)
                if words and len(words & german_only) / len(words) >= THRESHOLD:
                    salad[tag].add((namespace, key))

    reusable: Counter[str] = Counter()
    ambiguous: Counter[str] = Counter()
    orphan: Counter[str] = Counter()
    examples: list[str] = []

    for tag, leaves in salad.items():
        # Index this pack's clean translations by their English source.
        by_english: dict[str, set[str]] = defaultdict(set)
        for namespace in namespaces:
            for key, en_text in en_all[namespace].items():
                if (namespace, key) in leaves:
                    continue
                text = pack_all[tag][namespace].get(key)
                if not text:
                    continue
                by_english[nfc(en_text)].add(nfc(text))

        for namespace, key in sorted(leaves):
            source = nfc(en_all[namespace][key])
            donors = by_english.get(source, set())
            if not donors:
                orphan[tag] += 1
            elif len(donors) == 1:
                reusable[tag] += 1
                if len(examples) < 8:
                    examples.append(
                        f"{tag:8s} {namespace}:{key}\n"
                        f"    en    {source[:110]!r}\n"
                        f"    is    {nfc(pack_all[tag][namespace][key])[:110]!r}\n"
                        f"    reuse {next(iter(donors))[:110]!r}"
                    )
            else:
                ambiguous[tag] += 1

    print("tag      reusable  ambiguous  no-donor")
    for tag in sorted(salad):
        print(f"{tag:8s} {reusable[tag]:8d}  {ambiguous[tag]:9d}  {orphan[tag]:8d}")
    print(
        f"\n{sum(reusable.values())} leaf/leaves repairable by exact-English reuse, "
        f"{sum(ambiguous.values())} ambiguous, {sum(orphan.values())} need a translation"
    )
    if examples:
        print("\nexamples:")
        for line in examples:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
