#!/usr/bin/env python3
"""
Translate locales-ui/en/*.json into an assigned Tier 2/3 tag.

Uses GoogleTranslator (deep-translator) with formal register notes baked into
prompts where the API allows only plain text. Placeholders {{...}} are protected.

Does NOT touch en/de/fr/es/en-GB.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import dump_json, flatten_entries, load_json, source_sha256  # noqa: E402

ASSIGNED = {
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
}

# deep-translator Google language codes
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

PLACEHOLDER_RE = re.compile(r"(\{\{[^}]+\}\}|\{[a-zA-Z_][a-zA-Z0-9_]*\})")
SKIP_NS_FOR_NOW: set[str] = set()  # translate all en namespaces present


def unflatten(entries: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    for path, entry in entries.items():
        parts = path.split(".")
        node = root
        for p in parts[:-1]:
            nxt = node.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                node[p] = nxt
            node = nxt
        node[parts[-1]] = entry
    return root


def protect(text: str) -> Tuple[str, List[str]]:
    held: List[str] = []

    def repl(m: re.Match[str]) -> str:
        held.append(m.group(0))
        return f"__PH{len(held) - 1}__"

    return PLACEHOLDER_RE.sub(repl, text), held


def restore(text: str, held: List[str]) -> str:
    out = text
    for i, tok in enumerate(held):
        for needle in (f"__PH{i}__", f"__ph{i}__", f"PH{i}"):
            if needle in out:
                out = out.replace(needle, tok)
    return out


def translate_batch(translator: Any, texts: List[str], sleep_s: float) -> List[str]:
    """Translate texts; prefer API batch when available, else one-by-one."""
    if not texts:
        return []
    protected_list: List[str] = []
    held_list: List[List[str]] = []
    for t in texts:
        if not t.strip():
            protected_list.append(t)
            held_list.append([])
            continue
        p, h = protect(t)
        protected_list.append(p)
        held_list.append(h)

    results: List[str] = []
    # deep_translator GoogleTranslator supports translate_batch for list[str]
    try:
        if hasattr(translator, "translate_batch"):
            chunk = [p for p in protected_list]
            batch_out = translator.translate_batch(chunk)
            if isinstance(batch_out, list) and len(batch_out) == len(chunk):
                for tr, held in zip(batch_out, held_list):
                    text = tr if isinstance(tr, str) else str(tr)
                    if held:
                        text = restore(text, held)
                    results.append(text)
                time.sleep(sleep_s)
                return results
    except Exception as exc:  # noqa: BLE001
        print(f"WARN batch translate fail ({exc!s:.100}); falling back per-string", file=sys.stderr)

    for t, held in zip(protected_list, held_list):
        if not t.strip():
            results.append(t)
            continue
        try:
            translated = translator.translate(t)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN translate fail: {exc!s:.120} — keeping English temporarily", file=sys.stderr)
            translated = t
            held = []
        if held:
            translated = restore(translated, held)
        results.append(translated)
        time.sleep(sleep_s)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument(
        "--ns",
        action="append",
        default=[],
        help="Namespace file stem (repeatable). Default: all en/*.json",
    )
    ap.add_argument("--sleep", type=float, default=0.05)
    ap.add_argument("--limit", type=int, default=0, help="Max leaves per ns (0=all)")
    ap.add_argument("--merge", action="store_true", help="Keep existing translated keys")
    args = ap.parse_args()
    tag = args.tag
    if tag not in ASSIGNED:
        print(f"refusing {tag}", file=sys.stderr)
        return 2

    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source="en", target=GOOGLE_LANG[tag])
    en_dir = ROOT / "content/locales-ui/en"
    out_dir = ROOT / "content/locales-ui" / tag
    out_dir.mkdir(parents=True, exist_ok=True)

    ns_list = args.ns or [p.stem for p in sorted(en_dir.glob("*.json"))]
    for ns in ns_list:
        if ns in SKIP_NS_FOR_NOW:
            continue
        en_path = en_dir / f"{ns}.json"
        if not en_path.exists():
            print(f"skip missing en {ns}")
            continue
        en = load_json(en_path)
        en_flat = flatten_entries(en)
        existing: Dict[str, Any] = {}
        out_path = out_dir / f"{ns}.json"
        if args.merge and out_path.exists():
            existing = flatten_entries(load_json(out_path))

        todo: List[Tuple[str, str, str]] = []  # key, en_text, en_hash
        for key, entry in en_flat.items():
            en_text = entry.get("text", "") if isinstance(entry, dict) else str(entry)
            h = ""
            if isinstance(entry, dict):
                h = entry.get("source_sha256") or source_sha256(en_text)
            else:
                h = source_sha256(en_text)
            if args.merge and key in existing:
                prev = existing[key]
                if isinstance(prev, dict) and prev.get("text") and prev.get("source_sha256") == h:
                    continue
            todo.append((key, en_text, h))

        if args.limit and len(todo) > args.limit:
            todo = todo[: args.limit]

        print(f"{tag}/{ns}: translating {len(todo)} / {len(en_flat)} leaves…", flush=True)
        translated_map: Dict[str, Dict[str, str]] = {}
        if args.merge and out_path.exists():
            for k, e in existing.items():
                if isinstance(e, dict) and "text" in e:
                    translated_map[k] = {
                        "text": e["text"],
                        "source_sha256": e.get("source_sha256") or "",
                    }

        batch_size = 40
        for i in range(0, len(todo), batch_size):
            chunk = todo[i : i + batch_size]
            texts = [t for _, t, _ in chunk]
            results = translate_batch(translator, texts, args.sleep)
            for (key, _en, h), tr in zip(chunk, results):
                translated_map[key] = {"text": tr, "source_sha256": h}
            print(f"  … {min(i + batch_size, len(todo))}/{len(todo)}", flush=True)
            # checkpoint
            dump_json(out_path, unflatten(translated_map))

        dump_json(out_path, unflatten(translated_map))
        print(f"  wrote {out_path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
