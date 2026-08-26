#!/usr/bin/env python3
"""Build the repair batch for ipScanner leaves that lost their placeholders.

_gen_placeholder_repair.py splits placeholder mismatches into two classes and can
only fix one of them. A leaf whose identifier was *renamed* (`{{label}}` ->
`{{network}}`) keeps correct prose and repairs mechanically. A leaf that *dropped*
the placeholder cannot: `ipScanner.progressLog` says "entries" in five packs with
no `{{count}}` anywhere, and `analysisSummary` collapses four counts
(`analyzed`, `known`, `unknown`, `findings`) into one invented `{{count}}`.

Restoring the token means giving it a grammatical home, which is translation, not
a rename. Inventing that prose is exactly what produced the pidgin this cleanup
exists to remove, so this writes the *English source* into the target packs
instead and queues the leaves for native review.

That is deliberately a visible regression in kind: the operator reads English on
those eight strings rather than a sentence that silently drops a count, or braces
rendered literally on screen. Both alternatives are worse, and only this one is
honest about being unfinished.

Scope is the five SPA tags the parity gate covers. The same eight keys are broken
in ar/fi/ja/nl/sv/tr, which the gate does not check; those are queued rather than
touched here so this change stays reviewable.

Usage: _gen_ipscanner_dropped.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
OUT = ROOT / "content" / "language-packs" / "batches"

# The gate-blocking tags. en-GB is derived from en and is already clean.
TAGS = ["de", "es", "fr", "zh-Hans", "zh-TW"]

KEYS = [
    "ipScanner.analysisComplete",
    "ipScanner.analysisSummary",
    "ipScanner.checkDefaultsAria",
    "ipScanner.engineReady",
    "ipScanner.networksPicker",
    "ipScanner.probesHostsWorkers",
    "ipScanner.progressLog",
    "ipScanner.trackPoamAria",
]

PLACEHOLDER = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")


def descend(node, dotted: str):
    for step in dotted.split("."):
        if not isinstance(node, dict) or step not in node:
            return None
        node = node[step]
    return node


def main() -> int:
    en = json.loads((UI / "en" / "pages.json").read_text(encoding="utf-8"))

    source: dict[str, str] = {}
    for key in KEYS:
        leaf = descend(en, key)
        if not isinstance(leaf, dict) or not isinstance(leaf.get("text"), str):
            print(f"MISSING in en: {key}")
            return 1
        source[key] = leaf["text"]

    batch = {
        "_comment": (
            "These eight leaves dropped their interpolation placeholders during "
            "machine translation, so the rendered sentence silently omitted a count "
            "(progressLog lost {{count}}; analysisSummary collapsed four counts into "
            "one invented {{count}}). Restoring the token requires rewriting the "
            "sentence to give it a grammatical home, which is translation work and "
            "not a mechanical rename, so the English source is written here and the "
            "leaves are queued for native review. Reading English on these strings "
            "is a visible gap; reading a sentence that drops a count, or literal "
            "braces on screen, is a silent defect. AGENT DRAFT - not native review."
        ),
        "area": "locales-ui",
        "namespace": "pages",
        "source": source,
        "translations": {tag: dict(source) for tag in TAGS},
    }

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "ipscanner-dropped-placeholders-20260825.json"
    path.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"wrote {path.name}: {len(KEYS)} keys x {len(TAGS)} tags = {len(KEYS) * len(TAGS)} leaves")
    for key, text in source.items():
        found = ",".join(sorted(set(PLACEHOLDER.findall(text)))) or "(none)"
        print(f"  {key:34} [{found}]  {text[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
