#!/usr/bin/env python3
"""Generate the residual nav repair batch.

Two defects remain in `nav` after the fr/es wrong-language repair.

1. A handful of German leaves survived in nl, pl, and tr -- mostly the German
   abbreviations DSFA (for DPIA) and DSGVO (for GDPR), which a Dutch, Polish, or
   Turkish operator does not recognize. `nl/connect` ("Verbinden") and
   `sv/documentation` ("Dokumentation") are byte-identical to German but are the
   correct Dutch and Swedish words, so they are deliberately left alone -- an
   automated wrong-language check cannot tell a leak from a cognate.

2. `en-GB/nav.json` alone carries 184 NIST control-family identifiers as keys
   with title-cased values (`AC-1` -> "Ac-1", `SC-13` -> "Sc-13"). Nothing reads
   them: the only `nav` consumers are `QuickActionCardTile`, which looks up
   `slug(label)`, and `FavoritesSection`, which looks up `blocked_attacks`. A
   generator title-cased key and value together and wrote the result into one
   pack. They are deleted rather than repaired -- control identifiers stay Latin
   and uppercase per control-lists-short-title.mdc, and these leaves are dead
   weight shipped to the browser.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
OUT = ROOT / "content" / "language-packs" / "batches" / "nav-residual-20260825.json"

CONTROL_ID = re.compile(r"^[A-Z]{2}-\d+$")

NL = {
    "directory": "Directory",
    "dpia": "DPIA",
    "gdpr": "AVG",
    "rbac_lab": "RBAC-lab",
}
PL = {"dpia": "DPIA"}
TR = {"dpia": "DPIA"}


def main() -> int:
    en = json.loads((UI / "en" / "nav.json").read_text(encoding="utf-8"))

    keys = sorted(set(NL) | set(PL) | set(TR))
    missing = [k for k in keys if k not in en or "text" not in en[k]]
    if missing:
        print(f"error: no English source for {missing}")
        return 2

    gb = json.loads((UI / "en-GB" / "nav.json").read_text(encoding="utf-8"))
    dead = sorted(k for k in gb if CONTROL_ID.match(k))
    if not dead:
        print("error: no control-id keys found in en-GB/nav.json")
        return 2

    # Any control id that also exists in en would be a real key, not junk.
    claimed = [k for k in dead if k in en]
    if claimed:
        print(f"error: control ids present in en source, refusing to delete: {claimed}")
        return 2

    batch = {
        "_comment": (
            "Residual nav repair. nl/pl/tr carried the German abbreviations DSFA "
            "and DSGVO plus a few German words; nl/connect and sv/documentation "
            "are cognates, not leaks, and are left alone. en-GB additionally "
            "carried 184 NIST control identifiers as nav keys with title-cased "
            "values (AC-1 -> \"Ac-1\"); no code requests them -- the nav "
            "consumers look up slug(label) and blocked_attacks -- so they are "
            "deleted. Translations are agent drafts pending native review "
            "(localization-work-queue.mdc)."
        ),
        "area": "locales-ui",
        "namespace": "nav",
        "source": {k: en[k]["text"] for k in keys},
        "translations": {"nl": NL, "pl": PL, "tr": TR},
        "delete_keys": {"en-GB": dead},
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT.name}: {len(keys)} keys, delete {len(dead)} from en-GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
