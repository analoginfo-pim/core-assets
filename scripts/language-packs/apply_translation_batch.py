#!/usr/bin/env python3
"""Apply a reviewed translation batch to the canonical language packs.

`language_packs.py` migrates, hashes, and audits packs that already exist; it has
no command that introduces a new leaf or repairs a wrong-language value. Ad-hoc
scripts filled that gap and stamped `source_sha256` over their own output, which
made `mark-stale` report every touched leaf and turned the drift gate into noise.

This applier is the supported path instead. It imports `source_sha256`,
`load_json`, and `dump_json` from `language_packs` so hashing and byte
formatting cannot diverge from the canonical tool, and it always stamps the hash
of the ENGLISH source text -- never of the translation it just wrote.

Batch file shape:

    {
      "area": "locales-ui",          # subtree under content/
      "namespace": "nav",            # <tag>/<namespace>.json
      "source": { "<key>": "English source text", ... },
      "translations": { "<tag>": { "<key>": "translated text", ... }, ... },
      "delete_keys": { "<tag>": ["<key>", ...] }   # optional
    }

Keys may be dotted paths. `nav` packs are flat maps, but `pages`, `dashboard`,
and the rest nest under `chrome.<page>.<field>`, and i18next resolves a dotted key
by descending that tree. Writing `data["chrome.foo.bar"]` in a nested pack creates
a sibling the runtime never reads while leaving the real leaf untouched -- a repair
that silently does nothing. Every read, write, and delete therefore goes through
`resolve_path`, which walks the existing shape and only falls back to a flat key
when the pack has no matching tree.

Modes:
  --add-missing   write only keys absent from a pack (default)
  --overwrite     also replace the text of keys already present
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from language_packs import dump_json, load_json, source_sha256  # noqa: E402

# content/<area>/<tag>/<namespace>.json
AREAS = {"locales", "locales-ui"}


def resolve_path(
    data: dict, key: str, *, create: bool
) -> tuple[dict | None, str, bool] | None:
    """Locate `key` in `data`, honoring the pack's flat-or-nested shape.

    Returns `(container, leaf_key, existed)`, or None when the path cannot be
    resolved. A literal flat key wins when present, so a pack that genuinely
    stores dots in its key names keeps working. Otherwise the dotted path is
    walked. With `create=False` a missing path resolves to the container it would
    live in when that container already exists, so callers can report "absent"
    without mutating the tree.
    """
    if key in data:
        return data, key, True
    if "." not in key:
        return (data, key, False) if create else (data, key, False)

    *parents, leaf = key.split(".")
    node = data
    for i, segment in enumerate(parents):
        child = node.get(segment)
        if child is None:
            if not create:
                return None
            # Only build a subtree when the pack is already nested at this level;
            # inventing one in a flat pack would be the mirror of the bug above.
            if i == 0 and not any(isinstance(v, dict) and "text" not in v for v in data.values()):
                return data, key, False
            child = {}
            node[segment] = child
        if not isinstance(child, dict) or "text" in child:
            # A leaf sits where an intermediate node is required: the batch key and
            # the pack shape disagree, and guessing would corrupt the pack.
            return None
        node = child
    return node, leaf, leaf in node


def apply_batch(root: Path, batch: dict, overwrite: bool, dry_run: bool) -> int:
    area = batch["area"]
    if area not in AREAS:
        print(f"error: unsupported area {area!r}; expected one of {sorted(AREAS)}")
        return 2

    namespace = batch["namespace"]
    english = batch["source"]
    translations = batch.get("translations", {})
    deletions = batch.get("delete_keys", {})

    base = root / "content" / area
    if not base.is_dir():
        print(f"error: {base} is not a directory")
        return 2

    # Hash of the English source is the single value stamped into every pack,
    # so `mark-stale` compares like with like and only fires on real en drift.
    hashes = {key: source_sha256(text) for key, text in english.items()}

    # English is a pack like any other; it needs the leaf too. QuickActionCardTile
    # masks a missing en leaf with defaultValue, which is exactly why these holes
    # survived an English-only crawl.
    per_tag = {"en": english}
    for tag, mapping in translations.items():
        if tag == "en":
            print("error: put English text in 'source', not in 'translations.en'")
            return 2
        per_tag[tag] = mapping

    added = replaced = removed = skipped_untranslated = 0
    touched: list[str] = []

    for tag in sorted(set(per_tag) | set(deletions)):
        path = base / tag / f"{namespace}.json"
        if not path.is_file():
            print(f"skip {tag}/{namespace}.json (absent)")
            continue

        data = load_json(path)
        if not isinstance(data, dict):
            print(f"error: {path} is not a JSON object")
            return 2

        before = json.dumps(data, ensure_ascii=False, sort_keys=True)

        for key in deletions.get(tag, []):
            found = resolve_path(data, key, create=False)
            if found is None:
                continue
            container, leaf_key, existed = found
            if existed:
                del container[leaf_key]
                removed += 1

        for key, text in per_tag.get(tag, {}).items():
            if key not in english:
                print(f"error: {tag}.{key} has no English source entry")
                return 2
            if not text or not text.strip():
                skipped_untranslated += 1
                continue
            found = resolve_path(data, key, create=True)
            if found is None:
                print(
                    f"error: {tag}/{namespace}.json shape conflicts with key {key!r}; "
                    "a leaf occupies a path segment"
                )
                return 2
            container, leaf_key, existed = found
            leaf = {"text": text, "source_sha256": hashes[key]}
            if not existed:
                container[leaf_key] = leaf
                added += 1
            elif overwrite:
                existing = container[leaf_key]
                existing_text = (
                    existing.get("text") if isinstance(existing, dict) else existing
                )
                if existing_text != text or (
                    isinstance(existing, dict)
                    and existing.get("source_sha256") != hashes[key]
                ):
                    container[leaf_key] = leaf
                    replaced += 1

        after = json.dumps(data, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue

        touched.append(f"{tag}/{namespace}.json")
        if not dry_run:
            # Sorting a flat pack keeps the diff reviewable. A nested pack is left in
            # place: reordering its top level would bury the two-line repair under a
            # whole-file reshuffle. dump_json owns indent / ensure_ascii / newline so
            # packs stay byte-consistent either way.
            flat = all(
                isinstance(v, dict) and "text" in v for v in data.values()
            )
            dump_json(path, dict(sorted(data.items())) if flat else data)

    verb = "would apply" if dry_run else "applied"
    print(
        f"{verb}: +{added} added, ~{replaced} replaced, -{removed} removed "
        f"across {len(touched)} file(s)"
    )
    if skipped_untranslated:
        print(f"skipped {skipped_untranslated} empty translation value(s)")
    for name in touched:
        print(f"  {name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="Path to the batch JSON file")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="core-assets repo root",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace text of keys already present (wrong-language repair)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    return apply_batch(args.root, batch, args.overwrite, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
