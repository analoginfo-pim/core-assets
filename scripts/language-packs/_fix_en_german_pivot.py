#!/usr/bin/env python3
"""Restore authoritative English on catalog leaves that were built from German.

Nine `en` leaves ship German because a word-level find-and-replace ran over the
German pack instead of a translation from the English source. The substitution
list only covered common function words, so the German content words survived:

    de  "Sicheres Teilen fuer Endbenutzer"   (fuer written with umlaut)
    en  "Sicheres Teilen for Endbenutzer"    <- only fuer -> for
    code "Secure Share for end users"        <- the real English

`en` is the default locale and every pack's fallback, so this is operator-visible
German on the English UI. Each replacement below is the literal English from the
code that owns the string; the CODE field records where to re-verify it.

These keys are all built with template `t()` calls -- `t(`...${model.id}...`)`,
`t(`docs.${chapter.id}.title`)` -- so the static defaultValue extractor never saw
them and never seeded `en` from code. That gap is why German could fill them.

Run with --fix to write. Without it, reports and changes nothing.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

from _audit_english_german import ROOTS, leaves

# (area, namespace, dotted key, corrupt text, clean text, code provenance)
REPAIRS: list[tuple[str, str, str, str, str, str]] = [
    (
        "ui",
        "docs",
        "user.chapters.secure-share.title",
        "Sicheres Teilen for Endbenutzer",
        "Secure Share for end users",
        "ui/src/pages/docs/UserManualPage.tsx",
    ),
    (
        "ui",
        "docs",
        "auditor.chapters.audit-review.title",
        "Audit and Alarme (nur lesen)",
        "Auditing and alerts (read-only)",
        "ui/src/pages/docs/auditorWorkingChapters.ts",
    ),
    (
        "ui",
        "docs",
        "openapi.capped",
        " (Seitenliste auf 500 begrenzt)",
        " (page list capped at 500)",
        "ui/src/pages/docs/TechnicalOpenApiPage.tsx",
    ),
    (
        "ui",
        "pages",
        "chrome.licensing.model.jump_capacity.summary",
        "Jump-Knoten and lastverteilte Proxy-Flotten.",
        "Jump nodes and load-balanced proxy fleets.",
        "ui/src/licensing/supportedModels.ts",
    ),
    (
        "ui",
        "pages",
        "chrome.licensing.model.marketplace_metered.label",
        "Marketplace nach Verbrauch",
        "Marketplace metered",
        "ui/src/licensing/supportedModels.ts",
    ),
    (
        "ui",
        "pages",
        "chrome.licensing.model.workstation_seat.summary",
        "Feste Arbeitsplatzsitze (kleine Enclave 1\u201325).",
        "Dedicated workstation seats (SMB enclave 1\u201325).",
        "ui/src/licensing/supportedModels.ts",
    ),
    (
        "ui",
        "pages",
        "chrome.licensing.tamperClass.fingerprint_mismatch",
        "Fingerabdruck stimmt not",
        "Fingerprint mismatch",
        "ui/src/licensing/format.ts (tamperClassLabel)",
    ),
    (
        "ui",
        "pages",
        "headers.licensing.bullets.text[3]",
        "License Management ist a eigene AIC-Website. Kauf and Finanzhinweise liegen dort.",
        "License Management is a separate AIC website. Purchase and finance alerts live there.",
        "ui/src/help/pageIntros.ts",
    ),
    (
        "ui",
        "pages",
        "headers.tenants.bullets.text[1]",
        "Agents and Assistentenausgabe referenzieren tenant_guid aus the Multi-Tenant-Datensatz.",
        "Agents and wizard output reference tenant_guid from the multi-tenant record.",
        "ui/src/help/pageIntros.ts",
    ),
]

# en-GB mirrors the same German. It carries no UK variance for these strings, so
# the clean English above is also the correct en-GB text.
TAGS = ("en", "en-GB")

# Additional corrupt forms seen on a single tag. en-GB had UK spelling applied
# *on top of* the German ("Licence Management ist a eigene AIC-Website"), and a
# partly-cleaned audit title. Both resolve to the same authoritative English.
# "License Management" stays US-spelled: it names the AIC product, not a licence.
EXTRA_CORRUPT: dict[str, tuple[str, ...]] = {
    "auditor.chapters.audit-review.title": ("Audit and alerts (read-only)",),
    "headers.licensing.bullets.text[3]": (
        "Licence Management ist a eigene AIC-Website. Kauf and Finanzhinweise liegen dort.",
    ),
}


def sha(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def main() -> int:
    write = "--fix" in sys.argv[1:]
    repaired = 0
    skipped = 0
    corrupt_hashes: dict[str, tuple[str, str]] = {}

    for tag in TAGS:
        for area, namespace, key, corrupt, clean, code in REPAIRS:
            path = ROOTS[area] / tag / f"{namespace}.json"
            if not path.is_file():
                print(f"  MISSING FILE  [{tag}] {area}/{namespace}")
                skipped += 1
                continue

            data = json.loads(path.read_text(encoding="utf-8"))
            leaf = next((node for found, node in leaves(data) if found == key), None)
            if leaf is None:
                print(f"  NO SUCH KEY   [{tag}] {area}/{namespace} :: {key}")
                skipped += 1
                continue

            current = leaf["text"]
            if current == clean:
                continue

            accepted = (corrupt, *EXTRA_CORRUPT.get(key, ()))
            if current not in accepted:
                # Refuse to overwrite anything we did not diagnose.
                print(f"  UNEXPECTED    [{tag}] {area}/{namespace} :: {key}")
                print(f"      expected  {corrupt!r}")
                print(f"      found     {current!r}")
                skipped += 1
                continue

            corrupt_hashes.setdefault(sha(current), (f"{area}/{namespace}", key))
            print(f"  FIX  [{tag}] {area}/{namespace} :: {key}")
            print(f"      was   {current!r}")
            print(f"      now   {clean!r}")
            print(f"      code  {code}")
            repaired += 1

            if write:
                leaf["text"] = clean
                leaf["source_sha256"] = sha(clean)
                path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    print(f"\n{repaired} leaf/leaves {'repaired' if write else 'would be repaired'}")
    if skipped:
        print(f"{skipped} skipped (see above)")

    if corrupt_hashes:
        print("\nsource_sha256 of the German-built English -- any pack leaf")
        print("carrying one of these was translated from German-corrupted text:")
        for digest, (where, key) in sorted(corrupt_hashes.items()):
            print(f"  {digest}  {where} :: {key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
