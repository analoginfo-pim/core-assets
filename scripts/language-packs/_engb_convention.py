#!/usr/bin/env python3
"""Report the UK-variance convention the en-GB pack actually uses.

Before re-deriving en-GB leaves from en, we need to know what "derive" means
here -- which words this pack genuinely spells differently, and which it leaves
alone. Inventing a rule set risks manufacturing divergence, which is the defect
that corrupted this pack in the first place.

Method: look only at leaves that are correctly sourced (source_sha256 matches
the English text they claim to come from) and report every word-level
difference against en. That is the convention, observed rather than assumed.

Usage: _engb_convention.py
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


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


def main() -> int:
    swaps: Counter[tuple[str, str]] = Counter()
    identical = 0
    diverged = 0
    unsourced = 0

    for path in sorted((CATALOG / "en").glob("*.json")):
        gb_path = CATALOG / "en-GB" / path.name
        if not gb_path.is_file():
            continue
        en_leaves = {k: v["text"] for k, v in leaves(json.loads(path.read_text(encoding="utf-8")))}
        gb_data = json.loads(gb_path.read_text(encoding="utf-8"))

        for key, leaf in leaves(gb_data):
            english = en_leaves.get(key)
            if english is None:
                continue
            # Only trust leaves that claim to derive from this exact English.
            if leaf.get("source_sha256") != sha(english):
                unsourced += 1
                continue
            if leaf["text"] == english:
                identical += 1
                continue
            diverged += 1

            a, b = WORD.findall(english), WORD.findall(leaf["text"])
            for op, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b).get_opcodes():
                if op == "replace" and (i2 - i1) == (j2 - j1):
                    for x, y in zip(a[i1:i2], b[j1:j2]):
                        swaps[(x, y)] += 1

    print(f"correctly sourced and identical to en : {identical}")
    print(f"correctly sourced and diverged        : {diverged}")
    print(f"not sourced from current en           : {unsourced}")
    # Casing is never a UK/US difference, so split it out: a swap that survives
    # casefolding is a spelling or lexical choice, one that does not is casing.
    spelling = {p: n for p, n in swaps.items() if p[0].casefold() != p[1].casefold()}
    casing = {p: n for p, n in swaps.items() if p[0].casefold() == p[1].casefold()}

    print(f"\ncase-only swaps: {sum(casing.values())} across {len(casing)} word pairs")
    print("word-level swaps (en -> en-GB), case-insensitive:")
    for (x, y), count in sorted(spelling.items(), key=lambda kv: -kv[1]):
        print(f"  {count:4d}  {x}  ->  {y}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
