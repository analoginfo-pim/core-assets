#!/usr/bin/env python3
"""Restore the two en page bullets that shipped German, and mark the cascade stale.

Provenance for these two leaves, proved by _audit_en_german_overlap.py and
_probe_leaf.py: de is the real source (it alone carries no source hash), en was
produced from de by swapping a handful of function words (oder -> or, nicht ->
not, und -> and) and then re-hashed as if it were authored, so every digest check
passes it. en-GB copied en verbatim. Thirteen packs were then translated from
that pidgin en, and the results are not merely awkward:

    zh-Hans  "...Konfiguratoren 的坚果味"   nutty flavor -- nutzen read as "nuts"
    pl       "...i szerszy ruft danach"     widerruft read as "wider"
    fr       "n'utilise pas WinRM"          negation inverted; states the opposite
    ja       (elevation) pidgin en verbatim, never translated

The English in ui/src/help/pageIntros.ts is authoritative for page headers, so
this restores en and en-GB from it. Downstream text is deliberately left alone:
authoring eleven languages here would be an agent draft, and agent drafts do not
close localization work. What the fix does do is make the staleness detectable --
once en holds the real English, the downstream stored hashes no longer match it,
so the existing provenance tooling reports them instead of waving them through.

Both catalog trees are written: core-assets is the source of truth and the copy
under the server UI is what actually ships, and a fix applied to only one of them
would be reverted by the next sync in whichever direction ran last.

Usage:
    python _fix_en_pages_german_leak.py            # report
    python _fix_en_pages_german_leak.py --apply
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "content" / "locales-ui"
UI = (
    Path(__file__).resolve().parents[3]
    / "pim-offline-server"
    / "ui"
    / "src"
    / "i18n"
    / "locales"
)

# Authoritative English, quoted from ui/src/help/pageIntros.ts.
#   '/settings/agent/management' bullets[0]  (line 198)
#   '/elevation'                 bullets[1]  (line 455)
FIXES: dict[tuple[str, str], str] = {
    (
        "pages",
        "headers.settings__agent__management.bullets.text[0]",
    ): "Disconnected / air-gapped hosts still use local Tauri, Win32, or CLI configurators.",
    (
        "pages",
        "headers.elevation.bullets.text[1]",
    ): "Remote Non-Agent Local Elevation uses WinRM — not the agent pipe — then auto-revokes.",
}

# Neither sentence contains a word that UK English spells differently
# (air-gapped, configurators, revokes are identical), so en-GB derives to the
# same text. Deriving it explicitly rather than copying keeps the reason on the
# record: en-GB is a derivation of en, never an independent translation.
DERIVED = ("en", "en-GB")


def digest(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def resolve(node, dotted: str):
    """Walk a dotted path with [n] indices, returning the containing leaf dict."""
    for part in dotted.replace("[", ".").replace("]", "").split("."):
        if not part:
            continue
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def main() -> int:
    apply = "--apply" in sys.argv[1:]
    changed = 0
    stale: dict[str, int] = {}

    for label, root in (("core-assets", CORE), ("ui/src/i18n", UI)):
        if not root.is_dir():
            print(f"{label}: tree absent, skipped")
            continue
        print(f"=== {label}")

        old_hashes: set[str] = set()

        for tag in DERIVED:
            path = root / tag / "pages.json"
            if not path.is_file():
                print(f"  {tag}: pages.json absent")
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            touched = False
            for (namespace, dotted), english in FIXES.items():
                if namespace != "pages":
                    continue
                leaf = resolve(data, dotted)
                if not isinstance(leaf, dict) or not isinstance(leaf.get("text"), str):
                    print(f"  {tag}: {dotted} is not a leaf, skipped")
                    continue
                if leaf["text"] == english:
                    continue
                # Record what downstream packs were translated from, so the
                # cascade can be named rather than guessed at.
                old_hashes.add(digest(leaf["text"]))
                if leaf.get("source_sha256"):
                    old_hashes.add(leaf["source_sha256"])
                print(f"  {tag}: {dotted}")
                print(f"     was: {leaf['text'][:150]}")
                print(f"     now: {english[:150]}")
                leaf["text"] = english
                leaf["source_sha256"] = digest(english)
                touched = True
                changed += 1
            if touched and apply:
                path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

        # Every pack leaf still carrying one of the old hashes was translated
        # from the corrupted English and is stale by construction.
        for pack in sorted(p for p in root.iterdir() if p.is_dir()):
            if pack.name in DERIVED or pack.name == "de":
                continue
            path = pack / "pages.json"
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for _, dotted in FIXES:
                leaf = resolve(data, dotted)
                if not isinstance(leaf, dict):
                    continue
                stored = leaf.get("source_sha256") or ""
                if stored in old_hashes or digest(leaf.get("text", "")) in old_hashes:
                    stale[pack.name] = stale.get(pack.name, 0) + 1
        print()

    print(f"{changed} leaf/leaves {'rewritten' if apply else 'would change'}")
    if stale:
        total = sum(stale.values())
        print(
            f"\n{total} downstream leaves across {len(stale)} packs were translated from"
            f" the German-pivoted English and need native re-translation:"
        )
        for pack, count in sorted(stale.items()):
            print(f"  {count:3d}  {pack}")
    if not apply and changed:
        print("\n(dry run; pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
