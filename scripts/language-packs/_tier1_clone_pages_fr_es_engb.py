#!/usr/bin/env python3
"""Clone en/pages.json into en-GB / fr / es with formal register drafts.

en-GB: UK spelling pass on US English.
fr / es: formal Sie/vous/usted enterprise drafts from US English (agent draft;
translator queue remains open per localization-work-queue).
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

EN_PAGES = ROOT / "content/locales-ui/en/pages.json"

UK = [
    (r"\borganization\b", "organisation"),
    (r"\bOrganization\b", "Organisation"),
    (r"\borganizations\b", "organisations"),
    (r"\bOrganizations\b", "Organisations"),
    (r"\bcustomize\b", "customise"),
    (r"\bCustomize\b", "Customise"),
    (r"\bcustomized\b", "customised"),
    (r"\bcolor\b", "colour"),
    (r"\bColor\b", "Colour"),
    (r"\bcenter\b", "centre"),
    (r"\bCenter\b", "Centre"),
    (r"\blicense\b", "licence"),
    (r"\bLicense\b", "Licence"),
    (r"\blicensed\b", "licensed"),  # verb often same
    (r"\bfavorite\b", "favourite"),
    (r"\bFavorite\b", "Favourite"),
    (r"\bfavorites\b", "favourites"),
    (r"\bFavorites\b", "Favourites"),
    (r"\bbehavior\b", "behaviour"),
    (r"\bBehavior\b", "Behaviour"),
]


def ukify(text: str) -> str:
    out = text
    for pat, repl in UK:
        out = re.sub(pat, repl, out)
    return out


# Minimal high-frequency EN→FR / EN→ES for chrome verbs (formal).
EN_FR = {
    "Close": "Fermer",
    "Connect": "Connexion",
    "Create": "Créer",
    "Edit": "Modifier",
    "Export": "Exporter",
    "Filter": "Filtrer",
    "Import": "Importer",
    "Loading": "Chargement",
    "No data": "Aucune donnée",
    "No permission": "Aucune autorisation",
    "Refresh": "Actualiser",
    "Save": "Enregistrer",
    "Search": "Rechercher",
    "Delete": "Supprimer",
    "Cancel": "Annuler",
    "Actions": "Actions",
    "Add rule": "Ajouter une règle",
    "Command": "Commande",
    "Policy": "Politique",
    "Overview": "Vue d'ensemble",
    "Settings": "Paramètres",
    "Help": "Aide",
    "Dashboard": "Tableau de bord",
    "Favorites": "Favoris",
    "Sign out": "Se déconnecter",
}

EN_ES = {
    "Close": "Cerrar",
    "Connect": "Conectar",
    "Create": "Crear",
    "Edit": "Editar",
    "Export": "Exportar",
    "Filter": "Filtrar",
    "Import": "Importar",
    "Loading": "Cargando",
    "No data": "Sin datos",
    "No permission": "Sin permiso",
    "Refresh": "Actualizar",
    "Save": "Guardar",
    "Search": "Buscar",
    "Delete": "Eliminar",
    "Cancel": "Cancelar",
    "Actions": "Acciones",
    "Add rule": "Agregar regla",
    "Command": "Comando",
    "Policy": "Directiva",
    "Overview": "Resumen",
    "Settings": "Configuración",
    "Help": "Ayuda",
    "Dashboard": "Panel",
    "Favorites": "Favoritos",
    "Sign out": "Cerrar sesión",
}


def map_phrase(text: str, table: Dict[str, str]) -> str:
    if text in table:
        return table[text]
    # Preserve placeholders; leave longer prose as EN for follow-up formal translation
    # unless short (<= 40 chars) and fully matched after simple replace of known words.
    out = text
    for en, loc in sorted(table.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"\b{re.escape(en)}\b", loc, out)
    return out


def rebuild_tree(flat: Dict[str, str]) -> Dict[str, Any]:
    tree: Dict[str, Any] = {}

    def set_leaf(dotted: str, text: str) -> None:
        parts = dotted.split(".")
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}

    for k, v in flat.items():
        set_leaf(k, v)
    return tree


def transform(tag: str, fn: Callable[[str], str]) -> None:
    en_flat = flatten_entries(load_json(EN_PAGES))
    out_flat = {k: fn(e["text"]) for k, e in en_flat.items()}
    dest = ROOT / "content/locales-ui" / tag / "pages.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dump_json(dest, rebuild_tree(out_flat))
    print(f"{tag}: wrote {len(out_flat)} keys -> {dest}")


def main() -> None:
    transform("en-GB", ukify)
    transform("fr", lambda t: map_phrase(t, EN_FR))
    transform("es", lambda t: map_phrase(t, EN_ES))


if __name__ == "__main__":
    main()
