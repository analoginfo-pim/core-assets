#!/usr/bin/env python3
"""Find en-dashes and em-dashes inserted inside standard identifiers.

A typography pass somewhere in the pipeline treated the hyphen in "800-53" as a
number range and replaced it with an en-dash, producing "800–53". That is
typographically defensible for a range of pages and wrong for an identifier.

The identifier is the whole point of these strings. "NIST SP 800-53" is a
document number; an assessor searching a binder export for 800-53 does not match
800–53, and a crosswalk keyed on the identifier silently misses the row. The same
applies to CMMC practice ids, CVE ids, and ISO clause numbers.

Detection must be narrow. "A dash between two digits" is NOT the rule: the
corpus is full of legitimate ranges where an en-dash is typographically correct
-- "(0–23)", "(1–480)", "12–500 characters", "Modes 1–3". Rewriting those to
hyphens would damage good typography in eighteen packs to fix a handful of
identifiers.

So the rule is keyed on the identifier families this product actually cites:

  NIST SP 800-series      800-53, 800-171, 800-172, 800-37
  800-53 control families AC-2, AU-9, SC-8, IA-5, MP-6, ...
  document standards      CVE-, ISO-, IEC-, RFC-, FIPS-, SP-
  CMMC practice ids       AC.L2-3.1.1

Everything else keeps its dash. A false positive here silently corrupts a
control id; a false negative leaves a typographic nit. The asymmetry says be
conservative.

The repair is the inverse substitution applied only at the matched positions, so
an em-dash used correctly as sentence punctuation is untouched.

Usage: _audit_endash_identifiers.py [--fix]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "locales-ui"
SERVER = ROOT / "content" / "locales"

# Group 1 is the identifier prefix, kept verbatim; the dash after it is the defect.
# "\b800" so a genuine range like "1800-2000" is not caught by the 800-series arm.
CONTROL_FAMILIES = (
    "AC|AT|AU|CA|CM|CP|IA|IR|MA|MP|PE|PL|PM|PS|PT|RA|SA|SC|SI|SR"
)
STANDARDS = "CVE|ISO|IEC|RFC|FIPS|NIST|SP|CIS|CCI"
BAD = re.compile(
    r"("
    r"\b800"  # NIST SP 800-series document number
    rf"|\b(?:{CONTROL_FAMILIES})"  # 800-53 control family, e.g. AC-2
    rf"|\b(?:{STANDARDS})"  # document standard prefix
    r"|\bL\d"  # CMMC practice level, e.g. AC.L2-3.1.1
    r")"
    r"[\u2013\u2014]"
    r"(?=[0-9A-Za-z])"
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def walk(node, path=""):
    """Yield (dotted_path, leaf_dict) for every {"text": ...} leaf."""
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            yield path, node
            return
        for key, value in node.items():
            yield from walk(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}.{index}")


def main() -> int:
    do_fix = "--fix" in sys.argv[1:]

    roots = [("ui", CATALOG), ("server", SERVER)]
    total = 0
    by_tag: dict[str, int] = {}
    samples: list[tuple[str, str, str, str, str]] = []
    touched: dict[Path, dict] = {}

    for label, base in roots:
        if not base.exists():
            continue
        for tag_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            for path in sorted(tag_dir.glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                hits = 0
                for key, leaf in walk(data):
                    text = leaf["text"]
                    if not BAD.search(text):
                        continue
                    fixed = BAD.sub(r"\1-", text)
                    hits += 1
                    total += 1
                    tag = tag_dir.name
                    by_tag[tag] = by_tag.get(tag, 0) + 1
                    if len(samples) < 25:
                        samples.append((tag, f"{label}/{path.stem}", key, text, fixed))
                    if do_fix:
                        leaf["text"] = fixed
                        if "source_sha256" in leaf and leaf.get("source_sha256") == sha(text):
                            leaf["source_sha256"] = sha(fixed)
                if hits and do_fix:
                    touched[path] = data

    print(f"{total} leaf(s) carry a dash inside an identifier\n")
    for tag, count in sorted(by_tag.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:8s} {count}")

    print()
    for tag, ns, key, text, fixed in samples:
        window = next(iter(BAD.finditer(text)))
        start, end = max(0, window.start() - 30), min(len(text), window.end() + 30)
        print(f"  [{tag}] {ns} :: {key}")
        print(f"      ...{text[start:end]}...")
        print(f"   -> ...{fixed[start:end]}...")

    if not do_fix:
        print("\n(dry run -- pass --fix to restore the hyphens)")
        return 0

    for path, data in touched.items():
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"\nrewrote {len(touched)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
