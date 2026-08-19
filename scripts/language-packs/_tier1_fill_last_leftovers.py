"""Fill last Tier1 walk leftovers into correct namespaces."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from language_packs import dump_json, load_json, source_sha256  # noqa: E402

CA = Path(r"c:\analog-pim\core-assets\content\locales-ui")

HOWTO_EN = [
    "Open Swagger UI to try authenticated routes with your current session cookie or admin token header as documented in the security schemes.",
    "Download OpenAPI JSON for offline review or client generation; re-fetch after each server deploy that touches routes.",
    "Agent wire routes expect HMAC headers when agents sign; unsigned is still accepted only while AGENT_HMAC_ENFORCE_MODE=dual_mode.",
    "Startup wizard admin routes are under /api/admin/startup-wizard; Messaging email save paths remain /api/offline/messaging/email*.",
    "Prefer docs under /docs/admin for operator runbooks; this page is for API consumers and developers.",
]
LIMITS_EN = [
    "OpenAPI coverage tracks declared routes; a missing operation in the UI is not proven by downloading this file alone.",
    "Examples may omit lab-only or feature-gated routes until they are declared in the OpenAPI set.",
    "This page is not a certification package — keep SSP evidence in the Assessment Binder.",
]

NAV = {
    "en": {
        "general_settings": "General Settings",
        "tls_security": "TLS & security",
        "server_control": "Server Control",
        "technical_documentation": "Technical Documentation",
        "technische_dokumentation": "Technical Documentation",
        "blocked_attacks": "Blocked Attacks",
    },
    "de": {
        "general_settings": "Allgemeine Einstellungen",
        "tls_security": "TLS und Sicherheit",
        "server_control": "Serversteuerung",
        "technical_documentation": "Technische Dokumentation",
        "technische_dokumentation": "Technische Dokumentation",
        "blocked_attacks": "Blockierte Angriffe",
    },
    "fr": {
        "general_settings": "Parametres generaux",
        "tls_security": "TLS et securite",
        "server_control": "Controle du serveur",
        "technical_documentation": "Documentation technique",
        "technische_dokumentation": "Documentation technique",
        "blocked_attacks": "Attaques bloquees",
    },
    "es": {
        "general_settings": "Configuracion general",
        "tls_security": "TLS y seguridad",
        "server_control": "Control del servidor",
        "technical_documentation": "Documentacion tecnica",
        "technische_dokumentation": "Documentacion tecnica",
        "blocked_attacks": "Ataques bloqueados",
    },
}

COMPONENTS_DESC = {
    "en": "Blocked Attacks",
    "de": "Blockierte Angriffe",
    "fr": "Attaques bloquees",
    "es": "Ataques bloqueados",
}

OT_EMPTY = {
    "en": "Checking scanner status…",
    "de": "Scannerstatus wird geprueft…",
    "fr": "Verification de l'etat du scanner…",
    "es": "Comprobando el estado del escaner…",
}


def set_leaf(tree: dict, dotted: str, text: str) -> None:
    parts = dotted.split(".")
    node = tree
    for p in parts[:-1]:
        nxt = node.get(p)
        if not isinstance(nxt, dict) or (
            isinstance(nxt, dict)
            and "text" in nxt
            and set(nxt.keys()) <= {"text", "source_sha256", "note"}
        ):
            node[p] = {}
            nxt = node[p]
        node = nxt
    node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}


def main() -> None:
    for tag in ("en", "de", "fr", "es", "en-GB"):
        nav_map = NAV.get(tag, NAV["en"])
        nav = load_json(CA / tag / "nav.json")
        for k, v in nav_map.items():
            set_leaf(nav, k, v)
        dump_json(CA / tag / "nav.json", nav)

        comps = load_json(CA / tag / "components.json")
        set_leaf(
            comps,
            "sectionLanding.desc.blocked_attacks",
            COMPONENTS_DESC.get(tag, COMPONENTS_DESC["en"]),
        )
        dump_json(CA / tag / "components.json", comps)

        docs = load_json(CA / tag / "docs.json")
        for i, text in enumerate(HOWTO_EN):
            set_leaf(docs, f"technical.howTo.{i}", text)
        for i, text in enumerate(LIMITS_EN):
            set_leaf(docs, f"technical.limits.{i}", text)
        set_leaf(docs, "technische_dokumentation", nav_map["technische_dokumentation"])
        dump_json(CA / tag / "docs.json", docs)

        ot = load_json(CA / tag / "ot.json")
        set_leaf(ot, "ipScanner.emptyLoading", OT_EMPTY.get(tag, OT_EMPTY["en"]))
        dump_json(CA / tag / "ot.json", ot)

        # Also ensure common has bare nav aliases for defaultNS callers
        common = load_json(CA / tag / "common.json")
        for k, v in nav_map.items():
            set_leaf(common, k, v)
        dump_json(CA / tag / "common.json", common)

        print(tag, "ok")


if __name__ == "__main__":
    main()
