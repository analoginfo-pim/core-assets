#!/usr/bin/env python3
"""Measure how much of each pack is still English wearing a few native words.

The parity gate proves a key exists in every pack. It cannot prove the value was
translated, so a pack can pass every check while shipping this:

    fi  "Coverage counts show mapped näyttö delivery ja open POA&M rows.
         They ovat ei Met, compliant, certified, tai assessment-ready."

Four Finnish words were substituted into an English sentence. To a Finnish
operator that is not a translation, and to the honesty rules it is worse than a
missing key -- a missing key shows a banner, this looks finished.

The measure is token overlap against the English source, ignoring tokens that any
correct translation would keep: product nouns, standards, acronyms, and the
compliance status tokens that are deliberately literal. Whatever English survives
after that exclusion was simply not translated. Scored per leaf and aggregated per
pack, because the useful question is not "is this leaf bad" but "is this pack real".

Latin-script languages carry real cognates, so the threshold is high and every
score is printed; CJK/Hebrew/Arabic packs cannot have cognates, which makes any
Latin word there conclusive.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = (ROOT / "content" / "locales-ui", ROOT / "content" / "locales")

SKIP_TAGS = {"en", "en-GB"}  # en-GB is a spelling variant; residue is expected
WORD = re.compile(r"[A-Za-z]{3,}")
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")

# Tokens a correct translation legitimately keeps in Latin script: product names,
# standards bodies, file formats, and the deliberately-literal status vocabulary.
KEEP = {
    "aic", "cmmc", "nist", "poa", "fips", "iso", "iec", "nerc", "cip", "gdpr", "lgpd",
    "soc", "dfars", "far", "cui", "fci", "dib", "msp", "mssp", "cpao", "osa", "ssp",
    "met", "live", "partial", "blocked", "absent", "rev", "sql", "json", "csv", "pdf",
    "html", "url", "api", "http", "https", "tls", "ssh", "rdp", "vnc", "smtp", "ldap",
    "saml", "oidc", "mfa", "pam", "pim", "pum", "iga", "hsm", "kms", "vpn", "dns",
    "ots", "modbus", "opc", "dnp", "scada", "ics", "windows", "linux", "macos",
    "docker", "hyper", "azure", "aws", "microsoft", "server", "agent", "fix", "log",
    "sha", "uuid", "guid", "vm", "wa", "cirt", "soc", "siem", "eula", "dpa", "ropa",
    "dpia", "id", "ip", "os", "ui", "usb", "wifi", "bios", "tpm", "sid", "acl", "macl",
}


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def english_tokens(text: str) -> list[str]:
    stripped = PLACEHOLDER.sub(" ", nfc(text))
    return [t.casefold() for t in WORD.findall(stripped) if t.casefold() not in KEEP]


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    if out is None:
        out = {}
    for k, v in (obj or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            out[key] = v["text"]
        elif isinstance(v, dict):
            flatten(v, key, out)
    return out


def load(root: Path, tag: str, namespace: str) -> dict:
    path = root / tag / f"{namespace}.json"
    return flatten(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    verbose = "--list" in sys.argv
    want = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--tag=")), None)
    threshold = float(
        next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--min=")), "0.5")
    )

    leaves: Counter[str] = Counter()
    residual: Counter[str] = Counter()
    identical: Counter[str] = Counter()
    shown = 0

    for root in ROOTS:
        if not root.is_dir():
            continue
        for namespace in sorted(p.stem for p in (root / "en").glob("*.json")):
            en = load(root, "en", namespace)
            for tag_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                tag = tag_dir.name
                if tag in SKIP_TAGS or (want and tag != want):
                    continue
                pack = load(root, tag, namespace)
                for key, en_text in en.items():
                    text = pack.get(key)
                    if not text:
                        continue
                    src = english_tokens(en_text)
                    if len(src) < 4:
                        continue  # too short to score; a 2-word label may match legitimately
                    leaves[tag] += 1
                    if nfc(text) == nfc(en_text):
                        identical[tag] += 1
                        continue
                    kept = english_tokens(text)
                    if not kept:
                        continue
                    # Share of the English source's own words still standing.
                    survived = len(set(kept) & set(src)) / len(set(src))
                    if survived < threshold:
                        continue
                    residual[tag] += 1
                    if verbose and shown < 25:
                        shown += 1
                        print(f"\n{tag:8s} {namespace}:{key}   ({survived:.0%} English retained)")
                        print(f"  en  {en_text[:170]}")
                        print(f"  {tag:3s} {text[:170]}")

    print(f"\n{'tag':9s} {'scored':>7s} {'==en':>7s} {'residue':>8s} {'share':>7s}")
    for tag in sorted(leaves):
        total = leaves[tag]
        bad = residual[tag] + identical[tag]
        print(
            f"{tag:9s} {total:7d} {identical[tag]:7d} {residual[tag]:8d} "
            f"{bad / total if total else 0:6.1%}"
        )
    print(
        f"\n{sum(identical.values())} leaf/leaves byte-identical to English, "
        f"{sum(residual.values())} more retain >={threshold:.0%} of the English wording"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
