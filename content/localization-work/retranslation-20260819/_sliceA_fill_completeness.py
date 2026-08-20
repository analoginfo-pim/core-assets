#!/usr/bin/env python3
"""Slice A: eliminate raw-key / missing-key credibility defects.

1. Author clean US English for knownDefaults + actions in en.
2. Propagate draft translations to every Tier-1 tag.
3. Fill zh-Hans missing keys.
4. Replace leaf values that equal their own key path (stubs) by copying
   from docs.* in the same pack or from cleaned en.
5. Sync touched files into pim-offline-server/ui/src/i18n/locales.
"""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from pathlib import Path

CORE = Path(__file__).resolve().parents[3]
UI = CORE / "content" / "locales-ui"
SPA = Path(r"c:\analog-pim\pim-offline-server\ui\src\i18n\locales")
TAGS = ["en", "en-GB", "de", "fr", "es", "zh-Hans", "zh-TW"]

# US English for knownDefaults (operator-visible column/chrome labels)
KD_EN = {
    "title": "Known default credentials",
    "intro": (
        "Publicly documented vendor factory passwords for posture assessment. "
        "A match means a dangerous default password is still in use — change it "
        "to a platform-appropriate random password. This is delivery evidence, "
        "not a Met or certification claim."
    ),
    "tabCatalog": "Password catalog",
    "tabSources": "Dictionary sources",
    "tabPatterns": "Platform password patterns",
    "searchField": "Search field",
    "searchAll": "All fields",
    "searchVendor": "Vendor",
    "searchPlatform": "Platform",
    "searchOs": "Operating system",
    "searchUsername": "Username",
    "searchPassword": "Published password",
    "searchService": "Service",
    "searchQuery": "Search",
    "maskPasswords": "Mask passwords",
    "colUsername": "Username",
    "colPassword": "Published default",
    "colVendor": "Vendor",
    "colPlatform": "Platform",
    "colProduct": "Product",
    "colOs": "Operating system",
    "colUsedFor": "Used for",
    "colProtocol": "Service",
    "colActions": "Actions",
}

