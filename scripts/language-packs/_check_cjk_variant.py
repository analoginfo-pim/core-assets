#!/usr/bin/env python3
"""Check a batch's Chinese entries for cross-variant glyph leakage.

Traditional and Simplified Chinese are separate packs, and earlier in this pass
a zh-TW leaf shipped the Simplified form 可访问 where the pack's own convention
is 無障礙. A reviewer reading zh-TW cannot be expected to notice one Simplified
character inside an otherwise correct sentence, so the check is mechanical: a
character that exists only in one variant must not appear in the other's pack.

The character lists below are deliberately small and hand-picked from the
vocabulary these strings actually use -- credentials, certificates, records,
systems, access, settings, networks. A general-purpose variant table would be a
dependency; this is a spot check on the words in play.
"""

import json
import pathlib
import sys

# Simplified-only forms whose Traditional counterparts appear in these strings.
# 准 is deliberately absent: 准 and 準 are distinct Traditional characters, and
# 核准 ("to approve") is standard Taiwan administrative usage. Listing it as
# Simplified-only would flag correct text.
SIMPLIFIED_ONLY = "证认据应员网络组数设备问题类别报记录处说请转输检测从会内单双变换择权险户门关开启结构态级计算软硬储载执档纪审监标围凭复杂离续"
# Traditional-only forms whose Simplified counterparts appear in these strings.
TRADITIONAL_ONLY = "證認據應員網絡組數設備問題類別報記錄處說請轉輸檢測從會內單雙變換擇權險戶門關開啟結構態級計算軟硬儲載執檔紀審監標準圍憑複雜離續"

RULES = {"zh-TW": SIMPLIFIED_ONLY, "zh-Hans": TRADITIONAL_ONLY}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: _check_cjk_variant.py <batch.json>", file=sys.stderr)
        return 2
    batch = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    problems = 0
    for tag, forbidden in RULES.items():
        leaves = batch.get("translations", {}).get(tag)
        if not leaves:
            continue
        checked = 0
        for key, text in leaves.items():
            checked += 1
            hits = sorted({ch for ch in text if ch in forbidden})
            if hits:
                problems += 1
                print(f"WRONG-VARIANT {tag}:{key}  {''.join(hits)}")
                print(f"    {text}")
        print(f"{tag}: {checked} leaf/leaves checked")
    print(f"\n{problems} wrong-variant leaf/leaves")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
