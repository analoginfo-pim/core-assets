#!/usr/bin/env python3
"""Generate batches closing the Tier-1 parity holes the key-parity gate reports.

`assert-ui-locale-key-parity.mjs --keys-only` fails on 29 leaves that exist in the
US English source but not in a Tier-1 pack. A key present in `en` and absent in the
loaded pack is exactly the condition that renders the `Missing string: <id>` banner
per release-data-self-heal.mdc, so these are shipped operator-visible defects, not
catalog bookkeeping.

`en-GB` carries none of the 17 (14 `nav` + 3 `common`). Most are documentation nouns
and proper nouns with no US/UK divergence, so the UK text is legitimately identical
to the US text -- identical is not a leak when the two dialects genuinely agree.
`License models` is the one real divergence: UK English spells the noun *licence* and
reserves *license* for the verb, which is why en-GB is a full pack rather than an
alias of `en` (compliance-artifacts-must-localize.mdc).

`fr`, `es`, `zh-Hans`, and `zh-TW` are each missing the same three `appBar` labels.
`de` already has all of them, so this is a partial propagation, not a new surface.

English source text is read out of the `en` packs so the `source_sha256` the applier
stamps hashes the real source rather than a hand-retyped copy.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
BATCHES = ROOT / "content" / "language-packs" / "batches"

# en-GB nav: documentation nouns and proper nouns. None of "cookbooks", "guides",
# "manuals", "recipes", "NIST SP 800-53", "MSP", "C3PAO", "CMMC", or "enclave" has a
# UK spelling variant, so the UK rendering equals the US rendering.
EN_GB_NAV = {
    "all_cookbooks": "All cookbooks",
    "all_guides": "All guides",
    "all_manuals": "All manuals",
    "all_recipes": "All recipes",
    "cookbooks": "Cookbooks",
    "guides": "Guides",
    "manuals": "Manuals",
    "recipes": "Recipes",
    "nist_sp_800_53": "NIST SP 800-53",
    "msp_and_c3pao_demo_guide": "MSP and C3PAO demo guide",
    "cmmc_agent_seed": "CMMC Agent seed",
    "cmmc_agent_configuration": "CMMC Agent configuration",
    "cmmc_agent_and_enclave_scripts": "CMMC Agent and enclave scripts",
    "cmmc_enclave_scripted_build": "CMMC enclave scripted build",
}

# "Licence models" is the UK noun form; "Marketplace" is a product name and stays.
EN_GB_COMMON = {
    "appBar.supportedCommercialShapes": "Licence models",
    "appBar.remittanceSupervisor": "Marketplace billing",
    "appBar.cloudConsumptionAndPricing": "Cloud consumption and pricing",
}

FR_COMMON = {
    "appBar.supportedCommercialShapes": "Modeles de licence",
    "appBar.remittanceSupervisor": "Facturation Marketplace",
    "appBar.cloudConsumptionAndPricing": "Consommation et tarification cloud",
}

ES_COMMON = {
    "appBar.supportedCommercialShapes": "Modelos de licencia",
    "appBar.remittanceSupervisor": "Facturacion de Marketplace",
    "appBar.cloudConsumptionAndPricing": "Consumo y precios en la nube",
}

ZH_HANS_COMMON = {
    "appBar.supportedCommercialShapes": "\u8bb8\u53ef\u6a21\u5f0f",
    "appBar.remittanceSupervisor": "\u5e02\u573a\u8ba1\u8d39",
    "appBar.cloudConsumptionAndPricing": "\u4e91\u7528\u91cf\u4e0e\u5b9a\u4ef7",
}

ZH_TW_COMMON = {
    "appBar.supportedCommercialShapes": "\u6388\u6b0a\u6a21\u5f0f",
    "appBar.remittanceSupervisor": "\u5e02\u96c6\u8a08\u8cbb",
    "appBar.cloudConsumptionAndPricing": "\u96f2\u7aef\u4f7f\u7528\u91cf\u8207\u5b9a\u50f9",
}

# Accented French and Spanish forms, applied after the ASCII table above so the file
# itself stays ASCII-safe on a cp1252 console while the pack gets the real text.
ACCENTS = {
    "Modeles de licence": "Mod\u00e8les de licence",
    "Facturacion de Marketplace": "Facturaci\u00f3n de Marketplace",
}


def leaf_text(node):
    return node["text"] if isinstance(node, dict) and "text" in node else node


def resolve(data, dotted):
    node = data
    for segment in dotted.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(segment)
        if node is None:
            return None
    return node


def english_source(namespace: str, keys) -> dict[str, str] | None:
    data = json.loads((UI / "en" / f"{namespace}.json").read_text(encoding="utf-8"))
    source = {}
    for key in keys:
        text = leaf_text(resolve(data, key))
        if not isinstance(text, str):
            print(f"error: no English source for {namespace}.{key}")
            return None
        source[key] = text
    return source


def write_batch(name: str, namespace: str, comment: str, translations: dict) -> int:
    keys = sorted({k for table in translations.values() for k in table})
    source = english_source(namespace, keys)
    if source is None:
        return 2

    fixed = {
        tag: {k: ACCENTS.get(v, v) for k, v in table.items()}
        for tag, table in translations.items()
    }

    path = BATCHES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "_comment": comment,
                "area": "locales-ui",
                "namespace": namespace,
                "source": source,
                "translations": fixed,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {name}: {len(keys)} keys x {len(fixed)} packs")
    return 0


def main() -> int:
    rc = write_batch(
        "parity-holes-nav-20260825.json",
        "nav",
        "en-GB carried none of these 14 documentation nav keys while en, de, fr, es, "
        "zh-Hans, and zh-TW all did, so the Documentation sidebar rendered a "
        "Missing string banner for a UK operator. Cookbooks, guides, manuals, "
        "recipes, NIST SP 800-53, MSP, C3PAO, CMMC, and enclave have no UK spelling "
        "variant, so the UK text equals the US text here -- identical is correct when "
        "the dialects agree, and is not a source-leak.",
        {"en-GB": EN_GB_NAV},
    )
    if rc:
        return rc

    return write_batch(
        "parity-holes-common-20260825.json",
        "common",
        "Three appBar labels shipped in en and de but were never propagated to en-GB, "
        "fr, es, zh-Hans, or zh-TW, so those locales rendered a Missing string banner "
        "in the top bar. en-GB uses the UK noun 'Licence models'; Marketplace is a "
        "product name and is not translated. fr/es/zh translations are agent drafts "
        "pending native review per localization-work-queue.mdc -- a reviewed-pending "
        "French string is not a defect, a Missing string banner is.",
        {
            "en-GB": EN_GB_COMMON,
            "fr": FR_COMMON,
            "es": ES_COMMON,
            "zh-Hans": ZH_HANS_COMMON,
            "zh-TW": ZH_TW_COMMON,
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