KD_BY_TAG = {
    "en": KD_EN,
    "en-GB": {
        **KD_EN,
        "title": "Known default credentials",
        "colOs": "Operating system",
        "intro": KD_EN["intro"].replace("Met or certification", "Met or certification"),
    },
    "de": {
        "title": "Bekannte Standardkennwörter",
        "intro": (
            "Öffentlich dokumentierte Werkskennwörter der Hersteller zur "
            "Haltungsbewertung. Ein Treffer bedeutet, dass ein gefährliches "
            "Standardkennwort noch in Gebrauch ist — auf ein plattformgerechtes "
            "Zufallskennwort wechseln. Das ist Liefernachweis, kein Met- oder "
            "Zertifizierungsanspruch."
        ),
        "tabCatalog": "Kennwortkatalog",
        "tabSources": "Wörterbuchquellen",
        "tabPatterns": "Plattform-Kennwortmuster",
        "searchField": "Suchfeld",
        "searchAll": "Alle Felder",
        "searchVendor": "Hersteller",
        "searchPlatform": "Plattform",
        "searchOs": "Betriebssystem",
        "searchUsername": "Benutzername",
        "searchPassword": "Veröffentlichtes Kennwort",
        "searchService": "Dienst",
        "searchQuery": "Suchen",
        "maskPasswords": "Veröffentlichte Kennwörter ausblenden",
        "colUsername": "Benutzername",
        "colPassword": "Veröffentlichter Standard",
        "colVendor": "Hersteller",
        "colPlatform": "Plattform",
        "colProduct": "Produkt",
        "colOs": "Betriebssystem",
        "colUsedFor": "Verwendung",
        "colProtocol": "Dienst",
        "colActions": "Aktionen",
    },
    "fr": {
        "title": "Identifiants par défaut connus",
        "intro": (
            "Mots de passe d'usine documentés publiquement pour l'évaluation "
            "de la posture. Une correspondance signifie qu'un mot de passe par "
            "défaut dangereux est encore utilisé — remplacez-le par un mot de "
            "passe aléatoire adapté à la plateforme. Ceci est une preuve de "
            "livraison, pas une affirmation Met ou de certification."
        ),
        "tabCatalog": "Catalogue de mots de passe",
        "tabSources": "Sources de dictionnaire",
        "tabPatterns": "Modèles de mots de passe par plateforme",
        "searchField": "Champ de recherche",
        "searchAll": "Tous les champs",
        "searchVendor": "Fournisseur",
        "searchPlatform": "Plateforme",
        "searchOs": "Système d'exploitation",
        "searchUsername": "Nom d'utilisateur",
        "searchPassword": "Mot de passe publié",
        "searchService": "Service",
        "searchQuery": "Rechercher",
        "maskPasswords": "Masquer les mots de passe",
        "colUsername": "Nom d'utilisateur",
        "colPassword": "Défaut publié",
        "colVendor": "Fournisseur",
        "colPlatform": "Plateforme",
        "colProduct": "Produit",
        "colOs": "Système d'exploitation",
        "colUsedFor": "Utilisé pour",
        "colProtocol": "Service",
        "colActions": "Actions",
    },
    "es": {
        "title": "Credenciales predeterminadas conocidas",
        "intro": (
            "Contraseñas de fábrica documentadas públicamente para la evaluación "
            "de postura. Una coincidencia significa que una contraseña "
            "predeterminada peligrosa sigue en uso: cámbiela por una contraseña "
            "aleatoria adecuada a la plataforma. Esto es evidencia de entrega, "
            "no una afirmación Met o de certificación."
        ),
        "tabCatalog": "Catálogo de contraseñas",
        "tabSources": "Fuentes de diccionario",
        "tabPatterns": "Patrones de contraseña por plataforma",
        "searchField": "Campo de búsqueda",
        "searchAll": "Todos los campos",
        "searchVendor": "Proveedor",
        "searchPlatform": "Plataforma",
        "searchOs": "Sistema operativo",
        "searchUsername": "Nombre de usuario",
        "searchPassword": "Contraseña publicada",
        "searchService": "Servicio",
        "searchQuery": "Buscar",
        "maskPasswords": "Ocultar contraseñas",
        "colUsername": "Nombre de usuario",
        "colPassword": "Predeterminado publicado",
        "colVendor": "Proveedor",
        "colPlatform": "Plataforma",
        "colProduct": "Producto",
        "colOs": "Sistema operativo",
        "colUsedFor": "Usado para",
        "colProtocol": "Servicio",
        "colActions": "Acciones",
    },
    "zh-Hans": {
        "title": "已知默认凭据",
        "intro": (
            "公开记载的厂商出厂密码，用于态势评估。命中表示危险的默认密码仍在使用"
            "——请改为适合该平台的随机密码。这是交付证据，不是 Met 或认证主张。"
        ),
        "tabCatalog": "密码目录",
        "tabSources": "词典来源",
        "tabPatterns": "平台密码模式",
        "searchField": "搜索字段",
        "searchAll": "全部字段",
        "searchVendor": "厂商",
        "searchPlatform": "平台",
        "searchOs": "操作系统",
        "searchUsername": "用户名",
        "searchPassword": "已公布密码",
        "searchService": "服务",
        "searchQuery": "搜索",
        "maskPasswords": "隐藏密码",
        "colUsername": "用户名",
        "colPassword": "已公布默认值",
        "colVendor": "厂商",
        "colPlatform": "平台",
        "colProduct": "产品",
        "colOs": "操作系统",
        "colUsedFor": "用途",
        "colProtocol": "服务",
        "colActions": "操作",
    },
    "zh-TW": {
        "title": "已知預設憑證",
        "intro": (
            "公開記載的廠商出廠密碼，用於態勢評估。命中表示危險的預設密碼仍在使用"
            "——請改為適合該平台的隨機密碼。這是交付證據，不是 Met 或認證主張。"
        ),
        "tabCatalog": "密碼目錄",
        "tabSources": "詞典來源",
        "tabPatterns": "平台密碼模式",
        "searchField": "搜尋欄位",
        "searchAll": "全部欄位",
        "searchVendor": "廠商",
        "searchPlatform": "平台",
        "searchOs": "作業系統",
        "searchUsername": "使用者名稱",
        "searchPassword": "已公布密碼",
        "searchService": "服務",
        "searchQuery": "搜尋",
        "maskPasswords": "隱藏密碼",
        "colUsername": "使用者名稱",
        "colPassword": "已公布預設值",
        "colVendor": "廠商",
        "colPlatform": "平台",
        "colProduct": "產品",
        "colOs": "作業系統",
        "colUsedFor": "用途",
        "colProtocol": "服務",
        "colActions": "操作",
    },
}

ACTIONS = {
    "en": {"add": "Add", "import": "Import", "refresh": "Refresh"},
    "en-GB": {"add": "Add", "import": "Import", "refresh": "Refresh"},
    "de": {"add": "Hinzufügen", "import": "Importieren", "refresh": "Aktualisieren"},
    "fr": {"add": "Ajouter", "import": "Importer", "refresh": "Actualiser"},
    "es": {"add": "Agregar", "import": "Importar", "refresh": "Actualizar"},
    "zh-Hans": {"add": "添加", "import": "导入", "refresh": "刷新"},
    "zh-TW": {"add": "新增", "import": "匯入", "refresh": "重新整理"},
}

