#!/usr/bin/env python3
"""Slice 1: restore clean US English for contaminated en keys.

Recovery: translate German/splice → idiomatic US English (git/defaultValue
unavailable for these keys). Also mirrors same fixes into en-GB as US baseline
before UK phrasing pass. Does not touch other tags.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UI = ROOT / "content" / "locales-ui"

# file -> key -> US English
US_FIXES: dict[str, dict[str, str]] = {
    "binder.json": {
        "newInstance": "New instance",
    },
    "nav.json": {
        "auditor_handb_cher": "Auditor manuals",
        "benutzerhandb_cher": "User manuals",
        "admin_handb_cher": "Admin manuals",
    },
    "docs.json": {
        "user.chapters.getting-started.steps[3]": (
            "Leave the browser tab open while the session starts. "
            "Close it only after you disconnect."
        ),
        "user.chapters.my-workstations.summary": (
            "Power state, reconnecting, and what to do when a host is asleep."
        ),
        "user.chapters.my-workstations.body[0]": (
            "Power-on and wake controls apply only to machines assigned to you. "
            "Sleeping or offline states are normal when a host is powered off. "
            "Wait for wake to finish, or ask an administrator, before retrying repeatedly."
        ),
        "user.chapters.my-workstations.steps[1]": (
            "If status shows sleeping or offline, wait briefly and ask an "
            "administrator if the state does not change."
        ),
        "user.chapters.my-workstations.steps[2]": (
            "End the session in the broker when you are finished."
        ),
        "user.chapters.secure-share.steps[2]": (
            "Download only when the package allows it."
        ),
        "auditor.chapters.assessment-binder.steps[2]": (
            "Fill control narratives with honest status "
            "(Implemented / Partial / Planned)."
        ),
        "auditor.chapters.report-center.steps[0]": (
            "Filter the catalog by the report family you need."
        ),
        "auditor.chapters.report-center.steps[1]": (
            "Run the report and download the package your organization allows."
        ),
        "auditor.chapters.report-center.steps[3]": (
            "Escalate missing operator actions instead of fixing them yourself."
        ),
        "auditor.chapters.current-state.steps[1]": (
            "Filter to the population under review."
        ),
        "auditor.chapters.current-state.steps[2]": (
            "Treat Rescan / Fix-It as operator actions."
        ),
        "auditor.chapters.enhanced-controls.steps[1]": (
            "Read the honesty notice before you cite a row. It states the product boundary."
        ),
        "auditor.chapters.enhanced-controls.steps[2]": (
            "Treat Blocked rows as work for your organization, not as product defects."
        ),
        "admin.chapters.server-config.steps[2]": (
            "Set the organization profile before you export agent settings."
        ),
        "admin.chapters.server-config.steps[3]": (
            "Confirm that COMPLIANCE_PROFILE and ADMIN_AUTH_MODE match the deployment intent."
        ),
        "admin.chapters.server-config.steps[4]": (
            "After service-relevant changes, confirm aic-offline-server-service is RUNNING "
            "and runtime-status.json is current."
        ),
        "admin.chapters.agents.body[0]": (
            "Export or transfer agent settings only after organization disclosures are complete. "
            "After install, check agent check-in and health under Systems → System list."
        ),
        "admin.chapters.agents.steps[0]": (
            "Export or transfer settings from Configuration → Agent after organization "
            "disclosures are complete."
        ),
        "admin.chapters.agents.steps[1]": (
            "After install, check agent check-in and health on the system list."
        ),
        "admin.chapters.agents.steps[4]": (
            "Confirm the elevation pipe and elevation_configured before you mint elevation codes."
        ),
        "admin.chapters.proxied-access.steps[2]": (
            "Confirm recording-agent health and recording storage before you require recorded sessions."
        ),
        "admin.chapters.proxied-access.steps[3]": (
            "Bind SSH command filtering when you need command governance. "
            "In a live session, exercise one allow and one deny."
        ),
        "admin.chapters.evidence-audit.steps[4]": (
            "Configure syslog forwarding only when you have a collector. "
            "Verify delivery separately from loading the page."
        ),
        "admin.chapters.enhanced-controls.steps[1]": (
            "Set the delivery window before you record a CIRT exercise."
        ),
        "admin.chapters.enhanced-controls.steps[2]": (
            "Run hunt detectors, then record the CIRT exercise, then practice "
            "notification / SIEM stamping."
        ),
        "admin.chapters.backup-ops.steps[0]": (
            "After deployment, confirm HTTPS health and the admin session."
        ),
        "admin.chapters.backup-ops.steps[4]": (
            "Never run a destructive database initialization without the restore step."
        ),
        "openapi.listCapped": (
            "List capped at 500 rows for this page. Narrow the filter or download JSON "
            "for the full document."
        ),
    },
    "pages.json": {
        "chrome.jumpFleet.healthHealthy": "healthy",
        "chrome.jumpFleet.healthUnhealthy": "unhealthy",
        "chrome.localEnrollment.emailInvalid": "Enter a valid email address.",
        "chrome.localEnrollment.phoneInvalid": (
            "Enter a valid phone number in E.164 format (example: +15551234567)."
        ),
        "chrome.pamEntitlements.deny": "Deny",
        "chrome.sessionIoPolicy.clipboard_none": "Denied",
        "chrome.sessionIoPolicy.fileTransfer_deny": "Denied",
        "chrome.training.detailClaimNotBuilt": (
            "Access lockout, grading, and rule-based enrollment are not built."
        ),
        "headers.compliance__gdpr__ropa.bullets.text[2]": (
            "Distinguish controller entries (Art. 30(1)) from processor entries (Art. 30(2))."
        ),
        "headers.enclave__data-flows.bullets.text[2]": (
            "Derived controls and risk levels are computed by the server and shown read-only."
        ),
        "headers.enclave__wa-probe-packs.bullets.text[2]": (
            "Activate a later version when you are ready; silent push without agent pull is Planned."
        ),
        "headers.events__sharing.bullets.text[0]": (
            "Built-in sinks show platform sink status; Syslog settings opens collector transport."
        ),
        "headers.my-workstations.bullets.text[0]": (
            "Connect authorizes a recorded session (you confirm recording) and then opens "
            "the desktop viewer."
        ),
        "headers.my-workstations.bullets.text[3]": (
            "Recording proxy required — Connect stays blocked until the enclave can place a recording."
        ),
        "headers.pam__approvals.bullets.text[0]": (
            "Separation of duties prevents you from approving your own requests."
        ),
        "headers.pam__approver-profile.bullets.text[0]": (
            "Keep email and phone current so approval notifications reach you."
        ),
        "headers.pam__connection-points.bullets.text[2]": (
            "Every opened session is recorded by default (proxy or target-local)."
        ),
        "headers.pam__live__ot.bullets.text[0]": (
            "Recording runs until the session ends."
        ),
        "headers.pam__live__rdp.bullets.text[0]": (
            "Recording runs until the session ends."
        ),
        "headers.pam__live__ssh.bullets.text[0]": (
            "Recording runs until the session ends."
        ),
        "headers.pam__live__vnc.bullets.text[0]": (
            "Recording runs until the session ends."
        ),
        "headers.pam__my-requests.bullets.text[1]": (
            "Separation of duties prevents you from approving your own requests."
        ),
        "headers.pam__ot-connect.bullets.text[2]": (
            "With bound vault credentials, Connect can use them for the session."
        ),
        "headers.pam__ot-inventory.bullets.text[0]": (
            "Connect opens an OT protocol session — not SSH, RDP, or VNC."
        ),
        "headers.pam__sessions.bullets.text[1]": (
            "Decision chips show Allowed or Denied at recording time — not a compliance verdict."
        ),
        "headers.remote-access.bullets.text[0]": (
            "Connect opens a recorded proxy session when a PAM connection point matches the host."
        ),
        "headers.systems__list.bullets.text[0]": (
            "Agent rows add password rotation, elevation, and target-local recording."
        ),
    },
}

# UK overrides applied after US fix (genuine en-GB phrasing where it differs)
UK_OVERRIDES: dict[str, dict[str, str]] = {
    "binder.json": {
        "newInstance": "New instance",
    },
    "nav.json": {
        "auditor_handb_cher": "Auditor manuals",
        "benutzerhandb_cher": "User manuals",
        "admin_handb_cher": "Admin manuals",
    },
    "docs.json": {
        "user.chapters.getting-started.steps[3]": (
            "Leave the browser tab open while the session starts. "
            "Close it only after you disconnect."
        ),
        "auditor.chapters.assessment-binder.steps[2]": (
            "Fill control narratives with honest status "
            "(Implemented / Partial / Planned)."
        ),
        "auditor.chapters.report-center.steps[0]": (
            "Filter the catalogue by the report family you need."
        ),
        "auditor.chapters.enhanced-controls.steps[1]": (
            "Read the honesty notice before you cite a row. It states the product boundary."
        ),
        "admin.chapters.agents.body[0]": (
            "Export or transfer agent settings only after organisation disclosures are complete. "
            "After install, check agent check-in and health under Systems → System list."
        ),
        "admin.chapters.agents.steps[0]": (
            "Export or transfer settings from Configuration → Agent after organisation "
            "disclosures are complete."
        ),
        "admin.chapters.proxied-access.steps[3]": (
            "Bind SSH command filtering when you need command governance. "
            "In a live session, exercise one allow and one deny."
        ),
        "admin.chapters.enhanced-controls.steps[1]": (
            "Set the delivery window before you record a CIRT exercise."
        ),
        "openapi.listCapped": (
            "List capped at 500 rows for this page. Narrow the filter or download JSON "
            "for the full document."
        ),
    },
    "pages.json": {
        "chrome.localEnrollment.emailInvalid": "Enter a valid email address.",
        "chrome.training.detailClaimNotBuilt": (
            "Access lockout, grading, and rule-based enrolment are not built."
        ),
        "headers.enclave__data-flows.bullets.text[2]": (
            "Derived controls and risk levels are computed by the server and shown read-only."
        ),
        "headers.my-workstations.bullets.text[0]": (
            "Connect authorises a recorded session (you confirm recording) and then opens "
            "the desktop viewer."
        ),
        "headers.pam__approvals.bullets.text[0]": (
            "Separation of duties prevents you from approving your own requests."
        ),
        "headers.pam__my-requests.bullets.text[1]": (
            "Separation of duties prevents you from approving your own requests."
        ),
        "headers.pam__sessions.bullets.text[1]": (
            "Decision chips show Allowed or Denied at recording time — not a compliance verdict."
        ),
    },
    "components.json": {
        # Pure German sectionLanding strings observed on en-GB — US→UK chrome
        "sectionLanding.desc.approvals": (
            "Approve or deny access requests assigned to you."
        ),
        "sectionLanding.desc.connection_points": (
            "Define SSH and RDP targets, start brokered sessions, and manage credentials."
        ),
        "sectionLanding.desc.inventory": (
            "OT targets, status, and Connect or Configure per row."
        ),
        "sectionLanding.desc.recording_agents_health": (
            "Registered agents with check-in status and proxy or local recording mode."
        ),
        "sectionLanding.desc.session_control": (
            "Monitor and end active privileged sessions."
        ),
        "sectionLanding.desc.session_recordings": (
            "Browse and play back recorded brokered sessions."
        ),
        "sectionLanding.desc.sessions_evidence": (
            "Review open OT sessions and session evidence."
        ),
        "sectionLanding.group.recording_ops": "Recording operations",
        "sectionLanding.group.sessions": "Sessions",
    },
}


def set_by_path(obj, path: str, value: str) -> bool:
    """Set leaf text at dotted/bracket path. Returns True if found."""
    # Parse path into segments
    parts: list = []
    buf = ""
    i = 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if buf:
                parts.append(buf)
                buf = ""
            i += 1
        elif ch == "[":
            if buf:
                parts.append(buf)
                buf = ""
            j = path.index("]", i)
            parts.append(int(path[i + 1 : j]))
            i = j + 1
        else:
            buf += ch
            i += 1
    if buf:
        parts.append(buf)

    cur = obj
    for p in parts[:-1]:
        cur = cur[p]
    last = parts[-1]
    leaf = cur[last]
    if isinstance(leaf, dict) and "text" in leaf:
        leaf["text"] = value
        # Drop stale source_sha256 if present — sibling format may restamp
        if "source_sha256" in leaf:
            leaf["source_sha256"] = ""
        return True
    if isinstance(leaf, str):
        cur[last] = value
        return True
    return False


def apply_map(tag: str, fixes: dict[str, dict[str, str]]) -> dict:
    stats = {"files": {}, "applied": 0, "missing_keys": []}
    for fname, keymap in fixes.items():
        path = UI / tag / fname
        if not path.exists():
            stats["missing_keys"].append(f"{tag}/{fname} (file)")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        n = 0
        for key, text in keymap.items():
            text = unicodedata.normalize("NFC", text)
            if set_by_path(data, key, text):
                n += 1
                stats["applied"] += 1
            else:
                stats["missing_keys"].append(f"{tag}/{fname}:{key}")
        raw = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        # Prefer LF
        path.write_text(raw.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
        stats["files"][fname] = n
    return stats


def main() -> None:
    en_stats = apply_map("en", US_FIXES)
    # en-GB: start from US fixes then UK overrides
    engb_base: dict[str, dict[str, str]] = {}
    for fname, keymap in US_FIXES.items():
        engb_base[fname] = dict(keymap)
    for fname, keymap in UK_OVERRIDES.items():
        engb_base.setdefault(fname, {}).update(keymap)
    # Also fix en-GB-only German sectionLanding if not in US_FIXES
    for fname, keymap in UK_OVERRIDES.items():
        engb_base.setdefault(fname, {}).update(keymap)
    gb_stats = apply_map("en-GB", engb_base)

    report = {
        "en": en_stats,
        "en-GB": gb_stats,
        "recovery_source": "translated_from_german_idiomatic_us_en",
        "note": (
            "Git history and defaultValue did not yield clean priors for these "
            "keys; values authored as idiomatic US/UK English from DE intent."
        ),
    }
    out = (
        ROOT
        / "content"
        / "localization-work"
        / "retranslation-20260819"
        / "slice1-apply-report.json"
    )
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
