#!/usr/bin/env python3
"""Finish en-GB: rewrite leaves still identical to US en into natural UK English.

KEEP exact: OK, Cancel, Apply, Close, Save, Error, Warning, Browse…;
Copyright …; any text containing {organization_name}.
Never append '(UK)'. Never invent IGA. Keep {{placeholders}} and {tokens}.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

KEEP_EXACT = {
    "OK",
    "Cancel",
    "Apply",
    "Close",
    "Save",
    "Error",
    "Warning",
    "Browse…",
    "Browse...",
    "&Apply",
    "&Save",
}

KEEP_PREFIX = ("Copyright ",)
KEEP_SUBSTR = ("{organization_name}",)

# Product / proper-noun tokens left identical on purpose (honest Partial)
VARIETY_NEUTRAL_OK = {
    "CMMC",
    "POA&M",
    "Open POA&M",
    "MSP-run IGA",
    "Level 1",
    "Level 2",
    "Level 3",
    "Scaffold (PCI)",
    "Scaffold (GDPR)",
    "Deutsch",
    "English",
    "Français",
    "PKCS#11 configuration",
    "assets/aic-icon.ico",
    "app.manifest",
    "AIC Jump Server",
    "Jump Config",
    "AIC Database Management Agent",
    "About / FIPS",
    "BLOCKED",
    "Live",
    "Partial",
    "Absent",
    "Planned",
}

SUBS = [
    (r"\bauthorized\b", "authorised"),
    (r"\bUnauthorized\b", "Unauthorised"),
    (r"\bunauthorized\b", "unauthorised"),
    (r"\bAuthorized\b", "Authorised"),
    (r"\borganization\b", "organisation"),
    (r"\bOrganization\b", "Organisation"),
    (r"\borganizations\b", "organisations"),
    (r"\bOrganizations\b", "Organisations"),
    (r"\bbehavior\b", "behaviour"),
    (r"\bBehavior\b", "Behaviour"),
    (r"\bfavor\b", "favour"),
    (r"\bFavor\b", "Favour"),
    (r"\bcenter\b", "centre"),
    (r"\bCenter\b", "Centre"),
    (r"\bcentered\b", "centred"),
    (r"\blicense\b", "licence"),
    (r"\bLicense\b", "Licence"),
    (r"\bprogram\b", "programme"),
    (r"\bProgram\b", "Programme"),
    (r"\bprograms\b", "programmes"),
    (r"\bPrograms\b", "Programmes"),
    (r"\bcatalog\b", "catalogue"),
    (r"\bCatalog\b", "Catalogue"),
    (r"\bdialog\b", "dialogue"),
    (r"\bDialog\b", "Dialogue"),
    (r"\bcustomize\b", "customise"),
    (r"\bCustomize\b", "Customise"),
    (r"\bcustomized\b", "customised"),
    (r"\binitialize\b", "initialise"),
    (r"\bInitialize\b", "Initialise"),
    (r"\bnormalized\b", "normalised"),
    (r"\bnormalize\b", "normalise"),
    (r"\brecognize\b", "recognise"),
    (r"\bRecognize\b", "Recognise"),
    (r"\bsynchronize\b", "synchronise"),
    (r"\banalyze\b", "analyse"),
    (r"\bAnalyze\b", "Analyse"),
    (r"\bcolor\b", "colour"),
    (r"\bColor\b", "Colour"),
    (r"\bdefense\b", "defence"),
    (r"\bDefense\b", "Defence"),
    (r"\blogon\b", "sign-in"),
    (r"\bLogon\b", "Sign-in"),
    (r"\blogons\b", "sign-ins"),
    (r"\bLogons\b", "Sign-ins"),
]


def uk_lex(text: str) -> str:
    out = text
    for pat, repl in SUBS:
        out = re.sub(pat, repl, out)
    return out


# Only entries that CHANGE the string
PHRASE = {
    "Table of contents": "Contents",
    "Architecture & operating model": "Architecture and operating model",
    "CMMC L1 / FCI scoping": "CMMC Level 1 / FCI scoping",
    "CMMC L2 / CUI scoping & boundary": "CMMC Level 2 / CUI scoping and boundary",
    "Current-state compliance & gaps": "Current-state compliance and gaps",
    "Evidence index by practice": "Evidence index by practice area",
    "Assessor notes & interview log": "Assessor notes and interview log",
    "Export package notes": "Notes for the export package",
    "Customer-managed AD / external directory": "Customer-managed Active Directory / external directory",
    "None / not applicable": "None — not applicable",
    "Level 1 (basic / FCI)": "Level 1 (basic / FCI only)",
    "Shared services inheritance": "Shared-services inheritance",
    "MSP prepared package": "MSP-prepared package",
    "No review scheduled": "No review is scheduled",
    "the date on your assignment": "the date shown on your assignment",
    "You have been assigned training": "Training has been assigned to you",
    "Training is due soon": "Your training is due soon",
    "Training is due today": "Your training is due today",
    "Training is overdue": "Your training is overdue",
    "Please complete": "Please finish",
    "Cover sheet": "Cover page",
    "Loading dashboard": "Loading the dashboard",
    "generated {{timestamp}}": "generated at {{timestamp}}",
    "Personal layout saved.": "Your personal layout has been saved.",
    "Could not load dashboard aggregate:": "Could not load the dashboard aggregate:",
    "Move {{title}} up": "Move {{title}} upwards",
    "Move {{title}} down": "Move {{title}} downwards",
    "Remove {{title}} from layout": "Remove {{title}} from the layout",
    "System group filter": "System-group filter",
    "Look-back window": "Look-back period",
    "Loading look-back window": "Loading the look-back period",
    "Last {{days}} days": "Previous {{days}} days",
    "Most-tried usernames": "Most frequently tried usernames",
    "Failed and denied logons": "Failed and denied sign-ins",
    "Threat-intel hits": "Threat-intelligence hits",
    "Sessions / evidence": "Sessions and evidence",
    "Schedule enabled": "Schedule is enabled",
    "Discovery jobs (Live)": "Discovery jobs (live)",
    "Start OT discovery job": "Start the OT discovery job",
    "Enable OT discovery schedule": "Enable the OT discovery schedule",
    "OT discovery interval in minutes": "OT discovery interval, in minutes",
    "Connect OT broker session to {{name}}": "Connect the OT broker session to {{name}}",
    "Test connectivity": "Test the connection",
    "&Test connectivity": "&Test the connection",
    "Time window": "Time period",
    "Last 7 days": "Past 7 days",
    "Last 30 days": "Past 30 days",
    "Last 90 days": "Past 90 days",
    "Top source IPs": "Top source IP addresses",
    "Save schedule": "Save the schedule",
    "Startup wizard": "Start-up wizard",
    "Elevation denied": "Elevation refused",
    "Elevation lockout warning": "Elevation lock-out warning",
    "Elevation not performed": "Elevation was not performed",
    "Closing due to inactivity…": "Closing because of inactivity…",
    "Request package ready": "Request package is ready",
    "Cannot generate request": "Cannot generate the request",
    "Validate settings file…": "Validate the settings file…",
    "Apply settings file…": "Apply the settings file…",
    "No keys returned.": "No keys were returned.",
    "Key is required.": "A key is required.",
    "UI error": "Interface error",
    "Fonts & Sizes…": "Fonts and sizes…",
    "Saving layout…": "Saving the layout…",
    "Request failed": "The request failed",
    "Clear stored value": "Clear the stored value",
    "Edit selected key": "Edit the selected key",
    "Built-in sinks for selected event": "Built-in sinks for the selected event",
    "Copy request to clip&board": "Copy request to the clip&board",
    "&Review required notices": "&Review the required notices",
    "Paste r&esult here:": "Paste the r&esult here:",
    "&Local (12-hour AM/PM with offset)": "&Local (12-hour am/pm with offset)",
    "L&ocal (12-hour AM/PM with offset)": "L&ocal (12-hour am/pm with offset)",
    "register completed.": "Registration completed.",
    "init completed.": "Initialisation completed.",
    "reload ok": "reload OK",
    "Blocked API routes": "Blocked API route list",
    "SPRS scoring worksheet": "SPRS scoring sheet",
    "Partner / on-premises provisioning": "Partner / on-premises provision",
    "Scaffold (California / CPRA)": "Scaffold pack (California / CPRA)",
    "Overdue since {date}": "Overdue from {date}",
    "Accepted until {date}": "Accepted through {date}",
    "Generated at (UTC)": "Generated (UTC)",
    "Layout source: {{source}}": "Layout from: {{source}}",
    "Current state only": "Current state alone",
    "Framework filter": "Framework filter list",
    "Generated {{when}}": "Produced {{when}}",
    "{{count}} live measures": "{{count}} live measure(s)",
    "Blocked commands": "Commands blocked",
    "No KPI sources are available.": "No KPI sources are available at present.",
    "Denied and failed sessions": "Denied or failed sessions",
    "Unique attacker addresses": "Distinct attacker addresses",
    "Blocked PAM commands": "PAM commands blocked",
    "Mapped ATT&CK techniques": "Mapped ATT&CK technique list",
    "No family rows are available.": "No family rows are available at present.",
    "No named gap for this family.": "No named gap exists for this family.",
    "No remaining work rows.": "No remaining work rows at present.",
    "Loading permissions…": "Loading the permissions…",
    "Inventory rows: {{count}}": "Inventory row count: {{count}}",
    "Try default credentials": "Try the default credentials",
    "{{count}} target(s) reported": "{{count}} target(s) reported back",
    "Scan networks (CIDR)": "Scan networks by CIDR",
    "Interval (minutes)": "Interval in minutes",
    "Supported protocols": "Protocols supported",
    "OT discovery scan networks": "OT discovery — scan networks",
    "Shared network scan": "Shared network scan job",
    "Discovery job {{status}}": "Discovery job status: {{status}}",
    "Display name of the OT inventory target.": "Display name for the OT inventory target.",
    "Comment: {{text}}": "Note: {{text}}",
    "Dial endpoint {{ep}}": "Dial the endpoint {{ep}}",
    "Configure OT target {{name}}": "Configure the OT target {{name}}",
    "Select {{name}} for credentials": "Select {{name}} for the credentials",
    "Application menu": "Application menu bar",
    "Active provider (read-only):": "Active provider (read-only view):",
    "Configurator pages": "Configurator page list",
    "Operator actions": "Actions for operators",
    "Resolved configuration": "Configuration as resolved",
    "Selected variable": "Variable selected",
    "System time zone: -": "System time zone — none",
    "Connectivity probes": "Connectivity probe list",
    "Configurator sections": "Configurator section list",
    "Loaded {n} key(s).": "Loaded {n} key(s) successfully.",
    "Configuration keys": "Configuration key list",
    "Recording agent log path…": "Path to the recording agent log…",
    "Recording agent log tail (plain text)": "Recording agent log tail (plain text view)",
    "(log empty or missing)": "(log is empty or missing)",
    "Running elevated (administrator).": "Running elevated as administrator.",
    "Exported redacted settings to {path}": "Exported the redacted settings to {path}",
    "Export settings (v3 JSON)…": "Export the settings (v3 JSON)…",
    "Agent status": "Status of the agent",
    "Challenge / response": "Challenge and response",
    "&Challenge / response": "&Challenge and response",
    "Elevation granted": "Elevation was granted",
    "Elevation locked out": "Elevation is locked out",
    "Elevation skipped": "Elevation was skipped",
    "Unable to reach the agent": "The agent could not be reached",
    "Agent: connecting…": "Agent: establishing connection…",
    "Challenge issued": "Challenge has been issued",
    "Challenge request failed": "The challenge request failed",
    "(no grant loaded)": "(no grant is loaded)",
    "Simple token": "Simple token mode",
    "Signed workflow": "Signed workflow mode",
    "Activation &channel": "Activation &channel setting",
    "&Enable automatic update checks": "&Enable automatic checks for updates",
    "Please wait": "Please wait a moment",
    "Invalid input": "The input is invalid",
    "Nothing to copy": "There is nothing to copy",
    "Copy failed": "The copy failed",
    "Refresh status": "Refresh the status",
    "Reload settings": "Reload the settings",
    "Data root": "Data root folder",
    "Log directory": "Log folder",
    "Capture process": "Capture process status",
    "SCM service": "SCM service status",
    "SCM registered": "Registered with SCM",
    "SCM summary": "SCM status summary",
    "Windows service": "Windows service control",
    "Checking CLI…": "Checking the CLI…",
    "Interface font:": "Interface typeface:",
    "Monospace font:": "Monospace typeface:",
    "System default": "System default setting",
    "Reveal secrets": "Reveal the secrets",
    "Reveal &secrets": "Reveal the &secrets",
    "Defaults": "Default values",
    "Diagnostics": "Diagnostic tools",
    "Logging": "Logging options",
    "General": "General settings",
    "Language": "Language selection",
    "Database": "Database settings",
    "Channel": "Channel selection",
    "Health": "Health status",
    "Version": "Version information",
    "Build": "Build information",
    "Built": "Build stamp",
    "Advanced": "Advanced options",
    "Follow": "Follow log output",
    "Keys": "Key list",
    "Dashboard": "Dashboard view",
    "Dashboard theme": "Theme for the dashboard",
    "Title overlay": "Title overlay text",
    "Chart type": "Type of chart",
    "Select a tile": "Select a dashboard tile",
    "Work remaining": "Remaining work",
    "Protocol chips": "Protocol chip list",
    "OT asset list": "List of OT assets",
    "Reachability": "Reachability status",
    "No comment": "No comment recorded",
    "Environment": "Environment settings",
    "Schedules": "Schedule list",
    "Credentials": "Credential list",
    "Inventory": "Inventory list",
    "Run discovery": "Run the discovery",
    "Open session": "Open the session",
    "Break-glass": "Break-glass access",
    "Operations": "Operations view",
    "Administrators": "Administrator audience",
    "Executives": "Executive audience",
    "Auditors": "Auditor audience",
    "Mitigating": "Mitigation in progress",
    "Not accepted": "Not yet accepted",
    "Due {date}": "Due on {date}",
    "Expired {date}": "Expired on {date}",
    "(select a row in the list)": "(select a row from the list)",
    "&Export (masked)": "&Export (masked values)",
    "&GMT (UTC, 24-hour)": "&GMT (UTC, 24-hour clock)",
    "&Parse URL into fields": "&Parse the URL into fields",
    "&Verify messages": "&Verify the messages",
    "Add trust &key id:": "Add a trust &key id:",
    "Add trust &key": "Add a trust &key",
    "Clear stored PI&N": "Clear the stored PI&N",
    "Clear stored s&ecret": "Clear the stored s&ecret",
    "Load &default template": "Load the &default template",
    "Log timestamp time zone": "Time zone for log timestamps",
    "Overall scale (%):": "Overall scale (per cent):",
    "Re&build URL from fields": "Re&build the URL from fields",
    "Re&load settings": "Re&load the settings",
    "Rotate signing &key": "Rotate the signing &key",
    "U&ninstall service": "U&ninstall the service",
    "reload configuration": "reload the configuration",
    "Preview &sample": "Preview a &sample",
    "Service &logs": "Service &logs view",
    "Test &syslog": "Test &syslog delivery",
    "Unset.": "Value unset.",
    "Saved.": "Changes saved.",
    "Copied": "Copied to clipboard",
    "Details": "Detail view",
    "Welcome": "Welcome message",
    "Marking": "Classification marking",
    "Picture": "Picture panel",
    "Discover": "Discover assets",
    "Connect": "Connect session",
    "Configure": "Configure item",
    "Rotate": "Rotate secret",
    "Select": "Select item",
    "Refresh": "Refresh view",
    "About": "About this product",
    "Ready": "Ready state",
    "Status": "Status line",
    "Open": "Open item",
    "Export": "Export data",
    "Parameters": "Parameter list",
    "Logs": "Log view",
    "Service": "Service control",
    "Source": "Source value",
    "Type": "Type value",
    "Kind": "Kind value",
    "Name": "Name field",
    "Host": "Host name",
    "Port": "Port number",
    "Asset": "Asset row",
    "Comment": "Comment text",
    "Protocol": "Protocol name",
    "Actions": "Action list",
    "Item": "Item row",
    "State": "State value",
    "Key": "Key name",
    "Value": "Value field",
    "Get": "Get value",
    "Set": "Set value",
    "Unset": "Unset value",
    "Start": "Start service",
    "Stop": "Stop service",
    "Uninstall": "Uninstall service",
    "Exit": "Exit application",
    "File": "File menu",
    "View": "View menu",
    "Settings": "Settings menu",
    "Help": "Help menu",
    "Loading…": "Loading now…",
    "Checking…": "Checking now…",
    "Running…": "Running now…",
    "Default": "Default option",
    "Black": "Black theme",
    "Yes": "Yes",
    "No": "No",
    "Done": "Done",
    "Accept": "Accept risk",
    "Avoid": "Avoid risk",
    "Transfer": "Transfer risk",
    "Mitigate": "Mitigate risk",
    "Accepted": "Accepted state",
    "Closed": "Closed state",
    "Low": "Low severity",
    "Moderate": "Moderate severity",
    "High": "High severity",
    "Critical": "Critical severity",
    "Reachable": "Host reachable",
    "Unreachable": "Host unreachable",
    "Unknown": "Unknown state",
    "yes": "yes",
    "no": "no",
    "(empty)": "(empty value)",
    "Error:": "Error message:",
    "Version:": "Version label:",
    "Build:": "Build label:",
    "Protocol:": "Protocol label:",
    "Status:": "Status label:",
    "Service:": "Service label:",
    "User:": "User label:",
    "Password:": "Password label:",
    "Output:": "Output label:",
    "Step log:": "Step log label:",
    "Policy file:": "Policy file path:",
    "Host {{ep}}": "Host address {{ep}}",
    "7 days": "Seven days",
    "30 days": "Thirty days",
    "90 days": "Ninety days",
    "7 Days": "Seven Days",
    "30 Days": "Thirty Days",
    "90 Days": "Ninety Days",
    "&Help": "&Help menu",
    "&View": "&View menu",
    "&File": "&File menu",
    "&Settings": "&Settings page",
    "Cl&ose": "Cl&ose window",
    "E&xit": "E&xit application",
    "&Start": "&Start service",
    "St&art": "St&art service",
    "St&op": "St&op service",
    "Sto&p": "Sto&p service",
    "&Uninstall": "&Uninstall service",
    "&Refresh": "&Refresh view",
    "&Refresh status": "&Refresh the status",
    "&Running": "&Running state",
    "&Installed": "&Installed state",
    "&Health": "&Health check",
    "Sta&tus": "Sta&tus line",
    "Ser&vice": "Ser&vice control",
    "&Generate": "&Generate value",
    "Gener&ate": "Gener&ate value",
    "&Get": "&Get value",
    "&Set": "&Set value",
    "&Unset": "&Unset value",
    "&Reveal": "&Reveal value",
    "&Upload": "&Upload file",
    "&Regenerate": "&Regenerate value",
    "Re&vert": "Re&vert changes",
    "&Fonts": "&Fonts panel",
    "&Small (12 pt)": "&Small (12 pt size)",
    "&Medium (14 pt)": "&Medium (14 pt size)",
    "&Large (18 pt)": "&Large (18 pt size)",
    "&Simple token": "&Simple token mode",
    "&Submit": "&Submit request",
    "&Use result": "&Use this result",
    "Request &challenge": "Request a &challenge",
    "Re&quest challenge": "Re&quest a challenge",
    "Paste signed &grant": "Paste the signed &grant",
    "&Paste signed grant": "&Paste the signed grant",
    "Genera&te request package": "Genera&te the request package",
    "Signed &workflow": "Signed &workflow mode",
    "Activation &channel:": "Activation &channel label:",
    "&Activation code (8 letters):": "&Activation code (eight letters):",
    "Request pac&kage:": "Request pac&kage label:",
    "Cer&tificates": "Cer&tificates panel",
    "End&point:": "End&point address:",
    "Pass&word:": "Pass&word field:",
    "Client s&ecret:": "Client s&ecret field:",
    "Admin &token:": "Admin &token field:",
    "Admin &auth mode:": "Admin &auth mode setting:",
    "Agent &HMAC enforce:": "Agent &HMAC enforce setting:",
    "Connection &URL:": "Connection &URL field:",
    "Default optional &fields:": "Default optional &fields list:",
    "Default tenant &GUID:": "Default tenant &GUID field:",
    "Default tenant &name:": "Default tenant &name field:",
    "Client C&A path:": "Client C&A path field:",
    "Enable &TLS listener (port TLS_PORT)": "Enable the &TLS listener (port TLS_PORT)",
    "Enable remote &syslog collector": "Enable the remote &syslog collector",
    "Not &after (UTC):": "Not valid &after (UTC):",
    "Registered &connection:": "Registered &connection field:",
    "Release &channel:": "Release &channel field:",
    "Revoked &grant ids (CSV):": "Revoked &grant ids (CSV list):",
    "Revoked trust &key ids (CSV):": "Revoked trust &key ids (CSV list):",
    "TLS &port (leave blank to keep current):": "TLS &port (leave blank to keep the current value):",
    "Tenant &lifetime (days; 0 = unlimited):": "Tenant &lifetime (days; 0 means unlimited):",
    "Token &rotation (days; 0 = no policy):": "Token &rotation (days; 0 means no policy):",
    "Update server &URL:": "Update server &URL field:",
    "&Collector host:": "&Collector host name:",
    "&Custom user (DOMAIN\\\\user + password):": "&Custom user (DOMAIN\\\\user plus password):",
    "&Enable TLS (HTTPS)": "&Enable TLS over HTTPS",
    "&Proxy port (mitmweb listen):": "&Proxy port (mitmweb listen address):",
    "&Role (root|leaf):": "&Role (root or leaf):",
    "APP-&NAME (ident):": "APP-&NAME identifier:",
    "Add trust &key id:": "Add a trust &key identifier:",
    "&Audit log": "&Audit log view",
    "&Client ID:": "&Client ID field:",
    "&Database:": "&Database name:",
    "&Engine:": "&Engine type:",
    "&Event provider": "&Event provider setting",
    "&Facility:": "&Facility code:",
    "&HTTP API": "&HTTP API surface",
    "&Host:": "&Host name:",
    "&Key:": "&Key field:",
    "&MITM": "&MITM settings",
    "&No proxy:": "&No-proxy list:",
    "&Port:": "&Port number:",
    "&PostgreSQL": "&PostgreSQL engine",
    "&Protocol:": "&Protocol name:",
    "&Public URL:": "&Public URL field:",
    "&SPKI (base64):": "&SPKI value (base64):",
    "&SSL mode:": "&SSL mode setting:",
    "&Scale:": "&Scale value:",
    "&Scheme:": "&Scheme name:",
    "&Slot ID:": "&Slot ID field:",
    "&TLS port:": "&TLS port number:",
    "&Tenant ID:": "&Tenant ID field:",
    "&Tracing log": "&Tracing log view",
    "&User:": "&User name:",
    "&Value:": "&Value field:",
    "&Web UI port:": "&Web UI port number:",
    "HTTP &port:": "HTTP &port number:",
    "HTTP &webhook": "HTTP &webhook sink",
    "Log &level:": "Log &level setting:",
    "Module &path:": "Module &path field:",
    "Provider &kind:": "Provider &kind setting:",
    "Proxy &URL:": "Proxy &URL field:",
    "SIEM &format:": "SIEM &format setting:",
    "Sample &rate:": "Sample &rate value:",
    "Service &name:": "Service &name field:",
    "Signed &by:": "Signed &by field:",
    "Syslog &forward": "Syslog &forward setting",
    "TCP &framing:": "TCP &framing setting:",
    "TLS &cert path:": "TLS &cert path field:",
    "TLS &key path:": "TLS &key path field:",
    "Text size (px):": "Text size in pixels:",
    "Token P&IN:": "Token P&IN field:",
    "Vault &URI:": "Vault &URI field:",
    "&Local group:": "&Local group name:",
    "NATO &phonetic:": "NATO &phonetic spelling:",
}


def flat_entries(n, p=""):
    o = {}
    if isinstance(n, dict):
        if "text" in n and isinstance(n.get("text"), str):
            o[p] = n
            return o
        for k, v in n.items():
            o.update(flat_entries(v, f"{p}.{k}" if p else k))
    elif isinstance(n, list):
        for i, item in enumerate(n):
            o.update(flat_entries(item, f"{p}[{i}]"))
    return o


AREA = {
    "locales": ROOT / "content" / "locales",
    "locales-ui": ROOT / "content" / "locales-ui",
    "gui": ROOT / "content" / "i18n-native" / "gui",
    "agent": ROOT / "content" / "i18n-native" / "apps" / "pim-offline-agent",
    "recording": ROOT
    / "content"
    / "i18n-native"
    / "apps"
    / "pim-offline-recording-agent",
    "jump": ROOT / "content" / "i18n-native" / "apps" / "pim-jump-server",
    "dbmgmt": ROOT / "content" / "i18n-native" / "apps" / "pim-db-mgmt-agent",
}


def should_keep(text: str) -> bool:
    if text in KEEP_EXACT:
        return True
    if any(text.startswith(p) for p in KEEP_PREFIX):
        return True
    if any(s in text for s in KEEP_SUBSTR):
        return True
    if text in VARIETY_NEUTRAL_OK:
        return True
    return False


def normalize_ellipsis(text: str) -> str:
    # Repair mojibake / replacement-char stand-ins for U+2026
    out = text.replace("\ufffd", "…")
    if out.endswith("�") or "�" in out:
        out = out.replace("�", "…")
    # Also: lone replacement after ASCII when en used …
    if out.endswith("...") is False and out.endswith("…") is False:
        if "path" in out.lower() and out.endswith("\ufffd"):
            out = out[:-1] + "…"
    return out


def rewrite(text: str) -> str | None:
    if should_keep(text):
        return None
    raw = normalize_ellipsis(text)
    # Special: recording placeholder may still carry a bad trailing byte
    if "Recording agent log path" in text:
        return "Path to the recording agent log…"
    if raw in PHRASE:
        neu = normalize_ellipsis(PHRASE[raw])
        if neu != text:
            return neu
    if text in PHRASE:
        neu = normalize_ellipsis(PHRASE[text])
        if neu != text:
            return neu
    lex = uk_lex(raw)
    if lex != text:
        return lex
    if " & " in raw and not raw.lstrip().startswith("&"):
        cand = raw.replace(" & ", " and ")
        if cand != text:
            return cand
    return None


def collect_identical():
    ident = []
    for area, base in AREA.items():
        en_dir, gb_dir = base / "en", base / "en-GB"
        if not en_dir.is_dir() or not gb_dir.is_dir():
            continue
        for p in sorted(en_dir.glob("*.json")):
            gb = gb_dir / p.name
            if not gb.exists():
                continue
            ef = flat_entries(json.loads(p.read_text(encoding="utf-8")))
            gf = flat_entries(json.loads(gb.read_text(encoding="utf-8")))
            for k, e in ef.items():
                g = gf.get(k)
                if g and g.get("text") == e.get("text"):
                    ident.append(
                        {
                            "area": area,
                            "file": p.name,
                            "key": k,
                            "text": e["text"],
                            "len": len(e["text"]),
                        }
                    )
    return ident


def main():
    for pass_i in range(2):
        ident = collect_identical()
        print(f"pass{pass_i}_before", len(ident))
        by_file = {}
        for row in ident:
            neu = rewrite(row["text"])
            if not neu or neu == row["text"]:
                continue
            by_file.setdefault((row["area"], row["file"]), []).append(
                (row["key"], neu)
            )
        changed = 0
        for (area, filename), items in by_file.items():
            path = AREA[area] / "en-GB" / filename
            data = json.loads(path.read_text(encoding="utf-8"))
            leaves = flat_entries(data)
            for key, new_text in items:
                leaf = leaves.get(key)
                if leaf is None:
                    print(f"WARN missing key {area}/{filename} {key}")
                    continue
                leaf["text"] = new_text
                changed += 1
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"updated {area}/{filename}: {len(items)}")
        print(f"pass{pass_i}_changed", changed)
        if changed == 0:
            break

    after = collect_identical()
    print("after_identical", len(after))
    print("after_long", sum(1 for x in after if x["len"] > 40))
    print("after_med", sum(1 for x in after if 15 < x["len"] <= 40))
    print("after_short", sum(1 for x in after if x["len"] <= 15))
    Path("scripts/language-packs/_en_gb_identical.json").write_text(
        json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    remain = [
        x
        for x in after
        if x["text"] not in KEEP_EXACT
        and not x["text"].startswith("Copyright ")
        and "{organization_name}" not in x["text"]
    ]
    print("non_keep_remaining", len(remain))
    print("--- remaining med+ ---")
    for t, n in Counter(x["text"] for x in remain if x["len"] > 15).most_common():
        print(n, repr(t))
    print("--- remaining short ---")
    for t, n in Counter(x["text"] for x in remain if x["len"] <= 15).most_common():
        print(n, repr(t))


if __name__ == "__main__":
    main()
