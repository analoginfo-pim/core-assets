#!/usr/bin/env python3
"""
Build locales-ui/<tag>/pages.json from en/pages.json for Tier 2/3 tags.

Reads English text leaves; applies a translation map file if present, otherwise
leaves untranslated keys out of the output (caller must supply translations).

Usage:
  python _tier23_apply_pages_translations.py --tag ja --map scripts/language-packs/_tier23_pages_ja.json
  python _tier23_apply_pages_translations.py --tag ja --map ... --fill-from-en-blocked

Default: only write keys present in the map (plus structure). Prefer full maps.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

EN_PAGES = ROOT / "content/locales-ui/en/pages.json"
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


def set_path(tree: Dict[str, Any], dotted: str, text: str, en_hash: str) -> None:
    parts = dotted.split(".")
    node: Dict[str, Any] = tree
    for p in parts[:-1]:
        nxt = node.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            node[p] = nxt
        node = nxt
    node[parts[-1]] = {"text": text, "source_sha256": en_hash}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--map", required=True, help="JSON object key_path -> translated text")
    ap.add_argument(
        "--merge-existing",
        action="store_true",
        help="Merge into existing tag pages.json instead of rebuilding from map only",
    )
    args = ap.parse_args()
    tag = args.tag
    if tag not in ASSIGNED:
        print(f"refusing tag {tag} (not in assigned set)", file=sys.stderr)
        return 2
    if tag in {"en", "de", "fr", "es", "en-GB"}:
        print("refusing sibling-owned tag", file=sys.stderr)
        return 2

    en = load_json(EN_PAGES)
    en_flat = flatten_entries(en)
    raw_map = json.loads(Path(args.map).read_text(encoding="utf-8"))
    if not isinstance(raw_map, dict):
        print("map must be object", file=sys.stderr)
        return 2

    out: Dict[str, Any] = {}
    out_path = ROOT / "content/locales-ui" / tag / "pages.json"
    if args.merge_existing and out_path.exists():
        out = load_json(out_path)

    applied = 0
    skipped = 0
    for key, text in raw_map.items():
        if key not in en_flat:
            skipped += 1
            continue
        en_e = en_flat[key]
        en_text = en_e.get("text", "") if isinstance(en_e, dict) else str(en_e)
        h = en_e.get("source_sha256") if isinstance(en_e, dict) else ""
        if not h:
            h = source_sha256(en_text)
        set_path(out, key, str(text), h)
        applied += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(out_path, out)
    print(f"{tag}: applied={applied} skipped_unknown={skipped} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
