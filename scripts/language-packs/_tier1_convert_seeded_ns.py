#!/usr/bin/env python3
"""Convert German-seeded locales-ui JSON files for en (then clone to en-GB/fr/es)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

# Reuse rough translator from author script
from _tier1_author_en_from_de import rough_translate, EXACT  # noqa: E402

NS = [
    "binder.json",
    "catalog.json",
    "compliance.json",
    "dialogs.json",
    "docs.json",
    "reports.json",
    "risks.json",
]


def rebuild(flat: Dict[str, str]) -> Dict[str, Any]:
    tree: Dict[str, Any] = {}

    def set_leaf(dotted: str, text: str) -> None:
        parts = dotted.split(".")
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}

    for k, v in flat.items():
        set_leaf(k, v)
    return tree


def convert_tag_from_de(tag: str) -> None:
    de_dir = ROOT / "content/locales-ui/de"
    out_dir = ROOT / "content/locales-ui" / tag
    for name in NS:
        src = de_dir / name
        if not src.exists():
            continue
        flat_de = flatten_entries(load_json(src))
        out_flat = {}
        for k, e in flat_de.items():
            de_text = e["text"]
            if tag == "en":
                out_flat[k] = EXACT.get(k, rough_translate(de_text))
            elif tag == "en-GB":
                # start from EN if present else rough
                en_path = ROOT / "content/locales-ui/en" / name
                if en_path.exists():
                    en_flat = flatten_entries(load_json(en_path))
                    base = en_flat.get(k, {}).get("text") or rough_translate(de_text)
                else:
                    base = rough_translate(de_text)
                # light UK
                base = (
                    base.replace("organization", "organisation")
                    .replace("Organization", "Organisation")
                    .replace("favorite", "favourite")
                    .replace("Favorite", "Favourite")
                    .replace("color", "colour")
                    .replace("Color", "Colour")
                    .replace("center", "centre")
                    .replace("Center", "Centre")
                )
                # license noun
                base = re.sub(r"\blicense\b", "licence", base)
                base = re.sub(r"\bLicense\b", "Licence", base)
                out_flat[k] = base
            else:
                # fr/es: keep EN draft (from en file if available) — better than German
                en_path = ROOT / "content/locales-ui/en" / name
                if en_path.exists():
                    en_flat = flatten_entries(load_json(en_path))
                    out_flat[k] = en_flat.get(k, {}).get("text") or rough_translate(de_text)
                else:
                    out_flat[k] = rough_translate(de_text)
        dest = out_dir / name
        dump_json(dest, rebuild(out_flat))
        print(f"{tag}/{name}: {len(out_flat)} keys")


def main() -> None:
    convert_tag_from_de("en")
    convert_tag_from_de("en-GB")
    convert_tag_from_de("fr")
    convert_tag_from_de("es")


if __name__ == "__main__":
    main()
