#!/usr/bin/env python3
"""Fill remaining en/pages.json keys that still hold German text — from credits + deeper harvest."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

EN_PAGES = ROOT / "content/locales-ui/en/pages.json"
DE_PAGES = ROOT / "content/locales-ui/de/pages.json"
SPA = Path(r"c:\analog-pim\pim-offline-server\ui\src")
STILL = ROOT / "scripts/language-packs/_tier1_en_pages_still_de.json"

CREDITS_EN: Dict[str, str] = {
    "chrome.about.creditsTitle": "Open Source Credits",
    "chrome.about.creditsIntro": (
        "Every third-party open-source component incorporated into AIC Server "
        "(Cargo production graph, npm production graph, and incorporated assets). "
        "Each row names the project, license, and copyright notice when known. "
        "Expand a row to read the license text."
    ),
    "chrome.about.creditsLoadFailed": "Could not load the open-source credits inventory.",
    "chrome.about.creditsLoading": "Loading open-source credits",
    "chrome.about.creditsStatusLabel": "Inventory status: {{status}}",
    "chrome.about.creditsMeta": (
        "{{count}} third-party entries ({{withText}} with license text). Generated {{when}}. "
        "Cargo.lock packages: {{lockCount}}. Cargo.lock SHA-256: {{cargoSha}}. "
        "package-lock SHA-256: {{npmSha}}. Server SBOM SHA-256: {{sbomSha}}."
    ),
    "chrome.about.creditsBlocked": (
        "{{n}} package(s) are BLOCKED (no harvested license identity and/or license text). "
        "They remain listed below and are not omitted."
    ),
    "chrome.about.creditsBlockedChip": "BLOCKED",
    "chrome.about.creditsUnresolved": (
        "{{n}} direct Cargo dependencies did not receive a license string from the local "
        "Cargo registry cache at generation time (listed with a note)."
    ),
    "chrome.about.creditsFilter": "Filter components",
    "chrome.about.creditsFilterHelp": "Narrow the list by project name, license, or copyright text.",
    "chrome.about.creditsFilterAria": "Filter open-source credits by name or license",
    "chrome.about.creditsDownloadAppendix": "Download Cargo.lock appendix",
    "chrome.about.creditsDownloadAppendixHelp": (
        "Download the full Cargo.lock appendix with names and versions as JSON."
    ),
    "chrome.about.creditsDownloadInventory": "Download inventory JSON",
    "chrome.about.creditsDownloadInventoryHelp": (
        "Download the complete inventory JSON including honesty metadata."
    ),
    "chrome.about.creditsDownloadBlocked": "Download BLOCKED packages",
    "chrome.about.creditsDownloadBlockedHelp": "Download the BLOCKED package list as JSON.",
    "chrome.about.creditsShowing": "Showing {{shown}} of {{total}} (page {{page}} of {{pages}})",
    "chrome.about.creditsPaginationAria": "Open-source credits pages",
    "chrome.about.creditsListAria": "Open-source components",
    "chrome.about.creditsLicenseUnknown": "License not resolved",
    "chrome.about.creditsEcosystem": "Ecosystem: {{value}}",
    "chrome.about.creditsSource": "Source: {{value}}",
    "chrome.about.creditsLicenseTextAria": "License text for {{name}}",
    "chrome.about.creditsLicenseLoading": "Loading license text…",
    "chrome.about.creditsLicenseLoadStatus": "Could not load license text ({{status}}).",
    "chrome.about.creditsLicenseLoadFailed": "Could not load license text.",
    "chrome.about.creditsNoLicenseBody": "No license body was harvested for this package.",
    "chrome.about.creditsPagePrev": "Previous",
    "chrome.about.creditsPageNext": "Next",
    "chrome.about.creditsPageStatus": "Page {{page}} of {{pages}}",
}


def deep_harvest() -> Dict[str, str]:
    """Capture defaultValue even when the options object spans lines."""
    pat = re.compile(
        r"t\(\s*['\"](?:pages:)?([a-zA-Z0-9_.-]+)['\"]\s*,\s*\{(.{0,800}?)\}",
        re.S,
    )
    dv = re.compile(r"defaultValue\s*:\s*['\"]((?:\\.|[^'\\\"])*)['\"]")
    out: Dict[str, str] = {}
    for path in list(SPA.rglob("*.tsx")) + list(SPA.rglob("*.ts")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in pat.finditer(text):
            key = m.group(1)
            block = m.group(2)
            dm = dv.search(block)
            if dm:
                out[key] = bytes(dm.group(1), "utf-8").decode("unicode_escape")
    return out


def set_leaf(tree: Dict[str, Any], dotted: str, text: str) -> None:
    parts = dotted.split(".")
    node = tree
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict):
            node[p] = {}
        node = node[p]
        # unwrap accidental entry
        if "text" in node and len(node) <= 3 and all(k in ("text", "source_sha256", "note") for k in node):
            # shouldn't happen mid-path
            pass
    node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}


def looks_german(s: str) -> bool:
    markers = ("ä", "ö", "ü", "Ä", "Ö", "Ü", "ß", " und ", " für ", " der ", " die ", " das ", " nicht ")
    return any(m in s for m in markers)


def main() -> None:
    en = load_json(EN_PAGES)
    de_flat = flatten_entries(load_json(DE_PAGES))
    harvested = deep_harvest()
    print("deep harvest", len(harvested))
    still = json.loads(STILL.read_text(encoding="utf-8")) if STILL.exists() else []
    filled = 0
    remaining = []
    for key in still:
        text = CREDITS_EN.get(key) or harvested.get(key)
        if text is None:
            remaining.append(key)
            continue
        set_leaf(en, key, text)
        filled += 1
    # Also walk all en leaves that still look German
    en_flat = flatten_entries(en)
    for key, entry in en_flat.items():
        t = entry.get("text", "")
        if not looks_german(t):
            continue
        text = CREDITS_EN.get(key) or harvested.get(key)
        if text and text != t:
            set_leaf(en, key, text)
            filled += 1
            if key in remaining:
                remaining.remove(key)
    dump_json(EN_PAGES, en)
    STILL.write_text(json.dumps(remaining, indent=2) + "\n", encoding="utf-8")
    print(f"filled={filled} remaining_germanish={len(remaining)}")
    print("sample remaining", remaining[:20])


if __name__ == "__main__":
    main()
