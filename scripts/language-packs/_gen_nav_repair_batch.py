#!/usr/bin/env python3
"""Generate the fr/es nav wrong-language repair batch.

The French and Spanish `nav` packs carry German text for 109 keys -- the whole
sidebar and every section-landing tile rendered in German for those locales. The
English source text is read straight out of `en/nav.json` so the `source_sha256`
the applier stamps is the hash of the real source, not of a hand-retyped copy.

`admin_handb_cher` is slug("Admin-Handbuecher"): a generator slugified the German
label instead of the English one, so a bogus key was propagated into 17 packs.
Nothing reads it (`QuickActionCardTile` slugifies the English label constant from
`sectionLandings.tsx`), so it is deleted everywhere rather than translated.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
OUT = ROOT / "content" / "language-packs" / "batches" / "nav-de-leak-repair-20260825.json"

FR = {
    "access_control": "Contrôle d'accès",
    "active_grants": "Autorisations actives",
    "admin_manuals": "Manuels d'administration",
    "agent_management": "Gestion des agents",
    "agent_overview": "Vue d'ensemble des agents",
    "alert_groups": "Groupes d'alertes",
    "approvals": "Approbations",
    "assessment_binder": "Classeur d'évaluation",
    "attestation_ledger": "Registre des attestations",
    "audit_engagements": "Missions d'audit",
    "audit_frameworks": "Référentiels d'audit",
    "audit_log": "Journal d'audit",
    "audit_trail": "Piste d'audit",
    "auditor_text_playbooks": "Guides textuels de l'auditeur",
    "branding_style": "Image de marque et style",
    "bulk_provision": "Provisionnement en masse",
    "company_profile": "Profil de l'entreprise",
    "control_coverage": "Couverture des mesures",
    "current_state_compliance": "Conformité — état actuel",
    "data_flow_mapping": "Cartographie des flux de données",
    "demo_reset": "Réinitialiser la démonstration",
    "deploy_recording_agent": "Déployer l'agent d'enregistrement",
    "direct_elevation": "Élévation directe",
    "directory": "Annuaire",
    "discover": "Découverte",
    "discovery_jobs": "Tâches de découverte",
    "document_lifecycle": "Cycle de vie des documents",
    "documentation": "Documentation",
    "documentation_home": "Accueil de la documentation",
    "elevation_platform": "Plateforme d'élévation",
    "email_settings": "Paramètres de messagerie",
    "encryption_key_sets": "Jeux de clés de chiffrement",
    "encryption_settings": "Paramètres de chiffrement",
    "enrollment_and_access_control": "Enrôlement et contrôle d'accès",
    "entitlements": "Habilitations",
    "event_sharing": "Partage d'événements",
    "external_workstation_readiness": "Préparation des postes de travail externes",
    "favorites": "Favoris",
    "fleet_agent_versions": "Versions des agents du parc",
    "gdpr_impact_assessment": "RGPD — analyse d'impact",
    "gdpr_processing_register": "RGPD — registre des traitements",
    "gdpr_subject_rights": "RGPD — droits des personnes concernées",
    "hsm_connections": "Connexions HSM",
    "identity_template": "Modèle d'identité",
    "import_settings_migration": "Importer les paramètres (migration)",
    "initial_setup_wizard": "Assistant de configuration initiale",
    "inventory": "Inventaire",
    "ip_scanner": "Scanner IP",
    "ir_alert_groups": "Groupes d'alertes de réponse à incident",
    "jump_capacity": "Rebond et capacité",
    "jump_fleet_load_balancing": "Parc de rebond et répartition de charge",
    "known_default_credentials": "Identifiants par défaut connus",
    "lab_tools": "Outils de laboratoire",
    "license_and_billing": "Licence et facturation",
    "live_events": "Événements en direct",
    "local_iam_administration": "Administration IAM locale",
    "manage_issuances": "Gérer les émissions",
    "managed_identities": "Identités gérées",
    "message_snippets": "Fragments de message",
    "message_templates": "Modèles de message",
    "messaging": "Messagerie",
    "multi_tenancy": "Multi-locataire",
    "my_incident_reports": "Mes déclarations d'incident",
    "my_workspace": "Mon espace de travail",
    "my_workstations": "Mes postes de travail",
    "network_scan": "Analyse réseau",
    "operational_technology": "Technologies opérationnelles (OT)",
    "ot_inventory": "Inventaire OT",
    "platform_overview": "Vue d'ensemble de la plateforme",
    "policy": "Politique",
    "policy_approvals": "Approbations de politique",
    "privileged_identities": "Identités à privilèges",
    "privileged_user_management": "Gestion des utilisateurs à privilèges",
    "probe_packs": "Lots de sondes",
    "propagation_templates": "Modèles de propagation",
    "rdp_ocr_metadata": "OCR / métadonnées RDP",
    "recording_agents_health": "Agents d'enregistrement — état",
    "recording_ops": "Exploitation des enregistrements",
    "recording_storage": "Stockage des enregistrements",
    "reports": "Rapports",
    "reports_dashboards": "Rapports et tableaux de bord",
    "risk_register": "Registre des risques",
    "rotation_jobs": "Tâches de rotation",
    "secure_share": "Partage sécurisé",
    "security": "Sécurité",
    "service_logs": "Journaux de service",
    "session_control": "Contrôle des sessions",
    "session_i_o_policy": "Politique d'E/S de session",
    "session_recordings": "Enregistrements de session",
    "session_timeout_and_logoff": "Expiration de session et déconnexion",
    "settings": "Paramètres",
    "settings_wizard": "Assistant de paramétrage",
    "sms_settings": "Paramètres SMS",
    "ssh_command_filtering": "Filtrage des commandes SSH",
    "startup_wizard": "Assistant de démarrage",
    "syslog_forwarding": "Transfert syslog",
    "system_groups": "Groupes de systèmes",
    "systems": "Systèmes",
    "systems_list": "Liste des systèmes",
    "token_elevation": "Élévation par jeton",
    "training": "Formation",
    "training_and_awareness_packs": "Lots de formation et de sensibilisation",
    "training_awareness_packs": "Lots de formation et de sensibilisation",
    "training_programs": "Programmes de formation",
    "version_information": "Informations de version",
    "vm_management": "Gestion des machines virtuelles",
    "wa_probe_packs": "Lots de sondes WA",
    "workforce_roster": "Liste du personnel",
}

ES = {
    "access_control": "Control de acceso",
    "active_grants": "Concesiones activas",
    "admin_manuals": "Manuales de administración",
    "agent_management": "Gestión de agentes",
    "agent_overview": "Resumen de agentes",
    "alert_groups": "Grupos de alertas",
    "approvals": "Aprobaciones",
    "assessment_binder": "Carpeta de evaluación",
    "attestation_ledger": "Registro de atestaciones",
    "audit_engagements": "Trabajos de auditoría",
    "audit_frameworks": "Marcos de auditoría",
    "audit_log": "Registro de auditoría",
    "audit_trail": "Pista de auditoría",
    "auditor_text_playbooks": "Guías de texto del auditor",
    "branding_style": "Marca y estilo",
    "bulk_provision": "Aprovisionamiento masivo",
    "company_profile": "Perfil de la empresa",
    "control_coverage": "Cobertura de controles",
    "current_state_compliance": "Cumplimiento — estado actual",
    "data_flow_mapping": "Mapeo de flujos de datos",
    "demo_reset": "Restablecer la demostración",
    "deploy_recording_agent": "Implementar el agente de grabación",
    "direct_elevation": "Elevación directa",
    "directory": "Directorio",
    "discover": "Descubrimiento",
    "discovery_jobs": "Trabajos de descubrimiento",
    "document_lifecycle": "Ciclo de vida del documento",
    "documentation": "Documentación",
    "documentation_home": "Inicio de la documentación",
    "elevation_platform": "Plataforma de elevación",
    "email_settings": "Configuración de correo electrónico",
    "encryption_key_sets": "Conjuntos de claves de cifrado",
    "encryption_settings": "Configuración de cifrado",
    "enrollment_and_access_control": "Inscripción y control de acceso",
    "entitlements": "Derechos de acceso",
    "event_sharing": "Uso compartido de eventos",
    "external_workstation_readiness": "Preparación de estaciones de trabajo externas",
    "favorites": "Favoritos",
    "fleet_agent_versions": "Versiones de agentes de la flota",
    "gdpr_impact_assessment": "RGPD — evaluación de impacto",
    "gdpr_processing_register": "RGPD — registro de actividades de tratamiento",
    "gdpr_subject_rights": "RGPD — derechos de los interesados",
    "hsm_connections": "Conexiones HSM",
    "identity_template": "Plantilla de identidad",
    "import_settings_migration": "Importar configuración (migración)",
    "initial_setup_wizard": "Asistente de configuración inicial",
    "inventory": "Inventario",
    "ip_scanner": "Escáner de IP",
    "ir_alert_groups": "Grupos de alertas de respuesta a incidentes",
    "jump_capacity": "Salto y capacidad",
    "jump_fleet_load_balancing": "Flota de salto y balanceo de carga",
    "known_default_credentials": "Credenciales predeterminadas conocidas",
    "lab_tools": "Herramientas de laboratorio",
    "license_and_billing": "Licencia y facturación",
    "live_events": "Eventos en vivo",
    "local_iam_administration": "Administración de IAM local",
    "manage_issuances": "Gestionar emisiones",
    "managed_identities": "Identidades gestionadas",
    "message_snippets": "Fragmentos de mensaje",
    "message_templates": "Plantillas de mensaje",
    "messaging": "Mensajería",
    "multi_tenancy": "Multiinquilino",
    "my_incident_reports": "Mis informes de incidentes",
    "my_workspace": "Mi espacio de trabajo",
    "my_workstations": "Mis estaciones de trabajo",
    "network_scan": "Análisis de red",
    "operational_technology": "Tecnología operativa (OT)",
    "ot_inventory": "Inventario de OT",
    "platform_overview": "Resumen de la plataforma",
    "policy": "Política",
    "policy_approvals": "Aprobaciones de políticas",
    "privileged_identities": "Identidades privilegiadas",
    "privileged_user_management": "Gestión de usuarios privilegiados",
    "probe_packs": "Paquetes de sondas",
    "propagation_templates": "Plantillas de propagación",
    "rdp_ocr_metadata": "OCR / metadatos de RDP",
    "recording_agents_health": "Agentes de grabación — estado",
    "recording_ops": "Operaciones de grabación",
    "recording_storage": "Almacenamiento de grabaciones",
    "reports": "Informes",
    "reports_dashboards": "Informes y paneles",
    "risk_register": "Registro de riesgos",
    "rotation_jobs": "Trabajos de rotación",
    "secure_share": "Uso compartido seguro",
    "security": "Seguridad",
    "service_logs": "Registros del servicio",
    "session_control": "Control de sesiones",
    "session_i_o_policy": "Política de E/S de sesión",
    "session_recordings": "Grabaciones de sesión",
    "session_timeout_and_logoff": "Tiempo de espera de sesión y cierre",
    "settings": "Configuración",
    "settings_wizard": "Asistente de configuración",
    "sms_settings": "Configuración de SMS",
    "ssh_command_filtering": "Filtrado de comandos SSH",
    "startup_wizard": "Asistente de inicio",
    "syslog_forwarding": "Reenvío de syslog",
    "system_groups": "Grupos de sistemas",
    "systems": "Sistemas",
    "systems_list": "Lista de sistemas",
    "token_elevation": "Elevación por token",
    "training": "Formación",
    "training_and_awareness_packs": "Paquetes de formación y concienciación",
    "training_awareness_packs": "Paquetes de formación y concienciación",
    "training_programs": "Programas de formación",
    "version_information": "Información de versión",
    "vm_management": "Gestión de máquinas virtuales",
    "wa_probe_packs": "Paquetes de sondas de WA",
    "workforce_roster": "Lista del personal",
}

JUNK_KEY = "admin_handb_cher"


def main() -> int:
    en = json.loads((UI / "en" / "nav.json").read_text(encoding="utf-8"))

    keys = sorted(set(FR) | set(ES))
    missing = [k for k in keys if k not in en or "text" not in en[k]]
    if missing:
        print(f"error: no English source for {missing}")
        return 2
    if set(FR) != set(ES):
        print(f"error: fr/es key sets differ: {set(FR) ^ set(ES)}")
        return 2

    delete_keys = {
        tag.name: [JUNK_KEY]
        for tag in sorted(UI.iterdir())
        if tag.is_dir()
        and (tag / "nav.json").is_file()
        and JUNK_KEY in json.loads((tag / "nav.json").read_text(encoding="utf-8"))
    }

    batch = {
        "_comment": (
            "The fr and es nav packs carried German text for all 109 keys, so the "
            "sidebar and every section-landing tile rendered in German for those "
            "locales. English source is copied from en/nav.json so the stamped "
            "source_sha256 hashes the real source. admin_handb_cher is "
            "slug(\"Admin-Handbuecher\") -- a generator slugified the German label "
            "instead of the English one; nothing reads it, so it is deleted from "
            "every pack that carries it. Translations are agent drafts pending "
            "native review (localization-work-queue.mdc): German text shown to a "
            "French or Spanish operator is a shipped defect, a reviewed-pending "
            "French or Spanish string is not."
        ),
        "area": "locales-ui",
        "namespace": "nav",
        "source": {k: en[k]["text"] for k in keys},
        "translations": {"fr": FR, "es": ES},
        "delete_keys": delete_keys,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT.name}: {len(keys)} keys, delete from {len(delete_keys)} packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
