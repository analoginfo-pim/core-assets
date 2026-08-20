#!/usr/bin/env python3
"""One-shot builder for retranslation prep artifacts (2026-08-19).

Does not modify locale JSON. Writes only under this directory.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # core-assets
OUT = Path(__file__).resolve().parent
UI_EN = ROOT / "content" / "locales-ui" / "en"
SRV_EN = ROOT / "content" / "locales" / "en"

ASCII_DE = re.compile(
    r"(oeffnet|bestaetigen|geoeffnet|standardmaessig|Domaene|waehrend|"
    r"aufgezeichnete|autorisiert|Verweigert|gesund|ungesund|Zugangssperre|"
    r"Benotung|Einschreibung|Aufzeichnung)",
    re.I,
)
DE_CHIP = re.compile(r"^(gesund|ungesund|Verweigert|Erlaubt)$", re.I)
DE_MIX = re.compile(
    r"\b(Verbinden|Sitzung|Trennen|Browser-Tab|Desktop-Viewer)\b"
)


def leaf_texts(obj, prefix: str = ""):
    out = []
    if isinstance(obj, dict):
        if "text" in obj and isinstance(obj["text"], str) and not any(
            isinstance(v, (dict, list)) for v in obj.values()
        ):
            out.append((prefix, obj["text"]))
            return out
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            out.extend(leaf_texts(v, p))
    elif isinstance(obj, str):
        out.append((prefix, obj))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(leaf_texts(v, f"{prefix}[{i}]"))
    return out


def infer_context(ns: str, key: str) -> dict:
    k = key.lower()
    control = "string"
    if any(
        x in k
        for x in (
            "button",
            "btn",
            "action",
            "cta",
            "submit",
            "save",
            "cancel",
            "connect",
            "deny",
            "allow",
            "approve",
        )
    ):
        control = "button"
    elif any(
        x in k
        for x in ("column", "header", "grid.", "fieldlabel", "label")
    ):
        control = "column_or_label"
    elif any(
        x in k
        for x in ("helper", "hint", "description", "helptext", "subtitle", "intro")
    ):
        control = "helper_text"
    elif any(
        x in k for x in ("error", "fail", "invalid", "denied", "toast", "alert")
    ):
        control = "error_or_toast"
    elif any(x in k for x in ("title", "heading", "pagetitle")):
        control = "title"
    elif any(x in k for x in ("chip", "badge", "status", "state")):
        control = "chip_or_status"
    elif any(x in k for x in ("menu", "nav", "item")):
        control = "nav_item"
    elif "placeholder" in k or "empty" in k:
        control = "placeholder"
    top = key.split(".")[0] if key else ns
    length = None
    if control == "button":
        length = "prefer <= 24 chars EN; DE/FR may expand 30-50% — layout risk"
    elif control == "column_or_label":
        length = "prefer <= 18 chars EN; DataGrid clip risk at 1024"
    elif control == "chip_or_status":
        length = "prefer <= 16 chars EN"
    elif control == "nav_item":
        length = "prefer <= 22 chars EN; sidebar width"
    return {
        "page_or_namespace": ns,
        "key_top": top,
        "control_type": control,
        "length_note": length,
    }


def flag_text(text: str) -> list[str]:
    flags: list[str] = []
    if ASCII_DE.search(text) or DE_CHIP.match(text.strip()):
        flags.append("de_residue")
    if re.search(r"\bSie\b", text) and re.search(
        r"\b(the|and|not|Close)\b", text
    ):
        flags.append("de_en_splice")
    if DE_MIX.search(text) and re.search(r"\b(the|and|a|to)\b", text, re.I):
        if "de_residue" not in flags:
            flags.append("de_residue")
    return flags


def main() -> None:
    ns_counts: dict[str, int] = defaultdict(int)
    all_rows: list[dict] = []
    contam: list[dict] = []

    for tree, base in (("locales-ui", UI_EN), ("locales", SRV_EN)):
        for f in sorted(base.glob("*.json")):
            ns = f.stem
            data = json.loads(f.read_text(encoding="utf-8"))
            for path, text in leaf_texts(data):
                flags = flag_text(text)
                row = {
                    "id": f"{tree}:{ns}:{path}",
                    "tree": tree,
                    "namespace": ns,
                    "key": path,
                    "en_text": text,
                    "contamination_flags": flags,
                    "english_clean": len(flags) == 0,
                    "context": infer_context(ns, path),
                    "source_file": f"content/{tree}/en/{ns}.json",
                }
                all_rows.append(row)
                ns_counts[f"{tree}/{ns}"] += 1
                if flags:
                    contam.append(row)

    corpus = {
        "generated": "2026-08-19",
        "authority": (
            "core-assets/content/locales-ui/en + content/locales/en "
            "(pending sibling format migration)"
        ),
        "gate": (
            "ENGLISH_SOURCE_BLOCKED — do not translate until contamination cleared"
        ),
        "totals": {
            "all_keys": len(all_rows),
            "locales_ui": sum(1 for r in all_rows if r["tree"] == "locales-ui"),
            "locales_server": sum(1 for r in all_rows if r["tree"] == "locales"),
            "contamination_flagged": len(contam),
            "english_clean_heuristic": sum(
                1 for r in all_rows if r["english_clean"]
            ),
        },
        "per_namespace": dict(
            sorted(ns_counts.items(), key=lambda x: -x[1])
        ),
        "keys": all_rows,
    }
    (OUT / "english-source-corpus.json").write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "en-contamination-quarantine.json").write_text(
        json.dumps(
            {
                "note": (
                    "Heuristic quarantine from current en pack. Recover from "
                    "defaultValue / git history / fresh authoring — NEVER "
                    "reverse-MT from de. Clean de on same keys is a damage "
                    "locator only."
                ),
                "count": len(contam),
                "keys": contam,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# English source corpus summary",
        "",
        f"- Total keys: **{len(all_rows)}**",
        f"- locales-ui: **{corpus['totals']['locales_ui']}**",
        f"- locales (server): **{corpus['totals']['locales_server']}**",
        f"- Contamination flagged (heuristic): **{len(contam)}**",
        f"- Heuristic clean: **{corpus['totals']['english_clean_heuristic']}**",
        "",
        "## Per-namespace",
        "",
        "| Namespace | Keys |",
        "| --- | ---: |",
    ]
    for k, v in sorted(ns_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "## Gate",
        "",
        "**English is BLOCKED** per "
        "`docs/dev/localization-quality-audit-20260819.md`. "
        "Contaminated keys must be recovered before any target-language fan-out.",
        "",
        "Machine-readable corpus: `english-source-corpus.json`.",
        "Quarantine list: `en-contamination-quarantine.json`.",
        "",
    ]
    (OUT / "english-source-corpus-SUMMARY.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"total={len(all_rows)} contam={len(contam)} out={OUT}")


if __name__ == "__main__":
    main()
