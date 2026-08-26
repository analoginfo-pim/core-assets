#!/usr/bin/env python3
"""Find German that leaked into the English source catalog.

Every other detector in this directory assumes English is the clean side and asks
what the packs did to it. That assumption failed: openapi.capped ships
" (Seitenliste auf 500 begrenzt)" in content/locales-ui/en/docs.json, so an operator
running the product in English reads German. The German-pivot pipeline wrote back
into its own input.

This is worse than a bad translation. A wrong Finnish string reaches Finnish
operators; a wrong English string reaches the default locale, reaches en-GB which is
derived from it, and becomes the source hash every other pack is measured against.

Two independent signals, both closed-form so neither invents a judgment call:

    UMLAUT    a character that English orthography does not use
    FUNCTION  a token from a small closed set of German words with no English
              reading, so a single hit is proof rather than a guess

Reporting them separately lets a reviewer see which evidence fired.

Usage: _audit_german_in_english.py [--tag en|en-GB]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}

UMLAUT = re.compile(r"[äöüßÄÖÜ]")
WORD = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*")

# German words that are not also English words. "die" and "man" are German words but
# also English ones, so they are excluded: a detector that reports "die" on "die on
# error" teaches the reader to ignore it. Everything below is unambiguous.
GERMAN_ONLY = {
    "auf", "aus", "bei", "beim", "bis", "durch", "für", "fuer", "gegen", "mit",
    "nach", "seit", "über", "ueber", "unter", "vom", "von", "vor", "während",
    "waehrend", "wegen", "zum", "zur", "zwischen",
    "der", "des", "dem", "den", "das", "dass", "ein", "eine", "einen", "einem",
    "einer", "eines", "kein", "keine", "keinen",
    "und", "oder", "aber", "sondern", "weil", "wenn", "dann", "auch", "noch",
    "schon", "nur", "nicht", "nichts", "sich", "sein", "seine", "ihre", "ihrer",
    "ist", "sind", "war", "waren", "wird", "werden", "wurde", "wurden", "worden",
    "kann", "können", "koennen", "muss", "müssen", "muessen", "soll", "sollen",
    "darf", "dürfen", "duerfen", "hat", "haben", "hatte", "hatten",
    "begrenzt", "ausgewählt", "ausgewaehlt", "gewählt", "gewaehlt", "erforderlich",
    "verfügbar", "verfuegbar", "einstellungen", "berechtigung", "berechtigungen",
    "anmeldung", "abmeldung", "benutzer", "kennwort", "passwort", "sitzung",
    "seitenliste", "geräte", "geraete", "gerät", "geraet", "zugriff", "zugang",
    "verwaltung", "verbindung", "erhöhung", "erhoehung", "richtlinie", "nachweis",
    "prüfung", "pruefung", "bericht", "übersicht", "uebersicht", "verpackung",
    "befunde", "ausblenden", "einblenden", "speichern", "löschen", "loeschen",
    "hinzufügen", "hinzufuegen", "bearbeiten", "schließen", "schliessen",
}


def leaves(node: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            return [(prefix, node["text"])]
        for key, value in node.items():
            out.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
    return out


def main() -> int:
    argv = sys.argv[1:]
    tags = [argv[argv.index("--tag") + 1]] if "--tag" in argv else ["en", "en-GB"]

    findings: list[tuple[str, str, str, str, str, list[str]]] = []

    for area, root in ROOTS.items():
        if not root.is_dir():
            continue
        for tag in tags:
            tag_dir = root / tag
            if not tag_dir.is_dir():
                continue
            for path in sorted(tag_dir.glob("*.json")):
                namespace = path.stem
                for key, text in leaves(json.loads(path.read_text(encoding="utf-8"))):
                    hits = sorted(
                        {
                            w.lower()
                            for w in WORD.findall(text)
                            if w.lower() in GERMAN_ONLY
                        }
                    )
                    umlaut = UMLAUT.search(text) is not None
                    if not hits and not umlaut:
                        continue
                    why = "UMLAUT+FUNCTION" if hits and umlaut else ("UMLAUT" if umlaut else "FUNCTION")
                    findings.append((why, area, tag, namespace, key, hits))

    print(f"{len(findings)} English-catalog leaf(s) carry German evidence\n")

    by_ns: dict[tuple[str, str, str], int] = {}
    for _, area, tag, namespace, _, _ in findings:
        by_ns[(tag, area, namespace)] = by_ns.get((tag, area, namespace), 0) + 1
    for (tag, area, namespace), count in sorted(by_ns.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:6s} {area}/{namespace:16s} {count}")

    print()
    for why, area, tag, namespace, key, hits in findings:
        marker = " ".join(hits) if hits else "-"
        print(f"  [{why}] {tag} {area}/{namespace} :: {key}   ({marker})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
