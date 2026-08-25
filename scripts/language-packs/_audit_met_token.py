#!/usr/bin/env python3
"""Audit how the compliance status token `Met` was rendered in each pack.

`Met` is assessment vocabulary: a requirement is Met, Not Met, or Partial. It is
also, unfortunately, the past tense of an ordinary English verb and the nickname of
a New York museum, and a machine translator with no glossary picks whichever it
likes. The product's central honesty disclaimer -- "the product never reports Met"
-- therefore ships as "I have never met [a person]" in six languages and as "the
Metropolitan Museum of Art" in both Chinese packs.

That is not a style problem. `compliance-claims-honesty.mdc` makes the disclaimer
load-bearing, and an assessor reading the Portuguese pack cannot find it.

This classifies rather than merely flags, because the three outcomes need different
handling: a domain rendering is correct and must be left alone, a social rendering
is a mistranslation to repair, and a missing clause is a content-loss defect. The
vocabularies below are the renderings actually found in these packs, not a general
dictionary -- `--list` prints every leaf so a native reviewer can confirm the call.
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

# "requirement fulfilled" -- the correct assessment sense.
DOMAIN = {
    "de": ("erfüllt", "erfuellt"),
    "es": ("cumplid", "cumple", "satisfech"),
    "fr": ("satisfait", "rempli", "respecté", "conforme"),
    "it": ("soddisfatt", "adempiut"),
    "pt-BR": ("atendid", "cumprid", "satisfeit"),
    "nl": ("voldaan", "vervuld"),
    "sv": ("uppfyll", "uppnå"),
    "fi": ("täytett", "täyttyy", "saavutet"),
    "pl": ("spełni", "spelni"),
    "tr": ("karşılan", "karsilan", "sağlan"),
    "ja": ("満た", "充足"),
    "ko": ("충족", "달성"),
    "zh-Hans": ("满足", "达标", "符合"),
    "zh-TW": ("滿足", "達標", "符合"),
    "he": ("עומד", "מתקיים", "התקיים"),
    "ar": ("استيفاء", "مستوف", "تحقيق", "الوفاء", "يفي"),
    "en-GB": ("met",),
}

# "encountered a person" / a proper noun -- the wrong sense.
SOCIAL = {
    "de": ("getroffen", "begegnet"),
    "es": ("conocid", "encontrad"),
    "fr": ("rencontré", "connu"),
    "it": ("incontrat", "conosciut"),
    "pt-BR": ("conheci", "conhecid", "encontrei"),
    "nl": ("ontmoet", "gezien"),
    "sv": ("träffad", "träffat", "mött"),
    "fi": ("tavattu", "tapasi"),
    "pl": ("spotkał", "spotkan", "poznał"),
    "tr": ("tanış", "karşılaş", "buluş"),
    "ja": ("会っ", "出会", "メット"),
    "ko": ("만나", "만난", "만났"),
    "zh-Hans": ("大都会", "见过", "遇到", "会面"),
    "zh-TW": ("大都會", "見過", "遇到", "會面"),
    "he": ("נפגש", "פגש", "הכיר"),
    "ar": ("يلتق", "التق", "قابل"),
}

# The token as its own word, so "Metropolitan" or "method" in English does not match.
MET = re.compile(r"(?<![A-Za-z])Met(?![A-Za-z])")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


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


def has(text: str, needles: tuple[str, ...]) -> bool:
    low = nfc(text).casefold()
    return any(n.casefold() in low for n in needles)


def main() -> int:
    verbose = "--list" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--verdict=")), None)

    counts: Counter[tuple[str, str]] = Counter()
    rows: list[tuple[str, str, str, str, str]] = []

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            en = load(root, "en", namespace)
            carriers = {k: v for k, v in en.items() if MET.search(v)}
            if not carriers:
                continue
            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                tag = tag_dir.name
                if tag == "en":
                    continue
                pack = load(root, tag, namespace)
                for key, en_text in carriers.items():
                    text = pack.get(key)
                    if not text:
                        continue
                    if MET.search(text):
                        verdict = "literal"  # token kept as-is; acceptable
                    elif has(text, SOCIAL.get(tag, ())):
                        verdict = "SOCIAL"  # wrong sense -- repair
                    elif has(text, DOMAIN.get(tag, ())):
                        verdict = "domain"  # correct sense
                    else:
                        verdict = "MISSING"  # clause absent -- content loss
                    counts[(tag, verdict)] += 1
                    rows.append((verdict, tag, f"{namespace}:{key}", en_text, text))

    tags = sorted({t for t, _ in counts})
    print(f"{'tag':9s} {'literal':>8s} {'domain':>8s} {'SOCIAL':>8s} {'MISSING':>8s}")
    for tag in tags:
        print(
            f"{tag:9s} {counts[(tag,'literal')]:8d} {counts[(tag,'domain')]:8d} "
            f"{counts[(tag,'SOCIAL')]:8d} {counts[(tag,'MISSING')]:8d}"
        )
    bad = sum(v for (_, verdict), v in counts.items() if verdict == "SOCIAL")
    gone = sum(v for (_, verdict), v in counts.items() if verdict == "MISSING")
    print(f"\n{bad} leaf/leaves render the compliance token as the social verb")
    print(f"{gone} leaf/leaves have no recognizable rendering of the clause")

    if verbose:
        for verdict, tag, key, en_text, text in sorted(rows):
            if only and verdict != only:
                continue
            if verdict in ("literal", "domain") and not only:
                continue
            print(f"\n[{verdict}] {tag:8s} {key}")
            print(f"  en  {en_text[:190]}")
            print(f"  {tag:3s} {text[:190]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
