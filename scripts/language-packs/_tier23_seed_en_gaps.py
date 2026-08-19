#!/usr/bin/env python3
"""
Build US-English seed JSON for Tier2/3 gap keys (common appBar/iamToolbar +
dashboard chart/tile chrome). Source is SPA defaultValue harvest + authored
US English matched to dashboard key meanings — not en-GB/fr/es (German-polluted).

Does not modify en/de/fr/es/en-GB.
Writes: scripts/language-packs/_tier23_en_gap_seed/{common,dashboard}.json
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
UI_SRC = Path(r"c:\analog-pim\pim-offline-server\ui\src")
OUT = Path(__file__).resolve().parent / "_tier23_en_gap_seed"


def source_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def leaf(text: str) -> Dict[str, str]:
    return {"text": text, "source_sha256": source_sha256(text)}


def unflatten(entries: Dict[str, str]) -> Dict[str, Any]:
    tree: Dict[str, Any] = {}
    for path, text in entries.items():
        parts = path.split(".")
        node = tree
        for p in parts[:-1]:
            nxt = node.get(p)
            if not isinstance(nxt, dict) or "text" in nxt:
                nxt = {}
                node[p] = nxt
            node = nxt
        node[parts[-1]] = leaf(text)
    return tree


def harvest_default_values() -> Dict[str, str]:
    pat = re.compile(
        r"""t\(\s*['\"]((?:appBar|iamToolbar)\.[A-Za-z0-9_.]+)['\"]\s*,\s*\{[^}]*?defaultValue:\s*['\"]([^'\"]+)['\"]""",
        re.S,
    )
    found: Dict[str, str] = {}
    for p in UI_SRC.rglob("*.tsx"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in pat.finditer(text):
            found[m.group(1)] = m.group(2)
    return found


# Authored US English for dashboard keys present in de but absent from thin en.
DASHBOARD_EN: Dict[str, str] = {
    "chartCurrentCount": "Current count",
    "chartLabels.available": "Available",
    "chartLabels.blocked": "Blocked",
    "chartLabels.closed": "Closed",
    "chartLabels.covered": "Covered",
    "chartLabels.failed": "Failed",
    "chartLabels.log_derived": "Log-derived",
    "chartLabels.opened": "Opened",
    "chartLabels.physical_host": "Physical host",
    "chartLabels.uncovered": "Uncovered",
    "empty.collectorFailed": (
        "The data collector failed. No number is shown because a guessed zero "
        "would be misleading."
    ),
    "empty.deliveryStatusAbsent": (
        "This data source is not connected yet. There is nothing to count."
    ),
    "empty.noData": "No data is available for this tile.",
    "empty.partialSnapshotOnly": (
        "Partial delivery — current buffer only, no durable history."
    ),
    "tileDeepLinkHint": "{{action}} — delivery counts only, not an assessment result.",
    "tilePartial": "Partial",
    "tiles.compliance.attestations_recorded": "Attestations recorded",
    "tiles.compliance.pack_readiness": "Pack readiness",
    "tiles.compliance.poam_open": "Open POA&M items",
    "tiles.defense.blocked_attempts": "Blocked attacks",
    "tiles.env.discovered_systems": "Discovered systems",
    "tiles.env.physical_vs_log": "Physical vs log-derived",
    "tiles.env.probe_enabled_count": "Systems with probe enabled",
    "tiles.env.punch_list_open": "Open punch-list items",
    "tiles.env.systems_count": "Systems in the enclave",
    "tiles.events.by_type": "Events by type",
    "tiles.ir.cases_opened_closed": "Cases opened / closed",
    "tiles.ir.open_cases": "Open cases",
    "tiles.pum.endpoints_enrolled": "PUM endpoints enrolled",
    "tiles.pum.violations_24h": "PUM violations (24 h)",
    "tiles.training.framework_coverage": "Training framework coverage",
    "tiles.training.uncovered_frameworks": "Uncovered frameworks",
    "windowDefault": "Window: 7 / 30 / 90 days when data is available.",
    "windowSnapshot": "Current state (snapshot — no history window).",
}

# Fallbacks if harvest misses walk-critical chrome.
COMMON_FALLBACK: Dict[str, str] = {
    "appBar.about": "About",
    "appBar.docs": "Docs",
    "appBar.drawerTitle": "AIC Server",
    "appBar.licensing": "Licensing",
    "appBar.serverProduct": "Server",
    "iamToolbar.logOff": "Log off",
    "iamToolbar.security": "Security",
    "iamToolbar.signedIn": "Signed in",
}


def main() -> int:
    harvested = harvest_default_values()
    common = dict(COMMON_FALLBACK)
    common.update(harvested)
    OUT.mkdir(parents=True, exist_ok=True)
    common_path = OUT / "common.json"
    dash_path = OUT / "dashboard.json"
    common_path.write_text(
        json.dumps(unflatten(common), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    dash_path.write_text(
        json.dumps(unflatten(DASHBOARD_EN), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {common_path} ({len(common)} keys)")
    print(f"wrote {dash_path} ({len(DASHBOARD_EN)} keys)")
    for k in sorted(common):
        print(f"  common {k} => {common[k][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
