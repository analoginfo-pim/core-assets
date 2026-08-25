#!/usr/bin/env python3
"""List the English sources behind the German-pivot salad, sized for repair.

_audit_german_salad.py counts leaves (key x language). What a repair actually
needs is the distinct English strings, because each one is translated once per
affected language. Prints them grouped by namespace with a character budget so the
work can be split into batches that are reviewable rather than a single 1200-line
dump.

`--json` emits {namespace: {key: {"en": text, "tags": [...]}}} for a generator to
consume.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
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
    as_json = "--json" in sys.argv
    include_germanic = "--germanic" in sys.argv
    tags = sorted(p.name for p in UI.iterdir() if p.is_dir())
    result: dict[str, dict] = {}

    for namespace in sorted(p.stem for p in (UI / "en").glob("*.json")):
        en = load("en", namespace)
        de = load("de", namespace)
        if not de:
            continue
        packs = {t: load(t, namespace) for t in tags if t not in SKIP}

        for key, en_text in en.items():
            de_text = de.get(key)
            if not de_text:
                continue
            german_only = tokens(de_text) - tokens(en_text)
            if len(german_only) < 3:
                continue
            hit_tags = []
            for tag, pack in packs.items():
                if tag in GERMANIC and not include_germanic:
                    continue
                text = pack.get(key)
                if not text or nfc(text) == nfc(de_text):
                    continue
                words = tokens(text)
                if words and len(words & german_only) / len(words) >= THRESHOLD:
                    hit_tags.append(tag)
            if hit_tags:
                result.setdefault(namespace, {})[key] = {
                    "en": en_text,
                    "tags": sorted(hit_tags),
                }

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    grand_keys = grand_leaves = grand_chars = 0
    for namespace, entries in sorted(result.items()):
        chars = sum(len(e["en"]) for e in entries.values())
        leaves = sum(len(e["tags"]) for e in entries.values())
        grand_keys += len(entries)
        grand_leaves += leaves
        grand_chars += chars
        print(f"\n### {namespace}: {len(entries)} key(s), {leaves} leaf/leaves, {chars} en chars")
        for key, entry in sorted(entries.items(), key=lambda kv: -len(kv[1]["en"])):
            print(f"  [{len(entry['tags']):2d} tags] {key}")
            print(f"      {entry['en'][:150]!r}")

    print(f"\n=== {grand_keys} distinct English string(s), {grand_leaves} leaf/leaves, {grand_chars} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
