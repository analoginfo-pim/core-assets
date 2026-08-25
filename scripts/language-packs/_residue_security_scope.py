#!/usr/bin/env python3
"""Rank untranslated English leaves by whether misreading them has consequences.

_audit_english_residue.py measures how much of each pack is still English. That
number is in the thousands, which is a native-review queue, not a repair list.
This narrows it: an operator who cannot read a tooltip about a font size loses
nothing, but one who cannot read a sentence telling them a secret is accepted
once and never shown again may paste it somewhere and lose it, or assume it is
recoverable. Those strings are the ones worth repairing by hand now.

A leaf qualifies when it is byte-identical to English in at least MIN_PACKS
packs (so it is a pipeline gap rather than one pack's oversight) and its English
mentions a secret-bearing noun. Sorted by pack count so the widest gaps lead.

Usage: _residue_security_scope.py [min_packs]
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path("content")
AREAS = ("locales-ui", "locales")

# Nouns whose surrounding sentence tells the operator how a secret behaves.
# Deliberately narrow: "key" alone matches "keyboard" and "key metric", so it is
# spelled out as the credential senses only.
SECURITY = re.compile(
    r"\b(secret|secrets|password|passwords|passphrase|vault|vaulted|credential|credentials"
    r"|private key|ssh key|api key|bearer|activation code|recovery code|pin\b"
    r"|token|tokens|certificate|certificates|encrypt|encrypted|decrypt|redact|redacted"
    r"|masked|plaintext|cleartext)\b",
    re.I,
)

# en-GB legitimately matches en whenever no US/UK spelling difference exists, so
# it is never evidence of a pipeline gap and is excluded from the count.
EXCLUDE_TAGS = {"en", "en-GB"}


def flat(obj, prefix="", out=None):
    out = {} if out is None else out
    for key, value in (obj or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and isinstance(value.get("text"), str):
            out[path] = value["text"]
        elif isinstance(value, dict):
            flat(value, path, out)
    return out


def load(path):
    return flat(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def main() -> int:
    min_packs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    findings = []

    for area in AREAS:
        base = ROOT / area
        if not (base / "en").is_dir():
            continue
        tags = sorted(
            p.name for p in base.iterdir() if p.is_dir() and p.name not in EXCLUDE_TAGS
        )
        for namespace_path in sorted((base / "en").glob("*.json")):
            namespace = namespace_path.stem
            english = load(namespace_path)
            candidates = {
                k: v
                for k, v in english.items()
                if SECURITY.search(v) and len(v.split()) >= 4
            }
            if not candidates:
                continue
            packs = {tag: load(base / tag / f"{namespace}.json") for tag in tags}
            for key, text in candidates.items():
                same = [t for t in tags if packs[t].get(key) == text]
                if len(same) >= min_packs:
                    findings.append((len(same), area, namespace, key, text, same))

    findings.sort(key=lambda row: (-row[0], row[1], row[2], row[3]))
    print(
        f"{len(findings)} security-relevant leaf/leaves still English in "
        f"{min_packs}+ packs\n"
    )
    for count, area, namespace, key, text, same in findings:
        print(f"[{count} packs] {area}/{namespace}:{key}")
        print(f"    {text}")
        print(f"    {', '.join(same)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
