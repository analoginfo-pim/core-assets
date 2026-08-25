#!/usr/bin/env python3
"""Dump German-pivot keys with their English source and affected packs.

Authoring a repair batch needs three things per leaf that the audit prints only
in summary: the English source to translate from, the German text to be sure the
replacement actually differs from it, and the exact list of packs that carry the
corruption. Printing them together avoids the alternative, which is re-deriving
the pack list by hand per key and getting it subtly wrong -- a batch that names a
pack whose leaf is already clean would overwrite a good translation with a draft.

Namespace filtering exists because the corruption clusters by vocabulary rather
than spreading evenly. The `risks` namespace is one coherent risk-register
glossary -- likelihood, impact, acceptance, mitigate, avoid -- and translating it
as a set produces consistent terminology, where translating the same words
scattered across four batches invites four different renderings of "Accept".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    if out is None:
        out = {}
    for k, v in (obj or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            out[key] = v["text"]
        elif isinstance(v, dict):
            flatten(v, key, out)
    return out


def load(path: Path) -> dict:
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    want = sys.argv[1] if len(sys.argv) > 1 else None

    leaves = 0
    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            if want and namespace != want:
                continue
            english = load(root / "en" / f"{namespace}.json")
            german = load(root / "de" / f"{namespace}.json")
            if not german:
                continue

            packs = {
                d.name: load(d / f"{namespace}.json")
                for d in sorted(p for p in root.iterdir() if p.is_dir())
                if d.name not in {"en", "en-GB", "de"}
            }

            for key, de_text in sorted(german.items()):
                de_stripped = de_text.strip()
                en_stripped = (english.get(key) or "").strip()
                if not de_stripped or de_stripped == en_stripped:
                    continue
                agreeing = sorted(
                    tag for tag, pack in packs.items()
                    if (pack.get(key) or "").strip() == de_stripped
                )
                if len(agreeing) < 2:
                    continue
                leaves += len(agreeing)
                print(f"{namespace}:{key}")
                print(f"  en  {en_stripped}")
                print(f"  de  {de_stripped}")
                print(f"  ->  {' '.join(agreeing)}")

    print(f"\n{leaves} leaf/leaves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
