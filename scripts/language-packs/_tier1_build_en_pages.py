#!/usr/bin/env python3
"""Build locales-ui/en/pages.json from pageIntros + TSX harvest + de key tree."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/language-packs"))
from language_packs import (  # noqa: E402
    dump_json,
    flatten_entries,
    load_json,
    source_sha256,
)

DE_PAGES = ROOT / "content/locales-ui/de/pages.json"
OUT_EN = ROOT / "content/locales-ui/en/pages.json"
HARVEST = ROOT / "scripts/language-packs/_tier1_harvest_pages_en.json"
PAGE_INTROS = Path(r"c:\analog-pim\pim-offline-server\ui\src\help\pageIntros.ts")


def path_to_seg(pathname: str) -> str:
    normalized = pathname.rstrip("/") or "/"
    if normalized == "/":
        return "root"
    if normalized.startswith("/pam/live/"):
        proto = normalized.split("/")[3] if len(normalized.split("/")) > 3 else "session"
        return f"pam__live__{proto}"
    return normalized[1:].replace("/", "__")


def parse_page_intros_headers() -> Dict[str, str]:
    """Extract English header fields from pageIntros.ts exact + prefix maps."""
    text = PAGE_INTROS.read_text(encoding="utf-8")
    out: Dict[str, str] = {}

    # Match path blocks: '/foo': { title: '...', summary: '...', ... }
    # Bullets: '...'
    block_re = re.compile(
        r"['\"](/[^'\"]*|/)['\"]\s*:\s*\{",
    )
    for m in block_re.finditer(text):
        path = m.group(1)
        # find matching closing brace roughly by scanning
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]
        seg = path_to_seg(path)
        prefix = f"headers.{seg}"

        def grab(field: str) -> str | None:
            fm = re.search(
                rf"{field}\s*:\s*`([^`]*)`|{field}\s*:\s*'((?:\\'|[^'])*)'|{field}\s*:\s*\"((?:\\\"|[^\"])*)\"",
                body,
                re.S,
            )
            if not fm:
                return None
            return next(g for g in fm.groups() if g is not None)

        for field in ("title", "summary", "helpAriaLabel"):
            val = grab(field)
            if val is not None:
                out[f"{prefix}.{field}"] = val.replace("\\'", "'").replace('\\"', '"')

        bullets = re.findall(
            r"^\s*'((?:\\'|[^'])*)'\s*,?\s*$|^\s*\"((?:\\\"|[^\"])*)\"\s*,?\s*$",
            body,
            re.M,
        )
        # Better: find bullets: [ ... ]
        bm = re.search(r"bullets\s*:\s*\[(.*?)\]", body, re.S)
        if bm:
            items = re.findall(
                r"'((?:\\'|[^'])*)'|\"((?:\\\"|[^\"])*)\"",
                bm.group(1),
            )
            for idx, pair in enumerate(items):
                val = next(g for g in pair if g)
                out[f"{prefix}.bullets.{idx}"] = val.replace("\\'", "'").replace('\\"', '"')

    return out


def set_path(tree: Dict[str, Any], dotted: str, text: str) -> None:
    parts = dotted.split(".")
    node = tree
    for p in parts[:-1]:
        child = node.get(p)
        if not isinstance(child, dict):
            child = {}
            node[p] = child
        node = child
    node[parts[-1]] = {"text": text, "source_sha256": source_sha256(text)}


def main() -> None:
    de = load_json(DE_PAGES)
    de_flat = flatten_entries(de)
    harvest = json.loads(HARVEST.read_text(encoding="utf-8"))
    headers = parse_page_intros_headers()
    print(f"de keys={len(de_flat)} harvest={len(harvest)} headers_from_intros={len(headers)}")

    en_tree: Dict[str, Any] = {}
    missing = []
    for key in sorted(de_flat.keys()):
        text = None
        if key in headers:
            text = headers[key]
        elif key in harvest:
            text = harvest[key]
        elif key.startswith("about__open-source-credits"):
            # Credits page stays English; use de text only if it is already English-ish,
            # else use harvest chrome.about.* equivalents when present.
            text = harvest.get(key) or de_flat[key].get("text")
        if text is None:
            # Fall back: keep German temporarily marked — will be replaced after EN authoring.
            # Prefer not to invent; use empty marker for walk to catch.
            missing.append(key)
            # Use a readable English placeholder derived later; for now copy DE so structure
            # exists and en walk uses defaultValue where keys overlap. Source sha of EN TBD.
            text = de_flat[key]["text"]
        set_path(en_tree, key, text)

    OUT_EN.parent.mkdir(parents=True, exist_ok=True)
    dump_json(OUT_EN, en_tree)
    miss_path = ROOT / "scripts/language-packs/_tier1_en_pages_still_de.json"
    miss_path.write_text(json.dumps(missing, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_EN} keys={len(de_flat)} still_need_en_authoring={len(missing)}")
    print("sample missing", missing[:12])


if __name__ == "__main__":
    main()
