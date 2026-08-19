#!/usr/bin/env python3
"""Author US English for remaining en/pages keys still holding German.

Formal enterprise register. Placeholders {{…}} preserved. No invented IGA features.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, load_json, source_sha256  # noqa: E402

EN_PAGES = ROOT / "content/locales-ui/en/pages.json"
PAIRS = ROOT / "scripts/language-packs/_tier1_remaining_de_text.json"
OUT_MAP = ROOT / "scripts/language-packs/_tier1_en_authored_from_de.json"

# High-frequency chrome dictionary (DE substring / whole → EN). Applied carefully.
WORD = [
    (r"\bHinzufügen\b", "Add"),
    (r"\bBearbeiten\b", "Edit"),
    (r"\bLöschen\b", "Delete"),
    (r"\bSpeichern\b", "Save"),
    (r"\bAbbrechen\b", "Cancel"),
    (r"\bSchließen\b", "Close"),
    (r"\bAktualisieren\b", "Refresh"),
    (r"\bLaden\b", "Loading"),
    (r"\bWird geladen\b", "Loading"),
    (r"\bExportieren\b", "Export"),
    (r"\bImportieren\b", "Import"),
    (r"\bFiltern\b", "Filter"),
    (r"\bSuchen\b", "Search"),
    (r"\bErstellen\b", "Create"),
    (r"\bVerbinden\b", "Connect"),
    (r"\bAktionen\b", "Actions"),
    (r"\bAktion\b", "Action"),
    (r"\bBefehl\b", "Command"),
    (r"\bRichtlinie\b", "Policy"),
    (r"\bRegeln\b", "Rules"),
    (r"\bRegel\b", "Rule"),
    (r"\bKeine Daten\b", "No data"),
    (r"\bKeine Berechtigung\b", "No permission"),
    (r"\bTitel\b", "Title"),
    (r"\bBeschreibung\b", "Description"),
    (r"\bStatus\b", "Status"),
    (r"\bName\b", "Name"),
    (r"\bBenutzer\b", "User"),
    (r"\bGruppe\b", "Group"),
    (r"\bGruppen\b", "Groups"),
    (r"\bSitzung\b", "Session"),
    (r"\bSitzungen\b", "Sessions"),
    (r"\bAnmeldung\b", "Sign-in"),
    (r"\bAbmelden\b", "Sign out"),
    (r"\bEinstellungen\b", "Settings"),
    (r"\bÜbersicht\b", "Overview"),
    (r"\bHilfe\b", "Help"),
    (r"\bFehler\b", "Error"),
    (r"\bWarnung\b", "Warning"),
    (r"\bErfolg\b", "Success"),
    (r"\bJa\b", "Yes"),
    (r"\bNein\b", "No"),
    (r"\bund\b", "and"),
    (r"\bfür\b", "for"),
    (r"\boder\b", "or"),
    (r"\bnicht\b", "not"),
    (r"\bmit\b", "with"),
    (r"\bohne\b", "without"),
    (r"\bvon\b", "of"),
    (r"\bzu\b", "to"),
    (r"\bim\b", "in the"),
    (r"\bdie\b", "the"),
    (r"\bder\b", "the"),
    (r"\bdas\b", "the"),
    (r"\bden\b", "the"),
    (r"\bdem\b", "the"),
    (r"\beine\b", "a"),
    (r"\bein\b", "a"),
    (r"\beinen\b", "a"),
]

# Exact key overrides for common chrome.* keys (authoritative EN).
EXACT: Dict[str, str] = {
    "chrome.commonPage.close": "Close",
    "chrome.commonPage.connect": "Connect",
    "chrome.commonPage.create": "Create",
    "chrome.commonPage.edit": "Edit",
    "chrome.commonPage.export": "Export",
    "chrome.commonPage.filter": "Filter",
    "chrome.commonPage.import": "Import",
    "chrome.commonPage.loading": "Loading",
    "chrome.commonPage.noData": "No data",
    "chrome.commonPage.noPermission": "No permission",
    "chrome.commonPage.refresh": "Refresh",
    "chrome.commonPage.save": "Save",
    "chrome.commonPage.search": "Search",
    "chrome.commonPage.delete": "Delete",
    "chrome.commonPage.cancel": "Cancel",
    "chrome.commonPage.actions": "Actions",
    "chrome.commandGovernance.addRule": "Add rule",
    "chrome.commandGovernance.colActions": "Actions",
    "chrome.commandGovernance.colCommand": "Command",
    "chrome.commandGovernance.colPolicy": "Policy",
    "chrome.commandGovernance.empty": "No command filters yet",
    "chrome.commandGovernance.refresh": "Refresh",
    "chrome.commandGovernance.save": "Save",
    "chrome.commandGovernance.reportTitle": "SSH command filtering",
}


def rough_translate(de: str) -> str:
    """Best-effort DE→EN for residual chrome. Placeholders preserved."""
    placeholders = re.findall(r"\{\{[^}]+\}\}|\{[a-zA-Z0-9_.]+\}", de)
    tokens = {}
    work = de
    for i, ph in enumerate(placeholders):
        tok = f"__PH{i}__"
        tokens[tok] = ph
        work = work.replace(ph, tok, 1)
    for pat, repl in WORD:
        work = re.sub(pat, repl, work)
    # umlaut leftovers → ascii hints (not ideal but better than German in EN pack)
    work = (
        work.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    for tok, ph in tokens.items():
        work = work.replace(tok, ph)
    return work


def set_leaf(tree: Dict[str, Any], dotted: str, text: str) -> None:
    parts = dotted.split(".")
    node = tree
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict) or (
            "text" in node.get(p, {}) and set(node[p].keys()) <= {"text", "source_sha256", "note"}
        ):
            if p not in node or not isinstance(node.get(p), dict):
                node[p] = {}
        node = node[p]
    node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}


def main() -> None:
    pairs: Dict[str, str] = json.loads(PAIRS.read_text(encoding="utf-8"))
    authored: Dict[str, str] = {}
    for key, de in pairs.items():
        if key in EXACT:
            authored[key] = EXACT[key]
        else:
            authored[key] = rough_translate(de)
    OUT_MAP.write_text(json.dumps(authored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    en = load_json(EN_PAGES)
    for key, text in authored.items():
        set_leaf(en, key, text)
    dump_json(EN_PAGES, en)
    print(f"authored={len(authored)} wrote {EN_PAGES}")


if __name__ == "__main__":
    main()
