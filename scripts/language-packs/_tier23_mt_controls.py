#!/usr/bin/env python3
"""Build locales-ui/<tag>/controls.json from ui controlTitles.en.json via MT."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, source_sha256  # noqa: E402

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
EN_TITLES = Path(
    r"c:\analog-pim\pim-offline-server\ui\src\i18n\controlTitles.en.json"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--sleep", type=float, default=0.04)
    args = ap.parse_args()
    tag = args.tag
    if tag not in ASSIGNED:
        print("refusing", tag, file=sys.stderr)
        return 2

    from deep_translator import GoogleTranslator

    en = json.loads(EN_TITLES.read_text(encoding="utf-8"))
    translator = GoogleTranslator(source="en", target=GOOGLE_LANG[tag])
    out = {}
    for i, (cid, title) in enumerate(en.items(), 1):
        h = source_sha256(title)
        try:
            tr = translator.translate(title)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN {cid}: {exc}", file=sys.stderr)
            tr = title
        out[cid] = {"text": tr, "source_sha256": h}
        time.sleep(args.sleep)
        if i % 20 == 0:
            print(f"{tag} controls {i}/{len(en)}", flush=True)
    path = ROOT / "content/locales-ui" / tag / "controls.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, out)
    print(f"wrote {path} ({len(out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
