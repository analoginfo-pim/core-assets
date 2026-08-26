#!/usr/bin/env python3
"""Make core-assets a true superset of the consumer catalog, then heal the consumer.

core-assets is the declared source of truth and scripts/sync-to-projects.ps1
overwrites the consumer tree wholesale. That contract only holds if core-assets
actually contains everything the consumer has. It does not. A single forward
sync removed 5947 leaves from pim-offline-server/ui/src/i18n/locales -- 831
distinct keys, 573 of which the UI code still calls.

Nothing caught it, twice, for the same two reasons:

  - i18next falls back to the defaultValue in the code, so en kept rendering
    correct English and no missing-string banner appeared.
  - The parity gate's Check 2 asserts en is a subset of each tag. When a key
    leaves en as well, the subset still holds and the gate stays green.

So the failure is silent by construction, and what it destroys is the
translation. A German operator reads English on the affected pages while every
automated check reports success.

Recovery reads the pre-sync commit rather than the code, because git holds the
reviewed de / fr / es / zh / ja / ko / ar text. Re-deriving from defaultValue
would replace seventeen packs of reviewed translation with English and report it
as a fix.

Direction of authority on conflict: core-assets wins. A leaf present in both is
left alone, because the same sync that deleted these also delivered genuine
fixes -- the restored English catalog, the re-derived en-GB, the German-leak
repairs -- and those must survive. The consumer only supplies keys core-assets
does not have.

Both sides are written, and that is the point. Healing the consumer alone leaves
the same keys missing upstream, so the next sync deletes them again. Back-porting
is what ends the cycle.

Usage:
    python _recover_synced_away_leaves.py [--ref HEAD] [--namespace NS] [--fix]
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
SERVER = CORE.parent / "pim-offline-server"
CATALOG = CORE / "content" / "locales-ui"
SERVER_LOCALES = Path("ui/src/i18n/locales")


def git_show(ref: str, rel: str) -> dict | None:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"], cwd=SERVER, capture_output=True
    )
    if proc.returncode != 0:
        return None
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(proc.stdout.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def write_json(path: Path, data) -> None:
    """Write with a short retry.

    This run rewrites a couple of hundred JSON files back to back, and Windows
    Defender scanning one of them mid-write surfaces as OSError EINVAL rather
    than a sharing violation. Failing the whole run on that leaves the tree
    half-recovered, which is worse than either outcome. The merge only adds
    absent keys, so retrying -- or re-running the script -- is idempotent.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for attempt in range(5):
        try:
            path.write_text(body, encoding="utf-8")
            return
        except OSError as err:
            if attempt == 4:
                raise
            print(f"  retry {path.name} after {err.__class__.__name__}: {err}")
            time.sleep(0.4 * (attempt + 1))


def leaf_paths(node, prefix=()):
    """Yield tuple paths to leaves. A leaf is a string, or {text, source_sha256}."""
    if isinstance(node, str):
        yield prefix
        return
    if isinstance(node, dict):
        if isinstance(node.get("text"), str) and set(node) <= {"text", "source_sha256"}:
            yield prefix
            return
        for name, child in node.items():
            yield from leaf_paths(child, prefix + (name,))
        return
    if isinstance(node, list):
        for index, child in enumerate(node):
            yield from leaf_paths(child, prefix + (index,))


def is_leaf(node) -> bool:
    if isinstance(node, str):
        return True
    return (
        isinstance(node, dict)
        and isinstance(node.get("text"), str)
        and set(node) <= {"text", "source_sha256"}
    )


