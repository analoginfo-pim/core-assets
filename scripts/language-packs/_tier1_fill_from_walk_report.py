"""Seed Tier-1 fr/es/en-GB missing keys from walk report into the matching ns.

Looks up each missing key in de (then en) catalogs to find the namespace,
writes an EN draft (or de text) leaf so banners clear. Formal translation later.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from language_packs import dump_json, load_json, source_sha256  # noqa: E402

CA = Path(r"c:\analog-pim\core-assets\content\locales-ui")
REPORT = Path(
    r"c:\analog-pim\pim-offline-server\docs\dev\evidence"
    r"\language-pack-tier1-walk-20260818\missing-by-locale.json"
)
NSS = [
    "common",
    "nav",
    "pages",
    "help",
    "login",
    "compliance",
    "binder",
    "dashboard",
    "ot",
    "catalog",
    "dialogs",
    "components",
    "docs",
    "reports",
    "risks",
    "controls",
]


def dig(tree: dict, dotted: str):
    node = tree
    for p in dotted.split("."):
        if not isinstance(node, dict) or p not in node:
            return None
        node = node[p]
    return node


def set_leaf(tree: dict, dotted: str, text: str) -> None:
    parts = dotted.split(".")
    node = tree
    for p in parts[:-1]:
        nxt = node.get(p)
        if not isinstance(nxt, dict) or (
            isinstance(nxt, dict)
            and "text" in nxt
            and set(nxt.keys()) <= {"text", "source_sha256", "note"}
        ):
            node[p] = {}
            nxt = node[p]
        node = nxt
    node[parts[-1]] = {
        "text": text,
        "source_sha256": source_sha256(text),
        "note": "EN draft from Tier1 walk fill; formal register pending",
    }


def leaf_text(node) -> str | None:
    if isinstance(node, str):
        return node
    if isinstance(node, dict) and isinstance(node.get("text"), str):
        return node["text"]
    return None


def find_ns_and_text(key: str) -> tuple[str, str] | None:
    # Prefer en text, fall back to de location+text
    for tag in ("en", "de"):
        for ns in NSS:
            path = CA / tag / f"{ns}.json"
            if not path.exists():
                continue
            tree = load_json(path)
            node = dig(tree, key) if "." in key else tree.get(key)
            text = leaf_text(node)
            if text:
                return ns, text
    # Bare key → nav (menu labels), else common
    if "." not in key:
        return "nav", key.replace("_", " ").title()
    if key.startswith("headers.") or key.startswith("chrome.") or key.startswith("delivery."):
        return "pages" if key.startswith("headers.") or key.startswith("delivery.") else "common", key
    if key.startswith(("auditor.", "admin.", "user.", "disclosure.")):
        return "docs", key
    if key.startswith(("appBar.", "sectionLanding.", "knownDefaults.")):
        return "components", key
    return "common", key


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    for lng in ("fr", "es", "en-GB"):
        ids = sorted(
            {
                (x.split(":", 1)[1] if ":" in x else x)
                for vals in report[lng]["byRoute"].values()
                for x in vals
            }
        )
        by_ns: dict[str, dict] = {}
        for ns in NSS:
            p = CA / lng / f"{ns}.json"
            by_ns[ns] = load_json(p) if p.exists() else {}
        added = 0
        for key in ids:
            found = find_ns_and_text(key)
            if not found:
                continue
            ns, text = found
            # Prefer putting chrome.* and bare docs titles into common when
            # useTranslation() defaultNS is common — also seed pages if headers.
            if key.startswith("chrome."):
                ns = "common"
            existing = dig(by_ns[ns], key) if "." in key else by_ns[ns].get(key)
            if leaf_text(existing):
                continue
            set_leaf(by_ns[ns], key, text)
            added += 1
        for ns, tree in by_ns.items():
            dump_json(CA / lng / f"{ns}.json", tree)
        print(f"{lng}: added {added} leaves from {len(ids)} missing ids")


if __name__ == "__main__":
    main()
