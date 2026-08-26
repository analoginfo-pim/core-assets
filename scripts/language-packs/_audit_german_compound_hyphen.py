#!/usr/bin/env python3
"""Find German noun-compound hyphens that survived translation into other packs.

German closes noun compounds, hyphenating when one part is an acronym or a
borrowed word: OpenAPI-JSON, JSON-Datei, Token-Rotation. English writes the
same pair with a space: "OpenAPI JSON". So when en has

    Download OpenAPI JSON

and the Korean pack has

    OpenAPI-JSON 지원

the hyphen did not come from Korean. Korean does not hyphenate Latin
acronym pairs, and no translator working from the English would insert one.
It came from the German, which means German -- not English -- was the text
the translator actually read.

That matters because the pivot is where the meaning goes. On this one
button, German "herunterladen" contains "laden" (to load), and downstream
packs picked a load sense or lost the verb entirely:

    it       OpenAPI-JSON caricato      uploaded -- the opposite direction
    ko       OpenAPI-JSON 지원          support
    zh-Hans  OpenAPI-JSON 说明          description
    pl       Obciazono OpenAPI-JSON     was charged
    he       OpenAPI-JSON <...>         upholstered
    es       OpenAPI-JSON descargado    downloaded, past participle, on a button

None of those is a translation of "Download OpenAPI JSON". Every one of
them is downstream of a German pivot, and the hyphen is the receipt.

The check is deliberately narrow so a hit is evidence rather than a guess:
both sides of the hyphen must be the same ASCII tokens that en separates
with a single space. Any pair en itself hyphenates is invisible to it.

Crucially, German is not the only language that closes noun compounds.
Dutch, Swedish and Finnish do it too, and all three hyphenate after an
acronym exactly as German does, so "SSH-terminal" (nl), "SSH-terminal"
(sv) and "OpenAPI-JSON" (fi) are correct in those packs, not leaks. They
are exempt alongside de. Running without that exemption reports 142 hits,
of which 113 are correct orthography -- "fixing" those would replace good
Dutch and Swedish with bad. The remaining packs (Romance, Slavic, Turkic,
Semitic, CJK) do not hyphenate Latin acronym pairs, so there a hyphen is
evidence.

Usage: _audit_german_compound_hyphen.py [--show-all]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"

# An ASCII token pair separated by exactly one space, where at least one side
# carries an uppercase letter. The uppercase requirement keeps ordinary prose
# ("the file", "a token") out of it and holds the match to acronyms, product
# names, and identifiers -- the only places German would hyphenate.
PAIR = re.compile(r"(?<![-\w])([A-Za-z][A-Za-z0-9]*) ([A-Za-z][A-Za-z0-9]*)(?![-\w])")


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            yield prefix, node["text"]
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def compounds(english: str) -> list[tuple[str, str]]:
    """Token pairs en separates with a space that German would hyphenate."""
    out = []
    for left, right in PAIR.findall(english):
        if not any(c.isupper() for c in left + right):
            continue
        out.append((left, right))
    return out


def main() -> int:
    show_all = "--show-all" in sys.argv[1:]
    # Languages that close noun compounds and hyphenate after an acronym, so a
    # hyphen there is their own orthography rather than German showing through.
    COMPOUNDING = {"de", "nl", "sv", "fi"}
    tags = sorted(
        p.name
        for p in CATALOG.iterdir()
        if p.is_dir() and p.name != "en" and p.name not in COMPOUNDING
    )

    hits: list[tuple[str, str, str, str, str]] = []
    per_tag: Counter[str] = Counter()
    per_compound: Counter[str] = Counter()

    for en_path in sorted((CATALOG / "en").glob("*.json")):
        namespace = en_path.stem
        english = dict(leaves(json.loads(en_path.read_text(encoding="utf-8"))))
        wanted = {k: compounds(v) for k, v in english.items()}
        wanted = {k: v for k, v in wanted.items() if v}
        if not wanted:
            continue

        for tag in tags:
            path = CATALOG / tag / f"{namespace}.json"
            if not path.is_file():
                continue
            for key, text in leaves(json.loads(path.read_text(encoding="utf-8"))):
                pairs = wanted.get(key)
                if not pairs:
                    continue
                for left, right in pairs:
                    glued = f"{left}-{right}"
                    if re.search(rf"(?<![-\w]){re.escape(glued)}(?![-\w])", text):
                        hits.append((tag, namespace, key, glued, text))
                        per_tag[tag] += 1
                        per_compound[glued] += 1
                        break

    print(f"{len(hits)} leaf/leaves carry a German compound hyphen en writes as a space\n")

    if per_compound:
        print("by compound:")
        for glued, count in per_compound.most_common(20):
            print(f"  {count:5d}  {glued}")
        print()
        print("by pack:")
        for tag, count in per_tag.most_common():
            print(f"  {count:5d}  {tag}")
        print()

    shown = hits if show_all else hits[:30]
    for tag, namespace, key, glued, text in shown:
        print(f"  {tag:8s} {namespace} :: {key}")
        print(f"           {glued}  in  {text!r}")
    if not show_all and len(hits) > 30:
        print(f"\n  ... and {len(hits) - 30} more (--show-all)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
