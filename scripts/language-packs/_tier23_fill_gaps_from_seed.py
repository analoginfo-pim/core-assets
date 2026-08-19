#!/usr/bin/env python3
"""
Merge + MT `_tier23_en_gap_seed/{common,dashboard}.json` into assigned Tier2/3 tags.
Does not touch en/de/fr/es/en-GB.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

SEED = Path(__file__).resolve().parent / "_tier23_en_gap_seed"
ASSIGNED = [
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
GOOGLE_LANG = {
    "zh-Hans": "zh-CN",
    "zh-TW": "zh-TW",
    "ja": "ja",
    "ko": "ko",
    "pt-BR": "pt",
    "it": "it",
    "he": "iw",
    "pl": "pl",
    "tr": "tr",
    "nl": "nl",
    "sv": "sv",
    "fi": "fi",
    "ar": "ar",
}


def unflatten(entries: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    tree: Dict[str, Any] = {}
    for path, entry in entries.items():
        parts = path.split(".")
        node = tree
        for p in parts[:-1]:
            nxt = node.get(p)
            if not isinstance(nxt, dict) or "text" in nxt:
                nxt = {}
                node[p] = nxt
            node = nxt
        node[parts[-1]] = entry
    return tree


def merge_tree(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in overlay.items():
        if (
            isinstance(v, dict)
            and "text" not in v
            and isinstance(out.get(k), dict)
            and "text" not in out[k]
        ):
            out[k] = merge_tree(out[k], v)
        else:
            out[k] = v
    return out


def fill_ns(tag: str, ns: str, sleep: float, translator: Any) -> int:
    seed_path = SEED / f"{ns}.json"
    out_path = ROOT / "content/locales-ui" / tag / f"{ns}.json"
    if not seed_path.exists():
        print(f"skip missing seed {seed_path}")
        return 0
    src_flat = flatten_entries(load_json(seed_path))
    base_tree: Dict[str, Any] = {}
    existing: Dict[str, Any] = {}
    if out_path.exists():
        base_tree = load_json(out_path)
        existing = flatten_entries(base_tree)

    todo: List[Tuple[str, str, str]] = []
    for key, entry in src_flat.items():
        en_text = entry.get("text", "") if isinstance(entry, dict) else str(entry)
        h = entry.get("source_sha256") if isinstance(entry, dict) else ""
        if not h:
            h = source_sha256(en_text)
        if key in existing:
            prev = existing[key]
            if isinstance(prev, dict) and prev.get("text") and prev.get("text") != en_text:
                # keep existing translation unless it is still English source
                if prev.get("source_sha256") == h and prev.get("text") != en_text:
                    continue
                if prev.get("text") != en_text:
                    continue
        todo.append((key, en_text, h))

    print(f"{tag}/{ns}: translating {len(todo)} / {len(src_flat)}", flush=True)
    translated: Dict[str, Dict[str, str]] = {}
    for key, e in existing.items():
        if isinstance(e, dict) and "text" in e:
            translated[key] = {
                "text": e["text"],
                "source_sha256": e.get("source_sha256") or "",
            }

    batch = 20
    for i in range(0, len(todo), batch):
        chunk = todo[i : i + batch]
        texts = [t for _, t, _ in chunk]
        try:
            if hasattr(translator, "translate_batch"):
                results = translator.translate_batch(texts)
            else:
                results = [translator.translate(t) for t in texts]
        except Exception as exc:  # noqa: BLE001
            print(f"WARN batch: {exc}; per-string", file=sys.stderr)
            results = []
            for t in texts:
                try:
                    results.append(translator.translate(t))
                except Exception:
                    results.append(t)
                time.sleep(sleep)
        for (key, _en, h), tr in zip(chunk, results):
            translated[key] = {
                "text": tr if isinstance(tr, str) else str(tr),
                "source_sha256": h,
            }
        time.sleep(sleep)
        print(f"  … {min(i + batch, len(todo))}/{len(todo)}", flush=True)
        dump_json(out_path, merge_tree(base_tree, unflatten(translated)))

    dump_json(out_path, merge_tree(base_tree, unflatten(translated)))
    return len(todo)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--ns", action="append", default=["common", "dashboard"])
    ap.add_argument("--sleep", type=float, default=0.04)
    args = ap.parse_args()
    tags = args.tag or ASSIGNED
    from deep_translator import GoogleTranslator

    for tag in tags:
        if tag in {"en", "de", "fr", "es", "en-GB"}:
            print("refuse sibling", tag, file=sys.stderr)
            continue
        tr = GoogleTranslator(source="en", target=GOOGLE_LANG[tag])
        for ns in args.ns:
            fill_ns(tag, ns, args.sleep, tr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
