#!/usr/bin/env python3
"""Add Win32 menu / dialog / CLI keys for configurators (en + de). Stdlib only."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "content" / "i18n-native" / "apps" / "pim-offline-agent"
GUI = ROOT / "content" / "i18n-native" / "gui"
JUMP = ROOT / "content" / "i18n-native" / "apps" / "pim-jump-server"
DB = ROOT / "content" / "i18n-native" / "apps" / "pim-db-mgmt-agent"


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


# --- Agent Win32 menu bar (English source = .rc caption) ---
AGENT_MENU_EN = [
    "&File",
    "&Refresh status",
    "Re&load settings",
    "&Validate settings file...",
    "&Apply settings file...",
    "E&xport settings (v3 JSON)...",
    "E&xit",
    "&View",
    # GetMenuStringW form (RC `&&` becomes single `&`).
    "Fonts & Si&zes...",
    "Output log &options...",
    "&Open output log folder",
    "&Settings",
    "&Log Time...",
    "Server &Connection...",
    "&Network / Proxy...",
    "Sync &Schedule...",
    "Lo&gging...",
    "&Diagnostics & Telemetry...",
    "S&yslog Forwarding...",
    "&Security / Elevation...",
    "Elevation &Platform Policy...",
    "Asymmetric Grant &Signing...",
    "Pr&e and post scripts...",
    "De&pendent discovery...",
    "&Identity & Enrollment...",
    "&Managed Identities...",
    "Service &Account...",
    "&Updates...",
    "E&vent Log",
    "Install message &provider...",
    "Require self-test &pass on install",
    "Check &registration status...",
    "&Mirror events to Windows Event Log",
    "Ser&vice",
    "Sta&tus",
    "&Start",
    "Sto&p",
    "&Install...",
    "&Uninstall",
    "&Help",
    "&About...",
    "&Version...",
    "Settings &Reference...",
    "&LLM development mode",
]

# German with accelerators preserved where natural
AGENT_MENU_DE = {
    "&File": "&Datei",
    "&Refresh status": "Status a&ktualisieren",
    "Re&load settings": "Einstellungen neu &laden",
    "&Validate settings file...": "Einstellungsdatei &prüfen...",
    "&Apply settings file...": "Einstellungsdatei an&wenden...",
    "E&xport settings (v3 JSON)...": "Einstellungen e&xportieren (v3 JSON)...",
    "E&xit": "B&eenden",
    "&View": "&Ansicht",
    "Fonts & Si&zes...": "&Schrift und Größen...",
    "Output log &options...": "Ausgabeprotokoll-&Optionen...",
    "&Open output log folder": "Ausgabeprotokollordner &öffnen",
    "&Settings": "&Einstellungen",
    "&Log Time...": "&Protokollzeit...",
    "Server &Connection...": "Server&verbindung...",
    "&Network / Proxy...": "&Netzwerk / Proxy...",
    "Sync &Schedule...": "Sync-&Zeitplan...",
    "Lo&gging...": "Protokol&lierung...",
    "&Diagnostics & Telemetry...": "&Diagnose und Telemetrie...",
    "S&yslog Forwarding...": "S&yslog-Weiterleitung...",
    "&Security / Elevation...": "&Sicherheit / Elevation...",
    "Elevation &Platform Policy...": "Elevations-&Plattformrichtlinie...",
    "Asymmetric Grant &Signing...": "Asymmetrische Grant-&Signatur...",
    "Pr&e and post scripts...": "Vor- und Nach&skripte...",
    "De&pendent discovery...": "Abhängige &Erkennung...",
    "&Identity & Enrollment...": "&Identität und Enrollment...",
    "&Managed Identities...": "&Verwaltete Identitäten...",
    "Service &Account...": "Dienst&konto...",
    "&Updates...": "&Updates...",
    "E&vent Log": "E&reignisprotokoll",
    "Install message &provider...": "Nachrichten&anbieter installieren...",
    "Require self-test &pass on install": "Selbsttest-&Bestanden bei Installation verlangen",
    "Check &registration status...": "&Registrierungsstatus prüfen...",
    "&Mirror events to Windows Event Log": "Ereignisse in Windows-Ereignisprotokoll &spiegeln",
    "Ser&vice": "Die&nst",
    "Sta&tus": "Sta&tus",
    "&Start": "&Starten",
    "Sto&p": "Sto&ppen",
    "&Install...": "&Installieren...",
    "&Uninstall": "&Deinstallieren",
    "&Help": "&Hilfe",
    "&About...": "&Info...",
    "&Version...": "&Version...",
    "Settings &Reference...": "Einstellungen-&Referenz...",
    "&LLM development mode": "&LLM-Entwicklungsmodus",
}

# --- Server dialog bodies (English-source keys) ---
SERVER_DIALOG_EN = {
    "Connectivity test failed": "Connectivity test failed",
    "Loaded. Edit JSON then click OK to validate and save.": (
        "Loaded. Edit JSON then click OK to validate and save."
    ),
    "Loaded default template.": "Loaded default template.",
    "Saved to {}. Agents receive updates on next check-in.": (
        "Saved to {}. Agents receive updates on next check-in."
    ),
    "Grant trust keys missing — run wizard mint with machine_id or seed dev GSK.": (
        "Grant trust keys missing — run wizard mint with machine_id or seed dev GSK."
    ),
    "Edit revocation lists and click OK to persist to offline_global_settings.": (
        "Edit revocation lists and click OK to persist to offline_global_settings."
    ),
    "Revocation lists saved to offline_global_settings.": (
        "Revocation lists saved to offline_global_settings."
    ),
    "Trust key saved to elevation registry.": "Trust key saved to elevation registry.",
    "Add trust key failed: {e}": "Add trust key failed: {e}",
    "Rotate signing key failed: {e}": "Rotate signing key failed: {e}",
    "dialog.database_help": (
        "Edit components and click `Rebuild URL from fields` to assemble DATABASE_URL. "
        "Or paste a URL into the Connection URL field and click `Parse URL into fields` "
        "to back-fill the components. `Test connectivity` runs DNS + TCP + access probes "
        "against the URL above. Save writes DATABASE_HOST/PORT/USER/PASSWORD/NAME/SSL_MODE "
        "plus DATABASE_URL to platform storage."
    ),
    "dialog.proxy_help": (
        "Click `Test connectivity` to validate the proxy URL parses cleanly. "
        "`Save` writes HTTP_PROXY_URL, HTTP_PROXY_AUTH_KIND, HTTP_PROXY_USER, "
        "HTTP_PROXY_PASSWORD, and HTTP_NO_PROXY to platform storage."
    ),
    "dialog.syslog_help": (
        "Edit fields then click Test syslog or Preview sample using unsaved dialog values."
    ),
    "dialog.syslog_probe_uses_unsaved": "Probe uses unsaved dialog values.",
    "The AIC Server service was uninstalled successfully.": (
        "The AIC Server service was uninstalled successfully."
    ),
    "Configuration required: run the AIC Server Configurator": (
        "Configuration required: run the AIC Server Configurator"
    ),
}

SERVER_DIALOG_DE = {
    "Connectivity test failed": "Verbindungstest fehlgeschlagen",
    "Loaded. Edit JSON then click OK to validate and save.": (
        "Geladen. JSON bearbeiten, dann OK zum Prüfen und Speichern."
    ),
    "Loaded default template.": "Standardvorlage geladen.",
    "Saved to {}. Agents receive updates on next check-in.": (
        "Gespeichert unter {}. Agents erhalten Updates beim nächsten Check-in."
    ),
    "Grant trust keys missing — run wizard mint with machine_id or seed dev GSK.": (
        "Grant-Vertrauensschlüssel fehlen — Wizard-Mint mit machine_id oder Dev-GSK ausführen."
    ),
    "Edit revocation lists and click OK to persist to offline_global_settings.": (
        "Sperrlisten bearbeiten und OK zum Speichern in offline_global_settings."
    ),
    "Revocation lists saved to offline_global_settings.": (
        "Sperrlisten in offline_global_settings gespeichert."
    ),
    "Trust key saved to elevation registry.": (
        "Vertrauensschlüssel in Elevations-Registrierung gespeichert."
    ),
    "Add trust key failed: {e}": "Vertrauensschlüssel hinzufügen fehlgeschlagen: {e}",
    "Rotate signing key failed: {e}": "Signierschlüssel rotieren fehlgeschlagen: {e}",
    "dialog.database_help": (
        "Komponenten bearbeiten und `URL aus Feldern neu aufbauen` klicken, um DATABASE_URL "
        "zusammenzusetzen. Oder eine URL in Verbindungs-URL einfügen und "
        "`URL in Felder zerlegen` klicken. `Verbindung testen` prüft DNS + TCP + Zugriff. "
        "Speichern schreibt DATABASE_* und DATABASE_URL in die Plattformspeicherung."
    ),
    "dialog.proxy_help": (
        "`Verbindung testen` prüft die Proxy-URL. `Speichern` schreibt HTTP_PROXY_* "
        "in die Plattformspeicherung."
    ),
    "dialog.syslog_help": (
        "Felder bearbeiten, dann Syslog testen oder Vorschau mit ungespeicherten Werten."
    ),
    "dialog.syslog_probe_uses_unsaved": "Prüfung verwendet ungespeicherte Dialogwerte.",
    "The AIC Server service was uninstalled successfully.": (
        "Der AIC Server-Dienst wurde erfolgreich deinstalliert."
    ),
    "Configuration required: run the AIC Server Configurator": (
        "Konfiguration erforderlich: AIC Server-Konfigurator ausführen"
    ),
}

# --- Jump / DB CLI operator labels ---
JUMP_CLI_EN = {
    "cli.error_prefix": "error: {detail}",
    "cli.syslog_probe_load_failed": "error: syslog probe failed to read app-config: {detail}",
    "cli.syslog_serialize_failed": "error: failed to serialize syslog probe result: {detail}",
    "cli.syslog_probe_line": (
        "product={product} ok={ok} forwarding_enabled={forwarding}"
    ),
    "cli.syslog_step": "  [{outcome}] {label} ({ms} ms) — {detail}",
}

JUMP_CLI_DE = {
    "cli.error_prefix": "Fehler: {detail}",
    "cli.syslog_probe_load_failed": (
        "Fehler: Syslog-Prüfung konnte app-config nicht lesen: {detail}"
    ),
    "cli.syslog_serialize_failed": (
        "Fehler: Syslog-Prüfungsergebnis konnte nicht serialisiert werden: {detail}"
    ),
    "cli.syslog_probe_line": (
        "Produkt={product} ok={ok} weiterleitung_aktiv={forwarding}"
    ),
    "cli.syslog_step": "  [{outcome}] {label} ({ms} ms) — {detail}",
}

DB_CLI_EN = {
    "cli.error_prefix": "error: {detail}",
    "cli.unlocked": "unlocked",
    "cli.about_product": "product=AIC Database Management Agent Configurator",
    "cli.about_version": "version={version}",
    "cli.fips_validated": "fips=validated",
    "cli.fips_cert": "fips_cert={cert}",
    "cli.fips_module": "fips_module={module}",
    "cli.fips_module_version": "fips_module_version={version}",
    "cli.fips_url": "fips_url={url}",
    "cli.fips_publication": "fips_publication={publication}",
    "cli.fips_pending": "fips=pending",
    "cli.fips_list": "fips_list={list}",
    "cli.status_elevated": "elevated: {elevated}",
    "cli.status_master_hash": "master_hash_present: {present}",
    "cli.status_config_root": "config_root: {path}",
    "cli.status_settings_store": "settings_store: {store}",
    "cli.status_log_level": "log_level: {level}",
    "cli.status_backup_root": "backup_root: {path}",
    "cli.status_backup_encrypt": "backup_encrypt: {encrypt}",
    "cli.status_scm_name": "scm_name: {name}",
    "cli.status_scm_state": "scm_state: {state} ({detail})",
    "cli.status_service_state": "service_state: {state}",
    "cli.status_log_file": "log_file: {path}",
    "cli.status_runtime_missing": "runtime_status: (missing — agent not running)",
    "cli.vault_empty": "(vault empty — rotation populates history)",
    "cli.ok": "ok",
    "cli.syslog_probe_line": (
        "product={product} ok={ok} forwarding_enabled={forwarding}"
    ),
}

DB_CLI_DE = {
    "cli.error_prefix": "Fehler: {detail}",
    "cli.unlocked": "entsperrt",
    "cli.about_product": "Produkt=AIC Datenbankverwaltungs-Agent-Konfigurator",
    "cli.about_version": "Version={version}",
    "cli.fips_validated": "fips=validiert",
    "cli.fips_cert": "fips_zert={cert}",
    "cli.fips_module": "fips_modul={module}",
    "cli.fips_module_version": "fips_modul_version={version}",
    "cli.fips_url": "fips_url={url}",
    "cli.fips_publication": "fips_veröffentlichung={publication}",
    "cli.fips_pending": "fips=ausstehend",
    "cli.fips_list": "fips_liste={list}",
    "cli.status_elevated": "erhöht: {elevated}",
    "cli.status_master_hash": "master_hash_vorhanden: {present}",
    "cli.status_config_root": "config_wurzel: {path}",
    "cli.status_settings_store": "einstellungsspeicher: {store}",
    "cli.status_log_level": "protokollstufe: {level}",
    "cli.status_backup_root": "backup_wurzel: {path}",
    "cli.status_backup_encrypt": "backup_verschlüsseln: {encrypt}",
    "cli.status_scm_name": "scm_name: {name}",
    "cli.status_scm_state": "scm_status: {state} ({detail})",
    "cli.status_service_state": "dienststatus: {state}",
    "cli.status_log_file": "protokolldatei: {path}",
    "cli.status_runtime_missing": "laufzeitstatus: (fehlt — Agent läuft nicht)",
    "cli.vault_empty": "(Tresor leer — Rotation füllt den Verlauf)",
    "cli.ok": "ok",
    "cli.syslog_probe_line": (
        "Produkt={product} ok={ok} weiterleitung_aktiv={forwarding}"
    ),
}


def main() -> None:
    # Agent menus
    en_m = {k: leaf(k) for k in AGENT_MENU_EN}
    de_m = {k: leaf(k, AGENT_MENU_DE[k]) for k in AGENT_MENU_EN}
    merge(AGENT / "en" / "messages.json", en_m)
    merge(AGENT / "de" / "messages.json", de_m)

    # Server dialogs
    merge(GUI / "en" / "server_configurator.json", {k: leaf(v) for k, v in SERVER_DIALOG_EN.items()})
    merge(
        GUI / "de" / "server_configurator.json",
        {k: leaf(SERVER_DIALOG_EN[k], SERVER_DIALOG_DE[k]) for k in SERVER_DIALOG_EN},
    )

    # Jump / DB CLI
    merge(JUMP / "en" / "messages.json", {k: leaf(v) for k, v in JUMP_CLI_EN.items()})
    merge(
        JUMP / "de" / "messages.json",
        {k: leaf(JUMP_CLI_EN[k], JUMP_CLI_DE[k]) for k in JUMP_CLI_EN},
    )
    merge(DB / "en" / "messages.json", {k: leaf(v) for k, v in DB_CLI_EN.items()})
    merge(
        DB / "de" / "messages.json",
        {k: leaf(DB_CLI_EN[k], DB_CLI_DE[k]) for k in DB_CLI_EN},
    )
    print("ok agent menus", len(AGENT_MENU_EN))
    print("ok server dialogs", len(SERVER_DIALOG_EN))
    print("ok jump cli", len(JUMP_CLI_EN), "db cli", len(DB_CLI_EN))


if __name__ == "__main__":
    main()
