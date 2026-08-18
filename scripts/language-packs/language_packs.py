#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-AIC-Proprietary
"""Language pack hash / migrate / audit tools (Python 3 stdlib only).

Runs on Windows, macOS, and Linux. No pip packages. No environment variables.

Usage:
  python3 scripts/language-packs/language_packs.py hash --root .
  python3 scripts/language-packs/language_packs.py migrate --root .
  python3 scripts/language-packs/language_packs.py mark-stale --root .
  python3 scripts/language-packs/language_packs.py audit --root . --product aic-server
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ENTRY_KEYS = frozenset({"text", "source_sha256", "note"})
PLACEHOLDER_RE = re.compile(r"(\{\{[^}]+\}\}|\{[a-zA-Z0-9_.]+\})")


def repo_root_from(explicit: Optional[Path]) -> Path:
    if explicit is not None:
        return explicit.resolve()
    here = Path(__file__).resolve()
    # scripts/language-packs/language_packs.py -> repo root
    return here.parents[2]


def nfc_utf8(text: str) -> bytes:
    return unicodedata.normalize("NFC", text).encode("utf-8")


def source_sha256(english_text: str) -> str:
    return hashlib.sha256(nfc_utf8(english_text)).hexdigest()


def is_entry(obj: Any) -> bool:
    return (
        isinstance(obj, dict)
        and "text" in obj
        and isinstance(obj.get("text"), str)
        and set(obj.keys()).issubset(ENTRY_KEYS | {"source_sha256"})
        and ("source_sha256" in obj or len(obj) == 1 or "note" in obj)
    )


def is_bare_string_leaf_parent(obj: Dict[str, Any]) -> bool:
    """True if every value is a string (flat leaf map) — not used; we walk deeply."""
    return False


def walk_leaves(
    node: Any, prefix: str = ""
) -> Iterable[Tuple[str, Any, Optional[Dict[str, Any]], Optional[str]]]:
    """Yield (key_path, value, parent_dict, parent_key) for string or entry leaves."""
    if is_entry(node):
        # Caller handles entries at parent level
        return
    if isinstance(node, dict):
        for k, v in node.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str):
                yield path, v, node, k
            elif is_entry(v):
                yield path, v, node, k
            elif isinstance(v, dict):
                yield from walk_leaves(v, path)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    ip = f"{path}[{i}]"
                    if isinstance(item, str):
                        yield ip, item, None, None  # list string leaves: skip mutate
                    elif is_entry(item):
                        yield ip, item, None, None
                    elif isinstance(item, dict):
                        yield from walk_leaves(item, ip)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            ip = f"{prefix}[{i}]" if prefix else f"[{i}]"
            if isinstance(item, str):
                yield ip, item, None, None
            elif isinstance(item, dict):
                yield from walk_leaves(item, ip)


def migrate_node(node: Any) -> Tuple[Any, int]:
    """Convert bare string leaves to {text, source_sha256: ''}. Returns (node, count)."""
    changed = 0
    if isinstance(node, dict):
        if is_entry(node):
            if "source_sha256" not in node:
                node["source_sha256"] = ""
                changed += 1
            return node, changed
        out: Dict[str, Any] = {}
        for k, v in node.items():
            if isinstance(v, str):
                out[k] = {"text": v, "source_sha256": ""}
                changed += 1
            elif isinstance(v, dict):
                nv, c = migrate_node(v)
                out[k] = nv
                changed += c
            elif isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, str):
                        new_list.append({"text": item, "source_sha256": ""})
                        changed += 1
                    elif isinstance(item, (dict, list)):
                        ni, c = migrate_node(item)
                        new_list.append(ni)
                        changed += c
                    else:
                        new_list.append(item)
                out[k] = new_list
            else:
                out[k] = v
        return out, changed
    if isinstance(node, list):
        new_list = []
        for item in node:
            ni, c = migrate_node(item)
            new_list.append(ni)
            changed += c
        return new_list, changed
    return node, changed


def flatten_entries(node: Any, prefix: str = "") -> Dict[str, Dict[str, Any]]:
    """Map key_path -> entry dict {text, source_sha256, ...}."""
    result: Dict[str, Dict[str, Any]] = {}
    if isinstance(node, dict):
        if is_entry(node):
            return {prefix: node} if prefix else {}
        for k, v in node.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str):
                # legacy bare — treat as entry without hash
                result[path] = {"text": v, "source_sha256": ""}
            elif is_entry(v):
                result[path] = v
            elif isinstance(v, dict):
                result.update(flatten_entries(v, path))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    ip = f"{path}[{i}]"
                    if isinstance(item, str):
                        result[ip] = {"text": item, "source_sha256": ""}
                    elif is_entry(item):
                        result[ip] = item
                    elif isinstance(item, dict):
                        result.update(flatten_entries(item, ip))
    return result


def apply_hashes_to_en(node: Any) -> int:
    """Set source_sha256 on every entry from its text. Returns count updated."""
    count = 0
    if isinstance(node, dict):
        if is_entry(node) or ("text" in node and isinstance(node.get("text"), str)):
            h = source_sha256(node["text"])
            if node.get("source_sha256") != h:
                node["source_sha256"] = h
                count += 1
            return count
        for v in node.values():
            if isinstance(v, (dict, list)):
                count += apply_hashes_to_en(v)
    elif isinstance(node, list):
        for item in node:
            if isinstance(item, (dict, list)):
                count += apply_hashes_to_en(item)
    return count


def stamp_from_en(node: Any, en_map: Dict[str, Dict[str, Any]], prefix: str = "") -> Tuple[int, int]:
    """Copy source_sha256 from en for matching keys. Returns (stamped, stale_left)."""
    stamped = 0
    stale = 0
    if isinstance(node, dict):
        if "text" in node and isinstance(node.get("text"), str) and (
            is_entry(node) or "source_sha256" in node or set(node.keys()) <= ENTRY_KEYS
        ):
            # leaf entry at this prefix — handled by parent
            return 0, 0
        for k, v in node.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict) and "text" in v and isinstance(v.get("text"), str):
                en_e = en_map.get(path)
                if en_e is not None:
                    en_hash = en_e.get("source_sha256") or source_sha256(en_e["text"])
                    if v.get("source_sha256") != en_hash:
                        # Keep translation text; stamp current en hash only in hash/migrate
                        # For mark-stale we do NOT overwrite — leave mismatch.
                        pass
                    # During migrate after en hashed: stamp matching translations
                    if not v.get("source_sha256"):
                        v["source_sha256"] = en_hash
                        stamped += 1
                    elif v.get("source_sha256") != en_hash:
                        stale += 1
                else:
                    stale += 0
            elif isinstance(v, (dict, list)):
                s, t = stamp_from_en(v, en_map, path)
                stamped += s
                stale += t
    elif isinstance(node, list):
        for i, item in enumerate(node):
            ip = f"{prefix}[{i}]" if prefix else f"[{i}]"
            if isinstance(item, (dict, list)):
                s, t = stamp_from_en(item, en_map, ip)
                stamped += s
                stale += t
    return stamped, stale


def restamp_current(node: Any, en_map: Dict[str, Dict[str, Any]], prefix: str = "") -> int:
    """Force source_sha256 = current en hash for every key present in both (translator restamp)."""
    n = 0
    if isinstance(node, dict):
        for k, v in node.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict) and "text" in v and isinstance(v.get("text"), str):
                en_e = en_map.get(path)
                if en_e is not None:
                    h = en_e.get("source_sha256") or source_sha256(en_e["text"])
                    if v.get("source_sha256") != h:
                        v["source_sha256"] = h
                        n += 1
            elif isinstance(v, (dict, list)):
                n += restamp_current(v, en_map, path)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            ip = f"{prefix}[{i}]" if prefix else f"[{i}]"
            if isinstance(item, (dict, list)):
                n += restamp_current(item, en_map, ip)
    return n


def load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def catalog_trees(root: Path) -> List[Tuple[str, Path]]:
    """Return (area_name, path) for each tag directory under known trees."""
    trees = [
        ("locales", root / "content" / "locales"),
        ("locales-ui", root / "content" / "locales-ui"),
        ("i18n-native-gui", root / "content" / "i18n-native" / "gui"),
        (
            "i18n-native-agent",
            root / "content" / "i18n-native" / "apps" / "pim-offline-agent",
        ),
        (
            "i18n-native-recording",
            root / "content" / "i18n-native" / "apps" / "pim-offline-recording-agent",
        ),
        (
            "i18n-native-server-app",
            root / "content" / "i18n-native" / "apps" / "pim-offline-server",
        ),
    ]
    return [(n, p) for n, p in trees if p.is_dir()]


def iter_tag_json_files(tag_dir: Path) -> Iterable[Path]:
    if not tag_dir.is_dir():
        return []
    return sorted(tag_dir.glob("*.json"))


def list_tags(tree: Path) -> List[str]:
    if not tree.is_dir():
        return []
    return sorted(
        p.name for p in tree.iterdir() if p.is_dir() and not p.name.startswith("_")
    )


def placeholders(text: str) -> List[str]:
    return PLACEHOLDER_RE.findall(text)


def cmd_migrate(root: Path) -> int:
    total = 0
    files = 0
    for _area, tree in catalog_trees(root):
        for tag in list_tags(tree):
            for path in iter_tag_json_files(tree / tag):
                data = load_json(path)
                data, n = migrate_node(data)
                if n:
                    dump_json(path, data)
                    total += n
                    files += 1
                    print(f"migrate {path.relative_to(root)}: {n} leaves")
    print(f"migrate complete: {total} leaves in {files} files")
    return 0


def cmd_hash(root: Path) -> int:
    """Migrate if needed, hash all en entries, stamp empty hashes on other tags from en."""
    cmd_migrate(root)
    updated = 0
    for _area, tree in catalog_trees(root):
        en_dir = tree / "en"
        if not en_dir.is_dir():
            continue
        en_by_file: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for path in iter_tag_json_files(en_dir):
            data = load_json(path)
            n = apply_hashes_to_en(data)
            dump_json(path, data)
            updated += n
            en_by_file[path.name] = flatten_entries(data)
            print(f"hash en {path.relative_to(root)}: {n} updated")
        for tag in list_tags(tree):
            if tag == "en":
                continue
            for path in iter_tag_json_files(tree / tag):
                en_map = en_by_file.get(path.name)
                if not en_map:
                    continue
                data = load_json(path)
                # Only fill empty source_sha256 from en (do not clear stale)
                stamped = 0

                def fill_empty(node: Any, prefix: str = "") -> None:
                    nonlocal stamped
                    if isinstance(node, dict):
                        for k, v in list(node.items()):
                            path_k = f"{prefix}.{k}" if prefix else k
                            if (
                                isinstance(v, dict)
                                and "text" in v
                                and isinstance(v.get("text"), str)
                            ):
                                if not v.get("source_sha256"):
                                    en_e = en_map.get(path_k)
                                    if en_e is not None:
                                        v["source_sha256"] = en_e.get(
                                            "source_sha256"
                                        ) or source_sha256(en_e["text"])
                                        stamped += 1
                            elif isinstance(v, (dict, list)):
                                fill_empty(v, path_k)
                    elif isinstance(node, list):
                        for i, item in enumerate(node):
                            if isinstance(item, (dict, list)):
                                fill_empty(
                                    item, f"{prefix}[{i}]" if prefix else f"[{i}]"
                                )

                fill_empty(data)
                if stamped:
                    dump_json(path, data)
                    print(
                        f"stamp {path.relative_to(root)}: {stamped} empty hashes filled"
                    )
    print(f"hash complete: {updated} en entries recomputed")
    return 0


def cmd_mark_stale(root: Path) -> int:
    """Report stale keys; does not rewrite translation text. Exit 1 if any stale."""
    report = audit_product(root, product="aic-server", include_native=True)
    stale_total = sum(t["stale"] for t in report["tags"].values())
    print(json.dumps({"stale_total": stale_total, "tags": report["tags"]}, indent=2))
    return 1 if stale_total else 0


def audit_product(
    root: Path, product: str = "aic-server", include_native: bool = False
) -> Dict[str, Any]:
    areas: List[Tuple[str, Path]] = []
    if product == "aic-server":
        areas = [
            ("locales", root / "content" / "locales"),
            ("locales-ui", root / "content" / "locales-ui"),
        ]
    elif product == "shared-gui-chrome":
        areas = [("gui", root / "content" / "i18n-native" / "gui")]
    elif product == "aic-agent":
        areas = [
            (
                "agent",
                root / "content" / "i18n-native" / "apps" / "pim-offline-agent",
            )
        ]
    elif product == "aic-recording-agent":
        areas = [
            (
                "recording",
                root
                / "content"
                / "i18n-native"
                / "apps"
                / "pim-offline-recording-agent",
            )
        ]
    elif product == "all":
        areas = catalog_trees(root)
    else:
        areas = [
            ("locales", root / "content" / "locales"),
            ("locales-ui", root / "content" / "locales-ui"),
        ]
        if include_native:
            areas.extend(
                [
                    a
                    for a in catalog_trees(root)
                    if a[0] not in ("locales", "locales-ui")
                ]
            )

    en_keys: Dict[str, Dict[str, Any]] = {}
    # relative key: area/file/path
    for area_name, tree in areas:
        if not tree.is_dir():
            continue
        en_dir = tree / "en"
        if not en_dir.is_dir():
            continue
        for path in iter_tag_json_files(en_dir):
            data = load_json(path)
            flat = flatten_entries(data)
            for k, entry in flat.items():
                en_keys[f"{area_name}/{path.name}/{k}"] = entry

    tags: Dict[str, Any] = {}
    all_tags = set()
    for _area_name, tree in areas:
        if tree.is_dir():
            all_tags.update(list_tags(tree))
    all_tags.discard("en")

    for tag in sorted(all_tags):
        missing: List[str] = []
        stale: List[str] = []
        orphan: List[str] = []
        placeholder_broken: List[str] = []
        present = 0
        tag_keys: Dict[str, Dict[str, Any]] = {}
        for area_name, tree in areas:
            tag_dir = tree / tag
            if not tag_dir.is_dir():
                continue
            for path in iter_tag_json_files(tag_dir):
                data = load_json(path)
                flat = flatten_entries(data)
                for k, entry in flat.items():
                    full = f"{area_name}/{path.name}/{k}"
                    tag_keys[full] = entry

        for full, en_e in en_keys.items():
            te = tag_keys.get(full)
            if te is None:
                missing.append(full)
                continue
            present += 1
            en_hash = en_e.get("source_sha256") or source_sha256(en_e.get("text", ""))
            th = te.get("source_sha256") or ""
            if th and th != en_hash:
                stale.append(full)
            elif not th:
                stale.append(full)  # unhashed translation counts as needs restamp
            en_ph = placeholders(en_e.get("text", ""))
            tg_ph = placeholders(te.get("text", ""))
            if sorted(en_ph) != sorted(tg_ph):
                placeholder_broken.append(full)

        for full in tag_keys:
            if full not in en_keys:
                orphan.append(full)

        tags[tag] = {
            "present": present,
            "en_total": len(en_keys),
            "missing": len(missing),
            "stale": len(stale),
            "orphan": len(orphan),
            "placeholder_broken": len(placeholder_broken),
            "missing_sample": missing[:20],
            "stale_sample": stale[:20],
            "orphan_sample": orphan[:20],
        }

    return {
        "product": product,
        "en_total": len(en_keys),
        "tags": tags,
    }


def cmd_audit(root: Path, product: str, out: Optional[Path]) -> int:
    report = audit_product(root, product=product, include_native=(product == "all"))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {out}")
    print(text)
    # Exit 0 always for reporting; callers decide gates
    return 0


def _add_root(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/)",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AIC language pack tools (stdlib only)")
    _add_root(p)
    sub = p.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("migrate", "Convert bare string leaves to entry objects"),
        ("hash", "Recompute en source_sha256; fill empty hashes elsewhere"),
        ("mark-stale", "Exit 1 if any non-en key hash mismatches en"),
    ):
        sp = sub.add_parser(name, help=help_text)
        _add_root(sp)

    ap = sub.add_parser("audit", help="Missing / stale / orphan / placeholder report")
    _add_root(ap)
    ap.add_argument("--product", default="aic-server", help="Product id or 'all'")
    ap.add_argument("--out", type=Path, default=None, help="Write JSON report path")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root_from(args.root)
    if not (root / "content").is_dir():
        print(f"error: content/ not found under {root}", file=sys.stderr)
        return 2
    if args.command == "migrate":
        return cmd_migrate(root)
    if args.command == "hash":
        return cmd_hash(root)
    if args.command == "mark-stale":
        return cmd_mark_stale(root)
    if args.command == "audit":
        return cmd_audit(root, args.product, args.out)
    print(f"unknown command {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
