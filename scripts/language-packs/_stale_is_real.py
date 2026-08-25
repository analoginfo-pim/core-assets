#!/usr/bin/env python3
"""Decide whether a stale hash means English changed, or only that hashing did.

The census reports 19,639 stale leaves, and the applier's own docstring records
that earlier ad-hoc scripts stamped hashes over their own output and "turned the
drift gate into noise." Both facts can be true, and they lead to opposite
conclusions: either thousands of translations describe superseded behavior, or
the alarm is broken and the translations are fine. Acting on the wrong one is
expensive in both directions.

The two are distinguishable. A hash recorded from *some* English text can be
tested against candidate normalizations of today's English -- NFC/NFD, collapsed
whitespace, stripped ends. If a variant reproduces the stored hash, English never
changed and the mismatch is a formatting artifact in the hashing path. If nothing
reproduces it, the stored hash came from text that genuinely no longer exists.

Only the second class is a translation defect. Reporting them together would put
a normalization bug and a content-drift bug in one bucket and guarantee that
whichever is smaller gets buried.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from language_packs import source_sha256  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")
WS = re.compile(r"\s+")


def variants(text: str) -> dict[str, str]:
    """Plausible spellings of the same English, as a hashing path might have seen it."""
    out = {
        "nfc": unicodedata.normalize("NFC", text),
        "nfd": unicodedata.normalize("NFD", text),
        "nfkc": unicodedata.normalize("NFKC", text),
        "strip": text.strip(),
        "collapse-ws": WS.sub(" ", text).strip(),
        "crlf": text.replace("\n", "\r\n"),
        "no-nbsp": text.replace("\u00a0", " "),
    }
    return {k: v for k, v in out.items() if v != text}


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
    show = "--list" in sys.argv
    artifact: Counter[str] = Counter()
    real = 0
    real_keys: Counter[str] = Counter()
    shown = 0

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            en = load(root / "en" / f"{namespace}.json")
            canon = {k: source_sha256(v["text"]) for k, v in en.items()}
            # Hash each variant once per English string, not once per pack.
            alt: dict[str, dict[str, str]] = {}
            for k, v in en.items():
                alt[k] = {source_sha256(t): name for name, t in variants(v["text"]).items()}

            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                tag = tag_dir.name
                if tag == "en":
                    continue
                for key, node in load(tag_dir / f"{namespace}.json").items():
                    if key not in canon:
                        continue
                    got = node.get("source_sha256") or ""
                    if got == canon[key]:
                        continue
                    if not got:
                        artifact["(no hash recorded)"] += 1
                        continue
                    hit = alt[key].get(got)
                    if hit:
                        artifact[hit] += 1
                        continue
                    real += 1
                    real_keys[f"{root.name}/{namespace}:{key}"] += 1
                    if show and shown < 12:
                        shown += 1
                        print(f"\n{tag:8s} {namespace}:{key}")
                        print(f"  en now  {en[key]['text'][:150]}")
                        print(f"  {tag:6s}  {node['text'][:150]}")

    print("\nmismatches explained by a hashing/normalization difference:")
    for name, n in artifact.most_common():
        print(f"  {n:6d}  {name}")
    print(f"\n{real} mismatch(es) NOT explained by normalization -- English genuinely changed")
    print(f"  across {len(real_keys)} distinct English string(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
