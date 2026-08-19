"""Analyze Tier1 walk missing-by-locale.json buckets."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

p = Path(
    r"c:\analog-pim\pim-offline-server\docs\dev\evidence"
    r"\language-pack-tier1-walk-20260818\missing-by-locale.json"
)
data = json.loads(p.read_text(encoding="utf-8"))


def is_control(k: str) -> bool:
    return bool(
        re.match(r"^[\d.]+e?$", k)
        or re.match(
            r"^(AC|AU|CM|IA|SC|SI|AT|CA|CP|IR|MA|MP|PE|PL|PS|PT|RA|SA|PM)-",
            k,
            re.I,
        )
        or k.upper().startswith("CMMC")
        or "L2-" in k
        or re.match(r"^\d+\.\d+", k)
    )


for lng in ["de", "fr", "es", "en-GB"]:
    d = data[lng]
    allids: set[str] = set()
    for v in d["byRoute"].values():
        for x in v:
            allids.add(x.split(":", 1)[1] if ":" in x else x)
    ns: Counter[str] = Counter()
    samples: dict[str, list[str]] = {}
    for k in allids:
        if k.startswith(("headers.", "chrome.", "delivery.")):
            bucket = "pages"
        elif is_control(k):
            bucket = "controls"
        elif "." not in k:
            bucket = "bare"
        else:
            bucket = "other"
        ns[bucket] += 1
        samples.setdefault(bucket, [])
        if len(samples[bucket]) < 8:
            samples[bucket].append(k)
    print(
        f"{lng}: unique={d['uniqueMissingIds']} "
        f"routesMissing={d['routesWithMissing']} "
        f"nav={d.get('routesNavError')} buckets={dict(ns)}"
    )
    for b, ids in samples.items():
        print(f"  {b}: {ids}")
