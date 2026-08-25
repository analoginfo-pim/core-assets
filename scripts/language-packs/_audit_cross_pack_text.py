#!/usr/bin/env python3
"""Find leaves where a pack ships another pack's language verbatim.

The existing wrong-language detector only knew about German, because German was
the pivot the MT pipeline ran through and German leakage was the defect in front
of us. Looking up the Met-clause convention in Hebrew and Polish turned up
Italian sentences sitting in both packs, which the German-only detector cannot
see and which no other gate can see either: the key exists, the placeholders
match, and the hash is whatever it is, so parity passes and the operator gets a
language they do not read.

Byte-identity to a *different* pack is the whole test, and it is decisive rather
than heuristic -- two independent translators do not produce the same bytes for a
sentence. That makes this reportable without a native speaker, unlike fluency or
register, which is exactly why it belongs in an automated gate.

Two cases are excluded because identity there is expected rather than wrong:

  * Matching `en` is a separate defect (untranslated English) and has its own
    detector; folding it in here would bury the cross-pack cases under it.
  * `en-GB` legitimately shares most bytes with `en`.

Single-token leaves are separated from multi-word ones. One word can be a real
shared borrowing across two languages -- "Status", "Token", "Audit" -- while a
whole sentence cannot, so mixing them would let arguable cognates dilute a
report that is otherwise provable.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
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
    show = "--list" in sys.argv
    # (victim, donor) -> count, so a systematic bleed is distinguishable from a
    # one-off paste.
    pairs: Counter[tuple[str, str]] = Counter()
    single: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], list[str]] = defaultdict(list)

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            packs: dict[str, dict] = {}
            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                if tag_dir.name in {"en", "en-GB"}:
                    continue
                packs[tag_dir.name] = load(tag_dir / f"{namespace}.json")

            english = load(root / "en" / f"{namespace}.json")

            for tag, pack in packs.items():
                for key, text in pack.items():
                    stripped = text.strip()
                    if not stripped or stripped == (english.get(key) or "").strip():
                        continue  # untranslated English: different defect, own detector
                    for other, opack in packs.items():
                        if other == tag:
                            continue
                        if (opack.get(key) or "").strip() != stripped:
                            continue
                        # Report each colliding pair once, in a stable direction.
                        if tag > other:
                            continue
                        bucket = single if len(stripped.split()) == 1 else pairs
                        bucket[(tag, other)] += 1
                        if len(stripped.split()) > 1 and len(examples[(tag, other)]) < 2:
                            examples[(tag, other)].append(
                                f"    {namespace}:{key}\n      {stripped[:150]}"
                            )

    print("\nidentical multi-word text shared between two different packs:")
    for (a, b), n in pairs.most_common():
        print(f"  {n:5d}  {a} == {b}")
        if show:
            for line in examples[(a, b)]:
                print(line)

    print(f"\n{sum(pairs.values())} multi-word collision(s) -- provably one of the two is wrong")
    print(f"{sum(single.values())} single-token collision(s) -- may be a shared borrowing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
