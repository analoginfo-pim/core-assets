#!/usr/bin/env python3
"""Harvest help keys from fieldHelp.ts and fill Tier1 help.json catalogs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, load_json, source_sha256  # noqa: E402

FIELD_HELP_TS = Path(r"c:\analog-pim\pim-offline-server\ui\src\help\fieldHelp.ts")
UI = ROOT / "content/locales-ui"
TAGS = ["en", "de", "fr", "es", "en-GB"]

# Minimal formal DE for high-frequency action* keys; longer strings keep EN draft
# until translator review (queue open). Prefer real DE when short.
DE_EXACT: Dict[str, str] = {
    "actionDetails": "Details anzeigen",
    "actionTest": "Testen",
    "actionGenerate": "Erzeugen",
    "actionSave": "Speichern",
    "actionCancel": "Abbrechen",
    "actionDelete": "LÃ¶schen",
    "actionCreate": "Erstellen",
    "actionEdit": "Bearbeiten",
    "actionView": "Anzeigen",
    "actionRefresh": "Aktualisieren",
    "actionExport": "Exportieren",
    "actionImport": "Importieren",
    "actionNext": "Weiter",
    "actionBack": "ZurÃ¼ck",
    "actionClose": "SchlieÃŸen",
    "actionProbe": "PrÃ¼fen",
    "actionPush": "Ãœbertragen",
    "actionClone": "Duplizieren",
    "actionMove": "Verschieben",
    "actionUpload": "Hochladen",
    "actionElevate": "ErhÃ¶hen",
    "actionSleep": "Ruhezustand",
    "actionKeepAwake": "Wach halten",
    "currentPassword": "Aktuelles Passwort",
    "principalUsername": "Benutzername",
    "principalDisplayName": "Anzeigename",
    "principalEmail": "E-Mail",
    "machineName": "Systemname",
    "genericSelect": "Auswahl",
    "genericTextField": "Textfeld",
    "genericFormField": "Formularfeld",
    "genericControl": "Steuerelement",
}


def harvest_help_en() -> Dict[str, str]:
    text = FIELD_HELP_TS.read_text(encoding="utf-8")
    # Match key: '...' or key: `...` inside FIELD_HELP / CONTROL_HELP objects
    out: Dict[str, str] = {}
    for m in re.finditer(
        r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*'((?:\\'|[^'])*)'",
        text,
        re.M,
    ):
        out[m.group(1)] = m.group(2).replace("\\'", "'")
    for m in re.finditer(
        r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*\"((?:\\\"|[^\"])*)\"",
        text,
        re.M,
    ):
        out[m.group(1)] = m.group(2).replace('\\"', '"')
    # Drop non-help noise if any (imports etc. rarely match)
    return out


def localize(tag: str, en: str, key: str) -> str:
    if tag in ("en", "en-GB"):
        if tag == "en-GB":
            return (
                en.replace("organization", "organisation")
                .replace("Organization", "Organisation")
                .replace("favorite", "favourite")
                .replace("color", "colour")
            )
        return en
    if tag == "de":
        return DE_EXACT.get(key, en)  # draft: EN retained for long help until DE authored
    if tag == "fr":
        return DE_EXACT.get(key, en) if False else en  # keep EN draft in fr help for now
    if tag == "es":
        return en
    return en


def main() -> None:
    harvested = harvest_help_en()
    print(f"harvested help keys={len(harvested)}")
    # Prefer missing list from walk when present
    miss_path = ROOT / "scripts/language-packs/_tier1_de_pass2_still.json"
    walk_miss = []
    if miss_path.exists():
        walk_miss = json.loads(miss_path.read_text(encoding="utf-8"))
    # Also use full non-control banner list
    real_path = ROOT / "scripts/language-packs/_tier1_de_real_missing.json"
    if real_path.exists():
        walk_miss = sorted(set(walk_miss) | set(json.loads(real_path.read_text(encoding="utf-8"))))

    for tag in TAGS:
        path = UI / tag / "help.json"
        data: Dict[str, Any] = load_json(path) if path.exists() else {}
        added = 0
        # Fill all harvested keys (source completeness)
        for key, en in harvested.items():
            if key in data and isinstance(data[key], dict) and data[key].get("text"):
                continue
            text = localize(tag, en, key)
            data[key] = {"text": text, "source_sha256": source_sha256(en)}
            added += 1
        # Ensure walk-missing keys exist even if not harvested
        for key in walk_miss:
            if key.startswith("headers.") or key.startswith("chrome.") or key.startswith("sectionLanding") or key.startswith("ipScanner") or key.startswith("defense.") or key.startswith("reports:") or key.startswith("delivery."):
                continue  # pages ns
            if "." in key and not key.startswith("action"):
                # might still be help (defense.kpiHelp etc. is pages)
                if key.startswith("defense.") or key.startswith("headers."):
                    continue
            if key not in data:
                en = harvested.get(key) or key
                data[key] = {
                    "text": localize(tag, en if en != key else key.replace("_", " "), key),
                    "source_sha256": source_sha256(en if isinstance(en, str) else key),
                }
                added += 1
        dump_json(path, data)
        print(f"{tag}/help.json entries={len(data)} newly_setâ‰ˆ{added}")


if __name__ == "__main__":
    main()

