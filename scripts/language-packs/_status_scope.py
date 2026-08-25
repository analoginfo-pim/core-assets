#!/usr/bin/env python3
"""Ask whether the dirty tree contains anything that is not this session's work.

The tree is shared. Staging by `git status` is how one agent's unfinished edits
end up inside another agent's commit, attributed to a subject line that has
nothing to do with them -- and in a FedRAMP audit trail that misattribution is
the defect, not the extra file. So the question before staging is not "what
changed" but "what changed that is mine".

Groups the dirty paths by top-level area and separately lists anything outside
the localization paths this session touched, so a foreign edit is visible as a
foreign edit rather than as one more line in a 300-file status wall.
"""

from __future__ import annotations

import collections
import subprocess

MINE = (
    "content/locales",
    "content/locales-ui",
    "content/language-packs",
    "scripts/language-packs",
)


def main() -> int:
    out = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, check=True
    ).stdout.decode("utf-8", errors="replace")
    areas: collections.Counter[str] = collections.Counter()
    foreign: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        state, path = line[:2], line[3:].strip().strip('"')
        areas["/".join(path.split("/")[:2])] += 1
        if not any(path.startswith(prefix) for prefix in MINE):
            foreign.append((state, path))
    for area, count in areas.most_common(24):
        print(f"{count:5}  {area}")
    print()
    print(f"outside localization paths: {len(foreign)}")
    for state, path in foreign[:40]:
        print(f"   {state} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
