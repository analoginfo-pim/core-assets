#!/usr/bin/env python3
"""Prove the mojibake repair changed only what it was allowed to change.

Compares each repaired pack against its committed version leaf by leaf and asserts
four things, any of which failing means the repair overstepped:

  * the key set is identical -- no leaf added, none dropped
  * every `source_sha256` is byte-identical -- the English source was not touched
  * every changed `text` round-trips back to the committed text through a legacy
    code page -- so each edit is provably a decode fix, not a rewrite
  * placeholders are identical on both sides

Reads the committed copy with `git show` rather than a PowerShell redirect, because
piping through the console is the very code-page hazard being repaired.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_PAGES = ("cp437", "cp1252", "cp850")
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")

FILES = (
    "content/locales-ui/tr/help.json",
    "content/locales-ui/tr/components.json",
    "content/locales-ui/tr/ot.json",
    "content/locales-ui/tr/common.json",
)


def flatten(node, prefix=(), out=None):
    """Collect every leaf as key -> (text, source_sha256)."""
    if out is None:
        out = {}
    if not isinstance(node, dict):
        return out
    if isinstance(node.get("text"), str):
        out[".".join(prefix)] = (node["text"], node.get("source_sha256"))
        return out
    for key, value in node.items():
        flatten(value, prefix + (key,), out)
    return out


def committed(path: str) -> dict:
    raw = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    return flatten(json.loads(raw))


def is_decode_fix(before: str, after: str) -> bool:
    for page in LEGACY_PAGES:
        try:
            if before.encode(page).decode("utf-8") == after:
                return True
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return False


def main() -> int:
    problems: list[str] = []
    changed = unchanged = 0

    for rel in FILES:
        old = committed(rel)
        new = flatten(json.loads((ROOT / rel).read_text(encoding="utf-8")))

        if old.keys() != new.keys():
            added = sorted(new.keys() - old.keys())
            dropped = sorted(old.keys() - new.keys())
            problems.append(f"{rel}: key set moved (+{len(added)} / -{len(dropped)})")
            continue

        for key, (old_text, old_sha) in old.items():
            new_text, new_sha = new[key]
            if old_sha != new_sha:
                problems.append(f"{rel}:{key} source_sha256 changed")
            if old_text == new_text:
                unchanged += 1
                continue
            changed += 1
            if not is_decode_fix(old_text, new_text):
                problems.append(f"{rel}:{key} is not a pure decode fix\n    was {old_text!r}\n    now {new_text!r}")
            if PLACEHOLDER.findall(old_text) != PLACEHOLDER.findall(new_text):
                problems.append(f"{rel}:{key} placeholder set moved")

    print(f"{changed} leaf/leaves changed, {unchanged} untouched")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for line in problems[:25]:
            print(f"  {line}")
        return 1
    print("clean: every edit is a provable decode fix, no hash or placeholder moved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
