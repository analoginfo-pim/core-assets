#!/usr/bin/env python3
"""Harvest pages-namespace English defaultValues from SPA TS/TSX."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"c:\analog-pim\pim-offline-server\ui\src")
OUT = Path(r"c:\analog-pim\core-assets\scripts\language-packs\_tier1_harvest_pages_en.json")

# t('key', { defaultValue: '...' })  — single or double quotes, key may be pages:key
PAT_DV = re.compile(
    r"""t\(\s*['\"](?:pages:)?([a-zA-Z0-9_.-]+)['\"]\s*,\s*\{[^}]*?defaultValue\s*:\s*['\"]((?:\\.|[^'\\\"])*)['\"]""",
    re.S,
)
# t('key', 'English literal')
PAT_LIT = re.compile(
    r"""t\(\s*['\"](?:pages:)?([a-zA-Z0-9_.-]+)['\"]\s*,\s*['\"]((?:\\.|[^'\\\"])*)['\"]""",
)

found: dict[str, str] = {}
for path in list(ROOT.rglob("*.tsx")) + list(ROOT.rglob("*.ts")):
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in PAT_DV.finditer(text):
        found[m.group(1)] = bytes(m.group(2), "utf-8").decode("unicode_escape")
    for m in PAT_LIT.finditer(text):
        k, v = m.group(1), m.group(2)
        if k not in found:
            found[k] = bytes(v, "utf-8").decode("unicode_escape")

OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {len(found)} keys -> {OUT}")
# show header-ish
hdr = {k: v for k, v in found.items() if k.startswith("headers.")}
print("headers.*", len(hdr))
chrome = {k: v for k, v in found.items() if k.startswith("chrome.")}
print("chrome.*", len(chrome))
for k in list(sorted(hdr))[:8]:
    print(k, "=>", hdr[k][:70])
