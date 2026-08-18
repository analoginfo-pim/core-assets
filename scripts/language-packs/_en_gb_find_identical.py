#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

def flat(n, p=""):
    o = {}
    if isinstance(n, dict):
        if "text" in n and isinstance(n.get("text"), str):
            o[p] = n
            return o
        for k, v in n.items():
            o.update(flat(v, f"{p}.{k}" if p else k))
    elif isinstance(n, list):
        for i, item in enumerate(n):
            o.update(flat(item, f"{p}[{i}]"))
    return o

AREA = [
    ("locales", Path("content/locales")),
    ("locales-ui", Path("content/locales-ui")),
    ("gui", Path("content/i18n-native/gui")),
    ("agent", Path("content/i18n-native/apps/pim-offline-agent")),
    ("recording", Path("content/i18n-native/apps/pim-offline-recording-agent")),
    ("jump", Path("content/i18n-native/apps/pim-jump-server")),
    ("dbmgmt", Path("content/i18n-native/apps/pim-db-mgmt-agent")),
]
ident = []
for area, base in AREA:
    en_dir, gb_dir = base / "en", base / "en-GB"
    if not en_dir.is_dir() or not gb_dir.is_dir():
        continue
    for p in sorted(en_dir.glob("*.json")):
        gb = gb_dir / p.name
        if not gb.exists():
            continue
        ef = flat(json.loads(p.read_text(encoding="utf-8")))
        gf = flat(json.loads(gb.read_text(encoding="utf-8")))
        for k, e in ef.items():
            g = gf.get(k)
            if g and g.get("text") == e.get("text"):
                ident.append({"area": area, "file": p.name, "key": k, "text": e["text"], "len": len(e["text"])})
print("identical", len(ident))
print("long>40", sum(1 for x in ident if x["len"] > 40))
print("med15-40", sum(1 for x in ident if 15 < x["len"] <= 40))
print("short<=15", sum(1 for x in ident if x["len"] <= 15))
Path("scripts/language-packs/_en_gb_identical.json").write_text(json.dumps(ident, ensure_ascii=False, indent=2), encoding="utf-8")
long = [x for x in ident if x["len"] > 40]
print("LONG:")
for x in long[:20]:
    print(x["area"], x["file"], x["key"], repr(x["text"][:100]))
