#!/usr/bin/env python3
"""Find keys the MT pipeline pivoted through German, using pack agreement as proof.

The earlier wrong-language detector compared each pack against German and then
discarded single-token matches as possible cognates, on the theory that two
languages can legitimately share one word. That filter was wrong, and it hid the
worst leaf in the catalog: `catalog:rowCount` is "rows" in English and "Zeilen"
in German, and seven Latin packs ship the bare German word while every non-Latin
pack ships a phonetic transliteration of it -- Arabic `زيلين`, Hebrew `זיילן`,
katakana `ザイレン`, Hangul `자일렌`, Han `泽伦` / `澤倫`. Stripping `{{count}}`
leaves one token, so the cognate filter dropped all of it.

Agreement across unrelated packs is what makes this provable without a native
speaker. One pack matching German for a single word is arguable -- "Status" and
"Token" really are shared. Two packs from different families producing the *same*
German word for the same key is not a coincidence of translation; it is one
pivot, copied. So the threshold is on how many packs agree, not on how many words
they agree about, which is the inversion of the filter that hid this.

A flagged key is also a triage signal for the packs this test cannot see. The
non-Latin packs are never byte-identical to German, so they never appear in the
counts below, but a key that reached two Latin packs as raw German reached the
non-Latin packs through the same pivot -- and `rowCount` shows what that produced.
Latin-pack agreement is therefore reported as proof, and the same key in
non-Latin packs as suspect, rather than pretending the second group is clean.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")

# Packs written in Latin script can be byte-identical to German; the rest cannot,
# so they are counted separately as suspect rather than silently reported clean.
NON_LATIN = {"ar", "he", "ja", "ko", "zh-Hans", "zh-TW"}


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


def load(path: Path) -> dict:
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    show = "--list" in sys.argv
    # A key needs at least this many agreeing packs before it is called proof.
    threshold = 2

    proven_leaves = 0
    suspect_leaves = 0
    per_pack: defaultdict[str, int] = defaultdict(int)
    flagged: list[tuple[int, str, str, str, list[str]]] = []

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            english = load(root / "en" / f"{namespace}.json")
            german = load(root / "de" / f"{namespace}.json")
            if not german:
                continue

            packs = {
                d.name: load(d / f"{namespace}.json")
                for d in sorted(p for p in root.iterdir() if p.is_dir())
                if d.name not in {"en", "en-GB", "de"}
            }

            for key, de_text in german.items():
                de_stripped = de_text.strip()
                en_stripped = (english.get(key) or "").strip()
                # Identity with English means German never translated it either;
                # that is untranslated-English, a different defect.
                if not de_stripped or de_stripped == en_stripped:
                    continue

                agreeing = [
                    tag
                    for tag, pack in packs.items()
                    if (pack.get(key) or "").strip() == de_stripped
                ]
                if len(agreeing) < threshold:
                    continue

                proven_leaves += len(agreeing)
                for tag in agreeing:
                    per_pack[tag] += 1
                # Same key, same pivot, in the packs byte-identity cannot reach.
                suspect_leaves += sum(
                    1 for tag in NON_LATIN if (packs.get(tag) or {}).get(key)
                )
                flagged.append((len(agreeing), namespace, key, de_stripped, sorted(agreeing)))

    flagged.sort(key=lambda row: -row[0])

    print("keys where >=2 non-German packs ship byte-identical German:")
    for count, namespace, key, text, tags in flagged[: 40 if show else 15]:
        print(f"  {count:2d} packs  {namespace}:{key}")
        print(f"            {text[:110]}")
        if show:
            print(f"            {' '.join(tags)}")

    print()
    print(f"{len(flagged)} German-pivot key(s)")
    print(f"{proven_leaves} leaf/leaves provably shipping raw German (Latin-script packs)")
    print(f"{suspect_leaves} leaf/leaves on the same keys in non-Latin packs -- suspect, not counted as proof")
    print()
    print("raw-German leaves per pack:")
    for tag, n in sorted(per_pack.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
