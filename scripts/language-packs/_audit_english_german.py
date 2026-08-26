#!/usr/bin/env python3
"""Find German text shipped inside the English catalogs (en and en-GB).

en is the default locale and the fallback for every other pack. German in en is
not a translation-quality issue, it is the product showing German to an operator
who selected nothing at all, and it poisons any pack that falls back.

Evidence is a closed word list rather than a language detector: function words
and inflections that exist in German and not in English, so a hit is a fact and
not a probability. "Modus", "Standard", "Server", "Information" and similar
Anglo-German cognates are deliberately absent from the list -- they would fire on
correct English.

Usage: _audit_english_german.py [--tag en] [--fix-from-code]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}

TOKEN = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*")

# German function words and inflections with no English homograph.
GERMAN_ONLY = {
    "aber", "alle", "allen", "als", "andere", "auch", "auf", "aus", "bei",
    "beim", "bereits", "bis", "damit", "dann", "dar", "das", "dass", "dem",
    "den", "der", "des", "die", "dies", "diese", "diesem", "diesen", "dieser",
    "dieses", "durch", "ein", "eine", "einem", "einen", "einer", "eines",
    # "falls" is deliberately absent: "whose opened_at falls in the window" is
    # correct English and fired on two honesty notes. Homographs stay out.
    "erst", "erstellen", "für", "fuer", "gibt", "haben", "hat",
    "hier", "ihre", "ihren", "immer", "ist", "jede", "jeden", "jeder", "kann",
    "kein", "keine", "können", "koennen", "mehr", "mit", "muss", "müssen",
    "nach", "nicht", "noch", "nur", "ob", "oder", "ohne", "sein", "seine",
    "sich", "sie", "sind", "sowie", "über", "ueber", "und", "unter", "vom",
    "von", "vor", "wann", "wenn", "werden", "wird", "wurde", "zum", "zur",
    "zwischen",
    # Nouns and participles seen in the leaked strings.
    "alarme", "anzeigen", "arbeitsplatzsitze", "aufzeichnung", "begrenzt",
    "benutzer", "berechtigungen", "datenbank", "datenbankadapter",
    "einstellungen", "endbenutzer", "feste", "fingerabdruck", "handbuch",
    "handbuecher", "handbücher", "herunterladen", "hochladen", "knoten",
    "lastverteilte", "lesen", "letzter", "letzte", "sicheres", "sitzung",
    "sitzungen", "seitenliste", "stimmt", "teilen", "unternehmens",
    "verbrauch", "verwalten", "zugriff",
}


def leaves(node, prefix=""):
    """Yield (dotted_path, leaf_dict) for every {"text": ...} leaf."""
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            yield prefix, node
            return
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{prefix}[{index}]")


def german_words(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text) if t.lower() in GERMAN_ONLY]


def main() -> int:
    argv = sys.argv[1:]
    tags = [argv[argv.index("--tag") + 1]] if "--tag" in argv else ["en", "en-GB"]

    total = 0
    for tag in tags:
        for area, root in ROOTS.items():
            tag_dir = root / tag
            if not tag_dir.is_dir():
                continue
            for path in sorted(tag_dir.glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                for key, leaf in leaves(data):
                    hits = german_words(leaf["text"])
                    if not hits:
                        continue
                    total += 1
                    text = leaf["text"]
                    shown = text if len(text) <= 180 else text[:177] + "..."
                    print(f"  [{tag}] {area}/{path.stem} :: {key}")
                    print(f"      german  {sorted(set(hits))}")
                    print(f"      text    {shown!r}")

    print(f"\n{total} English leaf(s) contain German")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
