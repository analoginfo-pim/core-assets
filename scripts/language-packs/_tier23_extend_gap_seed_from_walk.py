#!/usr/bin/env python3
"""Author US English for remaining ja walk gaps; extend gap seed."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
UI_SRC = Path(r"c:\analog-pim\pim-offline-server\ui\src")
SEED = Path(__file__).resolve().parent / "_tier23_en_gap_seed"
WALK = Path(
    r"c:\analog-pim\pim-offline-server\docs\dev\evidence"
    r"\i18n-walk-tier23-20260818\walk-ja.json"
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def leaf(text: str) -> Dict[str, str]:
    return {"text": text, "source_sha256": sha(text)}


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


def flat(d: Any, p: str = "") -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(d, dict):
        return out
    for k, v in d.items():
        path = f"{p}.{k}" if p else k
        if isinstance(v, dict) and "text" in v:
            out[path] = str(v["text"])
        elif isinstance(v, dict):
            out.update(flat(v, path))
        elif isinstance(v, str):
            out[path] = v
    return out


def harvest_defaults(prefixes: tuple[str, ...]) -> Dict[str, str]:
    # t('sectionLanding.desc.foo', { defaultValue: '...' })
    keys_alt = "|".join(re.escape(p) for p in prefixes)
    pat = re.compile(
        rf"""t\(\s*['\"]((?:{keys_alt})\.[A-Za-z0-9_.]+)['\"]\s*,\s*\{{[^}}]*?defaultValue:\s*['\"]([^'\"]+)['\"]""",
        re.S,
    )
    found: Dict[str, str] = {}
    for p in UI_SRC.rglob("*.tsx"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in pat.finditer(text):
            found[m.group(1)] = m.group(2)
    return found


# Reasonable US English for section landing / tile actions when defaults absent.
# Prefer SPA harvest; these fill holes from key names + de meaning.
SECTION_FALLBACK: Dict[str, str] = {
    "sectionLanding.intro.lab": "Lab and development surfaces for this enclave.",
    "sectionLanding.intro.messaging": "Email, SMS, templates, and notification settings.",
    "sectionLanding.intro.ot": "Operational technology discovery and inventory.",
    "sectionLanding.intro.proxied": "Proxied remote access and jump capacity.",
    "sectionLanding.intro.systems": "Systems, groups, credentials, and inventory.",
    "sectionLanding.group.approvals": "Approvals",
    "sectionLanding.group.jump_capacity": "Jump capacity",
    "sectionLanding.group.ot_surfaces": "OT surfaces",
    "sectionLanding.group.policy": "Policy",
    "sectionLanding.group.recording_ops": "Recording operations",
    "sectionLanding.group.sessions": "Sessions",
    "sectionLanding.groupDesc.approvals": "Pending access and elevation approvals.",
    "sectionLanding.groupDesc.jump_capacity": "Jump fleet load and connection points.",
    "sectionLanding.groupDesc.ot_surfaces": "OT discovery, inventory, and related tools.",
    "sectionLanding.groupDesc.policy": "Session, command, and access policy.",
    "sectionLanding.groupDesc.recording_ops": "Recording agents, storage, and health.",
    "sectionLanding.groupDesc.sessions": "Live sessions and session evidence.",
}

HEADER_EN: Dict[str, str] = {
    "headers.settings__crypto.summary": "Encryption settings for keys at rest.",
    "headers.settings__crypto.title": "Encryption",
    "headers.settings__crypto__key-sets.summary": "Key sets used for encryption at rest.",
    "headers.settings__crypto__key-sets.title": "Key sets",
    "headers.settings__defaults__disclosures.summary": "Default disclosure text for end users.",
    "headers.settings__defaults__disclosures.title": "Disclosures",
    "headers.settings__defaults__server-disclosures.summary": "Server-side disclosure defaults.",
    "headers.settings__defaults__server-disclosures.title": "Server disclosures",
    "headers.settings__session-policy.summary": "Idle and absolute session lifetime policy.",
    "headers.settings__session-policy.title": "Session policy",
    "headers.systems__known-default-credentials.summary": "Known default credentials catalog.",
    "headers.systems__known-default-credentials.title": "Known default credentials",
}

GRID_EN: Dict[str, str] = {
    "grid.columns": "Columns",
    "grid.density": "Density",
    "grid.export": "Export",
    "grid.filters": "Filters",
}

# Nav-ish help keys sometimes surface without ns prefix from docs chrome.
NAVISH: Dict[str, str] = {
    "app_manifest": "App manifest",
    "demo_data": "Demo data",
    "elevation_mocks": "Elevation mocks",
    "general_settings": "General settings",
    "mitm_dev_only": "MITM (dev only)",
    "rbac_lab": "RBAC lab",
    "server_control": "Server control",
    "tls_security": "TLS security",
}


def title_from_key(key: str) -> str:
    leaf_name = key.rsplit(".", 1)[-1]
    return leaf_name.replace("_", " ").replace("-", " ").strip().title()


def main() -> int:
    missing = json.loads(WALK.read_text(encoding="utf-8"))["uniqueMissingKeys"]
    harvested = harvest_defaults(("sectionLanding", "tileLinkActions", "grid"))
    # Also pull English from en pages for headers that exist there
    en_pages = flat(json.loads((ROOT / "content/locales-ui/en/pages.json").read_text(encoding="utf-8")))
    en_comp = flat(
        json.loads((ROOT / "content/locales-ui/en/components.json").read_text(encoding="utf-8"))
    )

    by_ns: Dict[str, Dict[str, str]] = {
        "components": {},
        "dashboard": {},
        "pages": {},
        "common": {},
        "nav": {},
    }

    for key in missing:
        if key.startswith("sectionLanding."):
            text = (
                harvested.get(key)
                or en_comp.get(key)
                or SECTION_FALLBACK.get(key)
                or title_from_key(key)
            )
            by_ns["components"][key] = text
        elif key.startswith("tileLinkActions."):
            text = harvested.get(key) or f"Open {title_from_key(key)}"
            by_ns["dashboard"][key] = text
        elif key.startswith("headers."):
            text = en_pages.get(key) or HEADER_EN.get(key) or title_from_key(key)
            by_ns["pages"][key] = text
        elif key.startswith("grid."):
            text = harvested.get(key) or GRID_EN.get(key) or title_from_key(key)
            by_ns["common"][key] = text
        elif key in NAVISH or key in (
            "app_manifest",
            "demo_data",
            "elevation_mocks",
            "general_settings",
            "mitm_dev_only",
            "rbac_lab",
            "server_control",
            "tls_security",
        ):
            # These appear as bare keys — often nav or docs. Put in both nav + components.
            text = NAVISH.get(key, title_from_key(key))
            by_ns["nav"][key] = text
            by_ns["components"][key] = text
        else:
            print(f"unclassified {key}", file=sys.stderr)

    SEED.mkdir(parents=True, exist_ok=True)
    for ns, entries in by_ns.items():
        if not entries:
            continue
        path = SEED / f"{ns}.json"
        # merge with existing seed file if present
        existing: Dict[str, str] = {}
        if path.exists():
            existing = flat(json.loads(path.read_text(encoding="utf-8")))
        existing.update(entries)
        path.write_text(
            json.dumps(unflatten(existing), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path} (+{len(entries)} → {len(existing)} keys)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