SECTION_LANDING_SHORT = {
    "de": {
        "compliance": "Compliance",
        "events": "Ereignisse",
        "settings": "Einstellungen",
        "dashboard": "Dashboard",
    },
    "fr": {
        "compliance": "Conformité",
        "events": "Événements",
        "settings": "Paramètres",
        "dashboard": "Tableau de bord",
    },
    "es": {
        "compliance": "Cumplimiento",
        "events": "Eventos",
        "settings": "Configuración",
        "dashboard": "Panel",
    },
}


def set_text(obj: dict, key: str, value: str) -> bool:
    if key not in obj:
        return False
    leaf = obj[key]
    value = unicodedata.normalize("NFC", value)
    if isinstance(leaf, dict) and "text" in leaf:
        leaf["text"] = value
        if "source_sha256" in leaf:
            leaf["source_sha256"] = ""
        return True
    if isinstance(leaf, str):
        obj[key] = value
        return True
    return False


def walk_set(obj, prefix, out):
    if isinstance(obj, dict):
        if "text" in obj and isinstance(obj["text"], str) and not any(
            isinstance(v, (dict, list)) for v in obj.values()
        ):
            out[prefix] = obj
            return
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            walk_set(v, p, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_set(v, f"{prefix}[{i}]", out)


def is_stub(text: str, path: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if t == path or t == path.split(".")[-1]:
        return True
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+(\.\d+)?", t):
        if re.fullmatch(r"[A-Z0-9]+(\.[0-9]+)+", t):
            return False
        return True
    return False


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def ensure_leaf(parent: dict, key: str, text: str) -> None:
    text = unicodedata.normalize("NFC", text)
    if key not in parent:
        parent[key] = {"text": text, "source_sha256": ""}
    elif isinstance(parent[key], dict) and "text" in parent[key]:
        parent[key]["text"] = text
        parent[key]["source_sha256"] = ""
    else:
        parent[key] = {"text": text, "source_sha256": ""}


def fix_known_defaults_and_actions(tag: str) -> dict:
    path = UI / tag / "common.json"
    data = load(path)
    n = 0
    kd = data.setdefault("knownDefaults", {})
    for k, v in KD_BY_TAG[tag].items():
        if set_text(kd, k, v) or True:
            ensure_leaf(kd, k, v)
            n += 1
    actions = data.setdefault("actions", {})
    for k, v in ACTIONS[tag].items():
        ensure_leaf(actions, k, v)
        n += 1
    # sectionLanding short stubs in components
    if tag in SECTION_LANDING_SHORT:
        cpath = UI / tag / "components.json"
        cdata = load(cpath)
        desc = cdata.get("sectionLanding", {}).get("desc", {})
        for k, v in SECTION_LANDING_SHORT[tag].items():
            if k in desc:
                ensure_leaf(desc, k, v)
                n += 1
        save(cpath, cdata)
    save(path, data)
    return {"file": "common.json", "updates": n}


def fill_zh_hans_missing() -> list[str]:
    fixed = []
    # ot:ipScanner.emptyLoading
    ot_path = UI / "zh-Hans" / "ot.json"
    ot = load(ot_path)
    ip = ot.setdefault("ipScanner", {})
    ensure_leaf(ip, "emptyLoading", "正在检查扫描器状态…")
    save(ot_path, ot)
    fixed.append("ot:ipScanner.emptyLoading")
    # risks:level.medium
    risks_path = UI / "zh-Hans" / "risks.json"
    risks = load(risks_path)
    level = risks.setdefault("level", {})
    ensure_leaf(level, "medium", "中")
    save(risks_path, risks)
    fixed.append("risks:level.medium")
    return fixed


def replace_stubs(tag: str) -> dict:
    """Replace stub values with docs.* or en text when available."""
    # Build lookup from this tag's docs + en all namespaces
    lookups: dict[str, str] = {}
    for ns_file in (UI / tag).glob("*.json"):
        leaves = {}
        walk_set(load(ns_file), "", leaves)
        for k, leaf in leaves.items():
            t = leaf["text"]
            if not is_stub(t, k):
                lookups[f"{ns_file.stem}:{k}"] = t
                lookups[k] = t  # bare path
    en_lookups: dict[str, str] = {}
    for ns_file in (UI / "en").glob("*.json"):
        leaves = {}
        walk_set(load(ns_file), "", leaves)
        for k, leaf in leaves.items():
            t = leaf["text"]
            if not is_stub(t, k):
                en_lookups[f"{ns_file.stem}:{k}"] = t
                en_lookups[k] = t

    fixed = 0
    unresolved = []
    for ns_file in sorted((UI / tag).glob("*.json")):
        data = load(ns_file)
        leaves = {}
        walk_set(data, "", leaves)
        changed = False
        for k, leaf in leaves.items():
            t = leaf["text"]
            if not is_stub(t, k):
                continue
            # skip control identifiers
            if re.fullmatch(r"[A-Z0-9]+(\.[0-9A-Z]+)+", t):
                continue
            if re.fullmatch(r"[0-9]+(\.[0-9]+)+", t):
                continue
            # Prefer docs path for auditorSetup / technical stubs stored under common
            candidates = [
                f"docs:{t}",
                f"docs:{k}",
                f"{ns_file.stem}:{k}",
                t,
                k,
            ]
            replacement = None
            for c in candidates:
                if c in lookups:
                    replacement = lookups[c]
                    break
                if c in en_lookups:
                    replacement = en_lookups[c]
                    break
            # technical.howTo — often only under common; use en docs technical if any
            if replacement is None and t.startswith("technical."):
                for prefix in ("docs:", "common:", ""):
                    key = prefix + t if prefix else t
                    if key in en_lookups:
                        replacement = en_lookups[key]
                        break
            if replacement is None and t.startswith("auditorSetup."):
                # map auditorSetup.body.0 -> docs auditorSetup.body.0
                docs_key = "docs:" + t
                if docs_key in en_lookups:
                    replacement = en_lookups[docs_key]
                elif t in en_lookups:
                    replacement = en_lookups[t]
            if replacement and not is_stub(replacement, k):
                leaf["text"] = unicodedata.normalize("NFC", replacement)
                if "source_sha256" in leaf:
                    leaf["source_sha256"] = ""
                fixed += 1
                changed = True
            else:
                unresolved.append(f"{ns_file.stem}:{k}={t}")
        if changed:
            save(ns_file, data)
    return {"fixed": fixed, "unresolved": unresolved[:40], "unresolved_count": len(unresolved)}


def sync_spa(tag: str, files: list[str]) -> None:
    for fname in files:
        src = UI / tag / fname
        dst = SPA / tag / fname
        if src.exists() and dst.parent.exists():
            shutil.copy2(src, dst)


def parity(tag: str) -> dict:
    def keys(base: Path) -> set[str]:
        out = set()
        for f in base.glob("*.json"):
            leaves = {}
            walk_set(load(f), "", leaves)
            for k in leaves:
                out.add(f"{f.stem}:{k}")
        return out

    en = keys(UI / "en")
    tg = keys(UI / tag)
    missing = sorted(en - tg)
    extra = sorted(tg - en)
    stubs = 0
    for f in (UI / tag).glob("*.json"):
        leaves = {}
        walk_set(load(f), "", leaves)
        for k, leaf in leaves.items():
            t = leaf["text"]
            if is_stub(t, k) and not re.fullmatch(r"[A-Z0-9]+(\.[0-9A-Z]+)+", t):
                stubs += 1
    return {
        "en_keys": len(en),
        "tag_keys": len(tg),
        "missing": len(missing),
        "extra": len(extra),
        "stub_values": stubs,
        "missing_ids": missing,
    }


def main() -> None:
    report: dict = {"slice": "A", "tags": {}}
    # 1) knownDefaults + actions for all tags
    for tag in TAGS:
        kd = fix_known_defaults_and_actions(tag)
        report["tags"].setdefault(tag, {})["knownDefaults_actions"] = kd
    # 2) zh-Hans missing
    report["tags"]["zh-Hans"]["filled_missing"] = fill_zh_hans_missing()
    # 3) stub replacement per tag
    for tag in TAGS:
        report["tags"][tag]["stubs"] = replace_stubs(tag)
    # 4) parity after
    for tag in TAGS:
        if tag == "en":
            continue
        report["tags"][tag]["parity_after"] = parity(tag)
    # 5) sync SPA for critical files
    for tag in TAGS:
        sync_spa(tag, ["common.json", "components.json", "ot.json", "risks.json", "pages.json", "nav.json", "docs.json", "binder.json"])
    out = (
        CORE
        / "content"
        / "localization-work"
        / "retranslation-20260819"
        / "sliceA-report.json"
    )
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # print summary
    for tag in TAGS:
        if tag == "en":
            continue
        p = report["tags"][tag].get("parity_after", {})
        print(
            f"{tag}: missing={p.get('missing')} stubs={p.get('stub_values')} "
            f"stub_fixed={report['tags'][tag]['stubs']['fixed']}"
        )
    print("wrote", out)


if __name__ == "__main__":
    main()
