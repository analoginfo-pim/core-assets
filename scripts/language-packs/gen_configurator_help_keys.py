#!/usr/bin/env python3
"""Add screen/help keys for configurator packs (en + de). Stdlib only."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "content" / "i18n-native" / "gui"
AGENT = ROOT / "content" / "i18n-native" / "apps" / "pim-offline-agent"


def sha(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def leaf(en: str, loc: str | None = None) -> dict:
    return {"text": loc if loc is not None else en, "source_sha256": sha(en)}


def merge(path: Path, entries: dict[str, dict]) -> None:
    data = {}
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    data.update(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --- Server configurator help / status / dialog (English-source keys) ---
SERVER_EN = {
    "Confirm service action": "Confirm service action",
    "Cancelled": "Cancelled",
    "Details in the Output pane below.": "Details in the Output pane below.",
    "AIC Server Configurator": "AIC Server Configurator",
    "AIC PIM/PAM": "AIC PIM/PAM",
    "AIC Server Configurator (Tauri)": "AIC Server Configurator (Tauri)",
    "Notice": "Notice",
    "help.startup_banner": (
        "AIC Server Configurator (Win32) {bi}\r\n"
        "program: {program_id}\r\n"
        "SCM service: {scm}\r\n"
        "Help > Version for full build info.\r\n"
        "The Health group shows live probes; Status shows the last command only.\r\n"
        "Click Refresh to load manifest variables. Use Get/Set/Unset to "
        "manage individual keys. Long operations block the dialog thread.\r\n"
        "Open View > Fonts and Sizes to change scale and language.\r\n\r\n"
    ),
    "help.about_scope": (
        "Hook bundle scripts and propagation discovery are configured on the "
        "Agent configurator (Settings → Hook Bundles / Propagation / Managed Identities), "
        "not on this server program."
    ),
    "status.last_action_ok": "Last action: {label}: ok",
    "status.last_action_logs": "Last action: {label}: logs loaded",
    "status.last_action_stopped": "Last action: {label}: service stopped",
    "status.last_action_error": "Last action: {label}: error — {short}",
    "status.last_action_generic": "Last action: {label}: {summary}",
    "status.syslog_disabled": "Syslog forwarding: disabled",
    "status.syslog_ok": "Syslog forwarding: last delivery OK",
    "status.syslog_failed": "Syslog forwarding: last delivery failed ({err})",
    "status.syslog_pending": "Syslog forwarding: enabled (no delivery status yet)",
}

SERVER_DE = {
    "Confirm service action": "Dienstaktion bestätigen",
    "Cancelled": "Abgebrochen",
    "Details in the Output pane below.": "Details im Ausgabebereich unten.",
    "AIC Server Configurator": "AIC Server-Konfigurator",
    "AIC PIM/PAM": "AIC PIM/PAM",
    "AIC Server Configurator (Tauri)": "AIC Server-Konfigurator (Tauri)",
    "Notice": "Hinweis",
    "help.startup_banner": (
        "AIC Server-Konfigurator (Win32) {bi}\r\n"
        "Programm: {program_id}\r\n"
        "SCM-Dienst: {scm}\r\n"
        "Hilfe > Version für vollständige Build-Informationen.\r\n"
        "Die Gruppe Gesundheit zeigt Live-Prüfungen; Status zeigt nur den letzten Befehl.\r\n"
        "Klicken Sie auf Aktualisieren, um Manifestvariablen zu laden. Mit Get/Set/Unset "
        "verwalten Sie einzelne Schlüssel. Lange Vorgänge blockieren den Dialogthread.\r\n"
        "Öffnen Sie Ansicht > Schriftarten und Größen, um Skalierung und Sprache zu ändern.\r\n\r\n"
    ),
    "help.about_scope": (
        "Hook-Bundle-Skripte und Propagierungsentdeckung werden im "
        "Agenten-Konfigurator konfiguriert (Einstellungen → Hook-Bundles / Propagierung / "
        "Verwaltete Identitäten), nicht in diesem Serverprogramm."
    ),
    "status.last_action_ok": "Letzte Aktion: {label}: ok",
    "status.last_action_logs": "Letzte Aktion: {label}: Protokolle geladen",
    "status.last_action_stopped": "Letzte Aktion: {label}: Dienst gestoppt",
    "status.last_action_error": "Letzte Aktion: {label}: Fehler — {short}",
    "status.last_action_generic": "Letzte Aktion: {label}: {summary}",
    "status.syslog_disabled": "Syslog-Weiterleitung: deaktiviert",
    "status.syslog_ok": "Syslog-Weiterleitung: letzte Zustellung OK",
    "status.syslog_failed": "Syslog-Weiterleitung: letzte Zustellung fehlgeschlagen ({err})",
    "status.syslog_pending": "Syslog-Weiterleitung: aktiviert (noch kein Zustellstatus)",
}


def port_ui_json(src: Path, dest: Path, tag: str) -> None:
    """Copy local configurator ui.json into product pack with proper leaves."""
    raw = json.loads(src.read_text(encoding="utf-8"))
    # For non-en, need en source for hashes — load en sibling
    en_path = src.parent.parent / "en" / "ui.json"
    en_raw = json.loads(en_path.read_text(encoding="utf-8")) if en_path.is_file() else raw
    out = {}
    if dest.is_file():
        out = json.loads(dest.read_text(encoding="utf-8"))
    for k, v in raw.items():
        if not isinstance(v, str):
            continue
        en_text = en_raw.get(k, v) if isinstance(en_raw.get(k), str) else v
        out[k] = leaf(en_text, v)
    # Keep existing product stubs
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ported {src} -> {dest} ({tag}, {len(out)} keys)")


AGENT_ABOUT_EN = {
    "config.about.version": "Version: {version}",
    "config.about.built": "Built: {date}",
    "config.about.channel": "Channel: {channel}",
    "config.about.build": "Build: {profile}",
    "config.about.tls_crypto": "TLS crypto: {status}",
    "config.about.disclosures_heading": "Management disclosures (imported):",
    "config.about.not_loaded": "(not loaded)",
    "config.about.no_disclosures": "(no management disclosures imported)",
}
AGENT_ABOUT_DE = {
    "config.about.version": "Version: {version}",
    "config.about.built": "Erstellt: {date}",
    "config.about.channel": "Kanal: {channel}",
    "config.about.build": "Build: {profile}",
    "config.about.tls_crypto": "TLS-Krypto: {status}",
    "config.about.disclosures_heading": "Management-Offenlegungen (importiert):",
    "config.about.not_loaded": "(nicht geladen)",
    "config.about.no_disclosures": "(keine Management-Offenlegungen importiert)",
}


def main() -> None:
    merge(
        GUI / "en" / "server_configurator.json",
        {k: leaf(v) for k, v in SERVER_EN.items()},
    )
    merge(
        GUI / "de" / "server_configurator.json",
        {k: leaf(SERVER_EN[k], SERVER_DE[k]) for k in SERVER_EN},
    )
    print("merged server_configurator help/status keys (en+de)")

    # Jump / DB: port Tauri ui.json into product packs
    jump_en = ROOT.parent / "pim-jump-server" / "configurator-tauri" / "src" / "locales" / "en" / "ui.json"
    jump_de = ROOT.parent / "pim-jump-server" / "configurator-tauri" / "src" / "locales" / "de" / "ui.json"
    db_en = ROOT.parent / "pim-db-mgmt-agent" / "configurator-tauri" / "src" / "locales" / "en" / "ui.json"
    db_de = ROOT.parent / "pim-db-mgmt-agent" / "configurator-tauri" / "src" / "locales" / "de" / "ui.json"
    if jump_en.is_file():
        port_ui_json(jump_en, GUI / "en" / "jump_configurator.json", "en")
    if jump_de.is_file():
        port_ui_json(jump_de, GUI / "de" / "jump_configurator.json", "de")
    if db_en.is_file():
        port_ui_json(db_en, GUI / "en" / "db_mgmt_configurator.json", "en")
    if db_de.is_file():
        port_ui_json(db_de, GUI / "de" / "db_mgmt_configurator.json", "de")

    merge(AGENT / "en" / "messages.json", {k: leaf(v) for k, v in AGENT_ABOUT_EN.items()})
    merge(
        AGENT / "de" / "messages.json",
        {k: leaf(AGENT_ABOUT_EN[k], AGENT_ABOUT_DE[k]) for k in AGENT_ABOUT_EN},
    )
    print("merged agent config.about.* keys (en+de)")


if __name__ == "__main__":
    main()
