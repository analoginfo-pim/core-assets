#!/usr/bin/env python3
"""Measure the English catalog against the German one, in that direction.

_audit_german_in_english.py looks for German words it knows about, so it only finds
what its list already contains. It missed docs:openapi.untagged = "without Tag"
(word-for-word "ohne Tag", German noun capitalization intact) and
docs:openapi.title = "OpenAPI-Explorer" (German compound hyphenation), because
neither contains a German function word or an umlaut.

This asks a question that needs no vocabulary at all: how much of this English leaf
is the German leaf for the same key? A real English string and its German
translation share almost nothing but identifiers. When they share most of their
tokens, one was written by editing the other, and since German is the pivot the
edit direction was German to English.

    IDENTICAL   byte-for-byte the German string
    OVERLAP     shares >= --min of its tokens with German

Short labels are excluded because "Status", "Server", and "Import" are legitimately
the same word in both languages and reporting them trains the reader to skip the
output.

Usage: _audit_english_from_german.py [--tag en] [--min 0.6] [--min-tokens 3]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}

PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}|\{[A-Za-z_][A-Za-z0-9_.]*\}")
WORD = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*")


def leaves(node: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            return [(prefix, node["text"])]
        for key, value in node.items():
            out.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
    return out


def tokens(text: str) -> list[str]:
    return [w.lower() for w in WORD.findall(PLACEHOLDER.sub(" ", text))]


def main() -> int:
    argv = sys.argv[1:]

    def opt(name: str, default: str) -> str:
        return argv[argv.index(name) + 1] if name in argv else default

    tags = [opt("--tag", "")] if "--tag" in argv else ["en", "en-GB"]
    threshold = float(opt("--min", "0.6"))
    min_tokens = int(opt("--min-tokens", "3"))

    findings: list[tuple[str, float, str, str, str, str, str]] = []

    for area, root in ROOTS.items():
        if not root.is_dir():
            continue
        de_dir = root / "de"
        if not de_dir.is_dir():
            continue
        for tag in tags:
            tag_dir = root / tag
            if not tag_dir.is_dir():
                continue
            for path in sorted(tag_dir.glob("*.json")):
                namespace = path.stem
                de_path = de_dir / f"{namespace}.json"
                if not de_path.is_file():
                    continue
                german = dict(leaves(json.loads(de_path.read_text(encoding="utf-8"))))
                for key, text in leaves(json.loads(path.read_text(encoding="utf-8"))):
                    de_text = german.get(key)
                    if de_text is None:
                        continue
                    en_tokens = tokens(text)
                    if len(en_tokens) < min_tokens:
                        continue
                    if text == de_text:
                        findings.append(("IDENTICAL", 1.0, area, tag, namespace, key, text))
                        continue
                    de_tokens = set(tokens(de_text))
                    if not en_tokens:
                        continue
                    shared = sum(1 for t in en_tokens if t in de_tokens)
                    ratio = shared / len(en_tokens)
                    if ratio >= threshold:
                        findings.append(("OVERLAP", ratio, area, tag, namespace, key, text))

    findings.sort(key=lambda f: -f[1])
    print(
        f"{len(findings)} English leaf(s) share >= {threshold:.0%} of their wording "
        f"with German\n"
    )

    by_tag: dict[str, int] = {}
    for _, _, _, tag, _, _, _ in findings:
        by_tag[tag] = by_tag.get(tag, 0) + 1
    for tag, count in sorted(by_tag.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:6s} {count}")

    print()
    for why, ratio, area, tag, namespace, key, text in findings:
        print(f"  [{why:9s} {ratio:.0%}] {tag} {area}/{namespace} :: {key}")
        print(f"          {text!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
