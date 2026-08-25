#!/usr/bin/env python3
"""Accept or reject a wrong-language repair batch before it is applied.

A batch that replaces German text in the fr / es packs is only an improvement if
every replacement is (a) keyed to a real English source leaf, (b) no longer
byte-identical to the German text it replaces, and (c) carries the same
{{placeholder}} set as the English source. A dropped placeholder would trade a
German sentence for a French sentence missing the host name, which is a worse
defect than the one being fixed.

Reports, per batch, anything that fails those three checks plus the leaves that
came back byte-identical to English (legitimate for a product name, suspicious
for a sentence).
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "content" / "locales-ui"
BATCHES = ROOT / "content" / "language-packs" / "batches"

PLACEHOLDER = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")


def flatten(obj: dict, prefix: str = "", out: dict | None = None) -> dict:
    if out is None:
        out = {}
    for k, v in (obj or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            out[key] = v["text"]
        elif isinstance(v, dict):
            flatten(v, key, out)
    return out


def load(tag: str, namespace: str) -> dict:
    path = UI / tag / f"{namespace}.json"
    if not path.is_file():
        return {}
    return flatten(json.loads(path.read_text(encoding="utf-8")))


def ph(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(PLACEHOLDER.findall(text))))


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def main() -> int:
    patterns = sys.argv[1:] or ["leak-fr-es-*.json"]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(BATCHES.glob(pattern)))
    if not files:
        print("error: no batch files matched")
        return 2

    problems = 0
    identical = 0
    checked = 0

    for path in files:
        batch = json.loads(path.read_text(encoding="utf-8"))
        namespace = batch["namespace"]
        source = batch.get("source", {})
        en = load("en", namespace)
        de = load("de", namespace)

        for tag, entries in batch.get("translations", {}).items():
            current = load(tag, namespace)
            for key, text in entries.items():
                checked += 1
                en_text = en.get(key)

                if en_text is None:
                    print(f"MISSING-EN  {path.name} {tag}.{key}")
                    problems += 1
                    continue
                if source.get(key) is not None and nfc(source[key]) != nfc(en_text):
                    print(f"SOURCE-DRIFT {path.name} {tag}.{key}")
                    print(f"  batch says {source[key]!r}")
                    print(f"  en pack is {en_text!r}")
                    problems += 1

                if ph(text) != ph(en_text):
                    print(f"PLACEHOLDER {path.name} {tag}.{key}")
                    print(f"  en  {ph(en_text)}")
                    print(f"  new {ph(text)}")
                    problems += 1

                de_text = de.get(key)
                if de_text is not None and nfc(text) == nfc(de_text) and nfc(text) != nfc(en_text):
                    print(f"STILL-GERMAN {path.name} {tag}.{key}: {text!r}")
                    problems += 1

                # The leaf being replaced should currently BE the German text;
                # otherwise the batch is rewriting something it did not diagnose.
                cur = current.get(key)
                if cur is not None and de_text is not None and nfc(cur) != nfc(de_text):
                    print(f"NOT-LEAKED  {path.name} {tag}.{key}")
                    print(f"  current {cur!r}")
                    print(f"  german  {de_text!r}")
                    problems += 1

                if nfc(text) == nfc(en_text):
                    identical += 1
                    print(f"note: equals-english {tag}.{key}: {text!r}")

    print(
        f"\n{checked} replacements checked across {len(files)} batches: "
        f"{problems} problem(s), {identical} equal to English"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
