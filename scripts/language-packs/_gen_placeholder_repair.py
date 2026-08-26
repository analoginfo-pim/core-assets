#!/usr/bin/env python3
"""Generate the placeholder-identifier repair batch.

Two unrelated defects produce a placeholder mismatch against the English source,
and only one of them is mechanically repairable.

RENAMED (repairable). The machine-translation pass translated the *variable
identifier* inside the braces along with the prose: `{{name}}` became `{{nimi}}`
in Finnish, `{{reason}}` became `{{syy}}`, `{{account}}` became `{{tili}}`.
i18next interpolates by identifier, so it finds no `nimi` in the interpolation
values and renders the literal text `{{nimi}}` on screen. The surrounding prose is
untouched and correct -- only the identifier has to go back to English.

The identifier glossary is *learned*, not hand-written, and never guessed by
position -- Finnish word order moves `{{time}}` and `{{reason}}` relative to each
other, so a positional mapping would silently swap them. A mapping is only
accepted when it is forced: after applying what is already known, exactly one
English placeholder is missing from the leaf and exactly one foreign placeholder
is unaccounted for, so the pairing has no alternative.

Learning iterates to a fixpoint because one mapping unlocks the next. Finnish
`chrome.remoteAccess.openChoiceAria` starts as
`{account,host,port,protocol}` vs `{isäntä,port,protocol,tili}` -- two missing and
two extra, ambiguous on its own. Once `isäntä -> host` is established elsewhere
the leaf reduces to one missing (`account`) and one extra (`tili`), which forces
`tili -> account`.

DROPPED (not repairable here). The placeholder is absent entirely -- Hebrew
`chrome.tenants.revokeConfirm` asks the operator to confirm revoking a tenant
without naming which tenant. Restoring it means rewriting the sentence to give the
token a grammatical home, which is translation work, not a rename. Those leaves
are reported for the localization queue instead of being patched.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
OUT = ROOT / "content" / "language-packs" / "batches"

PLACEHOLDER = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")


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


def load(tag: str, ns: str) -> dict:
    p = UI / tag / f"{ns}.json"
    return flatten(json.loads(p.read_text(encoding="utf-8"))) if p.is_file() else {}


def main() -> int:
    namespaces = sorted(p.stem for p in (UI / "en").glob("*.json"))
    tags = sorted(d.name for d in UI.iterdir() if d.is_dir() and d.name != "en")

    # Cache every leaf that disagrees with the English source on placeholders.
    mismatched: list[tuple[str, str, str, set[str], set[str]]] = []
    for ns in namespaces:
        en = load("en", ns)
        for tag in tags:
            for key, text in load(tag, ns).items():
                if key not in en:
                    continue
                ep = set(PLACEHOLDER.findall(en[key]))
                tp = set(PLACEHOLDER.findall(text))
                if ep != tp:
                    mismatched.append((tag, ns, key, ep, tp))

    # Learn to a fixpoint. A mapping is accepted only when it is forced: exactly one
    # English placeholder unaccounted for, exactly one foreign placeholder left over.
    glossary: dict[str, dict[str, str]] = defaultdict(dict)
    conflicts: list[tuple[str, str, str, str]] = []
    while True:
        learned = 0
        for tag, _ns, _key, ep, tp in mismatched:
            gloss = glossary[tag]
            mapped = {gloss.get(p, p) for p in tp}
            missing = ep - mapped
            extra = {p for p in tp if gloss.get(p, p) not in ep}
            if len(missing) != 1 or len(extra) != 1:
                continue
            foreign_id = next(iter(extra))
            english_id = next(iter(missing))
            if foreign_id in gloss:
                if gloss[foreign_id] != english_id:
                    conflicts.append((tag, foreign_id, gloss[foreign_id], english_id))
                continue
            gloss[foreign_id] = english_id
            learned += 1
        if learned == 0:
            break

    glossary = {tag: gloss for tag, gloss in glossary.items() if gloss}

    # Pass 2: apply the glossary; report anything still mismatched.
    translations: dict[str, dict[str, str]] = defaultdict(dict)
    source: dict[str, str] = {}
    per_ns: dict[str, dict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    dropped: list[tuple[str, str, str, str, str]] = []

    for ns in namespaces:
        en = load("en", ns)
        for tag in tags:
            target = load(tag, ns)
            for key, text in target.items():
                if key not in en:
                    continue
                ep = set(PLACEHOLDER.findall(en[key]))
                tp = set(PLACEHOLDER.findall(text))
                if ep == tp:
                    continue

                gloss = glossary.get(tag, {})
                fixed = PLACEHOLDER.sub(
                    lambda m: "{{" + gloss.get(m.group(1), m.group(1)) + "}}", text
                )
                if set(PLACEHOLDER.findall(fixed)) == ep:
                    per_ns[ns][tag][key] = fixed
                else:
                    dropped.append(
                        (tag, ns, key, ",".join(sorted(ep)) or "(none)", ",".join(sorted(tp)) or "(none)")
                    )

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for ns, by_tag in sorted(per_ns.items()):
        en = load("en", ns)
        keys = sorted({k for m in by_tag.values() for k in m})
        batch = {
            "_comment": (
                "Placeholder identifiers were machine-translated along with the prose "
                "({{name}} -> {{nimi}}, {{reason}} -> {{syy}}), so i18next could not "
                "interpolate them and the operator saw the literal braces on screen. "
                "The identifier is restored to the English name; the surrounding prose "
                "is unchanged, so this is a mechanical repair and not a retranslation. "
                "The foreign-identifier glossary was learned from single-placeholder "
                "leaves rather than guessed by position, because word order moves "
                "placeholders relative to each other."
            ),
            "area": "locales-ui",
            "namespace": ns,
            "source": {k: en[k] for k in keys},
            "translations": {tag: m for tag, m in sorted(by_tag.items())},
        }
        path = OUT / f"placeholder-ids-{ns}-20260825.json"
        path.write_text(
            json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written.append((path.name, len(keys), sum(len(m) for m in by_tag.values())))

    print("glossary learned:")
    for tag, gloss in sorted(glossary.items()):
        pairs = ", ".join(f"{f}->{e}" for f, e in sorted(gloss.items()))
        print(f"  {tag:8} {pairs}")
    if conflicts:
        print("\nCONFLICT (one foreign identifier forced to two English names):")
        for tag, fid, first, second in conflicts:
            print(f"  {tag:8} {fid} -> {first} and {second}")

    print("\nbatches written:")
    for name, keys, leaves in written:
        print(f"  {name:44} {keys:4} keys {leaves:4} leaves")

    print(f"\ndropped placeholders (queue, not repairable here): {len(dropped)}")
    for tag, ns, key, ep, tp in dropped:
        print(f"  {tag:8} {ns:12} {key:52} en={ep} got={tp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
