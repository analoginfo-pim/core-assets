#!/usr/bin/env python3
"""Print one catalog subtree from core-assets, the consumer working tree, and a
consumer git ref, side by side.

PowerShell redirection writes UTF-16, so `git show > file` then reading it as
UTF-8 fails. Reading git's stdout directly avoids that entirely, and having the
three views in one place is what makes a shape mismatch obvious -- a bare list
of strings on one side and {text, source_sha256} objects on the other is not a
missing key, it is two incompatible schemas for the same key.

Usage:
    python _probe_leaf.py <tag> <namespace> <dotted.path> [--ref HEAD]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
SERVER = CORE.parent / "pim-offline-server"
CATALOG = CORE / "content" / "locales-ui"
SERVER_LOCALES = "ui/src/i18n/locales"


def decode(raw: bytes):
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def descend(node, dotted: str):
    for step in dotted.split("."):
        if node is None:
            return None
        if isinstance(node, list):
            try:
                node = node[int(step)]
                continue
            except (ValueError, IndexError):
                return None
        if not isinstance(node, dict) or step not in node:
            return None
        node = node[step]
    return node


def show(label: str, node) -> None:
    print(f"--- {label}")
    if node is None:
        print("    ABSENT")
        return
    text = json.dumps(node, ensure_ascii=False, indent=2)
    for line in text.splitlines()[:24]:
        print(f"    {line}")
    if len(text.splitlines()) > 24:
        print("    ...")


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) < 3:
        print(__doc__)
        return 2
    tag, namespace, dotted = argv[0], argv[1], argv[2]
    ref = argv[argv.index("--ref") + 1] if "--ref" in argv else "HEAD"

    core_path = CATALOG / tag / f"{namespace}.json"
    core = decode(core_path.read_bytes()) if core_path.is_file() else None
    show(f"core-assets {tag}/{namespace}", descend(core, dotted))

    work_path = SERVER / SERVER_LOCALES / tag / f"{namespace}.json"
    work = decode(work_path.read_bytes()) if work_path.is_file() else None
    show(f"consumer working tree {tag}/{namespace}", descend(work, dotted))

    rel = f"{SERVER_LOCALES}/{tag}/{namespace}.json"
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=SERVER, capture_output=True)
    old = decode(proc.stdout) if proc.returncode == 0 else None
    show(f"consumer {ref} {tag}/{namespace}", descend(old, dotted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
