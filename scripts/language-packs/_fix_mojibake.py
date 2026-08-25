#!/usr/bin/env python3
"""Repair wrong-code-page mojibake in place, and report the blast radius.

Detection and repair are the same operation: a leaf is mojibake exactly when its
characters re-encode cleanly into a legacy code page and that byte string decodes
as UTF-8 into different text with no replacement character. The decoded text *is*
the repair -- there is no translation judgment here, so this runs unattended.

Two guards keep it honest:

  * The repair must be idempotent. Re-running the round trip on the decoded text
    must not find a second layer, or the text was double-encoded and needs a human
    to decide how many layers to peel.
  * Placeholders must survive. `{{name}}` is ASCII and cannot be touched by a
    code-page fix, so any change to the placeholder set means the round trip
    escaped its lane and the leaf is skipped.

`--apply` writes; the default run only reports.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
SERVER = ROOT / "content" / "locales"

LEGACY_PAGES = ("cp437", "cp1252", "cp850")
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")


def repaired(text: str) -> str | None:
    for page in LEGACY_PAGES:
        try:
            raw = text.encode(page)
        except UnicodeEncodeError:
            continue
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if decoded != text and "\ufffd" not in decoded:
            return decoded
    return None


def walk(node, on_leaf, path=()):
    """Visit every {"text": str} leaf, letting on_leaf return a replacement."""
    if not isinstance(node, dict):
        return
    if isinstance(node.get("text"), str):
        new = on_leaf(".".join(path), node["text"])
        if new is not None:
            node["text"] = new
        return
    for key, value in node.items():
        walk(value, on_leaf, path + (key,))


def main() -> int:
    apply = "--apply" in sys.argv
    per_file: Counter[str] = Counter()
    skipped: list[str] = []
    fixed = 0

    for root in (UI, SERVER):
        if not root.is_dir():
            continue
        for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if tag_dir.name == "en":
                continue  # English is the source; a mojibake en leaf is a different bug
            for path in sorted(tag_dir.glob("*.json")):
                doc = json.loads(path.read_text(encoding="utf-8"))
                label = f"{root.name}/{tag_dir.name}/{path.name}"
                changed = 0

                def on_leaf(key: str, text: str) -> str | None:
                    nonlocal changed
                    if text.isascii():
                        return None
                    once = repaired(text)
                    if once is None:
                        return None
                    if repaired(once) is not None:
                        skipped.append(f"{label}:{key} (double-encoded)")
                        return None
                    if PLACEHOLDER.findall(once) != PLACEHOLDER.findall(text):
                        skipped.append(f"{label}:{key} (placeholder drift)")
                        return None
                    changed += 1
                    return once

                walk(doc, on_leaf)
                if changed:
                    per_file[label] = changed
                    fixed += changed
                    if apply:
                        path.write_text(
                            json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )

    for label, count in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{count:5d}  {label}")
    print(f"\n{fixed} leaf/leaves {'repaired' if apply else 'would be repaired'}")
    if skipped:
        print(f"\n{len(skipped)} skipped for human review:")
        for line in skipped[:20]:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
