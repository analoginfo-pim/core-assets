#!/usr/bin/env python3
"""Find leaves that are German text wearing a thin coat of the target language.

The byte-identical detector in _count_wrong_language.py only catches a leaf that
reproduces the German translation exactly. It misses the worse failure, where a
German pivot was run through a word-by-word substitution and the result is neither
language:

    fr  "Erweiterte Steuerungen listen jede the Produkt bekannte erweiterte
         Anforderung aus NIST SP 800-172 sowie the benannten ..."

A handful of French and English function words were swapped in, so the string is
not identical to German and slips through. To an operator it is unreadable.

The test avoids a hand-written German dictionary, which would be both incomplete
and wrong about cognates. Instead, for each key it takes the tokens present in the
German translation and absent from the English source -- those are the words German
contributed, so NIST, SP, 800-172, CMMC, and Live drop out automatically because
they appear in English too. If a non-German pack's translation of the same key is
built mostly out of that German-only vocabulary, the German pivot leaked through.

Reported as a ratio so the threshold is arguable and the evidence is printed;
`--list` shows each offending string next to its English source.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")

# Germanic packs share real vocabulary with German, so a high overlap there can be
# legitimate; they are reported separately rather than trusted or ignored.
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


def load(root: Path, tag: str, namespace: str) -> dict:
    path = root / tag / f"{namespace}.json"
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    verbose = "--list" in sys.argv
    per_pack: Counter[str] = Counter()
    per_key: Counter[str] = Counter()
    germanic_hits: Counter[str] = Counter()

    for root in ROOTS:
        if not root.is_dir():
            continue
        tags = sorted(p.name for p in root.iterdir() if p.is_dir())
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            en = load(root, "en", namespace)
            de = load(root, "de", namespace)
            if not de:
                continue
            packs = {t: load(root, t, namespace) for t in tags if t not in SKIP}

            for key, en_text in en.items():
                de_text = de.get(key)
                if not de_text:
                    continue
                german_only = tokens(de_text) - tokens(en_text)
                # Too little German-specific vocabulary to judge on.
                if len(german_only) < 3:
                    continue

                for tag, pack in packs.items():
                    text = pack.get(key)
                    if not text or nfc(text) == nfc(de_text):
                        continue  # absent, or the identical-leak case already counted
                    words = tokens(text)
                    if not words:
                        continue
                    ratio = len(words & german_only) / len(words)
                    if ratio < THRESHOLD:
                        continue
                    label = f"{root.name}/{tag}/{namespace}.json"
                    if tag in GERMANIC:
                        germanic_hits[label] += 1
                        continue
                    per_pack[label] += 1
                    per_key[f"{namespace}:{key}"] += 1
                    if verbose:
                        print(f"\n{tag:8s} {namespace}:{key}   ({ratio:.0%} German-only vocabulary)")
                        print(f"  en  {en_text[:200]!r}")
                        print(f"  {tag:3s} {text[:200]!r}")

    print(f"\n--- non-Germanic packs (German pivot leaked through) ---")
    for label, count in sorted(per_pack.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{count:5d}  {label}")
    print(f"{sum(per_pack.values())} leaf/leaves across {len(per_key)} key(s)")

    print(f"\n--- Germanic packs (overlap can be real vocabulary; needs a read) ---")
    for label, count in sorted(germanic_hits.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{count:5d}  {label}")
    print(f"{sum(germanic_hits.values())} leaf/leaves flagged")

    print(f"\nworst keys:")
    for key, count in per_key.most_common(15):
        print(f"{count:5d}  {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
