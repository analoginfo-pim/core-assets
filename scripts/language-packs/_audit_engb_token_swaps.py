#!/usr/bin/env python3
"""Frequency table of en -> en-GB word swaps the UK spelling rules do not explain.

Re-deriving en-GB from en is the obvious repair for a pack that was paraphrased
instead of derived, but it is only safe if the rule table knows every genuine UK
spelling in the pack. If it does not, re-derivation quietly deletes real British
orthography and replaces it with American, which is a worse defect than the one
being fixed.

So: before rewriting anything, list every word substitution actually present,
with its frequency. A swap that appears hundreds of times across unrelated files
is a systematic rule -- either a UK spelling the table is missing, or a bad pass
that needs reverting. A swap that appears once is a paraphrase. Both are visible
here, and the decision about which is which is made by reading the list, not by
a heuristic.

Only leaves whose en and en-GB token counts match are considered, so a paraphrase
that added or removed words does not produce spurious one-to-one pairs.

Usage: _audit_engb_token_swaps.py [--min N]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _audit_engb_derivation import ROOTS, TOKEN, leaves, uk_forms


def main() -> int:
    argv = sys.argv[1:]
    minimum = int(argv[argv.index("--min") + 1]) if "--min" in argv else 1

    swaps: dict[tuple[str, str], int] = {}
    where: dict[tuple[str, str], str] = {}

    for area, root in ROOTS.items():
        en_dir, gb_dir = root / "en", root / "en-GB"
        if not (en_dir.is_dir() and gb_dir.is_dir()):
            continue
        for en_path in sorted(en_dir.glob("*.json")):
            gb_path = gb_dir / en_path.name
            if not gb_path.is_file():
                continue
            english = dict(leaves(json.loads(en_path.read_text(encoding="utf-8"))))
            british = dict(leaves(json.loads(gb_path.read_text(encoding="utf-8"))))
            for key, gb_text in british.items():
                en_text = english.get(key)
                if en_text is None or en_text == gb_text:
                    continue
                en_tokens = TOKEN.findall(en_text)
                gb_tokens = TOKEN.findall(gb_text)
                if len(en_tokens) != len(gb_tokens):
                    continue
                for a, b in zip(en_tokens, gb_tokens):
                    if a == b or b.lower() in uk_forms(a):
                        continue
                    pair = (a, b)
                    swaps[pair] = swaps.get(pair, 0) + 1
                    where.setdefault(pair, f"{area}/{en_path.stem} :: {key}")

    ranked = sorted(swaps.items(), key=lambda kv: (-kv[1], kv[0]))
    shown = [(pair, count) for pair, count in ranked if count >= minimum]

    print(f"{len(ranked)} distinct unexplained swap(s), {sum(swaps.values())} occurrence(s)")
    print(f"showing {len(shown)} with count >= {minimum}\n")
    for (a, b), count in shown:
        print(f"  {count:5d}  {a!r} -> {b!r}")
        if count < 5:
            print(f"           {where[(a, b)]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
