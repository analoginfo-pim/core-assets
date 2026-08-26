#!/usr/bin/env python3
"""Find leaves that are the English string wearing a different amount of whitespace.

The residue detector compares bytes, so a leaf that copied the English sentence and
appended one trailing space is invisible to it: not equal to English, therefore
assumed translated. The pidgin detector caught these at 100% retention, which is the
clue that they are not translations at all.

This separates the two cases so a report can be honest about which it is:

    IDENTICAL   differs from English only in leading/trailing/collapsed whitespace
    PIDGIN      genuinely different words, measured elsewhere

Usage: _audit_whitespace_residue.py [--tag a,b] [--fix]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}

SPACE = re.compile(r"\s+")


def leaves(node: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            return [(prefix, node["text"])]
        for key, value in node.items():
            out.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
    return out


def squeeze(text: str) -> str:
    return SPACE.sub(" ", text).strip()


def main() -> int:
    argv = sys.argv[1:]
    only = [t for t in (argv[argv.index("--tag") + 1] if "--tag" in argv else "").split(",") if t]

    per_tag: dict[str, int] = {}
    samples: list[tuple[str, str, str, str, str]] = []

    for area, root in ROOTS.items():
        if not root.is_dir():
            continue
        en_dir = root / "en"
        if not en_dir.is_dir():
            continue
        tags = sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and p.name not in {"en", "en-GB"} and (not only or p.name in only)
        )
        for en_file in sorted(en_dir.glob("*.json")):
            namespace = en_file.stem
            english = dict(leaves(json.loads(en_file.read_text(encoding="utf-8"))))
            for tag in tags:
                path = root / tag / f"{namespace}.json"
                if not path.is_file():
                    continue
                pack = dict(leaves(json.loads(path.read_text(encoding="utf-8"))))
                for key, text in pack.items():
                    en_text = english.get(key)
                    if en_text is None or text == en_text:
                        continue  # missing, or plain residue the other detector owns
                    if squeeze(text) == squeeze(en_text):
                        per_tag[tag] = per_tag.get(tag, 0) + 1
                        if len(samples) < 12:
                            samples.append((area, tag, namespace, key, text))

    total = sum(per_tag.values())
    print(f"{total} leaf(s) are English differing only in whitespace\n")
    for tag, count in sorted(per_tag.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:9s} {count}")

    print()
    for area, tag, namespace, key, text in samples:
        print(f"  {tag:7s} {area}/{namespace} :: {key}")
        print(f"          {text!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
