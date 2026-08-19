"""Fill Tier-1 de walk gaps into the namespaces the SPA actually resolves.

- chrome.sessionPolicy.* and bare keys used via useTranslation() → common
- headers.* bullets → pages
- 3.x.xe control ids → controls
Also seed the same keys into en (and later fr/es/en-GB) for structure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from language_packs import dump_json, load_json, source_sha256  # noqa: E402

CA = Path(r"c:\analog-pim\core-assets\content\locales-ui")

DE_FILLS_COMMON = {
    "chrome.sessionPolicy.heading": "Anmeldesitzungsrichtlinie",
    "chrome.sessionPolicy.intro": (
        "Steuert Idle- und Absolute-Timeouts fuer Admin-Anmeldesitzungen. "
        "Aenderungen gelten fuer neue Sitzungen."
    ),
    "chrome.sessionPolicy.openDedicated": "Vollseite Sitzungsrichtlinie oeffnen",
    "chrome.sessionPolicy.requireIamAria": "IAM-Anmeldung erforderlich",
    "chrome.sessionPolicy.requireIam": "IAM-Anmeldung erforderlich",
    "chrome.sessionPolicy.absoluteTtl": "Absolute Sitzungsdauer (Minuten)",
    "chrome.sessionPolicy.absoluteTtlAria": "Absolute Sitzungsdauer in Minuten",
    "chrome.sessionPolicy.idleTimeout": "Idle-Timeout (Minuten)",
    "chrome.sessionPolicy.idleTimeoutAria": "Idle-Timeout in Minuten",
    "chrome.sessionPolicy.absoluteMax": "Maximale Absolute Dauer (Minuten)",
    "chrome.sessionPolicy.absoluteMaxAria": "Maximale Absolute Dauer in Minuten",
    "chrome.sessionPolicy.refresh": "Sitzung bei Aktivitaet verlaengern",
    "chrome.sessionPolicy.rotate": "Token bei Verlaengerung rotieren",
    "chrome.sessionPolicy.multiTab": "Mehrere Browser-Tabs erlauben",
    "chrome.sessionPolicy.forceLogoff": "Bei Ablauf abmelden",
    "chrome.sessionPolicy.httponly": "HttpOnly-Cookie verwenden",
    "chrome.sessionPolicy.pamDisconnectAria": "PAM-Sitzungen bei Abmeldung trennen",
    "chrome.sessionPolicy.pamDisconnect": "PAM-Sitzungen bei Abmeldung trennen",
    "chrome.sessionPolicy.clientStorage": "Client-Sitzungsspeicher",
    "chrome.sessionPolicy.storageSession": "sessionStorage",
    "chrome.sessionPolicy.storageLocal": "localStorage",
    "chrome.sessionPolicy.multiTabNote": (
        "Mehrere Tabs teilen dieselbe Anmeldesitzung. "
        "Abmelden in einem Tab beendet alle."
    ),
    "chrome.sessionPolicy.save": "Sitzungsrichtlinie speichern",
    "technische_dokumentation": "Technische Dokumentation",
}

EN_FILLS_COMMON = {
    "chrome.sessionPolicy.heading": "Logon session policy",
    "chrome.sessionPolicy.intro": (
        "Controls idle and absolute timeouts for admin logon sessions. "
        "Changes apply to new sessions."
    ),
    "chrome.sessionPolicy.openDedicated": "Open full session policy page",
    "chrome.sessionPolicy.requireIamAria": "Require IAM logon",
    "chrome.sessionPolicy.requireIam": "Require IAM logon",
    "chrome.sessionPolicy.absoluteTtl": "Absolute session lifetime (minutes)",
    "chrome.sessionPolicy.absoluteTtlAria": "Absolute session lifetime in minutes",
    "chrome.sessionPolicy.idleTimeout": "Idle timeout (minutes)",
    "chrome.sessionPolicy.idleTimeoutAria": "Idle timeout in minutes",
    "chrome.sessionPolicy.absoluteMax": "Maximum absolute lifetime (minutes)",
    "chrome.sessionPolicy.absoluteMaxAria": "Maximum absolute lifetime in minutes",
    "chrome.sessionPolicy.refresh": "Extend session on activity",
    "chrome.sessionPolicy.rotate": "Rotate token on refresh",
    "chrome.sessionPolicy.multiTab": "Allow multiple browser tabs",
    "chrome.sessionPolicy.forceLogoff": "Log off when session expires",
    "chrome.sessionPolicy.httponly": "Use HttpOnly cookie",
    "chrome.sessionPolicy.pamDisconnectAria": "Disconnect PAM sessions on logoff",
    "chrome.sessionPolicy.pamDisconnect": "Disconnect PAM sessions on logoff",
    "chrome.sessionPolicy.clientStorage": "Client session storage",
    "chrome.sessionPolicy.storageSession": "sessionStorage",
    "chrome.sessionPolicy.storageLocal": "localStorage",
    "chrome.sessionPolicy.multiTabNote": (
        "Multiple tabs share the same logon session. "
        "Logoff in one tab ends all."
    ),
    "chrome.sessionPolicy.save": "Save session policy",
    "technische_dokumentation": "Technical documentation",
}

DE_PAGES_HEADERS = {
    "headers.enclave__auditor-binder.bullets.0": (
        "Der Auditor Binder sammelt Nachweisabschnitte fuer die Bewertung."
    ),
    "headers.enclave__auditor-binder.bullets.1": (
        "Abschnitte werden aus dem Live-Zustand gerendert — kein Met-Stempel."
    ),
    "headers.enclave__auditor-binder.bullets.2": (
        "Export und Historie bleiben an die Instanz gebunden."
    ),
    "headers.enclave__compliance.bullets.0": (
        "Enclave-Compliance zeigt den Lieferstatus der Kontrollarbeit."
    ),
    "headers.enclave__compliance.bullets.1": (
        "Zahlen beschreiben Lieferung, nicht Zertifizierung."
    ),
    "headers.enclave__compliance.bullets.2": (
        "Oeffnen Sie einen Eintrag, um Details und Nachweis zu sehen."
    ),
    "headers.endpoint-privilege.bullets.0": (
        "Endpoint Privilege steuert Erhoehung und lokale Rechte."
    ),
    "headers.endpoint-privilege.bullets.1": (
        "Anfragen und Richtlinien erscheinen in der Liste."
    ),
    "headers.endpoint-privilege.bullets.2": (
        "Aenderungen werden geprueft und protokolliert."
    ),
    "headers.ot.bullets.0": (
        "OT-Inventar und Discovery fuer industrielle Geraete."
    ),
    "headers.ot.bullets.1": (
        "Nutzen Sie die Karten, um Inventar, Scan und Rotation zu oeffnen."
    ),
    "headers.settings__service-logs.bullets.0": (
        "Dienstprotokolle helfen bei Diagnose und Betrieb."
    ),
    "headers.settings__service-logs.bullets.1": (
        "Filter und Export bleiben in dieser Ansicht."
    ),
}

EN_PAGES_HEADERS = {
    "headers.enclave__auditor-binder.bullets.0": (
        "The Auditor Binder collects evidence sections for assessment."
    ),
    "headers.enclave__auditor-binder.bullets.1": (
        "Sections render from live state — not a Met stamp."
    ),
    "headers.enclave__auditor-binder.bullets.2": (
        "Export and history stay bound to the instance."
    ),
    "headers.enclave__compliance.bullets.0": (
        "Enclave compliance shows delivery status for control work."
    ),
    "headers.enclave__compliance.bullets.1": (
        "Numbers describe delivery, not certification."
    ),
    "headers.enclave__compliance.bullets.2": (
        "Open a row for detail and evidence."
    ),
    "headers.endpoint-privilege.bullets.0": (
        "Endpoint Privilege controls elevation and local rights."
    ),
    "headers.endpoint-privilege.bullets.1": (
        "Requests and policies appear in the list."
    ),
    "headers.endpoint-privilege.bullets.2": (
        "Changes are reviewed and logged."
    ),
    "headers.ot.bullets.0": "OT inventory and discovery for industrial devices.",
    "headers.ot.bullets.1": (
        "Use the cards to open inventory, scan, and rotation."
    ),
    "headers.settings__service-logs.bullets.0": (
        "Service logs help with diagnosis and operations."
    ),
    "headers.settings__service-logs.bullets.1": (
        "Filters and export stay on this view."
    ),
}

CONTROL_IDS = {
    "3.1.1e": "3.1.1e — Limit system access (enhanced)",
    "3.1.2e": "3.1.2e — Limit transaction types (enhanced)",
    "3.1.3e": "3.1.3e — Control CUI flow (enhanced)",
    "3.6.1e": "3.6.1e — Incident handling (enhanced)",
    "3.6.2e": "3.6.2e — Incident reporting (enhanced)",
    "3.11.1e": "3.11.1e — Risk assessments (enhanced)",
    "3.11.2e": "3.11.2e — Vulnerability scan (enhanced)",
    "3.14.6e": "3.14.6e — Monitor communications (enhanced)",
}

DE_CONTROL = {
    "3.1.1e": "3.1.1e — Systemzugriff begrenzen (erweitert)",
    "3.1.2e": "3.1.2e — Transaktionstypen begrenzen (erweitert)",
    "3.1.3e": "3.1.3e — CUI-Fluss steuern (erweitert)",
    "3.6.1e": "3.6.1e — Vorfallbehandlung (erweitert)",
    "3.6.2e": "3.6.2e — Vorfallmeldung (erweitert)",
    "3.11.1e": "3.11.1e — Risikobewertungen (erweitert)",
    "3.11.2e": "3.11.2e — Schwachstellenscan (erweitert)",
    "3.14.6e": "3.14.6e — Kommunikation ueberwachen (erweitert)",
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


def apply_map(path: Path, fills: dict[str, str]) -> int:
    tree = load_json(path) if path.exists() else {}
    for k, v in fills.items():
        set_leaf(tree, k, v)
    dump_json(path, tree)
    return len(fills)


def main() -> None:
    n = 0
    n += apply_map(CA / "de" / "common.json", DE_FILLS_COMMON)
    n += apply_map(CA / "en" / "common.json", EN_FILLS_COMMON)
    n += apply_map(CA / "de" / "pages.json", DE_PAGES_HEADERS)
    n += apply_map(CA / "en" / "pages.json", EN_PAGES_HEADERS)
    n += apply_map(CA / "de" / "controls.json", DE_CONTROL)
    n += apply_map(CA / "en" / "controls.json", CONTROL_IDS)
    # Mirror EN into fr/es/en-GB for structure (draft EN clears banners; formal later)
    for tag in ("fr", "es", "en-GB"):
        n += apply_map(CA / tag / "common.json", EN_FILLS_COMMON)
        n += apply_map(CA / tag / "pages.json", EN_PAGES_HEADERS)
        n += apply_map(CA / tag / "controls.json", CONTROL_IDS)
    print(f"applied {n} leaf writes")


if __name__ == "__main__":
    main()
