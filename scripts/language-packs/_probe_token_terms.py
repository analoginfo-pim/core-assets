#!/usr/bin/env python3
"""Ask a pack how it already renders one English word, before overwriting it.

A repair that invents its own vocabulary is a second translator's voice bolted
onto the first, and the operator now reads two different words for one concept
with no way to know they mean the same thing. So the question is never "what is
the right Chinese for token" -- it is "what does this pack already say", because
matching the pack's own reviewed majority is provable and inventing is not.

Counts every rendering of the probe word across both locale roots and prints the
distribution, so a minority rendering that disagrees with the pack's own
majority is visible as the outlier it is rather than as a judgment call.

Usage: _probe_token_terms.py <tag> <english-word> [candidate ...]
"""

from __future__ import annotations

import json
import pathlib
import re
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
    return out


def load(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    return flatten(json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip())
        return 2

    tag = sys.argv[1]
    word = sys.argv[2]
    candidates = sys.argv[3:]

    pattern = re.compile(rf"\b{re.escape(word)}s?\b", re.I)
    counts: Counter[str] = Counter()
    examples: dict[str, tuple[str, str, str]] = {}
    unclassified: list[tuple[str, str, str]] = []

    for area in ROOTS:
        base = ROOT / area
        if not base.is_dir():
            continue
        for namespace in sorted(p.stem for p in (base / "en").glob("*.json")):
            english = load(base / "en" / f"{namespace}.json")
            target = load(base / tag / f"{namespace}.json")
            if not target:
                continue
            for key, source in english.items():
                rendered = target.get(key)
                if not rendered or not pattern.search(source):
                    continue
                hit = next((c for c in candidates if c in rendered), None)
                if hit:
                    counts[hit] += 1
                    examples.setdefault(hit, (f"{area}/{namespace}:{key}", source, rendered))
                elif len(source.split()) <= 6:
                    unclassified.append((f"{area}/{namespace}:{key}", source, rendered))

    if candidates:
        print(f"=== {tag} :: how '{word}' is already rendered ===")
        for term, n in counts.most_common():
            where, source, rendered = examples[term]
            print(f"{term:10} {n:4}   {where}")
            print(f"{'':15} en {source!r}")
            print(f"{'':15} {tag} {rendered!r}")
        print()

    if unclassified:
        print(f"=== short leaves using '{word}' with no candidate term ({len(unclassified)}) ===")
        for where, source, rendered in unclassified[:12]:
            print(f"   {where}")
            print(f"      en   {source!r}")
            print(f"      {tag} {rendered!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
