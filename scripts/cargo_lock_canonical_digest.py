"""Canonical Cargo.lock digest for Open Source Credits freshness.

Hashes sorted ``[[package]]`` identity only (name, version, source, checksum).
``[[patch.unused]]`` and every other section are excluded so gitignored
``.cargo/config.toml`` overlay reorders cannot flip the digest.

This algorithm is the source of truth. ``pim-offline-server/build.rs`` and
``src/cargo_lock_canonical_digest.rs`` must compute the same bytes.

A real package add/remove/version/checksum/source change MUST change the digest.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# Identity line: name <TAB> version <TAB> source <TAB> checksum
# Empty source/checksum stay empty (path crates).


def cargo_lock_canonical_payload(lock_text: str) -> str:
    """Return the canonical UTF-8 payload (trailing newline when any package)."""
    rows: list[tuple[str, str, str, str]] = []
    in_package = False
    name = ""
    version = ""
    source = ""
    checksum = ""

    def flush() -> None:
        nonlocal in_package, name, version, source, checksum
        if in_package and name and version:
            rows.append((name, version, source, checksum))
        in_package = False
        name = ""
        version = ""
        source = ""
        checksum = ""

    for raw in lock_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if line == "[[package]]":
            flush()
            in_package = True
            continue
        if line.startswith("["):
            flush()
            continue
        if not in_package:
            continue
        for key, target in (
            ("name", "name"),
            ("version", "version"),
            ("source", "source"),
            ("checksum", "checksum"),
        ):
            prefix = f'{key} = "'
            if line.startswith(prefix) and line.endswith('"'):
                value = line[len(prefix) : -1]
                if target == "name" and not name:
                    name = value
                elif target == "version" and not version:
                    version = value
                elif target == "source" and not source:
                    source = value
                elif target == "checksum" and not checksum:
                    checksum = value
                break

    flush()
    rows.sort()
    if not rows:
        return ""
    return "".join(f"{n}\t{v}\t{s}\t{c}\n" for n, v, s, c in rows)


def cargo_lock_canonical_sha256(lock_text: str) -> str:
    payload = cargo_lock_canonical_payload(lock_text)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cargo_lock_canonical_sha256_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return cargo_lock_canonical_sha256(text)
