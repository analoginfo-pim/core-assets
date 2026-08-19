#!/usr/bin/env python3
"""Add dashboard chartLabels for OT/SecureShare/NetScan events (release packs)."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "content" / "locales-ui"

KEYS_EN = {
    "OtInventoryListed": "OT inventory listed",
    "SecureShareList": "Secure Share list viewed",
    "SecureShareBreakGlassPolicyRead": "Secure Share break-glass policy read",
    "NetworkScanJobStart": "Network scan job started",
}

I18N: dict[str, dict[str, str]] = {
    "en": KEYS_EN,
    "en-GB": dict(KEYS_EN),
    "de": {
        "OtInventoryListed": "OT-Inventar aufgelistet",
        "SecureShareList": "Secure-Share-Liste angezeigt",
        "SecureShareBreakGlassPolicyRead": "Secure-Share-Break-Glass-Richtlinie gelesen",
        "NetworkScanJobStart": "Netzwerkscanauftrag gestartet",
    },
    "fr": {
        "OtInventoryListed": "Inventaire OT liste",
        "SecureShareList": "Liste Secure Share consultee",
        "SecureShareBreakGlassPolicyRead": "Politique break-glass Secure Share lue",
        "NetworkScanJobStart": "Travail d'analyse reseau demarre",
    },
    "es": {
        "OtInventoryListed": "Inventario OT listado",
        "SecureShareList": "Lista de Secure Share consultada",
        "SecureShareBreakGlassPolicyRead": "Directiva break-glass de Secure Share leida",
        "NetworkScanJobStart": "Trabajo de analisis de red iniciado",
    },
    "zh-Hans": {
        "OtInventoryListed": "已列出 OT 资产清单",
        "SecureShareList": "已查看安全共享列表",
        "SecureShareBreakGlassPolicyRead": "已读取安全共享紧急访问策略",
        "NetworkScanJobStart": "网络扫描作业已启动",
    },
    "zh-TW": {
        "OtInventoryListed": "已列出 OT 資產清單",
        "SecureShareList": "已檢視安全共享清單",
        "SecureShareBreakGlassPolicyRead": "已讀取安全共享緊急存取原則",
        "NetworkScanJobStart": "網路掃描工作已啟動",
    },
    "ja": {
        "OtInventoryListed": "OT インベントリを一覧表示しました",
        "SecureShareList": "セキュア共有リストを表示しました",
        "SecureShareBreakGlassPolicyRead": "セキュア共有の緊急アクセスポリシーを読み取りました",
        "NetworkScanJobStart": "ネットワークスキャンジョブを開始しました",
    },
    "ko": {
        "OtInventoryListed": "OT 인벤토리 목록이 표시됨",
        "SecureShareList": "보안 공유 목록이 표시됨",
        "SecureShareBreakGlassPolicyRead": "보안 공유 비상 액세스 정책이 읽힘",
        "NetworkScanJobStart": "네트워크 검사 작업이 시작됨",
    },
    "pt-BR": {
        "OtInventoryListed": "Inventario OT listado",
        "SecureShareList": "Lista do Secure Share visualizada",
        "SecureShareBreakGlassPolicyRead": "Politica break-glass do Secure Share lida",
        "NetworkScanJobStart": "Trabalho de varredura de rede iniciado",
    },
    "it": {
        "OtInventoryListed": "Inventario OT elencato",
        "SecureShareList": "Elenco Secure Share visualizzato",
        "SecureShareBreakGlassPolicyRead": "Criterio break-glass Secure Share letto",
        "NetworkScanJobStart": "Processo di scansione di rete avviato",
    },
    "he": {
        "OtInventoryListed": "מלאי OT הוצג",
        "SecureShareList": "רשימת שיתוף מאובטח הוצגה",
        "SecureShareBreakGlassPolicyRead": "מדיניות break-glass של שיתוף מאובטח נקראה",
        "NetworkScanJobStart": "משימת סריקת רשת הופעלה",
    },
    "pl": {
        "OtInventoryListed": "Wyswietlono inwentarz OT",
        "SecureShareList": "Wyswietlono liste Secure Share",
        "SecureShareBreakGlassPolicyRead": "Odczytano zasady break-glass Secure Share",
        "NetworkScanJobStart": "Uruchomiono zadanie skanowania sieci",
    },
    "tr": {
        "OtInventoryListed": "OT envanteri listelendi",
        "SecureShareList": "Secure Share listesi goruntulendi",
        "SecureShareBreakGlassPolicyRead": "Secure Share break-glass ilkesi okundu",
        "NetworkScanJobStart": "Ag tarama isi baslatildi",
    },
    "nl": {
        "OtInventoryListed": "OT-inventaris weergegeven",
        "SecureShareList": "Secure Share-lijst weergegeven",
        "SecureShareBreakGlassPolicyRead": "Secure Share break-glass-beleid gelezen",
        "NetworkScanJobStart": "Netwerkscantaak gestart",
    },
    "sv": {
        "OtInventoryListed": "OT-inventering listad",
        "SecureShareList": "Secure Share-lista visad",
        "SecureShareBreakGlassPolicyRead": "Secure Share break-glass-princip last",
        "NetworkScanJobStart": "Natverksskanning startad",
    },
    "fi": {
        "OtInventoryListed": "OT-inventaario listattu",
        "SecureShareList": "Secure Share -luettelo naytetty",
        "SecureShareBreakGlassPolicyRead": "Secure Share break-glass -kaytanto luettu",
        "NetworkScanJobStart": "Verkkoskannaustyo kaynnistetty",
    },
    "ar": {
        "OtInventoryListed": "تم سرد جرد OT",
        "SecureShareList": "تم عرض قائمة المشاركة الآمنة",
        "SecureShareBreakGlassPolicyRead": "تمت قراءة سياسة الوصول الطارئ للمشاركة الآمنة",
        "NetworkScanJobStart": "بدأ عمل فحص الشبكة",
    },
}


def sha(en_text: str) -> str:
    return hashlib.sha256(
        unicodedata.normalize("NFC", en_text).encode("utf-8")
    ).hexdigest()


def main() -> None:
    # Fix FR accents that were ASCII-stripped above for PowerShell safety
    I18N["fr"] = {
        "OtInventoryListed": "Inventaire OT listé",
        "SecureShareList": "Liste Secure Share consultée",
        "SecureShareBreakGlassPolicyRead": "Politique break-glass Secure Share lue",
        "NetworkScanJobStart": "Travail d'analyse réseau démarré",
    }
    I18N["es"]["SecureShareBreakGlassPolicyRead"] = (
        "Directiva break-glass de Secure Share leída"
    )
    I18N["es"]["NetworkScanJobStart"] = "Trabajo de análisis de red iniciado"
    I18N["pt-BR"]["SecureShareBreakGlassPolicyRead"] = (
        "Política break-glass do Secure Share lida"
    )
    I18N["pl"] = {
        "OtInventoryListed": "Wyświetlono inwentarz OT",
        "SecureShareList": "Wyświetlono listę Secure Share",
        "SecureShareBreakGlassPolicyRead": "Odczytano zasady break-glass Secure Share",
        "NetworkScanJobStart": "Uruchomiono zadanie skanowania sieci",
    }
    I18N["tr"] = {
        "OtInventoryListed": "OT envanteri listelendi",
        "SecureShareList": "Secure Share listesi görüntülendi",
        "SecureShareBreakGlassPolicyRead": "Secure Share break-glass ilkesi okundu",
        "NetworkScanJobStart": "Ağ tarama işi başlatıldı",
    }
    I18N["sv"]["SecureShareBreakGlassPolicyRead"] = (
        "Secure Share break-glass-princip läst"
    )
    I18N["sv"]["NetworkScanJobStart"] = "Nätverksskanning startad"
    I18N["fi"] = {
        "OtInventoryListed": "OT-inventaario listattu",
        "SecureShareList": "Secure Share -luettelo näytetty",
        "SecureShareBreakGlassPolicyRead": "Secure Share break-glass -käytäntö luettu",
        "NetworkScanJobStart": "Verkkoskannaustyö käynnistetty",
    }

    updated: list[str] = []
    for tag_dir in sorted(ROOT.iterdir()):
        if not tag_dir.is_dir():
            continue
        tag = tag_dir.name
        path = tag_dir / "dashboard.json"
        if not path.exists():
            print("skip missing", path)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        cl = data.setdefault("chartLabels", {})
        texts = I18N.get(tag, KEYS_EN)
        changed = 0
        for k, en_text in KEYS_EN.items():
            loc = texts.get(k, en_text)
            entry = {"text": loc, "source_sha256": sha(en_text)}
            prev = cl.get(k)
            if not isinstance(prev, dict) or prev.get("text") != loc:
                cl[k] = entry
                changed += 1
        if changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            updated.append(f"{tag}:{changed}")
    print("updated", updated)


if __name__ == "__main__":
    main()