def merge(dst, src, added: list[tuple], conflicts: list[str], trail=()) -> None:
    """Copy anything src has that dst lacks. dst always wins where both hold a value.

    Merging structurally rather than leaf by leaf is what makes list-valued
    bullets recoverable. Those keys are absent from the destination *entirely* --
    node, list, and elements -- so there is no list to index into and a
    leaf-path insert can only refuse. Copying the whole missing subtree brings
    the list with it.
    """
    if isinstance(dst, dict) and isinstance(src, dict):
        for name, child in src.items():
            if name not in dst:
                dst[name] = copy.deepcopy(child)
                for path in leaf_paths(child, trail + (name,)):
                    added.append(path)
            elif not is_leaf(dst[name]):
                merge(dst[name], child, added, conflicts, trail + (name,))
        return

    if isinstance(dst, list) and isinstance(src, list):
        # Positional merge is only meaningful when the two lists describe the
        # same sequence. Different lengths means the arrays were authored
        # independently, and guessing an alignment would silently mistranslate.
        if len(dst) != len(src):
            conflicts.append(
                f"{'.'.join(map(str, trail))}: list length {len(dst)} vs {len(src)}"
            )
            return
        for index, (left, right) in enumerate(zip(dst, src)):
            if not is_leaf(left):
                merge(left, right, added, conflicts, trail + (index,))
        return

    conflicts.append(f"{'.'.join(map(str, trail))}: shape mismatch")


def main() -> int:
    argv = sys.argv[1:]
    write = "--fix" in argv
    ref = argv[argv.index("--ref") + 1] if "--ref" in argv else "HEAD"
    only_ns = argv[argv.index("--namespace") + 1] if "--namespace" in argv else None

    server_root = SERVER / SERVER_LOCALES
    if not server_root.is_dir():
        print(f"no consumer locales at {server_root}", file=sys.stderr)
        return 2

    healed = 0
    ported = 0
    refusals: list[str] = []
    per_tag: Counter[str] = Counter()
    distinct: set[tuple[str, tuple]] = set()

    for tag_dir in sorted(p for p in server_root.iterdir() if p.is_dir()):
        tag = tag_dir.name
        for path in sorted(tag_dir.glob("*.json")):
            namespace = path.stem
            if only_ns and namespace != only_ns:
                continue

            rel = (SERVER_LOCALES / tag / path.name).as_posix()
            old = git_show(ref, rel)
            if old is None:
                continue
            current = read_json(path)
            if current is None:
                refusals.append(f"{tag}/{namespace}: cannot read working tree")
                continue

            if not set(leaf_paths(old)) - set(leaf_paths(current)):
                continue

            # Heal the consumer so the running product regains the translation.
            added: list[tuple] = []
            conflicts: list[str] = []
            merge(current, old, added, conflicts)
            for line in conflicts:
                refusals.append(f"{tag}/{namespace} {line}")
            for leaf in added:
                distinct.add((namespace, leaf))
            per_tag[tag] += len(added)
            healed += len(added)
            if write and added:
                write_json(path, current)

            # Back-port so the next sync stops deleting them. Without this half
            # the recovery is undone the next time the sync runs.
            core_path = CATALOG / tag / f"{namespace}.json"
            core = read_json(core_path)
            if core is None:
                refusals.append(f"{tag}/{namespace}: no core-assets file to back-port into")
                continue
            back: list[tuple] = []
            merge(core, old, back, [])
            ported += len(back)
            if write and back:
                write_json(core_path, core)

    verb = "restored" if write else "would be restored"
    print(f"{healed} consumer leaf/leaves {verb}; {ported} back-ported to core-assets\n")
    for tag, count in per_tag.most_common():
        print(f"  {count:5d}  {tag}")

    if distinct:
        groups: Counter[str] = Counter()
        for namespace, leaf in distinct:
            groups[f"{namespace}:{'.'.join(map(str, leaf[:2]))}"] += 1
        print(f"\n{len(distinct)} distinct key(s), top groups:")
        for head, count in groups.most_common(15):
            print(f"  {count:5d}  {head}")

    if refusals:
        print(f"\n{len(refusals)} refusal(s):")
        for line in refusals[:40]:
            print(f"  {line}")
        if len(refusals) > 40:
            print(f"  ... +{len(refusals) - 40} more")

    if not write:
        print("\n(report only; pass --fix to heal the consumer and back-port)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
