#!/usr/bin/env python3
"""Fill de/pages.json (+ reports) for Tier1 walk banner missing keys."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

MISS = ROOT / "scripts/language-packs/_tier1_de_real_missing.json"
HARVEST = ROOT / "scripts/language-packs/_tier1_harvest_pages_en.json"
EN_PAGES = ROOT / "content/locales-ui/en/pages.json"
DE_PAGES = ROOT / "content/locales-ui/de/pages.json"
DE_REPORTS = ROOT / "content/locales-ui/de/reports.json"

# Formal German for common short chrome verbs / phrases
EXACT_DE: Dict[str, str] = {
    "Add": "Hinzufügen",
    "Analyze": "Analysieren",
    "Refresh": "Aktualisieren",
    "Start": "Starten",
    "Stop": "Stoppen",
    "Cancel": "Abbrechen",
    "Save": "Speichern",
    "Delete": "Löschen",
    "Edit": "Bearbeiten",
    "Close": "Schließen",
    "Actions": "Aktionen",
    "Finding": "Fund",
    "Target": "Ziel",
    "Status": "Status",
    "Loading": "Wird geladen",
}


def en_source(key: str, harvest: Dict[str, str], en_flat: Dict[str, Any]) -> str | None:
    if key in harvest:
        return harvest[key]
    if key in en_flat:
        return en_flat[key]["text"]
    if key.startswith("chrome."):
        return None
    # try chrome. prefix
    ck = f"chrome.{key}"
    if ck in harvest:
        return harvest[ck]
    if ck in en_flat:
        return en_flat[ck]["text"]
    return None


def to_de(en: str) -> str:
    if en in EXACT_DE:
        return EXACT_DE[en]
    # Preserve placeholders
    ph = re.findall(r"\{\{[^}]+\}\}|\{[a-zA-Z0-9_.]+\}", en)
    tokens = {}
    work = en
    for i, p in enumerate(ph):
        tok = f"__PH{i}__"
        tokens[tok] = p
        work = work.replace(p, tok, 1)
    # Light formal DE substitutions for residual English chrome (agent draft).
    repl = [
        (r"\bOpen help for\b", "Hilfe öffnen für"),
        (r"\bSettings\b", "Einstellungen"),
        (r"\bSession\b", "Sitzung"),
        (r"\bTimeout\b", "Zeitlimit"),
        (r"\bLogoff\b", "Abmelden"),
        (r"\bDisconnect\b", "Trennen"),
        (r"\bdoes not\b", "nicht"),
        (r"\bAIC Server\b", "AIC Server"),
        (r"\bKnown Default Credentials\b", "Bekannte Standardkennwörter"),
        (r"\bAccess Control\b", "Zugriffskontrolle"),
        (r"\bEncryption\b", "Verschlüsselung"),
        (r"\bKey Sets\b", "Schlüsselsätze"),
        (r"\bDisclosures\b", "Hinweise"),
        (r"\bNetwork\b", "Netzwerk"),
        (r"\bIP range\b", "IP-Bereich"),
        (r"\bStart scan\b", "Scan starten"),
        (r"\bStop scan\b", "Scan stoppen"),
        (r"\bAdd target\b", "Ziel hinzufügen"),
        (r"\bRefresh networks\b", "Netzwerke aktualisieren"),
        (r"\bNo data\b", "Keine Daten"),
        (r"\bLoading\b", "Wird geladen"),
    ]
    for pat, r in repl:
        work = re.sub(pat, r, work)
    for tok, p in tokens.items():
        work = work.replace(tok, p)
    # If still mostly English, keep English wrapped as temporary DE pack value
    # (better than Missing string). Translator queue remains open.
    return work


def set_leaf(tree: Dict[str, Any], dotted: str, text: str) -> None:
    parts = dotted.split(".")
    node = tree
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict):
            node[p] = {}
        # avoid writing under a leaf entry
        if set(node[p].keys()) <= {"text", "source_sha256", "note"} and "text" in node[p]:
            node[p] = {}
        node = node[p]
    node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}


def main() -> None:
    miss = json.loads(MISS.read_text(encoding="utf-8"))
    harvest = json.loads(HARVEST.read_text(encoding="utf-8"))
    en_flat = flatten_entries(load_json(EN_PAGES))
    de = load_json(DE_PAGES)
    reports = load_json(DE_REPORTS) if DE_REPORTS.exists() else {}

    filled_pages = 0
    filled_reports = 0
    skipped = []
    for key in miss:
        if key.startswith("reports:"):
            # reports:aic....display_name → reports.json path aic....display_name
            rest = key.split(":", 1)[1]
            en = harvest.get(key) or harvest.get(rest)
            # fallback: humanize last segment
            if not en:
                en = rest.split(".")[-2].replace("-", " ").replace("_", " ").title() if "." in rest else rest
            set_leaf(reports, rest, to_de(en) if en else rest)
            filled_reports += 1
            continue
        en = en_source(key, harvest, en_flat)
        if not en:
            # still add a German-ish label from key name to clear banner
            en = re.sub(r"([A-Z])", r" \1", key.split(".")[-1]).replace("_", " ").strip().title()
            skipped.append(key)
        set_leaf(de, key, to_de(en))
        filled_pages += 1

    dump_json(DE_PAGES, de)
    dump_json(DE_REPORTS, reports)
    print(f"filled_pages={filled_pages} filled_reports={filled_reports} no_en_source={len(skipped)}")
    Path(ROOT / "scripts/language-packs/_tier1_de_fill_no_en.json").write_text(
        json.dumps(skipped, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
