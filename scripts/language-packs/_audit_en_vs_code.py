#!/usr/bin/env python3
"""Compare the English catalog against the English literals in the UI source.

Every other detector here treats English as the clean side. That assumption is
dead: content/locales-ui/en/pages.json ships "Marketplace nach Verbrauch" for a
label the code declares as "Marketplace metered", and
content/locales-ui/en/docs.json ships " (Seitenliste auf 500 begrenzt)" for
" (page list capped at 500)". The German-pivot pipeline wrote back into its own
input.

The German ones are the easy half. The same block also ships:

    code            catalog
    Perpetual + maintenance      Permanent plus maintenance
    BYOL                         Bring your own license (BYOL)
    Time-boxed trial ...         Time-limited evaluation license ...

Those are valid English, so every German detector stays silent, yet they are
just as corrupt: the code says one thing and the operator reads another, and all
17 packs were translated from the drifted text rather than from the product.

This needs no vocabulary and no native reviewer. React calls carry their own
English:

    t('openapi.capped', { defaultValue: ' (page list capped at 500)' })

so the catalog entry for that key must be that string, byte for byte. Anything
else is drift, and which side is wrong is not a matter of taste -- the code is
what the product falls back to when a catalog entry is missing, so the code is
the source and the catalog is the copy.

    GERMAN   the catalog text carries German orthography or a German-only word
    DRIFT    the catalog text is different English from the code

Usage: _audit_en_vs_code.py [--ui-src PATH] [--class GERMAN] [--limit N]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"
DEFAULT_UI_SRC = ROOT.parent / "pim-offline-server" / "ui" / "src"

# t('key', { defaultValue: 'text' })  --  the first string argument, then a
# defaultValue string somewhere in the options object before the call closes.
# [^)]*? keeps the match from running past the end of the call into the next one.
CALL = re.compile(
    r"""\bt\(\s*
        (['"`])(?P<key>[^'"`\n]+?)\1        # 'ns:key' or 'key'
        \s*,\s*\{[^{}]*?
        defaultValue\s*:\s*
        (['"])(?P<value>(?:\\.|(?!\3).)*)\3  # '...' with escapes honored
    """,
    re.VERBOSE | re.DOTALL,
)

USE_NS = re.compile(r"""useTranslation\(\s*(['"])(?P<ns>[^'"]+)\1""")

UMLAUT = re.compile(r"[äöüßÄÖÜ]")
WORD = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*")

GERMAN_ONLY = {
    "auf", "aus", "bei", "für", "fuer", "mit", "nach", "und", "oder", "nicht",
    "ist", "sind", "wird", "werden", "der", "die", "das", "des", "dem", "den",
    "ein", "eine", "einer", "eines", "kein", "keine", "von", "vom", "zum",
    "zur", "über", "ueber", "unter", "zwischen", "begrenzt", "seitenliste",
    "verbrauch", "gleitend", "knoten", "lastverteilte", "feste", "kleine",
    "verwaltete", "privilegierte", "konten", "modul", "funktionspaket",
    "rollenumfang", "datenbank", "unternehmens", "datenbankadapter",
    "fingerabdruecke", "ausfallschonfrist", "eltern", "kindpaketen",
    "mandantenstandorte", "arbeitsplatzsitze", "alarme", "lesen", "nur",
    "herunterladen", "hochladen", "teilen", "endbenutzer", "sicheres",
}


def unescape(text: str) -> str:
    return (
        text.replace("\\'", "'")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\\\", "\\")
    )


def leaves(node: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            return [(prefix, node["text"])]
        for key, value in node.items():
            out.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
    return out


def load_catalog() -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    en = CATALOG / "en"
    if not en.is_dir():
        return out
    for path in sorted(en.glob("*.json")):
        for key, text in leaves(json.loads(path.read_text(encoding="utf-8"))):
            out[(path.stem, key)] = text
    return out


def is_german(text: str) -> bool:
    if UMLAUT.search(text):
        return True
    return any(w.lower() in GERMAN_ONLY for w in WORD.findall(text))


def main() -> int:
    argv = sys.argv[1:]

    def opt(name: str, default: str) -> str:
        return argv[argv.index(name) + 1] if name in argv else default

    ui_src = Path(opt("--ui-src", str(DEFAULT_UI_SRC)))
    wanted = set(opt("--class", "").split(",")) - {""}
    limit = int(opt("--limit", "0"))

    if not ui_src.is_dir():
        print(f"no UI source at {ui_src}", file=sys.stderr)
        return 2

    catalog = load_catalog()
    findings: list[tuple[str, str, str, str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    scanned = 0

    for path in sorted(ui_src.rglob("*.ts*")):
        if "i18n" in path.parts or path.name.endswith((".test.ts", ".test.tsx")):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        if "defaultValue" not in source:
            continue
        scanned += 1
        file_ns = USE_NS.search(source)
        fallback_ns = file_ns.group("ns") if file_ns else None

        for match in CALL.finditer(source):
            raw_key = match.group("key")
            value = unescape(match.group("value"))
            if ":" in raw_key:
                namespace, key = raw_key.split(":", 1)
            elif fallback_ns:
                namespace, key = fallback_ns, raw_key
            else:
                continue
            if "{" in key or "$" in key:
                continue  # interpolated key, cannot resolve statically
            if (namespace, key) in seen:
                continue
            seen.add((namespace, key))

            shipped = catalog.get((namespace, key))
            if shipped is None or shipped == value:
                continue
            verdict = "GERMAN" if is_german(shipped) else "DRIFT"
            if wanted and verdict not in wanted:
                continue
            findings.append(
                (verdict, namespace, key, value, shipped, str(path.relative_to(ui_src)))
            )

    findings.sort(key=lambda f: (f[0] != "GERMAN", f[1], f[2]))
    german = sum(1 for f in findings if f[0] == "GERMAN")

    print(
        f"scanned {scanned} source file(s), resolved {len(seen)} t() call(s) "
        f"with a defaultValue"
    )
    print(f"{len(findings)} catalog entr(ies) disagree with the code "
          f"({german} German, {len(findings) - german} drifted English)\n")

    by_ns: dict[str, int] = {}
    for _, namespace, *_ in findings:
        by_ns[namespace] = by_ns.get(namespace, 0) + 1
    for namespace, count in sorted(by_ns.items(), key=lambda kv: -kv[1]):
        print(f"  {namespace:12s} {count}")
    print()

    shown = findings[:limit] if limit else findings
    for verdict, namespace, key, code_text, shipped, where in shown:
        print(f"  [{verdict}] {namespace} :: {key}   ({where})")
        print(f"      code {code_text!r}")
        print(f"      en   {shipped!r}")
    if limit and len(findings) > limit:
        print(f"\n  ... {len(findings) - limit} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
