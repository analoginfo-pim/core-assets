#!/usr/bin/env python3
"""Find translations that silently dropped the "not Met" honesty clause.

Every pack keeps `Met` as a literal, untranslated status token -- German writes
"ist nicht Met", Japanese writes "Met ではありません", Hebrew writes "אינו Met".
That makes the clause machine-checkable: if the English source contains the token
`Met` and the translation does not, the translator dropped the sentence that says
this page is delivery evidence rather than a satisfied control.

That is not a cosmetic loss. compliance-claims-honesty.mdc forbids implying a
control is Met; a description whose disclaimer was dropped implies exactly that to
every operator reading the product in that language, while the English reviewer
sees a correctly hedged sentence and signs off.

Prints one line per defect so a repair batch can be scoped, and a per-tag count so
the worst pack is obvious.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"

TAGS = (
    "en-GB", "de", "fr", "es", "it", "pt-BR", "nl", "sv", "fi",
    "pl", "tr", "ja", "ko", "zh-Hans", "zh-TW", "he", "ar",
)

# `Met` as a standalone word, so "Meta", "Method", and German "Meldung" do not
# count as the status token.
MET = re.compile(r"(?<![A-Za-z])Met(?![A-Za-z])")


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
    verbose = "--list" in sys.argv
    namespaces = sorted(p.stem for p in (UI / "en").glob("*.json"))

    per_tag: Counter[str] = Counter()
    per_key: Counter[str] = Counter()
    total_sources = 0

    for namespace in namespaces:
        en = load("en", namespace)
        sources = {k: v for k, v in en.items() if MET.search(v)}
        if not sources:
            continue
        total_sources += len(sources)
        packs = {tag: load(tag, namespace) for tag in TAGS}
        for key, en_text in sources.items():
            for tag in TAGS:
                text = packs[tag].get(key)
                if text is None:
                    continue  # absent leaf is the Missing-string defect, not this one
                if MET.search(text):
                    continue
                per_tag[tag] += 1
                per_key[f"{namespace}:{key}"] += 1
                if verbose:
                    print(f"{tag:8s} {namespace}:{key}\n         {text!r}")

    print(f"\n{total_sources} English leaf/leaves carry the `Met` honesty token")
    for tag, count in sorted(per_tag.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:4d}  {tag}")
    print(f"\n{sum(per_tag.values())} translation(s) dropped the clause, across {len(per_key)} key(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
