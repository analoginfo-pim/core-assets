#!/usr/bin/env python3
"""Add the English leaves the code asks for but the catalog never carried.

`fallbackLng` is false and `resolveMissingKey` returns "Missing string: <key>" for
every non-English tag, so a key absent from the English catalog cannot be absent
quietly -- it paints its own key name onto the tile in all seventeen non-English
locales. The `defaultValue` at the call site does not save it, because i18next
runs `parseMissingKeyHandler` even when a default is supplied.

So these keys are not missing translations. They are missing sources, and until
the source exists there is nothing for a translator to translate.

The text is copied verbatim from the call site rather than rewritten, because the
English a US operator reads today is the English the pack must record; improving
the wording here would silently change what the other packs are translated from.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from language_packs import source_sha256  # noqa: E402

ROOT = pathlib.Path("content/locales-ui")

# slug -> description, verbatim from ui/src/config/sectionLandings.tsx
TILES = {
    "secure_program_launch": "Launch applications with vaulted passwords, SSH keys, or certificates without showing the secret. Entitlements control which app may use which credential.",
    "evidence_intake": "Record an out-of-band act or upload an artifact. The server stores a SHA-256. This is a statement that someone attested \u2014 not Met.",
    "evidence_intake_pe": "Visitor-log and escort procedure records. An attestation is not Met and is not certified.",
    "evidence_intake_sr": "Supplier questionnaire and signed flow-down records. An attestation is not Met and is not certified.",
    "evidence_intake_mp": "Witnessed-destruction procedure records. An attestation is not Met and is not certified.",
    "supplier_register": "Named suppliers with recorded scope and an assessment cycle. A register row is not Met and is not certified.",
    "personnel_screening": "Onboarding, offboarding, and periodic screening schedules with completion records. Not Met and not certified.",
    "tabletop_exercises": "Scheduled tabletop or practical exercises with participation records. Not Met and not certified.",
    "scheduled_maintenance": "Local and nonlocal maintenance events with approval and escort attestation. Not Met and not certified.",
    "contingency_drills": "Scheduled facility or contingency drills with after-action hashes. Not Met and not certified.",
    "assessment_engagements": "Penetration-test engagement records and remediation follow-up. The product does not perform the test. Not Met.",
    "facility_access_reviews": "Facility-access review and visitor-cycle schedules. Installing doors stays with the organization. Not Met.",
    "media_destruction": "Witnessed destruction and degauss-certificate records. The product does not operate the shredder. Not Met.",
    "retention_records": "Retention attestations and export-delivery hashes. Operating WORM storage stays with the organization. Not Met.",
    "posture_exceptions": "Endpoint-coverage exceptions and posture reviews. The product does not run enterprise EDR. Not Met.",
    "catalog_changes": "Local log of control-catalog and mapping byte changes. Due-diligence evidence, not Met.",
    "agents_download": "Download Agents and settings files for this instance. Inventory and required-state validation for the operating package in effect \u2014 not Met.",
}

# namespace -> dotted key -> text
HELP = {
    "actionLaunchProgram": "Launch a catalog program inside this recorded session. The password stays in the vault and is never shown on screen.",
}


def leaf(text: str) -> dict:
    return {"text": text, "source_sha256": source_sha256(text)}


def add(namespace: str, additions: dict[str, str], apply: bool) -> int:
    path = ROOT / "en" / f"{namespace}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    written = 0
    for dotted, text in additions.items():
        node = doc
        parts = dotted.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        name = parts[-1]
        if name in node:
            existing = node[name]
            have = existing.get("text") if isinstance(existing, dict) else existing
            if have == text:
                print(f"   skip (present, identical) {namespace}:{dotted}")
            else:
                print(f"   REFUSE {namespace}:{dotted} exists with different text")
                print(f"      have {have!r}")
                print(f"      want {text!r}")
            continue
        node[name] = leaf(text)
        written += 1
        print(f"   add  {namespace}:{dotted}")
    if apply and written:
        path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return written


def main() -> int:
    apply = "--apply" in sys.argv
    total = 0
    print("=== components ===")
    total += add(
        "components", {f"sectionLanding.desc.{k}": v for k, v in TILES.items()}, apply
    )
    print("=== help ===")
    total += add("help", HELP, apply)
    print()
    print(f"{total} English leaf(s) {'written' if apply else 'would be written'}")
    if not apply:
        print("re-run with --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
