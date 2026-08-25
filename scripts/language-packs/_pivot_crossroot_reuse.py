#!/usr/bin/env python3
"""Repair raw-German leaves from the other locale root's correct text for the same key.

The two locale roots -- `content/locales-ui` for the admin SPA and
`content/locales` for the server -- carry overlapping namespaces, and the German
pivot did not hit them equally. `risks:treatment.accept` is the German
"Akzeptieren" in the UI pack for Dutch, Swedish and French, while the server pack
for those same three languages says "Accepteren", "Acceptera", "Accepter". The
correct translation already exists in the repository; it is simply in the other
root.

That makes this class of repair categorically different from a fresh translation.
The donor is the same language's own text for the same English source, so copying
it introduces no new translator voice and no drafting judgment -- which matters
because localization-work-queue.mdc holds that agent drafts cannot close a
localization item, while a string the pack already shipped is not a draft. The
earlier reuse pass found only 13 candidates because it searched for a sibling key
inside one root; searching the same key across roots is a far larger donor pool.

Four guards keep a copy from becoming its own defect. The English source must
match in both roots, or the donor answers a different question and is not a
translation of this leaf at all. The donor must differ from the German being
replaced, or the repair propagates the pivot instead of undoing it. It must differ
from the English source, since untranslated English is a separate defect and not a
fix for this one. And the placeholder set must match the English source exactly,
because a copied string that silently loses a `{{date}}` renders a sentence with a
hole where the operator expected a value.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
SERVER = ROOT / "content" / "locales"

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


def read_root(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """namespace -> tag -> key -> text, loaded once so the join is not O(leaves)."""
    packs: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    if not root.is_dir():
        return packs
    for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
        for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            packs[namespace][tag_dir.name] = load(tag_dir / f"{namespace}.json")
    return packs


def pivot_leaves(packs: dict[str, dict[str, dict[str, str]]]):
    """Yield keys where >=2 non-German packs ship byte-identical German.

    Agreement across two unrelated packs is the proof: one language sharing a
    single word with German is an arguable borrowing, two producing the same
    German word for the same key is one pivot copied twice.
    """
    for namespace, tags in packs.items():
        english = tags.get("en", {})
        german = tags.get("de", {})
        if not german:
            continue
        for key, de_text in german.items():
            de_stripped = de_text.strip()
            en_stripped = (english.get(key) or "").strip()
            if not de_stripped or de_stripped == en_stripped:
                continue
            agreeing = sorted(
                tag
                for tag, pack in tags.items()
                if tag not in {"en", "en-GB", "de"}
                and (pack.get(key) or "").strip() == de_stripped
            )
            if len(agreeing) >= 2:
                yield namespace, key, en_stripped, de_stripped, agreeing


def main() -> int:
    show = "--list" in sys.argv
    emit = "--emit" in sys.argv

    ui = read_root(UI)
    server = read_root(SERVER)

    # The pivot damaged different keys in each root, so both directions have donors.
    directions = (("locales-ui", ui, server), ("locales", server, ui))

    repaired: defaultdict[str, defaultdict[str, dict[str, dict[str, str]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    count = 0
    no_donor = 0

    for area, victim, donor in directions:
        for namespace, key, en_text, de_text, tags in pivot_leaves(victim):
            donor_ns = donor.get(namespace)
            if not donor_ns:
                no_donor += len(tags)
                continue
            if (donor_ns.get("en", {}).get(key) or "").strip().casefold() != en_text.casefold():
                no_donor += len(tags)
                continue

            for tag in tags:
                donor_text = (donor_ns.get(tag, {}).get(key) or "").strip()
                if (
                    not donor_text
                    or donor_text == de_text
                    or donor_text.casefold() == en_text.casefold()
                    or holes(donor_text) != holes(en_text)
                ):
                    no_donor += 1
                    continue
                count += 1
                repaired[area][namespace].setdefault(tag, {})[key] = donor_text
                if show:
                    print(f"  {area:11s} {tag:8s} {namespace}:{key}")
                    print(f"              de   {de_text[:70]}")
                    print(f"              fix  {donor_text[:70]}")

    print()
    print(f"{count} leaf/leaves repairable from the other root (pack's own wording)")
    print(f"{no_donor} leaf/leaves with no cross-root donor")

    if emit:
        out = ROOT / "content" / "language-packs" / "batches"
        for area, namespaces in sorted(repaired.items()):
            english_root = ui if area == "locales-ui" else server
            other = "locales" if area == "locales-ui" else "locales-ui"
            for namespace, tags in sorted(namespaces.items()):
                english = english_root[namespace].get("en", {})
                keys = sorted({k for per in tags.values() for k in per})
                batch = {
                    "_comment": (
                        "German-pivot repair. Every value here is the same language's own "
                        f"text for the same English source, taken from the {other} locale "
                        "root, which the pivot did not corrupt for these keys. No new "
                        "translation was drafted, so this is not an agent draft under "
                        "localization-work-queue.mdc -- it restores wording the pack already "
                        "shipped. Placeholder sets were verified identical to the English "
                        "source before copying."
                    ),
                    "area": area,
                    "namespace": namespace,
                    "source": {k: english.get(k, "") for k in keys},
                    "translations": {tag: per for tag, per in sorted(tags.items())},
                }
                path = out / f"pivot-crossroot-{area}-{namespace}-20260825.json"
                path.write_text(
                    json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                print(f"wrote {path.name}  ({sum(len(v) for v in tags.values())} leaves)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
