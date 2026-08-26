#!/usr/bin/env python3
"""Find English catalog entries that were cut off by a quote-terminated parser.

content/locales-ui/en/pages.json ships:

    chrome.controlState.driftHelp = 'Drift means a control'

The code declares:

    "Drift means a control's evidence delivery regressed between two
     observations. It is not a finding and not a failed control."

The catalog text is a strict prefix of the code text, and it ends at exactly the
character where the code has an apostrophe. That is not an editorial decision, a
translation, or a style change -- it is a harvester that read the string with a
naive quote-delimited scan and stopped at the first inner quote.

This matters more than a truncated label looks. The clauses being deleted are the
honesty clauses:

    "... It is not a finding and not a failed control."
    "... They are not a claim that awareness training is satisfied."

Those sentences exist so an assessor is not told a control passed. Removing them
is a compliance defect, not a typo. And because the packs were translated from
the truncated English, every language dropped the same sentences.

The test needs no judgment at all:

    en_text is a strict prefix of code_text
    AND code_text[len(en_text)] is an apostrophe or a double quote

Both conditions together are proof. A human abbreviating a label does not
reliably stop on the quote character.

Usage: _audit_en_truncation.py [--ui-src PATH] [--fix]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _en_drift_provenance import code_defaults, leaf_at  # noqa: E402
from _audit_en_vs_code import DEFAULT_UI_SRC  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"

QUOTES = "'\"\u2019\u201c\u201d"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def set_leaf(node: dict, key: str, text: str) -> bool:
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    if not isinstance(node, dict) or "text" not in node:
        return False
    node["text"] = text
    node["source_sha256"] = sha(text)
    return True


def main() -> int:
    argv = sys.argv[1:]
    ui_src = Path(argv[argv.index("--ui-src") + 1] if "--ui-src" in argv else DEFAULT_UI_SRC)
    do_fix = "--fix" in argv

    defaults = code_defaults(ui_src)

    english: dict[str, dict] = {}
    for path in sorted((CATALOG / "en").glob("*.json")):
        english[path.stem] = json.loads(path.read_text(encoding="utf-8"))

    hits: list[tuple[str, str, str, str, str]] = []

    for (namespace, key), code_text in sorted(defaults.items()):
        if namespace not in english:
            continue
        leaf = leaf_at(english[namespace], key)
        if leaf is None:
            continue
        en_text = leaf["text"]
        if en_text == code_text or not en_text:
            continue
        if not code_text.startswith(en_text):
            continue
        cut = code_text[len(en_text)]
        if cut not in QUOTES:
            continue
        lost = code_text[len(en_text):]
        hits.append((namespace, key, en_text, code_text, lost))

    print(f"{len(hits)} English entr(ies) truncated at a quote character\n")

    by_ns: dict[str, int] = {}
    lost_chars = 0
    for namespace, _, _, _, lost in hits:
        by_ns[namespace] = by_ns.get(namespace, 0) + 1
        lost_chars += len(lost)
    for namespace, count in sorted(by_ns.items(), key=lambda kv: -kv[1]):
        print(f"  {namespace:12s} {count}")
    print(f"\n  {lost_chars} characters of English deleted from the catalog\n")

    for namespace, key, en_text, code_text, lost in hits:
        print(f"  {namespace} :: {key}")
        print(f"      kept {en_text!r}")
        print(f"      lost {lost!r}")

    if not do_fix:
        print("\n(dry run -- pass --fix to restore the code text)")
        return 0

    changed: dict[str, int] = {}
    for namespace, key, _, code_text, _ in hits:
        if set_leaf(english[namespace], key, code_text):
            changed[namespace] = changed.get(namespace, 0) + 1

    for namespace, count in changed.items():
        path = CATALOG / "en" / f"{namespace}.json"
        path.write_text(
            json.dumps(english[namespace], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nrestored {count} leaf(s) in {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
