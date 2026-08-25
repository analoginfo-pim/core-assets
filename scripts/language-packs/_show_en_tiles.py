#!/usr/bin/env python3
"""Print the English text now recorded for the eighteen newly added keys.

The generator copied these from the call site and the tile dumper read them from
the same file, but the two disagreed on two strings. One of them is what the
seventeen packs will be translated from, so the disagreement has to be settled
by reading the catalog rather than by trusting either script's memory of it.
"""

import json
import pathlib

ROOT = pathlib.Path("content/locales-ui/en")

SLUGS = [
    "secure_program_launch",
    "evidence_intake",
    "evidence_intake_pe",
    "evidence_intake_sr",
    "evidence_intake_mp",
    "supplier_register",
    "personnel_screening",
    "tabletop_exercises",
    "scheduled_maintenance",
    "contingency_drills",
    "assessment_engagements",
    "facility_access_reviews",
    "media_destruction",
    "retention_records",
    "posture_exceptions",
    "catalog_changes",
    "agents_download",
]


def main() -> int:
    components = json.loads((ROOT / "components.json").read_text(encoding="utf-8"))
    helps = json.loads((ROOT / "help.json").read_text(encoding="utf-8"))
    desc = components["sectionLanding"]["desc"]
    for slug in SLUGS:
        leaf = desc.get(slug)
        print(slug)
        print(f"   {leaf['text'] if leaf else '(ABSENT)'}")
    leaf = helps.get("actionLaunchProgram")
    print("help:actionLaunchProgram")
    print(f"   {leaf['text'] if leaf else '(ABSENT)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
