#!/usr/bin/env python3
"""Count leaves translated from English that no longer exists.

`source_sha256` is the drift alarm, and the enhanced-controls defect proved the
alarm works: the thirteen packs rendering "list" as "listen" and dropping the
Met clause were all stale, and the four correct packs were current. The alarm
fired years' worth of times and nobody read it, which made it functionally
identical to no alarm.

So the useful question is not "is this leaf stale" -- one command already answers
that -- but "how much of the shipped product is a translation of text that has
since been rewritten". A stale leaf is not garbled and not missing. It reads
fluently and describes behavior the product may no longer have, which is the one
failure mode a parity gate, a mojibake detector, and a placeholder check all pass
over in silence.

Sorted by count so triage starts where the operator-visible surface is widest.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from language_packs import source_sha256  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    if out is None:
        out = {}
    for k, v in (obj or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            out[key] = v
        elif isinstance(v, dict):
            flatten(v, key, out)
    return out


def load(path: Path) -> dict:
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    verbose = "--list" in sys.argv
    stale_per_tag: Counter[str] = Counter()
    total_per_tag: Counter[str] = Counter()
    stale_per_key: Counter[str] = Counter()

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            en = load(root / "en" / f"{namespace}.json")
            want = {k: source_sha256(v["text"]) for k, v in en.items()}
            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                tag = tag_dir.name
                if tag == "en":
                    continue
                pack = load(tag_dir / f"{namespace}.json")
                for key, node in pack.items():
                    if key not in want:
                        continue
                    total_per_tag[tag] += 1
                    if (node.get("source_sha256") or "") != want[key]:
                        stale_per_tag[tag] += 1
                        stale_per_key[f"{root.name}/{namespace}:{key}"] += 1

    print(f"\n{'tag':9s} {'leaves':>8s} {'stale':>8s} {'share':>7s}")
    for tag in sorted(total_per_tag):
        total = total_per_tag[tag]
        print(f"{tag:9s} {total:8d} {stale_per_tag[tag]:8d} {stale_per_tag[tag] / total:6.1%}")

    print(
        f"\n{sum(stale_per_tag.values())} stale leaf/leaves across "
        f"{len(stale_per_key)} distinct English string(s)"
    )
    if verbose:
        print("\nwidest surface first (packs affected x key):")
        for key, n in stale_per_key.most_common(40):
            print(f"  {n:3d}  {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
