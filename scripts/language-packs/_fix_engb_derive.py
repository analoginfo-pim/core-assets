#!/usr/bin/env python3
"""Re-derive en-GB from en, allowing UK spelling and nothing else.

en-GB is a derived pack: its only licence to differ from en is British
spelling. Everything observed beyond that was manufactured by an earlier
"force UK" pass and is corruption:

  casing        1162 swaps -- Procedures->procedures, Control->control.
                Capitalisation is not a UK/US difference in either direction.
  lexical       Refresh->Reload, Search->Find, manuals->handbooks,
                Admin->Administrator, Check->Verify, need->require.
                "Refresh" and "Search" are perfectly British words.
  transposed    Blocked<->Commands and Supported<->protocols swapped two
                column headers with each other, changing what the UI claims.
  misspelling   Enrolled->Enroled. UK keeps the double L.
  German pivot  109 leaves were translated from the German pack rather than
                from en, so en-GB shipped 'Angemeldet' and 'Loading swagger uI'.

The rule enforced here: a word may differ from en only if the (en, en-GB)
pair appears in UK_SPELLING. Any other difference is restored from en. This
deliberately does not regenerate en-GB wholesale -- where a translator chose
"licence" over "license", that judgement is on the allow-list and survives.

Two passes, because they need different treatment:

  align     leaves whose sentence skeleton still matches en. Compare word by
            word and restore anything not allow-listed.
  rederive  leaves provably built from German (source_sha256 matches the de
            text). Sentence structure is unreliable, so take en and apply the
            unambiguous half of the spelling map.

Usage: _fix_engb_derive.py [--fix] [--verbose]
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

# Splitting on a capturing group keeps the separators, so punctuation,
# {{placeholders}} and identifiers survive a rebuild untouched.
TOKEN = re.compile(r"([A-Za-z][A-Za-z'\u2019-]*)")

# US -> UK. Case is normalised away on lookup and restored on output, so each
# pair is listed once in lower case.
UK_SPELLING: dict[str, str] = {
    "enrollment": "enrolment",
    "enrollments": "enrolments",
    "enroll": "enrol",
    "enrolls": "enrols",
    "auto-enrollment": "auto-enrolment",
    "auto-enroll": "auto-enrol",
    "catalog": "catalogue",
    "catalogs": "catalogues",
    "catalog-only": "catalogue-only",
    "control-catalog": "control-catalogue",
    "license": "licence",
    "licenses": "licences",
    "center": "centre",
    "centers": "centres",
    "centralized": "centralised",
    "organization": "organisation",
    "organizations": "organisations",
    "organization's": "organisation's",
    "organizational": "organisational",
    "non-organizational": "non-organisational",
    "organize": "organise",
    "organizes": "organises",
    "favorite": "favourite",
    "favorites": "favourites",
    "program": "programme",
    "programs": "programmes",
    "authorize": "authorise",
    "authorizes": "authorises",
    "authorized": "authorised",
    "authorizing": "authorising",
    "authorization": "authorisation",
    "authorizations": "authorisations",
    "unauthorized": "unauthorised",
    "initialize": "initialise",
    "initialization": "initialisation",
    "color": "colour",
    "colors": "colours",
    "acknowledgment": "acknowledgement",
    "acknowledgments": "acknowledgements",
    "judgment": "judgement",
    "localize": "localise",
    "localized": "localised",
    "localization": "localisation",
    "customize": "customise",
    "customized": "customised",
    "analyze": "analyse",
    "analyzing": "analysing",
    "recognize": "recognise",
    "recognizes": "recognises",
    "behavior": "behaviour",
    "labeled": "labelled",
    "normalized": "normalised",
    "normalization": "normalisation",
    "emphasized": "emphasised",
    "role-emphasized": "role-emphasised",
    "artifact": "artefact",
    "dialog": "dialogue",
    "synchronize": "synchronise",
    "canceled": "cancelled",
    "honor": "honour",
    "defense": "defence",
    "offense": "offence",
    "gray": "grey",
    "fulfill": "fulfil",
    "traveled": "travelled",
    "modeling": "modelling",
    "signaling": "signalling",
    "toward": "towards",
    "while": "whilst",
}

# Pairs needing a human call about sense rather than spelling. "License" is a
# verb as well as a noun, and UK software keeps "program" for software while
# using "programme" for a training programme. Alignment preserves whatever the
# pack already chose for these; re-derivation refuses to guess and leaves the
# en form in place.
AMBIGUOUS = {"license", "licenses", "program", "programs", "while"}


def sha(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            yield prefix, node
            return
        for name, child in node.items():
            yield from leaves(child, f"{prefix}.{name}" if prefix else name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaves(child, f"{prefix}[{index}]")


def match_case(model: str, word: str) -> str:
    """Give `word` the capitalisation pattern of `model`."""
    if model.isupper() and len(model) > 1:
        return word.upper()
    if model[:1].isupper():
        return word[:1].upper() + word[1:]
    return word


def uk_allows(english: str, british: str) -> bool:
    """True when british is a sanctioned UK spelling of english."""
    want = UK_SPELLING.get(english.casefold())
    return want is not None and want == british.casefold()


def align(english: str, british: str) -> str | None:
    """Restore every word of `british` that UK spelling does not justify.

    Returns None when the two texts no longer share a sentence skeleton --
    that is a structural divergence, not a spelling one, and is left to the
    re-derive pass rather than guessed at here.
    """
    en_parts = TOKEN.split(english)
    gb_parts = TOKEN.split(british)
    if len(en_parts) != len(gb_parts):
        return None
    # Even indices are the separators: punctuation, spaces, placeholders.
    if en_parts[::2] != gb_parts[::2]:
        return None

    out = list(gb_parts)
    for i in range(1, len(en_parts), 2):
        e, g = en_parts[i], gb_parts[i]
        if e == g or uk_allows(e, g):
            continue
        out[i] = e
    return "".join(out)


def rederive(english: str, previous: str = "") -> str:
    """Build en-GB from en using only the unambiguous spelling swaps.

    Ambiguous words are normally left in their en form, because choosing
    between them is a question of sense rather than spelling -- UK English
    writes "a licence" but "to license", and keeps "program" for software
    while using "programme" for a training programme. Guessing wrong there
    produces a mistake a British reader notices immediately.

    The one case where guessing is unnecessary: the pack already answered.
    When the text being replaced used the UK form, that call was made by
    someone reading the string in context, so it is honoured rather than
    thrown away for the sake of a uniform rule.
    """
    settled = {
        uk
        for us, uk in UK_SPELLING.items()
        if us in AMBIGUOUS and re.search(rf"\b{uk}\b", previous, re.IGNORECASE)
    }
    parts = TOKEN.split(english)
    for i in range(1, len(parts), 2):
        word = parts[i]
        folded = word.casefold()
        uk = UK_SPELLING.get(folded)
        if not uk:
            continue
        if folded in AMBIGUOUS and uk not in settled:
            continue
        parts[i] = match_case(word, uk)
    return "".join(parts)


def main() -> int:
    write = "--fix" in sys.argv[1:]
    verbose = "--verbose" in sys.argv[1:]
    stats: Counter[str] = Counter()
    samples: list[tuple[str, str, str, str, str]] = []
    divergent: list[tuple[str, str, str, str, str]] = []

    for en_path in sorted((CATALOG / "en").glob("*.json")):
        gb_path = CATALOG / "en-GB" / en_path.name
        de_path = CATALOG / "de" / en_path.name
        if not gb_path.is_file():
            continue

        en_text = {k: v["text"] for k, v in leaves(json.loads(en_path.read_text(encoding="utf-8")))}
        de_text = {}
        if de_path.is_file():
            de_text = {k: v["text"] for k, v in leaves(json.loads(de_path.read_text(encoding="utf-8")))}

        gb_data = json.loads(gb_path.read_text(encoding="utf-8"))
        dirty = False

        for key, leaf in leaves(gb_data):
            english = en_text.get(key)
            if english is None:
                stats["no en counterpart"] += 1
                continue

            german = de_text.get(key)
            pivoted = (
                german is not None
                and german != english
                and leaf.get("source_sha256") == sha(german)
            )

            current = leaf["text"]
            if pivoted:
                wanted = rederive(english, current)
                reason = "rederive"
            else:
                wanted = align(english, current)
                reason = "align"
                if wanted is None:
                    # The sentence no longer lines up with en, so there is no
                    # word-by-word repair to make. Leaving it would be the
                    # comfortable choice and the wrong one: en-GB may differ
                    # from en by spelling and nothing else, so a structural
                    # difference is corruption by definition. Observed in this
                    # bucket: "Open OT protocol sessions" rendered as "log
                    # sessions" (German Protokoll is both words), a screen
                    # reader description reduced to "Log out", an error that
                    # no longer names the permission it needs, and invented
                    # advice the product never wrote. Re-derive and report.
                    wanted = rederive(english, current)
                    reason = "rederive (structural)"
                    divergent.append((en_path.stem, key, english, current, wanted))

            if wanted == current and leaf.get("source_sha256") == sha(english):
                stats["already correct"] += 1
                continue

            if wanted != current:
                stats[reason] += 1
                if len(samples) < 40:
                    samples.append((en_path.stem, key, current, wanted, reason))
            else:
                stats["source hash repaired only"] += 1

            leaf["text"] = wanted
            leaf["source_sha256"] = sha(english)
            dirty = True

        if dirty and write:
            gb_path.write_text(
                json.dumps(gb_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    if verbose:
        for namespace, key, was, now, reason in samples:
            print(f"  [{reason}] {namespace} :: {key}")
            print(f"      was  {was!r}")
            print(f"      now  {now!r}")
        print()

    if "--show-divergent" in sys.argv[1:]:
        print(f"{len(divergent)} leaf/leaves rebuilt from a structural divergence:\n")
        for namespace, key, english, british, now in divergent:
            print(f"  {namespace} :: {key}")
            print(f"      en     {english!r}")
            print(f"      was    {british!r}")
            print(f"      now    {now!r}")
        print()

    if "--report" in sys.argv[1:]:
        # A rebuilt sentence is the right default, but a handful of genuine
        # British constructions ("in hospital", "at the weekend") are
        # grammatical rather than orthographic and this script cannot keep
        # them. Hand a reviewer the exact before/after so anything real can
        # be restored on purpose instead of mourned.
        path = Path(sys.argv[sys.argv.index("--report") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                [
                    {"namespace": ns, "key": k, "en": en, "was": was, "now": now}
                    for ns, k, en, was, now in divergent
                ],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"structural rebuilds written to {path}\n")

    for label, count in stats.most_common():
        print(f"  {count:6d}  {label}")
    changed = stats["align"] + stats["rederive"] + stats["rederive (structural)"]
    print(f"\n{changed} leaf/leaves {'rewritten' if write else 'would be rewritten'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
