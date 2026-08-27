#!/usr/bin/env python3
"""Unit tests: canonical Cargo.lock digest ignores [[patch.unused]] reorder."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from cargo_lock_canonical_digest import (  # noqa: E402
    cargo_lock_canonical_payload,
    cargo_lock_canonical_sha256,
)

LOCK_A = """# cargo lock
version = 4

[[package]]
name = "zeta"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "aaaa"

[[package]]
name = "alpha"
version = "2.0.0"
source = "git+https://github.com/example/alpha#deadbeef"
checksum = "bbbb"

[[package]]
name = "path-only"
version = "0.1.0"

[[patch.unused]]
name = "pim-orm"
version = "0.3.17"

[[patch.unused]]
name = "pim-orm-events"
version = "0.1.21"
"""

LOCK_B_REORDERED_UNUSED = """# cargo lock
version = 4

[[package]]
name = "zeta"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "aaaa"

[[package]]
name = "alpha"
version = "2.0.0"
source = "git+https://github.com/example/alpha#deadbeef"
checksum = "bbbb"

[[package]]
name = "path-only"
version = "0.1.0"

[[patch.unused]]
name = "pim-orm-events"
version = "0.1.21"

[[patch.unused]]
name = "pim-orm"
version = "0.3.17"

[[patch.unused]]
name = "pim-orm"
version = "0.3.17"
"""

LOCK_C_VERSION_BUMP = LOCK_A.replace(
    'name = "zeta"\nversion = "1.0.0"',
    'name = "zeta"\nversion = "1.0.1"',
)

LOCK_D_NO_UNUSED = """# cargo lock
version = 4

[[package]]
name = "zeta"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "aaaa"

[[package]]
name = "alpha"
version = "2.0.0"
source = "git+https://github.com/example/alpha#deadbeef"
checksum = "bbbb"

[[package]]
name = "path-only"
version = "0.1.0"
"""


class CanonicalDigestTests(unittest.TestCase):
    def test_payload_is_sorted_and_tab_separated(self) -> None:
        payload = cargo_lock_canonical_payload(LOCK_A)
        lines = [ln for ln in payload.split("\n") if ln]
        self.assertEqual(len(lines), 3)
        self.assertTrue(payload.endswith("\n"))
        self.assertEqual(
            lines[0],
            "alpha\t2.0.0\tgit+https://github.com/example/alpha#deadbeef\tbbbb",
        )
        self.assertEqual(lines[1], "path-only\t0.1.0\t\t")
        self.assertEqual(
            lines[2],
            "zeta\t1.0.0\tregistry+https://github.com/rust-lang/crates.io-index\taaaa",
        )

    def test_patch_unused_reorder_and_dupes_do_not_change_digest(self) -> None:
        a = cargo_lock_canonical_sha256(LOCK_A)
        b = cargo_lock_canonical_sha256(LOCK_B_REORDERED_UNUSED)
        d = cargo_lock_canonical_sha256(LOCK_D_NO_UNUSED)
        self.assertEqual(a, b)
        self.assertEqual(a, d)
        self.assertEqual(len(a), 64)

    def test_real_package_version_change_invalidates(self) -> None:
        a = cargo_lock_canonical_sha256(LOCK_A)
        c = cargo_lock_canonical_sha256(LOCK_C_VERSION_BUMP)
        self.assertNotEqual(a, c)

    def test_checksum_change_invalidates(self) -> None:
        changed = LOCK_A.replace("checksum = \"aaaa\"", "checksum = \"cccc\"")
        self.assertNotEqual(
            cargo_lock_canonical_sha256(LOCK_A),
            cargo_lock_canonical_sha256(changed),
        )

    def test_source_change_invalidates(self) -> None:
        changed = LOCK_A.replace(
            "registry+https://github.com/rust-lang/crates.io-index",
            "registry+https://example.invalid/index",
        )
        self.assertNotEqual(
            cargo_lock_canonical_sha256(LOCK_A),
            cargo_lock_canonical_sha256(changed),
        )

    def test_added_package_invalidates(self) -> None:
        added = LOCK_D_NO_UNUSED + "\n[[package]]\nname = \"new\"\nversion = \"0.0.1\"\n"
        self.assertNotEqual(
            cargo_lock_canonical_sha256(LOCK_D_NO_UNUSED),
            cargo_lock_canonical_sha256(added),
        )


if __name__ == "__main__":
    unittest.main()
