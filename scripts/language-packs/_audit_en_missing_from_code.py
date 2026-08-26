#!/usr/bin/env python3
"""Find keys the UI declares a defaultValue for that the en catalog does not hold.

_fix_en_from_code.py compares code against catalog leaf by leaf, so it can only
correct leaves that already exist. A key the code calls and en has never held is
invisible to it -- and that gap is not theoretical. Three feature areas shipped
their English only in the server tree's copy of the catalog, never in
core-assets, so the next forward sync (core-assets is the source of truth and the
sync overwrites consumers wholesale) deleted 79 live keys:

    chrome.accessControl.classificationGov.*   18  ClassificationPanel.tsx
    chrome.operatingLevel.*                    10  SettingsPage.tsx
    enclaveRegularUsers.*                      51  EnclaveRegularUsersPage.tsx

i18next falls back to defaultValue, so nothing crashed and no missing-string
banner appeared in en. But every other pack lost the key too, and there a
translated pack with no entry is exactly the state release-data-self-heal.mdc
requires to surface as a named-string error.

The fix direction is one-way on purpose: catalog entries are added from the code,
never the reverse. A key that lives only in a consumer tree is a key waiting to
be deleted.

Usage:
    python _audit_en_missing_from_code.py [--show-all]
    python _audit_en_missing_from_code.py --fix
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"
UI_SRC = ROOT.parent / "pim-offline-server" / "ui" / "src"

CALL = re.compile(
    r"""\bt\(\s*
        (['"`])(?P<key>[^'"`\n]+?)\1
        \s*,\s*\{[^{}]*?
        defaultValue\s*:\s*
        (['"])(?P<value>(?:\\.|(?!\3).)*)\3
    """,
    re.VERBOSE | re.DOTALL,
)
USE_NS = re.compile(r"""useTranslation\(\s*(['"])(?P<ns>[^'"]+)\1""")


def sha(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def unescape(text: str) -> str:
    return (
        text.replace("\\'", "'")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\\\", "\\")
    )


def code_literals() -> dict[tuple[str, str], tuple[str, str]]:
    """(namespace, key) -> (defaultValue, declaring file name)."""
    found: dict[tuple[str, str], tuple[str, str]] = {}
    for path in sorted(UI_SRC.rglob("*.ts*")):
        if "i18n" in path.parts or path.name.endswith((".test.ts", ".test.tsx")):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        if "defaultValue" not in source:
            continue
        file_ns = USE_NS.search(source)
        fallback = file_ns.group("ns") if file_ns else None
        for match in CALL.finditer(source):
            raw = match.group("key")
            if ":" in raw:
                namespace, key = raw.split(":", 1)
            elif fallback:
                namespace, key = fallback, raw
            else:
                continue
            if "{" in key or "$" in key:
                continue
            found.setdefault((namespace, key), (unescape(match.group("value")), path.name))
    return found


def existing_keys(namespace: str) -> set[str]:
    path = CATALOG / "en" / f"{namespace}.json"
    if not path.is_file():
        return set()

    def walk(node, prefix=""):
        if isinstance(node, dict):
            if isinstance(node.get("text"), str):
                yield prefix
                return
            for name, child in node.items():
                yield from walk(child, f"{prefix}.{name}" if prefix else name)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                yield from walk(child, f"{prefix}[{index}]")

    return set(walk(json.loads(path.read_text(encoding="utf-8"))))


def insert(root: dict, dotted: str, text: str) -> bool:
    """Create root[a][b][c] = leaf. False when an existing node blocks the path."""
    parts = dotted.split(".")
    node = root
    for part in parts[:-1]:
        child = node.get(part)
        if child is None:
            child = {}
            node[part] = child
        elif not isinstance(child, dict) or "text" in child:
            # A leaf already occupies an ancestor position; adding here would
            # shadow it. Report rather than clobber.
            return False
        node = child
    last = parts[-1]
    if last in node:
        return False
    node[last] = {"text": text, "source_sha256": sha(text)}
    return True


def main() -> int:
    argv = sys.argv[1:]
    fix = "--fix" in argv
    show_all = "--show-all" in argv

    if not UI_SRC.is_dir():
        print(f"no UI source at {UI_SRC}", file=sys.stderr)
        return 2

    literals = code_literals()
    namespaces = sorted({namespace for namespace, _ in literals})

    missing: list[tuple[str, str, str, str]] = []  # ns, key, text, file
    for namespace in namespaces:
        if not (CATALOG / "en" / f"{namespace}.json").is_file():
            # A namespace with no catalog file at all is a different problem.
            continue
        have = existing_keys(namespace)
        for (ns, key), (text, origin) in literals.items():
            if ns != namespace or key in have:
                continue
            # Keys built at runtime cannot be pre-declared.
            if any(char in key for char in " {}$"):
                continue
            missing.append((namespace, key, text, origin))

    print(
        f"{len(missing)} key(s) declared in code with a defaultValue are absent from en\n"
        f"({len(literals)} declarations scanned across {len(namespaces)} namespaces)"
    )
    if not missing:
        return 0

    by_ns = Counter(namespace for namespace, _, _, _ in missing)
    print("\nby namespace:")
    for namespace, count in by_ns.most_common():
        print(f"  {count:5d}  {namespace}")

    by_file = Counter(origin for _, _, _, origin in missing)
    print("\nby declaring file:")
    for origin, count in by_file.most_common(15):
        print(f"  {count:5d}  {origin}")

    print()
    shown = missing if show_all else missing[:30]
    for namespace, key, text, origin in shown:
        print(f"  {namespace} :: {key}   ({origin})")
        print(f"     {text[:140]}")
    if not show_all and len(missing) > len(shown):
        print(f"\n  ... {len(missing) - len(shown)} more (--show-all)")

    if not fix:
        print("\n(report only; pass --fix to add them to en)")
        return 0

    added = 0
    blocked: list[tuple[str, str]] = []
    for namespace in sorted(by_ns):
        path = CATALOG / "en" / f"{namespace}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        touched = False
        for ns, key, text, _ in missing:
            if ns != namespace:
                continue
            if insert(data, key, text):
                added += 1
                touched = True
            else:
                blocked.append((namespace, key))
        if touched:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    print(f"\nadded {added} leaf/leaves to en")
    if blocked:
        print(f"{len(blocked)} could not be placed (a leaf occupies an ancestor path):")
        for namespace, key in blocked:
            print(f"  {namespace} :: {key}")
    print(
        "\nen-GB must be re-derived and the other packs queued: every added key is\n"
        "absent from all 17 translated packs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
