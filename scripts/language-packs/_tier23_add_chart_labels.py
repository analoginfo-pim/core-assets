#!/usr/bin/env python3
"""
Add dashboard chartLabels keys to assigned Tier 2/3 tags only.

Keys (US English source):
  OtInventoryListed
  SecureShareList
  SecureShareBreakGlassPolicyRead
  NetworkScanJobStart

Does not touch en/de/fr/es/en-GB.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSIGNED = [
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
]
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

# Formal US English chart series labels (operator-facing).
EN: dict[str, str] = {
    "OtInventoryListed": "OT inventory listed",
    "SecureShareList": "Secure share list",
    "SecureShareBreakGlassPolicyRead": "Secure share break-glass policy read",
    "NetworkScanJobStart": "Network scan job started",
}


def source_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    from deep_translator import GoogleTranslator

    for tag in ASSIGNED:
        path = ROOT / "content/locales-ui" / tag / "dashboard.json"
        if not path.exists():
            print(f"skip missing {path}", file=sys.stderr)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        charts = data.setdefault("chartLabels", {})
        if not isinstance(charts, dict):
            print(f"bad chartLabels in {tag}", file=sys.stderr)
            continue
        tr = GoogleTranslator(source="en", target=GOOGLE_LANG[tag])
        added = 0
        for key, en_text in EN.items():
            h = source_sha256(en_text)
            existing = charts.get(key)
            if (
                isinstance(existing, dict)
                and existing.get("text")
                and existing.get("source_sha256") == h
            ):
                continue
            try:
                text = tr.translate(en_text)
            except Exception as exc:  # noqa: BLE001
                print(f"WARN {tag}/{key}: {exc}", file=sys.stderr)
                text = en_text
            charts[key] = {"text": text, "source_sha256": h}
            added += 1
            time.sleep(0.05)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{tag}: added/updated {added} chartLabels -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
