"""List the exact keys a pack still ships byte-identical to English.

_residue_by_pack.py answers "how many"; this answers "which ones", so a
remaining count can be judged as an intentional cognate (Dutch "Database")
versus a real untranslated string.

usage: _list_residue_keys.py <area> <namespace> <key-prefix> [tag ...]
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2] / "content"


def leaves(node, prefix=""):
    if isinstance(node, dict):
        if "text" in node and isinstance(node.get("text"), str):
            yield prefix, node["text"]
            return
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)


def load(area: str, tag: str, namespace: str) -> dict[str, str]:
    path = ROOT / area / tag / f"{namespace}.json"
    if not path.exists():
        return {}
    return dict(leaves(json.loads(path.read_text(encoding="utf-8"))))


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    area, namespace, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    wanted = sys.argv[4:]

    english = load(area, "en", namespace)
    tags = wanted or sorted(
        p.name for p in (ROOT / area).iterdir() if p.is_dir() and p.name != "en"
    )

    for tag in tags:
        pack = load(area, tag, namespace)
        same = [
            key
            for key, text in pack.items()
            if key.startswith(prefix) and english.get(key) == text
        ]
        if not same:
            continue
        print(f"\n{tag}  {len(same)} key(s) identical to English")
        for key in sorted(same):
            print(f"    {key} = {english[key]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
