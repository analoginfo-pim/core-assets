#!/usr/bin/env python3
"""Ask each pack how it already ends a sentence with a compliance disclaimer.

Sixteen of the eighteen tile descriptions being added close with one of four
honesty clauses -- "Not Met.", "Not Met and not certified.", "An attestation is
not Met and is not certified.", "not Met." -- and those clauses are the reason
the tiles exist. Drafting them freshly per pack would put a second translator's
voice next to the first, and an operator comparing two tiles would read two
different disclaimers for one legal statement.

So the clause is not translated. It is looked up: find English leaves that
already end this way, show what each pack ended them with, and reuse that.

Prints the tail after the last sentence boundary so the disclaimer is visible
without the leading prose it happens to be attached to.

Usage: _probe_clause_tails.py "<english tail>" [...]
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path("content")
ROOTS = ("locales-ui", "locales")


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    out = {} if out is None else out
    for key, value in (obj or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and isinstance(value.get("text"), str):
            out[path] = value["text"]
        elif isinstance(value, dict):
            flatten(value, path, out)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    out[f"{path}[{i}]"] = item["text"]
    return out


def load(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    return flatten(json.loads(path.read_text(encoding="utf-8")))


def tail(text: str) -> str:
    """Last sentence, by the widest set of terminators the packs actually use."""
    best = 0
    for mark in (". ", "。", "! ", "؟ ", "\u2014 "):
        idx = text.rfind(mark, 0, max(len(text) - 1, 0))
        if idx > best:
            best = idx + len(mark)
    return text[best:].strip()


def main() -> int:
    wanted = sys.argv[1:]
    if not wanted:
        print(__doc__.strip())
        return 2
    tags = sorted(p.name for p in (ROOT / "locales-ui").iterdir() if p.is_dir())
    for want in wanted:
        print(f"===== English tail: {want!r} =====")
        hits: dict[str, Counter[str]] = {t: Counter() for t in tags}
        example = None
        for area in ROOTS:
            base = ROOT / area
            if not base.is_dir():
                continue
            for namespace in sorted(p.stem for p in (base / "en").glob("*.json")):
                english = load(base / "en" / f"{namespace}.json")
                keys = [k for k, v in english.items() if v.rstrip().endswith(want)]
                if not keys:
                    continue
                example = example or f"{area}/{namespace}:{keys[0]}"
                for tag in tags:
                    pack = load(base / tag / f"{namespace}.json")
                    for key in keys:
                        if pack.get(key):
                            hits[tag][tail(pack[key])] += 1
        print(f"   (example source: {example})")
        for tag in tags:
            if tag == "en":
                continue
            counter = hits[tag]
            if not counter:
                print(f"   {tag:8} -- no leaf ends this way")
                continue
            top, n = counter.most_common(1)[0]
            spread = f" [{len(counter)} variants]" if len(counter) > 1 else ""
            print(f"   {tag:8} {n:3}x{spread}  {top}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
