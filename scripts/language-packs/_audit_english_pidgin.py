#!/usr/bin/env python3
"""Find leaves that kept the English sentence and swapped a few words.

The pure-English-residue detector only catches leaves byte-identical to English,
and the German-pivot detector only catches leaves byte-identical to German. A
word-by-word machine substitution lands between the two: the English skeleton
survives, two or three function words become native, and the leaf is now
different from both English and German, so neither detector sees it.

    en  Read-only step log from the last connectivity or authentication probe.
    fi  Read-only step log from the last connectivity tai authentication probe.

Retention is the share of the English source's alphabetic tokens that survive
verbatim in the translation. A real translation retains only proper nouns and
identifiers, so retention is low. A substitution pidgin retains most of the
sentence. Reporting the retained words alongside the ratio lets a reader confirm
the call instead of trusting the number.

Usage: _audit_english_pidgin.py [--root ui|server] [--min-tokens N] [--ratio R]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"ui": ROOT / "content" / "locales-ui", "server": ROOT / "content" / "locales"}

WORD = re.compile(r"[A-Za-z][A-Za-z'-]+")

# Placeholders must survive a translation byte-identically, so their contents are
# retained English by construction. Counting them makes a perfect translation look
# like a pidgin: "Endpoint {{endpoint.machine_name}} failed at {{event.timestamp}}"
# donates endpoint, machine, name, event, timestamp to both sides no matter what the
# translator wrote. Strip them before tokenizing or the detector measures the schema
# instead of the prose.
PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}|\{[A-Za-z_][A-Za-z0-9_.]*\}")

# Tokens that survive a correct translation and therefore prove nothing: product
# names, protocol and vendor identifiers, file extensions, units. Anything here
# is subtracted from both sides before the ratio is taken.
KEEPS = {
    "aic", "pim", "api", "url", "urls", "uri", "id", "ids", "sql", "ssl", "tls",
    "ssh", "css", "html", "json", "yaml", "csv", "pdf", "http", "https", "dns",
    "ip", "tcp", "udp", "smtp", "ldap", "saml", "oidc", "jwt", "hsm", "pkcs",
    "fips", "nist", "cmmc", "gdpr", "iso", "soc", "rdp", "vnc", "vm", "vms",
    "postgresql", "postgres", "windows", "linux", "macos", "chrome", "chromium",
    "edge", "firefox", "playwright", "docker", "kubernetes", "azure", "aws",
    "syslog", "mailpit", "softhsm", "radius", "kerberos", "oauth", "totp",
    "webauthn", "fido", "yubikey", "cyberark", "delinea", "beyondtrust",
    "hashicorp", "vault", "bitwarden", "onepassword", "modbus", "dnp", "opc",
    "ua", "scada", "ics", "poam", "ropa", "dpia", "eula", "sbom", "cve", "cwe",
    "ok", "n", "a", "mb", "kb", "gb", "ms", "utc", "iso-", "rfc", "uuid",
}


def leaves(node: dict, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            return [(prefix, node["text"])]
        for key, value in node.items():
            out.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
    return out


def tokens(text: str) -> list[str]:
    stripped = PLACEHOLDER.sub(" ", text)
    return [w.lower() for w in WORD.findall(stripped) if w.lower() not in KEEPS]


def main() -> int:
    argv = sys.argv[1:]

    def opt(name: str, default: str) -> str:
        if name in argv:
            return argv[argv.index(name) + 1]
        return default

    which = opt("--root", "")
    min_tokens = int(opt("--min-tokens", "6"))
    ratio_floor = float(opt("--ratio", "0.5"))
    # en-GB is a spelling overlay of en, so total retention is correct there and
    # would drown out every real finding. It is excluded unless asked for by name.
    only = [t for t in opt("--tag", "").split(",") if t]
    roots = [ROOTS[which]] if which else list(ROOTS.values())

    findings: list[tuple[float, str, str, str, str, str, list[str]]] = []

    for root in roots:
        if not root.is_dir():
            continue
        en_dir = root / "en"
        if not en_dir.is_dir():
            continue
        tags = sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and p.name != "en" and (p.name in only if only else p.name != "en-GB")
        )
        for en_file in sorted(en_dir.glob("*.json")):
            namespace = en_file.stem
            english = dict(leaves(json.loads(en_file.read_text(encoding="utf-8"))))
            for tag in tags:
                path = root / tag / f"{namespace}.json"
                if not path.is_file():
                    continue
                pack = dict(leaves(json.loads(path.read_text(encoding="utf-8"))))
                for key, en_text in english.items():
                    text = pack.get(key)
                    if text is None or text == en_text:
                        continue  # missing, or plain residue -- other detectors own those
                    en_tokens = tokens(en_text)
                    if len(en_tokens) < min_tokens:
                        continue
                    have = tokens(text)
                    pool = list(have)
                    kept: list[str] = []
                    for token in en_tokens:
                        if token in pool:
                            pool.remove(token)
                            kept.append(token)
                    ratio = len(kept) / len(en_tokens)
                    if ratio >= ratio_floor:
                        findings.append(
                            (ratio, root.name, tag, namespace, key, text, kept)
                        )

    findings.sort(key=lambda f: (-f[0], f[2], f[3], f[4]))
    by_tag: dict[str, int] = {}
    for ratio, _, tag, _, _, _, _ in findings:
        by_tag[tag] = by_tag.get(tag, 0) + 1

    print(f"{len(findings)} leaf(s) retain >= {ratio_floor:.0%} of the English wording\n")
    for tag, count in sorted(by_tag.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:9s} {count}")

    if "--by-source" in argv:
        # One English string can be pidgin in every pack at once. Grouping by the
        # source shows where a single act of comprehension repairs the most leaves.
        spread: dict[tuple[str, str, str], set[str]] = {}
        for _, area, tag, namespace, key, _, _ in findings:
            spread.setdefault((area, namespace, key), set()).add(tag)
        print()
        ranked = sorted(spread.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        for (area, namespace, key), affected in ranked[:40]:
            print(f"  {len(affected):2d} packs  {area}/{namespace} :: {key}")
            print(f"            {' '.join(sorted(affected))}")
        print(f"\n{len(ranked)} distinct English source(s) affected")
        return 0

    if "--by-namespace" in argv:
        groups: dict[tuple[str, str], set[str]] = {}
        for _, area, tag, namespace, key, _, _ in findings:
            groups.setdefault((area, namespace), set()).add(key)
        print()
        for (area, namespace), keys in sorted(
            groups.items(), key=lambda kv: -len(kv[1])
        ):
            print(f"  {area}/{namespace:22s} {len(keys):4d} distinct key(s)")
        return 0

    print()
    for ratio, area, tag, namespace, key, text, kept in findings[:60]:
        print(f"{ratio:5.0%}  {tag:7s} {area}/{namespace} :: {key}")
        print(f"        {text}")
        print(f"        kept: {' '.join(kept)}")
    if len(findings) > 60:
        print(f"\n... {len(findings) - 60} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
