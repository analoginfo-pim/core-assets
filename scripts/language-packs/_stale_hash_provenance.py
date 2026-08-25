#!/usr/bin/env python3
"""Ask what text a stale `source_sha256` was actually computed from.

`binder:newInstance` reads stale in almost every pack while carrying a correct
translation of the current English. A stale hash on a correct translation is a
contradiction, so one of the two claims is wrong, and the hash is the cheaper one
to test: it is supposed to be `sha256` of the ENGLISH source, and there are only a
few other things it could plausibly be.

The applier's docstring already names the suspect -- earlier ad-hoc scripts
"stamped `source_sha256` over their own output" -- which would make the stored
value the hash of the translation rather than of English. That is testable
directly, and it matters enormously which answer comes back:

  * hash of own translation  -> the alarm is broken, the translations are fine,
                               and 14,900 "stale" leaves are a bookkeeping bug.
                               Re-stamping is mechanical and safe.
  * hash of unknown text     -> English really did move, and each leaf needs a
                               human to re-read it.

Reporting a bookkeeping bug as 14,900 translation defects would send a native
reviewer after thousands of correct strings, so this has to be settled first.
"""

from __future__ import annotations

import json
import sys
import unicodedata
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
    verdicts: Counter[str] = Counter()
    per_tag_self: Counter[str] = Counter()
    unknown_examples: list[str] = []

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            en = load(root / "en" / f"{namespace}.json")
            canon = {k: source_sha256(v["text"]) for k, v in en.items()}
            # Hash of every OTHER pack's rendering, so "stamped a sibling's text"
            # is distinguishable from "stamped its own".
            sibling: dict[str, dict[str, str]] = {}

            packs: dict[str, dict] = {}
            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                if tag_dir.name == "en":
                    continue
                packs[tag_dir.name] = load(tag_dir / f"{namespace}.json")

            for tag, pack in packs.items():
                for key, node in pack.items():
                    if key not in canon:
                        continue
                    got = node.get("source_sha256") or ""
                    if got == canon[key]:
                        continue
                    if not got:
                        verdicts["no hash recorded"] += 1
                        continue
                    if got == source_sha256(node["text"]):
                        verdicts["hash of its OWN translation"] += 1
                        per_tag_self[tag] += 1
                        continue
                    if key not in sibling:
                        sibling[key] = {}
                        for other, opack in packs.items():
                            onode = opack.get(key)
                            if onode:
                                sibling[key].setdefault(source_sha256(onode["text"]), other)
                    other = sibling[key].get(got)
                    if other:
                        verdicts[f"hash of another pack's text"] += 1
                        continue
                    verdicts["hash of text not present anywhere"] += 1
                    if len(unknown_examples) < 15:
                        unknown_examples.append(
                            f"  {tag:8s} {namespace}:{key}\n"
                            f"      en  {en[key]['text'][:120]}\n"
                            f"      {tag:3s} {node['text'][:120]}"
                        )

    print("\nwhat the stale hashes were computed from:")
    for name, n in verdicts.most_common():
        print(f"  {n:6d}  {name}")

    if per_tag_self:
        print("\nself-stamped (alarm broken, translation untouched) by pack:")
        for tag, n in sorted(per_tag_self.items()):
            print(f"  {tag:9s} {n:6d}")

    if unknown_examples:
        print("\nunexplained -- English may genuinely have moved:")
        for line in unknown_examples:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
