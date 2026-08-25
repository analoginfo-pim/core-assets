"""Self-check the Simplified/Traditional character lists in _check_cjk_variant.py.

A character that appears in *both* lists is a character that was never
simplified -- it is written identically in Simplified and Traditional Chinese.
Leaving it in either list makes the variant checker reject correct text, which
is how a legitimate translation gets rewritten into a wrong one to satisfy a
broken gate.

Run this after editing either list.
"""

from __future__ import annotations

import pathlib
import re
import sys

CHECKER = pathlib.Path(__file__).with_name("_check_cjk_variant.py")


def extract(src: str, name: str) -> str:
    match = re.search(name + r' = "([^"]*)"', src)
    if match is None:
        raise SystemExit(f"error: could not find {name} in {CHECKER}")
    return match.group(1)


def main() -> int:
    src = CHECKER.read_text(encoding="utf-8")
    simplified = extract(src, "SIMPLIFIED_ONLY")
    traditional = extract(src, "TRADITIONAL_ONLY")

    shared = [c for c in simplified if c in traditional]
    dup_s = sorted({c for c in simplified if simplified.count(c) > 1})
    dup_t = sorted({c for c in traditional if traditional.count(c) > 1})

    print(f"SIMPLIFIED_ONLY  {len(simplified)} char(s)")
    print(f"TRADITIONAL_ONLY {len(traditional)} char(s)")

    problems = 0
    if shared:
        problems += len(shared)
        print(f"\nin BOTH lists -- not variant pairs, remove from both: {''.join(shared)}")
        for c in shared:
            print(f"    U+{ord(c):04X}  {c}")
    if dup_s:
        problems += len(dup_s)
        print(f"\nrepeated inside SIMPLIFIED_ONLY: {''.join(dup_s)}")
    if dup_t:
        problems += len(dup_t)
        print(f"\nrepeated inside TRADITIONAL_ONLY: {''.join(dup_t)}")

    if problems == 0:
        print("\nlists are clean")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
