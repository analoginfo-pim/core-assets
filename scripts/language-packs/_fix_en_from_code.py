#!/usr/bin/env python3
"""Restore the English catalog from the English literals in the UI source.

The en catalog was round-tripped through German. The result is not German
text -- a vocabulary detector reports zero hits -- it is fluent English
carrying German idiom, which is far harder to see and just as wrong:

    code                                    en catalog
    Assessor workflows live under ...       Assessor procedures lie beneath ...
    agent HMAC dual_mode soak               agent-HMAC dual_mode inflow
    enrollment bootstrap residual           enrollment bootstrap rest
    untagged                                without Tag
    Failed to load the control catalog.     Control catalog could not be loaded.
    800-53 Crosswalk                        Crosswalk 800-53

"lie beneath" is liegen unter read literally. "inflow" is Zulauf. "rest" is
Rest. "without Tag" keeps the German capital on a common noun. The passive
reconstructions are konnte nicht geladen werden coming back the other way.

Two of the drifted entries are honesty regressions rather than style: the
caveat that dual-mode agent HMAC is a soak posture "not a claim that every
agent already signs" was replaced with an unrelated sentence, and the login
helper tells operators that Use fills the username only when the code fills
username and password. Those are the ones that make this a correctness fix.

Which side wins is not a matter of taste. The code literal is what i18next
falls back to when a catalog entry is missing, so the code is the source and
the catalog is the copy. This restores the copy.

Downstream packs translated from the corrupted English are recorded rather
than touched. Their source_sha256 still names the text they were built from,
so the ones that were built from a corrupt parent can be listed exactly and
sent for native review instead of being silently left wrong.

Usage: _fix_en_from_code.py [--fix] [--report PATH]
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


def leaves(node, prefix=""):
    """Yield (dotted key, leaf dict) so callers can mutate the leaf in place."""
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            yield prefix, node
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def code_literals() -> dict[tuple[str, str], str]:
    """Every (namespace, key) -> defaultValue the UI declares."""
    found: dict[tuple[str, str], str] = {}
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
            found.setdefault((namespace, key), unescape(match.group("value")))
    return found


def main() -> int:
    argv = sys.argv[1:]
    write = "--fix" in argv
    report_path = Path(argv[argv.index("--report") + 1]) if "--report" in argv else None

    if not UI_SRC.is_dir():
        print(f"no UI source at {UI_SRC}", file=sys.stderr)
        return 2

    literals = code_literals()
    tags = sorted(p.name for p in CATALOG.iterdir() if p.is_dir() and p.name != "en")

    restored: list[tuple[str, str, str, str]] = []
    per_ns: Counter[str] = Counter()
    # old en text hash -> the key it belonged to, so downstream packs built
    # from the corrupt parent can be named precisely.
    stale_parents: dict[str, tuple[str, str]] = {}

    for en_path in sorted((CATALOG / "en").glob("*.json")):
        namespace = en_path.stem
        data = json.loads(en_path.read_text(encoding="utf-8"))
        dirty = False

        for key, leaf in leaves(data):
            wanted = literals.get((namespace, key))
            if wanted is None:
                continue
            current = leaf["text"]
            if current == wanted:
                if leaf.get("source_sha256") != sha(wanted):
                    leaf["source_sha256"] = sha(wanted)
                    dirty = True
                continue

            restored.append((namespace, key, current, wanted))
            per_ns[namespace] += 1
            stale_parents.setdefault(sha(current), (namespace, key))
            leaf["text"] = wanted
            leaf["source_sha256"] = sha(wanted)
            dirty = True

        if dirty and write:
            en_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    # Name the downstream leaves whose parent text we just replaced. Those were
    # translated from German-corrupted English and cannot be trusted, even
    # though nothing about them looks wrong in isolation.
    invalidated: list[tuple[str, str, str, str]] = []
    for tag in tags:
        for path in sorted((CATALOG / tag).glob("*.json")):
            namespace = path.stem
            for key, leaf in leaves(json.loads(path.read_text(encoding="utf-8"))):
                parent = leaf.get("source_sha256")
                if not parent:
                    continue
                owner = stale_parents.get(parent)
                if owner and owner == (namespace, key):
                    invalidated.append((tag, namespace, key, leaf["text"]))

    for namespace, count in per_ns.most_common():
        print(f"  {count:5d}  {namespace}")
    verb = "restored" if write else "would be restored"
    print(f"\n{len(restored)} en leaf/leaves {verb} from the code")

    by_tag: Counter[str] = Counter(tag for tag, *_ in invalidated)
    if by_tag:
        print(f"\n{len(invalidated)} downstream leaf/leaves were translated from the "
              f"corrupt English and need native review:")
        for tag, count in by_tag.most_common():
            print(f"  {count:5d}  {tag}")

    if report_path:
        report = {
            "restored": [
                {"namespace": ns, "key": k, "was": was, "now": now}
                for ns, k, was, now in restored
            ],
            "needs_native_review": [
                {"tag": tag, "namespace": ns, "key": k, "text": text}
                for tag, ns, k, text in invalidated
            ],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nreport written to {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
