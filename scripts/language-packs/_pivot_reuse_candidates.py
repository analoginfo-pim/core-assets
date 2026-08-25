#!/usr/bin/env python3
"""Repair raw-German leaves from the pack's own correct translations, where possible.

The German-pivot audit found 533 leaves shipping bare German words in packs that
do not read German. Most are short UI labels -- Likelihood, Impact, Accept, Avoid,
stale -- and the same English word almost always appears at some other key in the
catalog too. Where that sibling key was translated correctly, its text is a repair
that needs no translation judgment at all: the pack already decided how it says
that word, and this only copies that decision onto the leaf the pivot corrupted.

That distinction matters because agent-drafted translations cannot close a
localization item; a reused string is the pack's own reviewed wording, so it is a
different class of change from a fresh draft. Both beat shipping German to a
French operator, but only one of them is provable here.

Two guards keep a reuse from being a new defect. The donor must not itself be the
German text -- otherwise the repair copies the same corruption sideways, which is
how a pivot spreads. And the donor's placeholder set must match the recipient's
English source exactly, since two keys can share wording while differing in what
they interpolate, and a copied string that drops a `{{count}}` renders a sentence
with a hole in it.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")

PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}")


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


def holes(text: str) -> frozenset[str]:
    return frozenset(PLACEHOLDER.findall(text or ""))


def main() -> int:
    show = "--list" in sys.argv

    repairable: list[tuple[str, str, str, str, str, str]] = []
    unrepairable: defaultdict[str, set[str]] = defaultdict(set)

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            english = load(root / "en" / f"{namespace}.json")
            german = load(root / "de" / f"{namespace}.json")
            if not german:
                continue

            # Same threshold as the pivot audit: agreement across two unrelated
            # packs is what makes a single German word provable rather than a
            # possible shared borrowing.
            corrupted: dict[str, list[str]] = {}
            packs = {
                d.name: load(d / f"{namespace}.json")
                for d in sorted(p for p in root.iterdir() if p.is_dir())
                if d.name not in {"en", "en-GB", "de"}
            }
            for key, de_text in german.items():
                de_stripped = de_text.strip()
                if not de_stripped or de_stripped == (english.get(key) or "").strip():
                    continue
                agreeing = [
                    tag for tag, pack in packs.items()
                    if (pack.get(key) or "").strip() == de_stripped
                ]
                if len(agreeing) >= 2:
                    corrupted[key] = agreeing

            # Index each pack's clean translations by their English source, so a
            # donor can be found by meaning rather than by key name.
            for key, tags in corrupted.items():
                en_text = (english.get(key) or "").strip()
                if not en_text:
                    continue
                de_text = german[key].strip()

                for tag in tags:
                    pack = packs[tag]
                    donor = None
                    for other_key, other_text in pack.items():
                        if other_key == key:
                            continue
                        if (english.get(other_key) or "").strip().casefold() != en_text.casefold():
                            continue
                        candidate = other_text.strip()
                        # Refuse a donor that is the same German corruption, and
                        # refuse one whose holes do not match this English source.
                        if not candidate or candidate == de_text:
                            continue
                        if candidate.casefold() == en_text.casefold():
                            continue  # untranslated English is not a repair
                        if holes(candidate) != holes(en_text):
                            continue
                        donor = (other_key, candidate)
                        break

                    if donor:
                        repairable.append((tag, namespace, key, en_text, donor[1], donor[0]))
                    else:
                        unrepairable[f"{namespace}:{key}"].add(tag)

    print("provable repairs -- pack's own wording for the same English source:")
    for tag, namespace, key, en_text, text, donor_key in repairable[: 60 if show else 20]:
        print(f"  {tag:8s} {namespace}:{key}")
        print(f"           en   {en_text[:80]}")
        print(f"           fix  {text[:80]}   (from {donor_key})")

    total_unrepairable = sum(len(v) for v in unrepairable.values())
    print()
    print(f"{len(repairable)} leaf/leaves repairable by reuse (no translation judgment)")
    print(f"{total_unrepairable} leaf/leaves need a translation across {len(unrepairable)} key(s)")
    print()
    print("keys with no donor anywhere, by how many packs need them:")
    for key, tags in sorted(unrepairable.items(), key=lambda kv: -len(kv[1]))[:20]:
        print(f"  {len(tags):2d} packs  {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
