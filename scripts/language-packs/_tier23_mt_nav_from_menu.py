#!/usr/bin/env python3
"""
Build locales-ui/<tag>/nav.json covering de nav key set using English labels
harvested from menuItems.tsx (and a small alias map), then MT en→tag.

Never writes en/de/fr/es/en-GB.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

ASSIGNED = {
    "zh-Hans",
    "zh-TW",
    "ja",
    "ko",
    "pt-BR",
    "it",
    "he",
    "pl",
    "tr",
    "nl",
    "sv",
    "fi",
    "ar",
}
GOOGLE_LANG = {
    "zh-Hans": "zh-CN",
    "zh-TW": "zh-TW",
    "ja": "ja",
    "ko": "ko",
    "pt-BR": "pt",
    "it": "it",
    "he": "iw",
    "pl": "pl",
    "tr": "tr",
    "nl": "nl",
    "sv": "sv",
    "fi": "fi",
    "ar": "ar",
}
MENU = Path(r"c:\analog-pim\pim-offline-server\ui\src\config\menuItems.tsx")
DE_NAV = ROOT / "content/locales-ui/de/nav.json"

# Keys that do not match a harvested label exactly.
ALIASES: Dict[str, str] = {
    "dashboard": "Dashboard",
    "overview": "Overview",
    "platform_overview": "Platform overview",
    "favorites": "Favorites",
    "reports_dashboards": "Reports and dashboards",
    "my_workspace": "My workspace",
    "access_identity": "Access and identity",
    "directory": "Directory",
    "endpoint_privilege": "Endpoint privilege",
    "proxied_access": "Proxied access",
    "operational_technology": "Operational technology",
    "systems": "Systems",
    "configuration": "Configuration",
    "documentation": "Documentation",
    "about_licensing": "About and licensing",
    "security": "Security",
    "incidents": "Incidents",
    "training": "Training",
    "compliance_evidence": "Compliance and evidence",
}


def path_to_key(pathname: str) -> str:
    normalized = pathname.rstrip("/") or "/"
    if normalized == "/":
        return "dashboard"
    return normalized[1:].replace("/", "_").replace("-", "_").replace("?", "_")


def harvest_menu_labels() -> Dict[str, str]:
    text = MENU.read_text(encoding="utf-8")
    out: Dict[str, str] = {}
    # path + nearby label
    for m in re.finditer(
        r"path:\s*'(/[^']*)'[\s\S]{0,200}?label:\s*'([^']+)'",
        text,
    ):
        path, label = m.group(1), m.group(2)
        key = path_to_key(path.split("?")[0].split("#")[0])
        out[key] = label
    # bare labels on group nodes
    for m in re.finditer(r"label:\s*'([^']+)'", text):
        label = m.group(1)
        snake = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
        out.setdefault(snake, label)
    return out


def unflatten(entries: Dict[str, Dict[str, str]]) -> dict:
    tree: dict = {}
    for path, entry in entries.items():
        parts = path.split(".")
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = entry
    return tree


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--sleep", type=float, default=0.05)
    args = ap.parse_args()
    tag = args.tag
    if tag not in ASSIGNED:
        print("refuse", tag, file=sys.stderr)
        return 2

    from deep_translator import GoogleTranslator

    de_keys = list(flatten_entries(load_json(DE_NAV)).keys())
    harvested = harvest_menu_labels()
    en_map: Dict[str, str] = {}
    for k in de_keys:
        if k in ALIASES:
            en_map[k] = ALIASES[k]
        elif k in harvested:
            en_map[k] = harvested[k]
        else:
            # Title-case the snake key as last resort (still English source)
            en_map[k] = k.replace("_", " ").strip().title()

    translator = GoogleTranslator(source="en", target=GOOGLE_LANG[tag])
    out: Dict[str, Dict[str, str]] = {}
    for i, (k, en_text) in enumerate(en_map.items(), 1):
        h = source_sha256(en_text)
        try:
            tr = translator.translate(en_text)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN {k}: {exc}", file=sys.stderr)
            tr = en_text
        out[k] = {"text": tr, "source_sha256": h}
        time.sleep(args.sleep)
        if i % 25 == 0:
            print(f"{tag} nav {i}/{len(en_map)}", flush=True)

    path = ROOT / "content/locales-ui" / tag / "nav.json"
    dump_json(path, unflatten(out))
    print(f"wrote {path} keys={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
