#!/usr/bin/env python3
"""Count leaves that are byte-identical to another pack's translation.

A leaf whose text equals the German text and differs from the English source was
not translated into its own language -- the value was copied from the pack the MT
pass pivoted through. That is provable from the packs alone: no dictionary, no
language-detection heuristic, no false positives from cognates, because a French
cognate of a German word is not byte-identical to the whole German sentence.

Reports per (tag, namespace) so a repair batch can be scoped to one file, plus the
donor tag each leak came from, because a leak from `de` and a leak from `en` need
different fixes: the first is a pivot artifact, the second is an untranslated
leaf.
"""

from __future__ import annotations

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"

# Latin-script packs only. A zh / ar / he leaf equal to German is caught by the
# untranslated-leaf audit instead, and mixing the two hides which pipeline broke.
DONORS = ("de",)


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
    if not path.is_file():
        return {}
    return flatten(json.loads(path.read_text(encoding="utf-8")))


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def main() -> int:
    tags = sorted(p.name for p in UI.iterdir() if p.is_dir())
    namespaces = sorted({p.stem for tag in tags for p in (UI / tag).glob("*.json")})
    only = set(sys.argv[1:])

    # A single German token can legitimately be the correct Germanic-language word
    # ("Aktiv" is right in both de and sv while en says "Active"), so a one-word
    # match is only suspicious. A whole German sentence reproduced verbatim in a
    # Swedish pack cannot be a coincidence.
    per_pack: Counter[tuple[str, str]] = Counter()
    cognate: Counter[tuple[str, str]] = Counter()
    total = 0
    maybe = 0

    for namespace in namespaces:
        en = load("en", namespace)
        donors = {d: load(d, namespace) for d in DONORS}
        for tag in tags:
            if tag in DONORS or tag in ("en",):
                continue
            if only and tag not in only:
                continue
            current = load(tag, namespace)
            for key, text in current.items():
                en_text = en.get(key)
                if en_text is None or nfc(text) == nfc(en_text):
                    continue
                for donor_map in donors.values():
                    donor_text = donor_map.get(key)
                    if donor_text is None or nfc(text) != nfc(donor_text):
                        continue
                    if len(text.split()) >= 2:
                        per_pack[(tag, namespace)] += 1
                        total += 1
                    else:
                        cognate[(tag, namespace)] += 1
                        maybe += 1
                    break

    for (tag, namespace), count in sorted(per_pack.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{count:5d}  {tag}/{namespace}.json")
    print(
        f"\n{total} multi-word leaf/leaves reproduce a {'/'.join(DONORS)} translation verbatim "
        f"(provably wrong language)"
    )
    print(f"{maybe} single-token match(es) -- possible legitimate cognate, needs a native read")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
