#!/usr/bin/env python3
"""Find en leaves that are really German, by verbatim overlap with the de pack.

Hash provenance cannot catch this class. When the pipeline wrote German into en
it also re-hashed that German as the source, so the leaf is self-consistent and
every digest check passes it. Comparing en against the code catches it, but the
en catalog has also been edited deliberately since pageIntros.ts was written --
honesty clauses added, nav names corrected -- so "en differs from code" is far
too broad to act on. Restoring all of those from code would delete real edits.

What is not ambiguous: an English sentence and its German translation share
almost no long verbatim runs. Function words differ, word order differs,
morphology differs. So a long common substring between en[key] and de[key] means
one was produced from the other, and since German is never the source language,
en is the corrupted side.

Identifiers, URLs and product names are shared legitimately, so a run has to
contain a lowercase German-looking word to count -- otherwise "AGENT_HMAC_ENFORCE
_MODE=dual_mode" alone would trip it.

Usage:
    python _audit_en_german_overlap.py [--min N] [--show-all]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"

# Words that appear in German prose and not in English prose. Kept short and
# unambiguous on purpose: every entry here would be a bug in an English string.
GERMAN_MARKERS = re.compile(
    r"\b(?:der|die|das|den|dem|des|und|oder|nicht|nur|weiterhin|werden|wird|"
    r"wurde|sind|ist|sich|auch|noch|kein|keine|eine|einen|einem|einer|mit|"
    r"nutzen|nutzt|erwarten|zeigt|zeigen|siehe|unter|ueber|über|fuer|für|"
    r"lokale|lokalen|getrennte|luftgekapte|luftgekapselte|Konfiguratoren|"
    r"Endpunkte|Propagierung|Offenlegungen|Faehigkeiten|Fähigkeiten|"
    r"Verweildauer|Eintrag|erfasst|gesehen|Exportformaten|lebendiger)\b"
)


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            yield prefix, node
            return
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{prefix}[{index}]")


def load(tag: str) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    directory = CATALOG / tag
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for dotted, leaf in leaves(data):
            out[(path.stem, dotted)] = leaf["text"]
    return out


def longest_common_substring(a: str, b: str) -> str:
    """Classic DP, but rolling so a long page bullet does not blow up memory."""
    if not a or not b:
        return ""
    previous = [0] * (len(b) + 1)
    best_length = 0
    best_end = 0
    for i in range(1, len(a) + 1):
        current = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                current[j] = previous[j - 1] + 1
                if current[j] > best_length:
                    best_length = current[j]
                    best_end = i
        previous = current
    return a[best_end - best_length : best_end]


def main() -> int:
    argv = sys.argv[1:]
    show_all = "--show-all" in argv
    minimum = 25
    if "--min" in argv:
        minimum = int(argv[argv.index("--min") + 1])

    english = load("en")
    german = load("de")
    if not german:
        print("de pack not found", file=sys.stderr)
        return 1

    hits: list[tuple[str, str, int, str, str, str]] = []
    for key, en_text in english.items():
        de_text = german.get(key)
        if not de_text or en_text == de_text:
            # Identical text is a separate defect (untranslated de), not this one.
            continue
        if not GERMAN_MARKERS.search(en_text):
            continue
        run = longest_common_substring(en_text, de_text)
        if len(run) < minimum:
            continue
        if not GERMAN_MARKERS.search(run):
            continue
        hits.append((key[0], key[1], len(run), run, en_text, de_text))

    hits.sort(key=lambda row: -row[2])
    print(
        f"{len(hits)} en leaf/leaves share a >={minimum}-char German run with the de pack\n"
        f"({len(english)} en leaves scanned)"
    )
    if not hits:
        return 0
    print()
    shown = hits if show_all else hits[:40]
    for namespace, dotted, length, run, en_text, de_text in shown:
        print(f"  {namespace} :: {dotted}   (run={length})")
        print(f"     en: {en_text[:170]}")
        print(f"     de: {de_text[:170]}")
    if not show_all and len(hits) > len(shown):
        print(f"\n  ... {len(hits) - len(shown)} more (--show-all)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
