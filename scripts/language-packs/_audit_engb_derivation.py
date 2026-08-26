#!/usr/bin/env python3
"""Audit en-GB as a derived pack: every difference from en must be a UK spelling rule.

en-GB is not an independent translation. The rule file says so explicitly and the
product treats it that way. That makes it the one pack whose correctness is fully
decidable without a native reviewer: take the en string, apply UK orthography, and
the result must be the en-GB string. Anything else is a defect, and it is provable
rather than a matter of taste.

The evidence that this needed checking: en-GB ships "NIST SP 800-171" as
"NIST SP 800-171" with an en dash, which is not a spelling variant, it is a broken
standards identifier that a compliance mapping is keyed on. It also ships
"AIC server" for the product name AIC Server, "Loading swagger uI" for Swagger UI,
"Please open findings" where en says "Open findings" (adjective turned imperative in
a compliance honesty note), and outright German in four leaves.

Classification, most severe first:

    GERMAN      contains German that en does not have
    PUNCT       hyphen, dash, or quote changed - breaks identifiers
    CASE        differs only in letter case - product and proper nouns
    SHAPE       words inserted, removed, or reordered - meaning may have moved
    LEXICAL     a word was swapped for one no UK rule explains

Differences the UK rules below explain are silent, because a report that lists
"organisation" as a finding is a report nobody reads.

Usage: _audit_engb_derivation.py [--class GERMAN,PUNCT] [--limit N]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}

TOKEN = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*")

# A US token maps to a UK token when one of these rewrites turns the first into the
# second. Expressed as rewrites rather than a word list so a new word inherits the
# rule instead of needing an entry.
UK_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ization\b"), "isation"),
    (re.compile(r"izations\b"), "isations"),
    (re.compile(r"ize\b"), "ise"),
    (re.compile(r"izes\b"), "ises"),
    (re.compile(r"ized\b"), "ised"),
    (re.compile(r"izing\b"), "ising"),
    (re.compile(r"yze\b"), "yse"),
    (re.compile(r"yzed\b"), "ysed"),
    (re.compile(r"yzes\b"), "yses"),
    (re.compile(r"yzing\b"), "ysing"),
    (re.compile(r"^color"), "colour"),
    (re.compile(r"^behavior"), "behaviour"),
    (re.compile(r"^favor"), "favour"),
    (re.compile(r"^honor"), "honour"),
    (re.compile(r"^labor"), "labour"),
    (re.compile(r"^neighbor"), "neighbour"),
    (re.compile(r"^center"), "centre"),
    (re.compile(r"^meter\b"), "metre"),
    (re.compile(r"^liter\b"), "litre"),
    (re.compile(r"^catalog"), "catalogue"),
    (re.compile(r"^dialog"), "dialogue"),
    (re.compile(r"^analog\b"), "analogue"),
    (re.compile(r"^license"), "licence"),
    (re.compile(r"^defense"), "defence"),
    (re.compile(r"^offense"), "offence"),
    (re.compile(r"^pretense"), "pretence"),
    (re.compile(r"^enroll"), "enrol"),
    (re.compile(r"^fulfill"), "fulfil"),
    (re.compile(r"^install\b"), "instal"),
    (re.compile(r"^skillful"), "skilful"),
    (re.compile(r"^gray"), "grey"),
    (re.compile(r"^math\b"), "maths"),
    (re.compile(r"^aluminum"), "aluminium"),
    (re.compile(r"^acknowledgment"), "acknowledgement"),
    (re.compile(r"^judgment"), "judgement"),
    (re.compile(r"^practice\b"), "practise"),
    (re.compile(r"^program\b"), "programme"),
    (re.compile(r"^programs\b"), "programmes"),
    (re.compile(r"eled\b"), "elled"),
    (re.compile(r"eling\b"), "elling"),
    (re.compile(r"eler\b"), "eller"),
    (re.compile(r"^traveling"), "travelling"),
    (re.compile(r"^canceled"), "cancelled"),
    (re.compile(r"^modeling"), "modelling"),
    (re.compile(r"^signaling"), "signalling"),
]

GERMAN_ONLY = {
    "auf", "aus", "bei", "für", "fuer", "mit", "nach", "nur", "und", "oder",
    "nicht", "ist", "sind", "wird", "werden", "der", "die", "das", "des", "dem",
    "den", "ein", "eine", "einer", "eines", "kein", "keine", "von", "vom", "zum",
    "zur", "über", "ueber", "unter", "zwischen", "begrenzt", "seitenliste",
    "herunterladen", "hochladen", "letzter", "datenbank", "unternehmens",
    "sicheres", "teilen", "endbenutzer", "knoten", "lastverteilte", "feste",
    "arbeitsplatzsitze", "kleine", "verbrauch", "fingerabdruck", "stimmt",
    "alarme", "lesen", "datenbankadapter",
}

# Punctuation an identifier depends on. A hyphen becoming an en dash is not a
# typographic nicety when the string is NIST SP 800-171.
DASHES = "\u2010\u2011\u2012\u2013\u2014\u2015"


def leaves(node: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            return [(prefix, node["text"])]
        for key, value in node.items():
            out.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
    return out


def uk_forms(token: str) -> set[str]:
    """Every UK spelling the rules can produce from this US token."""
    lower = token.lower()
    out = {lower}
    for pattern, replacement in UK_RULES:
        rewritten, count = pattern.subn(replacement, lower)
        if count:
            out.add(rewritten)
    return out


def classify(en: str, gb: str) -> str | None:
    if en == gb:
        return None

    en_tokens = TOKEN.findall(en)
    gb_tokens = TOKEN.findall(gb)

    if any(t.lower() in GERMAN_ONLY for t in gb_tokens) and not any(
        t.lower() in GERMAN_ONLY for t in en_tokens
    ):
        return "GERMAN"

    # Strip letters out and compare the skeleton: catches a hyphen that became an
    # en dash, a straight quote that became curly, a colon that vanished.
    en_marks = [c for c in en if not c.isalnum() and not c.isspace()]
    gb_marks = [c for c in gb if not c.isalnum() and not c.isspace()]
    if en_marks != gb_marks:
        if any(c in DASHES for c in gb_marks) and "-" in en_marks:
            return "PUNCT"
        if len(en_marks) == len(gb_marks):
            return "PUNCT"

    if en.lower() == gb.lower():
        return "CASE"

    if len(en_tokens) != len(gb_tokens):
        return "SHAPE"

    for a, b in zip(en_tokens, gb_tokens):
        if a == b:
            continue
        if b.lower() in uk_forms(a):
            continue
        if a.lower() == b.lower():
            return "CASE"
        return "LEXICAL"

    # Tokens all reconcile; whatever is left is spacing or punctuation.
    return "PUNCT" if en_marks != gb_marks else None


SEVERITY = {"GERMAN": 0, "PUNCT": 1, "CASE": 2, "SHAPE": 3, "LEXICAL": 4}


def main() -> int:
    argv = sys.argv[1:]
    wanted = set(
        (argv[argv.index("--class") + 1] if "--class" in argv else "").split(",")
    ) - {""}
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 0

    findings: list[tuple[str, str, str, str, str, str]] = []

    for area, root in ROOTS.items():
        en_dir, gb_dir = root / "en", root / "en-GB"
        if not (en_dir.is_dir() and gb_dir.is_dir()):
            continue
        for en_path in sorted(en_dir.glob("*.json")):
            gb_path = gb_dir / en_path.name
            if not gb_path.is_file():
                continue
            english = dict(leaves(json.loads(en_path.read_text(encoding="utf-8"))))
            british = dict(leaves(json.loads(gb_path.read_text(encoding="utf-8"))))
            for key, gb_text in british.items():
                en_text = english.get(key)
                if en_text is None:
                    continue
                verdict = classify(en_text, gb_text)
                if verdict and (not wanted or verdict in wanted):
                    findings.append(
                        (verdict, area, en_path.stem, key, en_text, gb_text)
                    )

    findings.sort(key=lambda f: (SEVERITY[f[0]], f[1], f[2], f[3]))

    counts: dict[str, int] = {}
    for verdict, *_ in findings:
        counts[verdict] = counts.get(verdict, 0) + 1

    print(f"{len(findings)} en-GB leaf(s) differ from en by something other than UK spelling\n")
    for verdict in sorted(counts, key=lambda v: SEVERITY[v]):
        print(f"  {verdict:8s} {counts[verdict]}")
    print()

    shown = findings[:limit] if limit else findings
    for verdict, area, namespace, key, en_text, gb_text in shown:
        print(f"  [{verdict}] {area}/{namespace} :: {key}")
        print(f"      en    {en_text!r}")
        print(f"      en-GB {gb_text!r}")
    if limit and len(findings) > limit:
        print(f"\n  ... {len(findings) - limit} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
