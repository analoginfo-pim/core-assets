#!/usr/bin/env python3
"""Generate fr/es batches that replace German-text leaks outside `nav`.

A broken machine-translation pass pivoted through German and left German
operator chrome in the French and Spanish UI packs for keys across catalog,
common, compliance, components, dashboard, docs, pages, and risks. A French
or Spanish operator currently reads German on those screens. That is a shipped
defect; a reviewed-pending French or Spanish string is not
(localization-work-queue.mdc).

English `source` is read from `content/locales-ui/en/<namespace>.json` so the
applier stamps `source_sha256` of the real English leaf, not of the TSV copy.
Translations are authored from that English text — never from the German column
that caused the bug.

Two ES-only TSV rows address array-indexed leaves
(`headers.pam__approvals.bullets.text.0` and
`headers.pam__my-requests.bullets.text.1`). The batch applier walks object trees
only and cannot replace a list element; those keys are omitted here and must be
repaired by a follow-up that understands array leaves.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
OUT_DIR = ROOT / "content" / "language-packs" / "batches"
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

# namespace -> key -> French. Keys match the dotted paths the SPA resolves.
FR: dict[str, dict[str, str]] = {
    "catalog": {
        "activeStandard": "Norme active",
        "rowCount": "{{count}} lignes",
    },
    "common": {
        "appBar.approvalsAria": "Approbations en attente",
        "appBar.approvalsTooltip": "Approbations PAM en attente",
        "appBar.currentLicense": "Licence actuelle",
        "appBar.importLicenseKey": "Importer la clé de licence",
        "appBar.themeAria": "Modifier l'apparence",
        "appBar.themeHighContrast": "Contraste élevé",
        "appBar.themeTooltip": "Modifier l'apparence",
        "appBar.versionInformation": "Informations de version",
    },
    "compliance": {
        "levels.171_1_suffix": " Basic / FCI",
        "scopeLabels.53_moderate": "Conditionnement 800-53 Moderate",
        "cscRescanAll": "Tout rescanner",
        "cscRescanSelected": "Rescanner la sélection",
        "showDetails": "Ce que signifie cette norme",
        "csc.machinesChip": "{{count}} système",
        "csc.machinesChip_plural": "{{count}} systèmes",
        "csc.syncInventory": "Synchronisation de l'inventaire",
        "csc.gridLastScan": "Dernier scan",
        "csc.alertSuffix": "constats ci-dessous sous",
        "csc.machinesChip_one": "{{count}} système",
        "csc.machinesChip_other": "{{count}} systèmes",
        "csc.fixItSelected": "Sélection Fix-It",
        "csc.fixItSelectedCount": "Sélection Fix-It ({{count}})",
    },
    "components": {
        "sectionLanding.desc.agent_event_forwarding": (
            "Clés par défaut du journal d'événements et de syslog dans les "
            "paramètres d'agent émis."
        ),
        "sectionLanding.desc.agent_management": (
            "Vue d'ensemble des agents connectés, paramètres autorisés, "
            "diagnostics Push et carte des capacités."
        ),
        "sectionLanding.desc.agent_overview": (
            "Fichiers de paramètres, provisionnement et valeurs par défaut "
            "reçues par les points de terminaison."
        ),
        "sectionLanding.desc.applications": (
            "Catalogue des applications sensibles avec Duration ; importer un "
            "CSV fourni ou un CSV client."
        ),
        "sectionLanding.desc.approvals": (
            "Approuver ou refuser les demandes d'accès en attente qui vous "
            "sont assignées."
        ),
        "sectionLanding.desc.approver_profile": (
            "Canaux de contact utilisés lorsque l'on vous demande d'approuver "
            "un accès."
        ),
        "sectionLanding.desc.audit_log": (
            "Piste de conformité durable stockée dans PostgreSQL."
        ),
        "sectionLanding.desc.bulk_provision": (
            "Provisionner de nombreux points de terminaison à partir d'un "
            "téléversement CSV ou tableur."
        ),
        "sectionLanding.desc.connection_points": (
            "Définir des cibles SSH et RDP, lancer des sessions proxifiées et "
            "gérer les identifiants."
        ),
        "sectionLanding.desc.create_settings_file": (
            "Émettre le JSON des paramètres d'agent avec un jeton d'enrôlement."
        ),
        "sectionLanding.desc.credentials": (
            "Faire tourner les mots de passe à la demande, demander une "
            "révélation break-glass et ouvrir les planifications par cible."
        ),
        "sectionLanding.desc.demo_data": (
            "Utilitaires de développement pour initialiser ou réinitialiser "
            "des données d'exemple."
        ),
        "sectionLanding.desc.discovery_jobs": (
            "Exécuter des tâches de découverte, gérer les planifications de "
            "scan et examiner la liste Asset."
        ),
        "sectionLanding.desc.enrollment_and_access_control": (
            "Matrice de l'évaluateur : qui peut modifier les champs "
            "d'enrôlement et quels événements d'audit prouvent les changements."
        ),
        "sectionLanding.desc.entitlements": (
            "Qui peut demander ou lancer quelles cibles de connexion."
        ),
        "sectionLanding.desc.event_sharing": (
            "Transfert SIEM, ServiceNow, Jira et webhook HTTPS générique, plus "
            "les puits intégrés."
        ),
        "sectionLanding.desc.fleet_agent_versions": (
            "Versions d'agent en lecture seule, ancienneté du check-in, "
            "accessibilité Push et avertissements d'exécution depuis Systems List."
        ),
        "sectionLanding.desc.identity_template": (
            "Modifier les comptes gérés initialisés sur les nouveaux membres "
            "du groupe."
        ),
        "sectionLanding.desc.import_settings_files": (
            "Valider le JSON des paramètres hérités pour l'examen de migration."
        ),
        "sectionLanding.desc.inventory": (
            "Parcourir les cibles OT, l'état, et Connect ou Configure par ligne."
        ),
        "sectionLanding.desc.jump_fleet_load_balancing": (
            "Configurer les hôtes Jump externes et la capacité aic-server-local, "
            "drain/poids, placement Probe et push."
        ),
        "sectionLanding.desc.lab_advanced": (
            "Lecture du manifeste, outils de laboratoire MITM et utilitaires "
            "de données de démonstration."
        ),
        "sectionLanding.desc.live_events": (
            "Flux opérationnel quasi temps réel provenant des agents et de ce "
            "serveur."
        ),
        "sectionLanding.desc.manage_issuances": (
            "Faire tourner, révoquer et retélécharger les paquets de paramètres "
            "émis."
        ),
        "sectionLanding.desc.operator_disclosures": (
            "Texte de divulgation standard avant les actions sensibles de "
            "l'opérateur."
        ),
        "sectionLanding.desc.password_defaults": (
            "Politique de mot de passe au niveau du programme, en bas de la "
            "chaîne d'héritage."
        ),
        "sectionLanding.desc.privileged_user_management": (
            "Affectation de paquets WDAC / AppLocker, surveillance des hachages "
            "effectifs et approbations d'exception."
        ),
        "sectionLanding.desc.propagation_templates": (
            "Catalogue de scripts de propagation, push connecté et export "
            "air-gap."
        ),
        "sectionLanding.desc.rbac_lab": (
            "Mode test RBAC et profils fictifs — accès propriétaire par défaut."
        ),
        "sectionLanding.desc.rdp_ocr_metadata": (
            "File d'attente des tâches Tesseract de laboratoire, résultats de "
            "recherche et métadonnées par machine (Live pour le laboratoire). "
            "Les moteurs OCR de production au-delà de Tesseract restent Planned "
            "(P2-7). L'indexation du terminal SSH reste hors périmètre."
        ),
        "sectionLanding.desc.recording_agents_health": (
            "Agents enrôlés avec l'état de check-in et la prise en charge de "
            "l'enregistrement proxy ou local à la cible."
        ),
        "sectionLanding.desc.server_configuration": (
            "Comment ce serveur fonctionne : TLS, identité, crypto et contrôle."
        ),
        "sectionLanding.desc.session_control": (
            "Surveiller et terminer les sessions privilégiées actives."
        ),
        "sectionLanding.desc.session_recordings": (
            "Parcourir et rejouer les sessions proxifiées enregistrées."
        ),
        "sectionLanding.desc.sessions_evidence": (
            "Examiner les sessions OT ouvertes et les preuves de session."
        ),
        "sectionLanding.desc.startup_wizard": (
            "Parcours guidé d'un environnement OT vide vers des actifs "
            "découverts et enrôlés."
        ),
        "sectionLanding.desc.system_groups": (
            "Politique de mot de passe partagée, modèles d'identité et valeurs "
            "par défaut de l'assistant."
        ),
        "sectionLanding.desc.systems_list": (
            "Chaque système connu, avec ou sans agent, avec accessibilité, "
            "état de collecte et santé de l'agent."
        ),
        "sectionLanding.group.jump_capacity": "Jump et capacité",
        "sectionLanding.group.recording_ops": "Exploitation des enregistrements",
    },
    "dashboard": {
        "defense.colUnique": "Adresses uniques",
        "defense.geoAbsentBefore": (
            "La correspondance de pays est Absent. Le cadre de la carte reste "
            "visible. Installez la base GeoIP depuis"
        ),
        "defense.heatMapAria": (
            "Carte thermique mondiale des tentatives bloquées et échouées par "
            "pays. Le tableau classé est la source accessible."
        ),
    },
    "docs": {
        "openapi.showRaw": "Afficher le JSON brut",
        "openapi.hideRaw": "Masquer le JSON brut",
        "openapi.totalPart": " ({{total}} au total)",
        # en leaf is itself German; intended English: " (page list capped at 500)"
        "openapi.capped": " (liste de pages limitée à 500)",
    },
    "pages": {
        "chrome.elevation.elevationConfigured": "Élévation configurée",
        "chrome.jumpFleet.testAll": "Tout tester",
        "chrome.licensing.model.enterprise_infra.label": (
            "Infrastructure d'entreprise"
        ),
        "chrome.messaging.tlsMode.implicit": "TLS implicite",
        "chrome.networkScan.scanNetworks": "Analyser les réseaux",
        "chrome.pum.assignPack": "Affecter le paquet",
        "chrome.sessionIoPolicy.fileTransfer_download_only": (
            "Téléchargement uniquement"
        ),
        "chrome.sessionIoPolicy.role_server_administrator": (
            "Administrateur du serveur"
        ),
        "chrome.systemsList.colLastCheckIn": "Dernier check-in",
        "chrome.training.detailInProgressN": "En cours {{count}}",
        "headers.settings__session-policy.helpAriaLabel": (
            "Ouvrir l'aide pour settings / session-policy"
        ),
        "headers.systems__known-default-credentials.helpAriaLabel": (
            "Ouvrir l'aide pour systems / known-default-credentials"
        ),
        "defense.legendPoint": "Point de légende",
        "defense.tacticTotal": "Total de la tactique",
        "defense.unlocatedOrigin": "Origine sans localisation",
    },
    "risks": {
        "allSeverities": "Toutes les sévérités",
        "loadingRegister": "Chargement du registre…",
        "acceptance_expired": "Expiré {{date}}",
        "acceptance_until": "Accepté jusqu'au {{date}}",
    },
}

ES: dict[str, dict[str, str]] = {
    "catalog": {
        "activeStandard": "Estándar activo",
        "rowCount": "{{count}} filas",
    },
    "common": {
        "appBar.approvalsAria": "Aprobaciones pendientes",
        "appBar.approvalsTooltip": "Aprobaciones PAM pendientes",
        "appBar.currentLicense": "Licencia actual",
        "appBar.importLicenseKey": "Importar clave de licencia",
        "appBar.themeAria": "Cambiar la apariencia",
        "appBar.themeHighContrast": "Alto contraste",
        "appBar.themeTooltip": "Cambiar la apariencia",
        "appBar.versionInformation": "Información de versión",
    },
    "compliance": {
        "levels.171_1_suffix": " Basic / FCI",
        "scopeLabels.53_moderate": "Empaquetado 800-53 Moderate",
        "cscRescanAll": "Volver a analizar todo",
        "cscRescanSelected": "Volver a analizar la selección",
        "showDetails": "Qué significa este estándar",
        "csc.machinesChip": "{{count}} sistema",
        "csc.machinesChip_plural": "{{count}} sistemas",
        "csc.syncInventory": "Sincronización de inventario",
        "csc.gridLastScan": "Último análisis",
        "csc.alertSuffix": "hallazgos abajo bajo",
        "csc.machinesChip_one": "{{count}} sistema",
        "csc.machinesChip_other": "{{count}} sistemas",
        "csc.fixItSelected": "Selección Fix-It",
        "csc.fixItSelectedCount": "Selección Fix-It ({{count}})",
    },
    "components": {
        "sectionLanding.desc.agent_event_forwarding": (
            "Claves predeterminadas del registro de eventos y de syslog en la "
            "configuración de agente emitida."
        ),
        "sectionLanding.desc.agent_management": (
            "Resumen de agentes conectados, configuración permitida, "
            "diagnósticos Push y mapa de capacidades."
        ),
        "sectionLanding.desc.agent_overview": (
            "Archivos de configuración, aprovisionamiento y valores "
            "predeterminados que reciben los puntos de conexión."
        ),
        "sectionLanding.desc.applications": (
            "Catálogo de aplicaciones sensibles con Duration; importe un CSV "
            "incluido o un CSV del cliente."
        ),
        "sectionLanding.desc.approvals": (
            "Apruebe o deniegue las solicitudes de acceso pendientes "
            "asignadas a usted."
        ),
        "sectionLanding.desc.approver_profile": (
            "Canales de contacto usados cuando se le pide aprobar un acceso."
        ),
        "sectionLanding.desc.audit_log": (
            "Pista de cumplimiento duradera almacenada en PostgreSQL."
        ),
        "sectionLanding.desc.bulk_provision": (
            "Aprovisione muchos puntos de conexión desde una carga CSV o de "
            "hoja de cálculo."
        ),
        "sectionLanding.desc.connection_points": (
            "Defina destinos SSH y RDP, inicie sesiones con proxy y gestione "
            "credenciales."
        ),
        "sectionLanding.desc.create_settings_file": (
            "Emita el JSON de configuración del agente con un token de inscripción."
        ),
        "sectionLanding.desc.credentials": (
            "Rote contraseñas a demanda, solicite revelación break-glass y abra "
            "programaciones por destino."
        ),
        "sectionLanding.desc.demo_data": (
            "Utilidades de desarrollo para generar o restablecer datos de ejemplo."
        ),
        "sectionLanding.desc.discovery_jobs": (
            "Ejecute trabajos de descubrimiento, gestione programaciones de "
            "análisis y revise la lista Asset."
        ),
        "sectionLanding.desc.enrollment_and_access_control": (
            "Matriz del evaluador: quién puede editar los campos de inscripción "
            "y qué eventos de auditoría demuestran los cambios."
        ),
        "sectionLanding.desc.entitlements": (
            "Quién puede solicitar o iniciar qué destinos de conexión."
        ),
        "sectionLanding.desc.event_sharing": (
            "Reenvío SIEM, ServiceNow, Jira y webhook HTTPS genérico, más "
            "sumideros integrados."
        ),
        "sectionLanding.desc.fleet_agent_versions": (
            "Versiones de agente de solo lectura, antigüedad del check-in, "
            "alcance Push y advertencias de tiempo de ejecución desde Systems List."
        ),
        "sectionLanding.desc.identity_template": (
            "Edite qué cuentas administradas se generan en los nuevos miembros "
            "del grupo."
        ),
        "sectionLanding.desc.import_settings_files": (
            "Valide el JSON de configuración heredada para la revisión de migración."
        ),
        "sectionLanding.desc.inventory": (
            "Examine destinos OT, estado, y Connect o Configure por fila."
        ),
        "sectionLanding.desc.jump_fleet_load_balancing": (
            "Configure hosts Jump externos y la capacidad aic-server-local, "
            "drain/peso, ubicación Probe y push."
        ),
        "sectionLanding.desc.lab_advanced": (
            "Lectura del manifiesto, herramientas de laboratorio MITM y "
            "utilidades de datos de demostración."
        ),
        "sectionLanding.desc.live_events": (
            "Flujo operativo casi en tiempo real de los agentes y de este servidor."
        ),
        "sectionLanding.desc.manage_issuances": (
            "Rote, revoque y vuelva a descargar los paquetes de configuración emitidos."
        ),
        "sectionLanding.desc.operator_disclosures": (
            "Texto de divulgación estándar antes de acciones sensibles del operador."
        ),
        "sectionLanding.desc.password_defaults": (
            "Directiva de contraseñas a nivel de programa al final de la cadena "
            "de herencia."
        ),
        "sectionLanding.desc.privileged_user_management": (
            "Asignación de paquetes WDAC / AppLocker, supervisión de hashes "
            "efectivos y aprobaciones de excepción."
        ),
        "sectionLanding.desc.propagation_templates": (
            "Catálogo de scripts de propagación, push conectado y exportación air-gap."
        ),
        "sectionLanding.desc.rbac_lab": (
            "Modo de prueba RBAC y perfiles de prueba — acceso de propietario "
            "de forma predeterminada."
        ),
        "sectionLanding.desc.rdp_ocr_metadata": (
            "Cola de trabajos Tesseract de laboratorio, resultados de búsqueda "
            "y metadatos por máquina (Live para el laboratorio). Los motores OCR "
            "de producción más allá de Tesseract siguen Planned (P2-7). La "
            "indexación del terminal SSH permanece fuera de alcance."
        ),
        "sectionLanding.desc.recording_agents_health": (
            "Agentes inscritos con estado de check-in y compatibilidad de "
            "grabación proxy o local en el destino."
        ),
        "sectionLanding.desc.server_configuration": (
            "Cómo se ejecuta este servidor: TLS, identidad, cifrado y control."
        ),
        "sectionLanding.desc.session_control": (
            "Supervise y finalice las sesiones privilegiadas activas."
        ),
        "sectionLanding.desc.session_recordings": (
            "Examine y reproduzca las sesiones con proxy grabadas."
        ),
        "sectionLanding.desc.sessions_evidence": (
            "Revise las sesiones OT abiertas y la evidencia de sesión."
        ),
        "sectionLanding.desc.startup_wizard": (
            "Ruta guiada desde un entorno OT vacío hasta activos descubiertos "
            "e inscritos."
        ),
        "sectionLanding.desc.system_groups": (
            "Directiva de contraseñas compartida, plantillas de identidad y "
            "valores predeterminados del asistente."
        ),
        "sectionLanding.desc.systems_list": (
            "Cada sistema conocido, con o sin agente, con alcanzabilidad, "
            "estado de recopilación y estado del agente."
        ),
        "sectionLanding.group.jump_capacity": "Jump y capacidad",
        "sectionLanding.group.recording_ops": "Operaciones de grabación",
    },
    "dashboard": {
        "defense.colUnique": "Direcciones únicas",
        "defense.geoAbsentBefore": (
            "La búsqueda de país está Absent. El marco del mapa permanece "
            "visible. Instale la base de datos GeoIP desde"
        ),
        "defense.heatMapAria": (
            "Mapa de calor mundial de intentos bloqueados y fallidos por país. "
            "La tabla clasificada es la fuente accesible."
        ),
    },
    "docs": {
        "openapi.showRaw": "Mostrar JSON sin formato",
        "openapi.hideRaw": "Ocultar JSON sin formato",
        "openapi.totalPart": " ({{total}} en total)",
        # en leaf is itself German; intended English: " (page list capped at 500)"
        "openapi.capped": " (lista de páginas limitada a 500)",
    },
    "pages": {
        "chrome.elevation.elevationConfigured": "Elevación configurada",
        "chrome.jumpFleet.testAll": "Probar todo",
        "chrome.licensing.model.enterprise_infra.label": (
            "Infraestructura empresarial"
        ),
        "chrome.messaging.tlsMode.implicit": "TLS implícito",
        "chrome.networkScan.scanNetworks": "Analizar redes",
        "chrome.pum.assignPack": "Asignar paquete",
        "chrome.sessionIoPolicy.fileTransfer_download_only": (
            "Solo descarga"
        ),
        "chrome.sessionIoPolicy.role_server_administrator": (
            "Administrador del servidor"
        ),
        "chrome.systemsList.colLastCheckIn": "Último check-in",
        "chrome.training.detailInProgressN": "En curso {{count}}",
        "headers.settings__session-policy.helpAriaLabel": (
            "Abrir la ayuda de settings / session-policy"
        ),
        "headers.systems__known-default-credentials.helpAriaLabel": (
            "Abrir la ayuda de systems / known-default-credentials"
        ),
        "defense.legendPoint": "Punto de leyenda",
        "defense.tacticTotal": "Total de la táctica",
        "defense.unlocatedOrigin": "Origen sin ubicación",
    },
    "risks": {
        "allSeverities": "Todas las severidades",
        "loadingRegister": "Cargando el registro…",
        "acceptance_expired": "Vencido {{date}}",
        "acceptance_until": "Aceptado hasta {{date}}",
    },
}

COMMENT = (
    "The fr and es UI packs carried German text for these keys after a "
    "machine-translation pass that pivoted through German. English source is "
    "copied from en/<namespace>.json so the stamped source_sha256 hashes the "
    "real source. Translations are agent drafts pending native review "
    "(localization-work-queue.mdc): German text shown to a French or Spanish "
    "operator is a shipped defect; a reviewed-pending French or Spanish string "
    "is not. Array-indexed bullet leaves under pages headers are omitted — the "
    "batch applier cannot replace list elements."
)


def resolve_english_text(data: dict, key: str) -> str | None:
    """Return the leaf text for a dotted or flat key, or None if missing."""
    if key in data:
        node = data[key]
        if isinstance(node, dict) and "text" in node:
            text = node["text"]
            return text if isinstance(text, str) else None
        if isinstance(node, str):
            return node
    if "." not in key:
        return None
    node: object = data
    for segment in key.split("."):
        if not isinstance(node, dict) or segment not in node:
            return None
        node = node[segment]
    if isinstance(node, dict) and "text" in node:
        text = node["text"]
        return text if isinstance(text, str) else None
    if isinstance(node, str):
        return node
    return None


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(text))


def main() -> int:
    if set(FR) != set(ES):
        print(f"error: fr/es namespace sets differ: {set(FR) ^ set(ES)}")
        return 2

    wrote: list[tuple[str, int]] = []

    for namespace in sorted(FR):
        fr_map = FR[namespace]
        es_map = ES[namespace]
        if set(fr_map) != set(es_map):
            print(
                f"error: {namespace}: fr/es key sets differ: "
                f"{sorted(set(fr_map) ^ set(es_map))}"
            )
            return 2

        en_path = UI / "en" / f"{namespace}.json"
        if not en_path.is_file():
            print(f"error: missing English pack {en_path}")
            return 2
        en_data = json.loads(en_path.read_text(encoding="utf-8"))

        source: dict[str, str] = {}
        for key in sorted(fr_map):
            text = resolve_english_text(en_data, key)
            if text is None:
                print(f"error: no English source for {namespace}.{key}")
                return 2
            source[key] = text

            fr_ph = placeholders(fr_map[key])
            es_ph = placeholders(es_map[key])
            en_ph = placeholders(text)
            if fr_ph != en_ph:
                print(
                    f"error: {namespace}.{key} fr placeholders {sorted(fr_ph)} "
                    f"!= en {sorted(en_ph)}"
                )
                return 2
            if es_ph != en_ph:
                print(
                    f"error: {namespace}.{key} es placeholders {sorted(es_ph)} "
                    f"!= en {sorted(en_ph)}"
                )
                return 2

        batch = {
            "_comment": COMMENT,
            "area": "locales-ui",
            "namespace": namespace,
            "source": source,
            "translations": {"fr": fr_map, "es": es_map},
        }

        out = OUT_DIR / f"leak-fr-es-{namespace}-20260825.json"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        wrote.append((out.name, len(source)))
        print(f"wrote {out.name}: {len(source)} keys")

    print(f"total namespaces: {len(wrote)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
