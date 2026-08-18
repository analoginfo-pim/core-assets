#!/usr/bin/env python3
"""Generate Jump + DB Mgmt native catalogs for all Wave A-D tags.

Writes:
  content/i18n-native/apps/pim-jump-server/<tag>/messages.json
  content/i18n-native/apps/pim-db-mgmt-agent/<tag>/messages.json
  content/i18n-native/gui/<tag>/jump_configurator.json
  content/i18n-native/gui/<tag>/db_mgmt_configurator.json

US English source_sha256 is SHA-256 of UTF-8 NFC of en text (developer standard).
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "content" / "i18n-native"

TAGS = [
    "en",
    "en-GB",
    "de",
    "fr",
    "es",
    "zh-Hans",
    "zh-TW",
    "ja",
    "ko",
    "pt-BR",
    "it",
    "he",
    "pl",
    "tr",
    "nl",
    "sv",
    "fi",
    "ar",
]


def sha_en(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def leaf(en_text: str, localized: str) -> dict:
    return {"text": localized, "source_sha256": sha_en(en_text)}


# English sources
JUMP_EN = {
    "product.name": "AIC Jump Server",
    "cli.status": "Status",
    "config.window_title": "Jump Config",
}
DB_EN = {
    "product.name": "AIC Database Management Agent",
    "cli.status": "Status",
    "service.display_name": "AIC Database Management Agent",
}

# Formal register translations (enterprise-localization). Product brand "AIC" stays Latin.
JUMP_TX = {
    "en": JUMP_EN,
    "en-GB": {
        "product.name": "AIC Jump Server",
        "cli.status": "Status",
        "config.window_title": "Jump Config",
    },
    "de": {
        "product.name": "AIC Jump-Server",
        "cli.status": "Status",
        "config.window_title": "Jump-Konfiguration",
    },
    "fr": {
        "product.name": "Serveur Jump AIC",
        "cli.status": "État",
        "config.window_title": "Configuration Jump",
    },
    "es": {
        "product.name": "Servidor Jump AIC",
        "cli.status": "Estado",
        "config.window_title": "Configuración Jump",
    },
    "zh-Hans": {
        "product.name": "AIC Jump 服务器",
        "cli.status": "状态",
        "config.window_title": "Jump 配置",
    },
    "zh-TW": {
        "product.name": "AIC Jump 伺服器",
        "cli.status": "狀態",
        "config.window_title": "Jump 設定",
    },
    "ja": {
        "product.name": "AIC ジャンプサーバー",
        "cli.status": "状態",
        "config.window_title": "ジャンプ設定",
    },
    "ko": {
        "product.name": "AIC Jump 서버",
        "cli.status": "상태",
        "config.window_title": "Jump 구성",
    },
    "pt-BR": {
        "product.name": "Servidor Jump AIC",
        "cli.status": "Status",
        "config.window_title": "Configuração Jump",
    },
    "it": {
        "product.name": "Server Jump AIC",
        "cli.status": "Stato",
        "config.window_title": "Configurazione Jump",
    },
    "he": {
        "product.name": "שרת Jump של AIC",
        "cli.status": "מצב",
        "config.window_title": "תצורת Jump",
    },
    "pl": {
        "product.name": "Serwer Jump AIC",
        "cli.status": "Stan",
        "config.window_title": "Konfiguracja Jump",
    },
    "tr": {
        "product.name": "AIC Jump Sunucusu",
        "cli.status": "Durum",
        "config.window_title": "Jump Yapılandırması",
    },
    "nl": {
        "product.name": "AIC Jump-server",
        "cli.status": "Status",
        "config.window_title": "Jump-configuratie",
    },
    "sv": {
        "product.name": "AIC Jump-server",
        "cli.status": "Status",
        "config.window_title": "Jump-konfiguration",
    },
    "fi": {
        "product.name": "AIC Jump-palvelin",
        "cli.status": "Tila",
        "config.window_title": "Jump-asetukset",
    },
    "ar": {
        "product.name": "خادم Jump من AIC",
        "cli.status": "الحالة",
        "config.window_title": "تكوين Jump",
    },
}

DB_TX = {
    "en": DB_EN,
    "en-GB": {
        "product.name": "AIC Database Management Agent",
        "cli.status": "Status",
        "service.display_name": "AIC Database Management Agent",
    },
    "de": {
        "product.name": "AIC-Datenbankverwaltungs-Agent",
        "cli.status": "Status",
        "service.display_name": "AIC-Datenbankverwaltungs-Agent",
    },
    "fr": {
        "product.name": "Agent de gestion de base de données AIC",
        "cli.status": "État",
        "service.display_name": "Agent de gestion de base de données AIC",
    },
    "es": {
        "product.name": "Agente de administración de bases de datos AIC",
        "cli.status": "Estado",
        "service.display_name": "Agente de administración de bases de datos AIC",
    },
    "zh-Hans": {
        "product.name": "AIC 数据库管理代理",
        "cli.status": "状态",
        "service.display_name": "AIC 数据库管理代理",
    },
    "zh-TW": {
        "product.name": "AIC 資料庫管理代理程式",
        "cli.status": "狀態",
        "service.display_name": "AIC 資料庫管理代理程式",
    },
    "ja": {
        "product.name": "AIC データベース管理エージェント",
        "cli.status": "状態",
        "service.display_name": "AIC データベース管理エージェント",
    },
    "ko": {
        "product.name": "AIC 데이터베이스 관리 에이전트",
        "cli.status": "상태",
        "service.display_name": "AIC 데이터베이스 관리 에이전트",
    },
    "pt-BR": {
        "product.name": "Agente de gerenciamento de banco de dados AIC",
        "cli.status": "Status",
        "service.display_name": "Agente de gerenciamento de banco de dados AIC",
    },
    "it": {
        "product.name": "Agente di gestione database AIC",
        "cli.status": "Stato",
        "service.display_name": "Agente di gestione database AIC",
    },
    "he": {
        "product.name": "סוכן ניהול מסדי נתונים של AIC",
        "cli.status": "מצב",
        "service.display_name": "סוכן ניהול מסדי נתונים של AIC",
    },
    "pl": {
        "product.name": "Agent zarządzania bazą danych AIC",
        "cli.status": "Stan",
        "service.display_name": "Agent zarządzania bazą danych AIC",
    },
    "tr": {
        "product.name": "AIC Veritabanı Yönetim Aracısı",
        "cli.status": "Durum",
        "service.display_name": "AIC Veritabanı Yönetim Aracısı",
    },
    "nl": {
        "product.name": "AIC-databasebeheeragent",
        "cli.status": "Status",
        "service.display_name": "AIC-databasebeheeragent",
    },
    "sv": {
        "product.name": "AIC databasadministrationsagent",
        "cli.status": "Status",
        "service.display_name": "AIC databasadministrationsagent",
    },
    "fi": {
        "product.name": "AIC-tietokannan hallinta-agentti",
        "cli.status": "Tila",
        "service.display_name": "AIC-tietokannan hallinta-agentti",
    },
    "ar": {
        "product.name": "وكيل إدارة قواعد البيانات من AIC",
        "cli.status": "الحالة",
        "service.display_name": "وكيل إدارة قواعد البيانات من AIC",
    },
}


def write_catalog(path: Path, en_map: dict[str, str], loc_map: dict[str, str]) -> None:
    out = {k: leaf(en_map[k], loc_map[k]) for k in en_map}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for tag in TAGS:
        jump_loc = JUMP_TX[tag]
        db_loc = DB_TX[tag]
        write_catalog(
            I18N / "apps" / "pim-jump-server" / tag / "messages.json", JUMP_EN, jump_loc
        )
        write_catalog(
            I18N / "apps" / "pim-db-mgmt-agent" / tag / "messages.json", DB_EN, db_loc
        )
        # Product configurator catalogs (manifest areas) — same keys as app messages.
        write_catalog(
            I18N / "gui" / tag / "jump_configurator.json", JUMP_EN, jump_loc
        )
        write_catalog(
            I18N / "gui" / tag / "db_mgmt_configurator.json", DB_EN, db_loc
        )
        # chrome.json must already exist for shared-gui-chrome
        chrome = I18N / "gui" / tag / "chrome.json"
        if not chrome.is_file():
            raise SystemExit(f"missing shared-gui-chrome: {chrome}")
    print(f"wrote Jump+DB native packs for {len(TAGS)} tags under {I18N}")


if __name__ == "__main__":
    main()
