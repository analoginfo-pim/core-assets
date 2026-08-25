#!/usr/bin/env python3
"""Show, per pack, the wording it already uses for the concepts the tiles describe.

The eighteen tile descriptions are new keys, so no pack has a translation to
copy. But the pages those tiles link to are already translated, and they already
name the same things -- a tabletop exercise, a degauss certificate, a WORM
store, the honesty clause. Drafting a tile without looking at them produces a
tile whose vocabulary disagrees with the page it opens, and an operator reading
"Notfallübung" on the tile and something else on the page has no way to know
they are the same feature.

So this prints the donor leaves grouped by pack: the workflow titles and
summaries that mirror six of the tiles, the intake and supplier-register
honesty clauses, and each pack's established rendering of the disclaimer. The
drafts are then written in the pack's own words rather than in a translator's.

Usage: _dump_tile_donors.py <tag> [tag ...]
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path("content/locales-ui")

DONORS = [
    ("compliance", "coverageWorkflow.ps.title"),
    ("compliance", "coverageWorkflow.ps.summary"),
    ("compliance", "coverageWorkflow.at.title"),
    ("compliance", "coverageWorkflow.at.summary"),
    ("compliance", "coverageWorkflow.ma.title"),
    ("compliance", "coverageWorkflow.ma.summary"),
    ("compliance", "coverageWorkflow.cp.title"),
    ("compliance", "coverageWorkflow.cp.summary"),
    ("compliance", "coverageWorkflow.ca.title"),
    ("compliance", "coverageWorkflow.ca.summary"),
    ("compliance", "coverageWorkflow.pe.title"),
    ("compliance", "coverageWorkflow.pe.summary"),
    ("compliance", "coverageWorkflow.honesty"),
    ("compliance", "coverageIntake.summary"),
    ("compliance", "coverageIntake.honesty"),
    ("compliance", "supplierRegister.honesty"),
    ("components", "sectionLanding.desc.data_flow_mapping"),
    ("components", "sectionLanding.desc.media_destruction_page"),
    ("components", "sectionLanding.desc.retention"),
]


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    out = {} if out is None else out
    for key, value in (obj or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and isinstance(value.get("text"), str):
            out[path] = value["text"]
        elif isinstance(value, dict):
            flatten(value, path, out)
    return out


def load(tag: str, namespace: str) -> dict:
    path = ROOT / tag / f"{namespace}.json"
    if not path.is_file():
        return {}
    return flatten(json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    tags = sys.argv[1:]
    if not tags:
        print(__doc__.strip())
        return 2
    cache: dict[tuple[str, str], dict] = {}

    def get(tag: str, namespace: str) -> dict:
        if (tag, namespace) not in cache:
            cache[(tag, namespace)] = load(tag, namespace)
        return cache[(tag, namespace)]

    for tag in tags:
        print(f"########## {tag} ##########")
        for namespace, key in DONORS:
            english = get("en", namespace).get(key)
            rendered = get(tag, namespace).get(key)
            if english is None and rendered is None:
                continue
            print(f"-- {namespace}:{key}")
            if english:
                print(f"   en  {english}")
            print(f"   {tag:6} {rendered if rendered else '(ABSENT)'}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
