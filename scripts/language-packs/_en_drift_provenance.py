#!/usr/bin/env python3
"""Decide, for each en-vs-code disagreement, which side the packs were built on.

_audit_en_vs_code.py finds 230 keys where the English catalog says something
different from the t() defaultValue in the code. It cannot say which side is
wrong, and the two cases need opposite repairs:

    catalog:loadFailed
        code 'Failed to load the control catalog.'
        en   'Control catalog could not be loaded.'
        de   'Kontrollkatalog konnte nicht geladen werden.'
      The English is a word-for-word rendering of the German passive. German was
      the pivot and the English catalog is a back-translation of it. Restoring
      the code text is the fix.

    common:quickSearch.ariaLabel
        code 'Quick access search for tasks and machines'
        en   'Search for a daily task or a managed machine, then jump to that page.'
        de   'Schnellsuche für Aufgaben und Maschinen'
      Here German translates the *code* string, and the English is a longer
      hand-written improvement that landed later. Restoring the code text would
      revert real work.

Reading the prose cannot separate those reliably, but the bookkeeping can.
Every translated leaf stores source_sha256, the hash of the English it was made
from. So:

    PACKS-FROM-EN     packs hash to today's en  -> en drifted before they were
                      translated, so the drift is upstream of everything and the
                      whole subtree is built on it
    PACKS-FROM-CODE   packs hash to the code string -> packs predate the en edit,
                      so en moved alone and is probably a deliberate improvement
    SPLIT             some of each -- en changed mid-flight and only some packs
                      were retranslated
    UNKNOWN           hashes match neither

Only PACKS-FROM-EN with German evidence is safe to restore mechanically. The
rest is reported, not touched.

Usage: _en_drift_provenance.py [--ui-src PATH] [--verdict PACKS-FROM-EN] [--limit N]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _audit_en_vs_code import (  # noqa: E402
    CALL,
    DEFAULT_UI_SRC,
    USE_NS,
    is_german,
    unescape,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def leaf_at(node: dict, key: str) -> dict | None:
    for part in key.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, dict) and "text" in node else None


def code_defaults(ui_src: Path) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for path in sorted(ui_src.rglob("*.ts*")):
        if "i18n" in path.parts or path.name.endswith((".test.ts", ".test.tsx")):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        if "defaultValue" not in source:
            continue
        file_ns = USE_NS.search(source)
        fallback_ns = file_ns.group("ns") if file_ns else None
        for match in CALL.finditer(source):
            raw_key = match.group("key")
            if ":" in raw_key:
                namespace, key = raw_key.split(":", 1)
            elif fallback_ns:
                namespace, key = fallback_ns, raw_key
            else:
                continue
            if "{" in key or "$" in key:
                continue
            out.setdefault((namespace, key), unescape(match.group("value")))
    return out


def main() -> int:
    argv = sys.argv[1:]

    def opt(name: str, default: str) -> str:
        return argv[argv.index(name) + 1] if name in argv else default

    ui_src = Path(opt("--ui-src", str(DEFAULT_UI_SRC)))
    wanted = set(opt("--verdict", "").split(",")) - {""}
    limit = int(opt("--limit", "0"))

    defaults = code_defaults(ui_src)
    tags = sorted(
        p.name for p in CATALOG.iterdir() if p.is_dir() and p.name not in {"en", "en-GB"}
    )

    # namespace -> tag -> parsed json, loaded once
    packs: dict[str, dict[str, dict]] = {}

    def pack(namespace: str, tag: str) -> dict:
        if namespace not in packs:
            packs[namespace] = {}
        if tag not in packs[namespace]:
            path = CATALOG / tag / f"{namespace}.json"
            packs[namespace][tag] = (
                json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
            )
        return packs[namespace][tag]

    english: dict[str, dict] = {}
    for path in sorted((CATALOG / "en").glob("*.json")):
        english[path.stem] = json.loads(path.read_text(encoding="utf-8"))

    rows: list[tuple[str, bool, str, str, str, str, int, int]] = []

    for (namespace, key), code_text in sorted(defaults.items()):
        if namespace not in english:
            continue
        en_leaf = leaf_at(english[namespace], key)
        if en_leaf is None:
            continue
        en_text = en_leaf["text"]
        if en_text == code_text:
            continue

        h_code, h_en = sha(code_text), sha(en_text)
        from_en = from_code = 0
        for tag in tags:
            leaf = leaf_at(pack(namespace, tag), key)
            if leaf is None:
                continue
            stored = leaf.get("source_sha256") or ""
            if stored == h_en:
                from_en += 1
            elif stored == h_code:
                from_code += 1

        if from_en and from_code:
            verdict = "SPLIT"
        elif from_en:
            verdict = "PACKS-FROM-EN"
        elif from_code:
            verdict = "PACKS-FROM-CODE"
        else:
            verdict = "UNKNOWN"

        if wanted and verdict not in wanted:
            continue
        rows.append(
            (verdict, is_german(en_text), namespace, key, code_text, en_text,
             from_en, from_code)
        )

    order = {"PACKS-FROM-EN": 0, "SPLIT": 1, "UNKNOWN": 2, "PACKS-FROM-CODE": 3}
    rows.sort(key=lambda r: (order[r[0]], not r[1], r[2], r[3]))

    counts: dict[str, int] = {}
    german = 0
    for verdict, is_de, *_ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
        german += bool(is_de)

    print(f"{len(rows)} disagreement(s) between the English catalog and the code\n")
    for verdict in sorted(counts, key=lambda v: order[v]):
        print(f"  {verdict:16s} {counts[verdict]}")
    print(f"\n  of which the en text still carries German: {german}\n")

    shown = rows[:limit] if limit else rows
    for verdict, is_de, namespace, key, code_text, en_text, n_en, n_code in shown:
        flag = " GERMAN" if is_de else ""
        print(f"  [{verdict}{flag}] {namespace} :: {key}   (en={n_en} code={n_code})")
        print(f"      code {code_text!r}")
        print(f"      en   {en_text!r}")
    if limit and len(rows) > limit:
        print(f"\n  ... {len(rows) - limit} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
