#!/usr/bin/env python3
"""Diff the en pages catalog against the authoritative English in pageIntros.ts.

Page headers are the one operator-visible surface whose English never passes
through t(..., { defaultValue }). pageIntros.ts holds them as plain string
literals in a route-keyed object, so the earlier "restore en from code" pass --
which harvested defaultValue -- could not see them. That blind spot is how the
default locale ended up shipping

    Getrennte / luftgekapte Hosts nutzen weiterhin lokale ... Konfiguratoren.

as headers.settings__agent__management.bullets.text[0], with source_sha256
equal to the hash of that German sentence. The pipeline re-hashed German as if
it were the English source, so the leaf looks self-consistent and every
hash-based provenance check waves it through. Only the code disagrees.

This reads the literals out of pageIntros.ts and compares them to en. The code
wins, always. With --fix it rewrites en, restamps source_sha256 from the code
text, and reports which downstream leaves were translated from the old (wrong)
en text so they can be re-queued rather than silently left stale.

Usage:
    python _audit_page_intros_vs_en.py [--show-all]
    python _audit_page_intros_vs_en.py --fix
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
INTROS = (
    ROOT.parent / "pim-offline-server" / "ui" / "src" / "help" / "pageIntros.ts"
)

FIELDS = ("title", "summary", "helpAriaLabel")


def digest(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# A small JS string reader. The file uses single quotes, occasional double
# quotes for sentences containing apostrophes, and backticks where a product
# name is interpolated. Escapes matter: 'it\'s' must not end the literal.
# --------------------------------------------------------------------------

def read_string(source: str, index: int) -> tuple[str | None, int]:
    """Read one JS string literal starting at source[index]. Returns (value, next)."""
    quote = source[index]
    if quote not in "'\"`":
        return None, index
    out: list[str] = []
    position = index + 1
    while position < len(source):
        char = source[position]
        if char == "\\":
            nxt = source[position + 1] if position + 1 < len(source) else ""
            out.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
            position += 2
            continue
        if char == quote:
            return "".join(out), position + 1
        if quote == "`" and char == "$" and source[position : position + 2] == "${":
            # Keep the placeholder verbatim so a diff against the catalog,
            # which stores the resolved product name, is reported not "fixed".
            close = source.find("}", position)
            if close == -1:
                return None, position
            out.append(source[position : close + 1])
            position = close + 1
            continue
        out.append(char)
        position += 1
    return None, position


def read_concatenated(source: str, index: int) -> tuple[str | None, int]:
    """Read a string literal plus any ' + ' continuations that follow it."""
    value, position = read_string(source, index)
    if value is None:
        return None, position
    while True:
        probe = position
        while probe < len(source) and source[probe] in " \t\r\n":
            probe += 1
        if probe >= len(source) or source[probe] != "+":
            return value, position
        probe += 1
        while probe < len(source) and source[probe] in " \t\r\n":
            probe += 1
        if probe >= len(source) or source[probe] not in "'\"`":
            return value, position
        more, position = read_string(source, probe)
        if more is None:
            return value, position
        value += more


ROUTE = re.compile(r"^\s*'(/[^']*)'\s*:\s*\{", re.MULTILINE)


def parse_intros(source: str) -> dict[str, dict]:
    """Extract {route: {title, summary, helpAriaLabel, bullets[]}} from the file."""
    pages: dict[str, dict] = {}
    for match in ROUTE.finditer(source):
        route = match.group(1)
        # Walk to the matching close brace so nested arrays stay inside.
        depth = 0
        position = match.end() - 1
        while position < len(source):
            if source[position] == "{":
                depth += 1
            elif source[position] == "}":
                depth -= 1
                if depth == 0:
                    break
            elif source[position] in "'\"`":
                _, position = read_string(source, position)
                continue
            position += 1
        body = source[match.end() : position]

        entry: dict = {}
        for field in FIELDS:
            hit = re.search(rf"\b{field}\s*:\s*", body)
            if not hit:
                continue
            cursor = hit.end()
            while cursor < len(body) and body[cursor] in " \t\r\n":
                cursor += 1
            if cursor < len(body) and body[cursor] in "'\"`":
                value, _ = read_concatenated(body, cursor)
                if value is not None:
                    entry[field] = value

        hit = re.search(r"\bbullets\s*:\s*\[", body)
        if hit:
            bullets: list[str] = []
            cursor = hit.end()
            while cursor < len(body):
                char = body[cursor]
                if char == "]":
                    break
                if char in "'\"`":
                    value, cursor = read_concatenated(body, cursor)
                    if value is not None:
                        bullets.append(value)
                    continue
                cursor += 1
            if bullets:
                entry["bullets"] = bullets

        if entry:
            pages[route] = entry
    return pages


def catalog_key(route: str) -> str:
    trimmed = route.strip("/")
    return trimmed.replace("/", "__") if trimmed else "root"


def main() -> int:
    argv = sys.argv[1:]
    fix = "--fix" in argv
    show_all = "--show-all" in argv

    pages = parse_intros(INTROS.read_text(encoding="utf-8"))
    print(f"parsed {len(pages)} routes from pageIntros.ts")

    en_path = CATALOG / "en" / "pages.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    headers = en.get("headers")
    if not isinstance(headers, dict):
        print("en/pages.json has no headers object", file=sys.stderr)
        return 1

    drift: list[tuple[str, str, str, str]] = []  # path, field, en text, code text
    missing: list[str] = []
    placeholder_skips = 0
    old_hashes: dict[str, str] = {}  # old en hash -> dotted path

    def compare(node, dotted: str, code_text: str) -> None:
        nonlocal placeholder_skips
        if not isinstance(node, dict) or not isinstance(node.get("text"), str):
            return
        if "${" in code_text:
            placeholder_skips += 1
            return
        if node["text"] == code_text:
            return
        drift.append((dotted, "", node["text"], code_text))
        if node.get("source_sha256"):
            old_hashes[node["source_sha256"]] = dotted
        if fix:
            node["text"] = code_text
            node["source_sha256"] = digest(code_text)

    for route, entry in sorted(pages.items()):
        key = catalog_key(route)
        header = headers.get(key)
        if not isinstance(header, dict):
            missing.append(f"{route}  ->  headers.{key}")
            continue
        for field in FIELDS:
            if field in entry and isinstance(header.get(field), dict):
                compare(header[field], f"headers.{key}.{field}", entry[field])
        if "bullets" in entry:
            # Two shapes exist in the wild: bullets[] and bullets.text[].
            bullets = header.get("bullets")
            items = None
            if isinstance(bullets, list):
                items = bullets
                shape = "bullets"
            elif isinstance(bullets, dict) and isinstance(bullets.get("text"), list):
                items = bullets["text"]
                shape = "bullets.text"
            elif isinstance(bullets, dict):
                # Numeric-keyed object, produced by a flattening applier.
                items = [bullets[k] for k in sorted(bullets, key=lambda s: (len(s), s)) if k.isdigit()]
                shape = "bullets.<n>"
            if items:
                for index, code_text in enumerate(entry["bullets"]):
                    if index < len(items):
                        compare(items[index], f"headers.{key}.{shape}[{index}]", code_text)

    print(f"{len(drift)} en leaf/leaves disagree with pageIntros.ts")
    if placeholder_skips:
        print(f"  ({placeholder_skips} skipped: code text interpolates a product name)")
    if missing:
        print(f"  ({len(missing)} routes have no headers entry in en)")
        for line in missing[: (None if show_all else 10)]:
            print(f"    {line}")

    if drift:
        print()
        shown = drift if show_all else drift[:25]
        for dotted, _, en_text, code_text in shown:
            print(f"  {dotted}")
            print(f"     en  : {en_text[:150]}")
            print(f"     code: {code_text[:150]}")
        if not show_all and len(drift) > len(shown):
            print(f"\n  ... {len(drift) - len(shown)} more (--show-all)")

    if fix and drift:
        en_path.write_text(
            json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nrewrote {en_path.relative_to(ROOT)} ({len(drift)} leaves)")

        # Any pack leaf whose source hash was the old en text was translated
        # from the corrupted English and is now stale by construction.
        stale = Counter()
        for pack in sorted(p for p in CATALOG.iterdir() if p.is_dir()):
            if pack.name == "en":
                continue
            path = pack / "pages.json"
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for old in old_hashes:
                if old in text:
                    stale[pack.name] += 1
        if stale:
            total = sum(stale.values())
            print(
                f"\n{total} downstream leaves across {len(stale)} packs were translated"
                f" from the old en text and now need re-translation:"
            )
            for pack, count in stale.most_common():
                print(f"  {count:5d}  {pack}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
