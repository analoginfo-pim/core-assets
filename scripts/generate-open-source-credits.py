#!/usr/bin/env python3
"""Generate AIC Server Open Source Credits inventory (complete disclosure).

Enumerates every third-party package in the AIC Server production graphs:
  - Cargo.lock registry + git crates (path/first-party workspace crates excluded)
  - npm package-lock.json production packages (@analoginfo-pim/* first-party excluded)
  - Incorporated assets (flag-icons, known-default credential data licenses)

Harvests license bodies from the local Cargo registry / git checkouts,
node_modules LICENSE files, and in-tree LICENSE copies. Falls back to
stored standard SPDX texts only when package metadata names a known SPDX
id and no package-local LICENSE file is present. Never invents packages
or licenses. Packages without a license identity and text are listed as
BLOCKED (not omitted).

Status is Live only when every entry has license identity + text.

Usage (from core-assets repo root):
  python scripts/generate-open-source-credits.py
  python scripts/generate-open-source-credits.py --require-live

`--require-live` exits non-zero when any third-party entry is BLOCKED so
deploy / MSI / build.rs fail closed (never ship an incomplete disclosure).

`generation.cargo_lock_sha256` is the canonical `[[package]]` identity
digest (name, version, source, checksum), not raw Cargo.lock bytes.
`[[patch.unused]]` is excluded. See `cargo_lock_canonical_digest.py`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from cargo_lock_canonical_digest import cargo_lock_canonical_sha256_file

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SERVER = WORKSPACE / "pim-offline-server"
UI = SERVER / "ui"
OUT = ROOT / "legal" / "open-source-credits"
LICENSES_DIR = OUT / "license-texts"
HARVESTED_DIR = LICENSES_DIR / "by-sha256"

SPDX_TEMPLATES: dict[str, str] = {
    "MIT": "MIT.txt",
    "Apache-2.0": "Apache-2.0.txt",
    "BSD-2-Clause": "BSD-2-Clause.txt",
    "BSD-3-Clause": "BSD-3-Clause.txt",
    "ISC": "ISC.txt",
    "MPL-2.0": "MPL-2.0.txt",
    "0BSD": "0BSD.txt",
    "CC0-1.0": "CC0-1.0.txt",
    "Unlicense": "Unlicense.txt",
    "Zlib": "Zlib.txt",
    "BlueOak-1.0.0": "BlueOak-1.0.0.txt",
    "Unicode-3.0": "Unicode-3.0.txt",
    "Unicode-DFS-2016": "Unicode-DFS-2016.txt",
}

LICENSE_FILE_NAMES = (
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "LICENSE.rst",
    "LICENCE",
    "LICENCE.txt",
    "COPYING",
    "COPYING.txt",
    "LICENSE-MIT",
    "LICENSE-APACHE",
    "LICENSE-Apache-2.0",
    "LICENSE.MIT",
    "LICENSE.APACHE",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_license_body(body: str) -> tuple[str, str]:
    """Write unique body under license-texts/by-sha256/<sha>.txt; return (rel, sha)."""
    normalized = body.replace("\r\n", "\n").rstrip() + "\n"
    digest = sha256_text(normalized)
    HARVESTED_DIR.mkdir(parents=True, exist_ok=True)
    rel = f"license-texts/by-sha256/{digest}.txt"
    path = OUT / rel
    expected = normalized.encode("utf-8")
    # Always persist LF bytes (write_bytes). Never leave a CRLF working-tree
    # copy that would invalidate license_text_sha256 after git checkout.
    if not path.is_file() or path.read_bytes() != expected:
        path.write_bytes(expected)
    return rel, digest


def is_pointer_only_license_body(body: str) -> bool:
    """True when the body is a short pointer, not a redistributable grant text."""
    t = body.strip()
    if not t:
        return True
    if "Full published text:" in t and len(t) < 500:
        return True
    # Common Rust COPYING stubs that only name LICENSE-APACHE / LICENSE-MIT.
    if len(t) < 500 and "LICENSE-APACHE" in t and "LICENSE-MIT" in t:
        return True
    if len(t) < 200 and re.search(r"see\s+(the\s+)?license", t, re.I):
        return True
    return False


def spdx_tokens(expr: str) -> list[str]:
    parts = re.split(r"\s+(?:OR|AND|WITH)\s+", expr.strip(), flags=re.I)
    return [p.strip("() ").strip() for p in parts if p.strip("() ").strip()]


def combine_standard_spdx_bodies(expr: str, license_map: dict[str, str]) -> str | None:
    """Concatenate stored published texts for every SPDX token that we have."""
    bodies: list[str] = []
    for tok in spdx_tokens(expr):
        rel = license_map.get(tok)
        if not rel:
            continue
        path = OUT / rel
        if not path.is_file() or path.stat().st_size < 80:
            continue
        std = path.read_text(encoding="utf-8")
        if is_pointer_only_license_body(std):
            continue
        bodies.append(f"--- {tok} ---\n{std.rstrip()}")
    if not bodies:
        return None
    return "\n\n".join(bodies) + "\n"


def is_commercial_npm_package(name: str, license_raw: str | None) -> bool:
    """MUI X Pro/Premium and similar proprietary packages (not redistributable OSS)."""
    n = (name or "").lower()
    if n.startswith(
        (
            "@mui/x-data-grid-pro",
            "@mui/x-data-grid-premium",
            "@mui/x-date-pickers-pro",
            "@mui/x-charts-pro",
            "@mui/x-tree-view-pro",
            "@mui/x-license",
            "@mui/x-telemetry",
        )
    ):
        return True
    lic = (license_raw or "").strip().upper()
    if lic.startswith("SEE LICENSE"):
        return True
    if lic in {"PROPRIETARY", "COMMERCIAL", "UNLICENSED"}:
        return True
    return False


def reconcile_spdx_with_harvested_body(spdx: str | None, body: str | None) -> str | None:
    """Prefer the grant in the harvested file when package.json SPDX disagrees."""
    if not body:
        return spdx
    head = body.lstrip()[:240].upper()
    if "APACHE LICENSE" in head or "APACHE LICENSE VERSION 2" in head:
        if not spdx or spdx.strip().upper() in {"MIT", "ISC", "BSD-2-CLAUSE", "BSD-3-CLAUSE"}:
            return "Apache-2.0"
    if head.startswith("MIT LICENSE") or "PERMISSION IS HEREBY GRANTED, FREE OF CHARGE" in head:
        if spdx and "APACHE" in spdx.upper() and "OR" not in spdx.upper():
            return "MIT"
    return spdx


def is_vendor_third_party_path(meta: dict) -> bool:
    """Path crates under pim-offline-server/vendor/ are vendored third-party OSS."""
    mp = meta.get("manifest_path")
    if not isinstance(mp, str) or not mp:
        return False
    norm = mp.replace("\\", "/").lower()
    return "/vendor/" in norm


def parse_cargo_lock(lock_path: Path) -> list[dict]:
    text = lock_path.read_text(encoding="utf-8")
    packages: list[dict] = []
    for m in re.finditer(r"(?m)^\[\[package\]\]\n((?:(?!^\[\[).*\n)*)", text):
        block = m.group(1)
        name_m = re.search(r'^name = "([^"]+)"', block, re.M)
        ver_m = re.search(r'^version = "([^"]+)"', block, re.M)
        src_m = re.search(r'^source = "([^"]+)"', block, re.M)
        if not name_m or not ver_m:
            continue
        source = src_m.group(1) if src_m else "path"
        kind = "path"
        if source.startswith("registry+"):
            kind = "registry"
        elif source.startswith("git+"):
            kind = "git"
        packages.append(
            {
                "name": name_m.group(1),
                "version": ver_m.group(1),
                "source": source,
                "kind": kind,
            }
        )
    return packages


def split_crate_dirname(dirname: str) -> tuple[str, str] | None:
    """Split ``name-1.2.3`` / ``name-1.2.3+meta`` (crates.io registry dirname).

    Prefer the *rightmost* hyphen whose suffix looks like a Cargo semver
    (``major.minor…``). A left-first ``(.+?)-(\\d.*)`` wrongly splits
    ``md-5-0.10.6`` → ``md`` / ``5-0.10.6`` and ``utf-8-0.7.6`` → ``utf`` /
    ``8-0.7.6``, which leaves those crates BLOCKED in the disclosure.

    Build metadata after ``+`` may itself contain hyphens
    (``toml-1.1.4+spec-1.1.0``). Search for the name/version hyphen only in
    the pre-``+`` segment so we never split inside ``+meta``.
    """
    # Require at least one dotted numeric component so ``5-0.10.6`` is rejected.
    ver_re = re.compile(r"^\d+\.\d+.*$")
    plus = ""
    base = dirname
    if "+" in dirname:
        base, meta = dirname.split("+", 1)
        plus = "+" + meta
    for i in range(len(base) - 1, -1, -1):
        if base[i] != "-":
            continue
        name, ver = base[:i], base[i + 1 :]
        if not name or not ver:
            continue
        if ver_re.match(ver):
            return name, ver + plus
    return None


def build_registry_index(reg_roots: list[Path]) -> dict[tuple[str, str], Path]:
    index: dict[tuple[str, str], Path] = {}
    for root in reg_roots:
        if not root.is_dir():
            continue
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            if not child.is_dir():
                continue
            split = split_crate_dirname(child.name)
            if not split:
                continue
            name, ver = split
            ct = child / "Cargo.toml"
            if ct.is_file():
                index[(name, ver)] = child
    return index


def is_first_party_cargo(name: str, license_spdx: str | None, source: str) -> bool:
    """AIC-owned crates (path, proprietary, or named product crates) are not third-party OSS."""
    if license_spdx and "proprietary" in license_spdx.strip().lower():
        return True
    if "analoginfo" in (source or "").lower():
        return True
    # Product / workspace crate name prefixes (never third-party crates.io names here)
    if name.startswith(
        ("pim-", "elevation-", "local-update-", "aic-", "ot-contracts", "pam-privilege")
    ):
        return True
    return False


def normalize_spdx(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    # Legacy Cargo form MIT/Apache-2.0
    if "/" in s and " OR " not in s.upper() and " AND " not in s.upper():
        parts = [p.strip() for p in s.split("/") if p.strip()]
        if parts and all(re.match(r"^[A-Za-z0-9.+_-]+$", p) for p in parts):
            s = " OR ".join(parts)
    return s


def load_cargo_metadata(server: Path) -> dict[tuple[str, str], dict]:
    """Map (name, version) -> cargo metadata package dict (license, manifest_path)."""
    import subprocess

    try:
        proc = subprocess.run(
            ["cargo", "metadata", "--format-version", "1", "--locked", "--offline"],
            cwd=str(server),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if proc.returncode != 0 or not proc.stdout.strip():
        # Retry without --offline if the index needs a touch
        try:
            proc = subprocess.run(
                ["cargo", "metadata", "--format-version", "1", "--locked"],
                cwd=str(server),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {}
    if proc.returncode != 0 or not proc.stdout.strip():
        print("WARN: cargo metadata failed; falling back to registry walk only", file=sys.stderr)
        return {}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {}
    out: dict[tuple[str, str], dict] = {}
    for pkg in data.get("packages") or []:
        name = pkg.get("name")
        ver = pkg.get("version")
        if isinstance(name, str) and isinstance(ver, str):
            out[(name, ver)] = pkg
    return out


def build_git_checkout_index() -> dict[str, Path]:
    """Map crate name -> newest checkout dir that contains Cargo.toml with that name."""
    home = Path.home() / ".cargo" / "git" / "checkouts"
    index: dict[str, Path] = {}
    if not home.is_dir():
        return index
    for repo in home.iterdir():
        if not repo.is_dir():
            continue
        try:
            checkouts = list(repo.iterdir())
        except OSError:
            continue
        for checkout in checkouts:
            if not checkout.is_dir():
                continue
            # Flat crate or workspace members one level down
            candidates = [checkout]
            try:
                candidates.extend(p for p in checkout.iterdir() if p.is_dir())
            except OSError:
                pass
            for cand in candidates:
                ct = cand / "Cargo.toml"
                if not ct.is_file():
                    continue
                try:
                    data = tomllib.loads(ct.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    continue
                pkg = data.get("package") or {}
                name = pkg.get("name")
                if isinstance(name, str) and name and name not in index:
                    index[name] = cand
    return index


def registry_roots() -> list[Path]:
    home = Path.home() / ".cargo" / "registry" / "src"
    if not home.is_dir():
        return []
    return [p for p in home.iterdir() if p.is_dir()]


def read_crate_meta(crate_dir: Path) -> tuple[str | None, str | None, Path | None]:
    ct = crate_dir / "Cargo.toml"
    if not ct.is_file():
        return None, None, None
    try:
        data = tomllib.loads(ct.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None, None, None
    pkg = data.get("package") or {}
    license_spdx = pkg.get("license")
    license_file = pkg.get("license-file")
    authors = pkg.get("authors")
    copyright = None
    if isinstance(authors, list) and authors:
        copyright = "; ".join(str(a) for a in authors)
    elif isinstance(authors, str):
        copyright = authors
    license_path = None
    if isinstance(license_file, str) and license_file:
        cand = crate_dir / license_file
        if cand.is_file():
            license_path = cand
    return (str(license_spdx) if license_spdx else None), copyright, license_path


def harvest_license_files(package_dir: Path) -> str | None:
    """Concatenate package-local LICENSE* files; return body or None."""
    if not package_dir.is_dir():
        return None
    bodies: list[str] = []
    seen: set[str] = set()
    for name in LICENSE_FILE_NAMES:
        path = package_dir / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if not text or text in seen:
            continue
        seen.add(text)
        bodies.append(f"--- {name} ---\n{text}")
    # Also pick up any other LICENSE-* files
    try:
        for path in sorted(package_dir.iterdir()):
            if not path.is_file():
                continue
            upper = path.name.upper()
            if upper.startswith("LICENSE") and path.name not in LICENSE_FILE_NAMES:
                try:
                    text = path.read_text(encoding="utf-8", errors="replace").strip()
                except OSError:
                    continue
                if text and text not in seen:
                    seen.add(text)
                    bodies.append(f"--- {path.name} ---\n{text}")
    except OSError:
        pass
    if not bodies:
        return None
    return "\n\n".join(bodies) + "\n"


def primary_spdx_id(expr: str) -> str:
    token = re.split(r"\s+(?:OR|AND|WITH)\s+", expr, maxsplit=1)[0].strip()
    return token.strip("()")


def write_standard_license_texts() -> dict[str, str]:
    """Write common SPDX license texts; return map SPDX -> relative path."""
    LICENSES_DIR.mkdir(parents=True, exist_ok=True)
    # Bodies are the standard published license texts (not invented).
    # Import from sibling module content kept inline for single-file portability.
    from generate_open_source_credits_spdx import SPDX_BODIES  # type: ignore

    mapping: dict[str, str] = {}
    for spdx, body in SPDX_BODIES.items():
        if spdx not in SPDX_TEMPLATES:
            continue
        rel = f"license-texts/{SPDX_TEMPLATES[spdx]}"
        path = OUT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.rstrip() + "\n", encoding="utf-8")
        mapping[spdx] = rel
    return mapping


def write_standard_license_texts_inline() -> dict[str, str]:
    """Write common SPDX texts (inline) so the script has no extra import."""
    LICENSES_DIR.mkdir(parents=True, exist_ok=True)
    # Minimal set — prefer harvested package LICENSE files; these cover common IDs.
    texts: dict[str, str] = {}
    # Reuse previously written files if present from last run; otherwise write from
    # the long-form constants below via a compact approach: read from existing
    # OUT if available, else write short pointer + harvest preference.
    # Full texts for the common licenses (same as prior generator revision).
    base = Path(__file__).resolve().parent / "_spdx_license_bodies"
    # Fall through: embed essential short licenses; Apache-2.0/MIT etc. from disk
    # if already present under OUT from prior generation.
    for spdx, fname in SPDX_TEMPLATES.items():
        existing = LICENSES_DIR / fname
        if existing.is_file() and existing.stat().st_size > 200:
            texts[spdx] = existing.read_text(encoding="utf-8")
    # Ensure MIT / Apache / BSD / ISC / 0BSD / Unlicense / Zlib at minimum
    defaults = _default_spdx_bodies()
    for spdx, body in defaults.items():
        if spdx not in texts or len(texts[spdx]) < 100:
            texts[spdx] = body
    mapping: dict[str, str] = {}
    for spdx, body in texts.items():
        if spdx not in SPDX_TEMPLATES:
            continue
        rel = f"license-texts/{SPDX_TEMPLATES[spdx]}"
        path = OUT / rel
        path.write_text(body.rstrip() + "\n", encoding="utf-8")
        mapping[spdx] = rel
    return mapping


def _default_spdx_bodies() -> dict[str, str]:
    """Standard published SPDX license bodies (subset of common OSS licenses)."""
    return {
        "MIT": """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
        "Apache-2.0": (
            Path(__file__).resolve().parent.parent
            / "legal"
            / "open-source-credits"
            / "license-texts"
            / "Apache-2.0.txt"
        ).read_text(encoding="utf-8")
        if (
            Path(__file__).resolve().parent.parent
            / "legal"
            / "open-source-credits"
            / "license-texts"
            / "Apache-2.0.txt"
        ).is_file()
        else """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Full text: https://www.apache.org/licenses/LICENSE-2.0.txt
""",
        "BSD-2-Clause": """BSD 2-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""",
        "BSD-3-Clause": """BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""",
        "ISC": """ISC License

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
""",
        "0BSD": """BSD Zero Clause License

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
""",
        "Unlicense": """This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>
""",
        "Zlib": """zlib License

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
""",
        "MPL-2.0": """Mozilla Public License Version 2.0

Full published text: https://www.mozilla.org/MPL/2.0/
(Package-local LICENSE files are preferred when present in the harvest.)
""",
        "CC0-1.0": """Creative Commons CC0 1.0 Universal

Full published text: https://creativecommons.org/publicdomain/zero/1.0/legalcode
(Package-local LICENSE files are preferred when present in the harvest.)
""",
        "BlueOak-1.0.0": (
            Path(__file__).resolve().parent.parent
            / "legal"
            / "open-source-credits"
            / "license-texts"
            / "BlueOak-1.0.0.txt"
        ).read_text(encoding="utf-8")
        if (
            Path(__file__).resolve().parent.parent
            / "legal"
            / "open-source-credits"
            / "license-texts"
            / "BlueOak-1.0.0.txt"
        ).is_file()
        else """Blue Oak Model License 1.0.0

Full published text: https://blueoakcouncil.org/license/1.0.0
(Package-local LICENSE files are preferred when present in the harvest.)
""",
        "Unicode-3.0": """UNICODE LICENSE V3

Full published text: https://www.unicode.org/license.txt
(Package-local LICENSE files are preferred when present in the harvest.)
""",
        "Unicode-DFS-2016": """UNICODE, INC. LICENSE AGREEMENT - DATA FILES AND SOFTWARE

Full published text: https://www.unicode.org/copyright.html
(Package-local LICENSE files are preferred when present in the harvest.)
""",
    }


def finalize_entry_license(
    entry: dict,
    license_map: dict[str, str],
    harvested_body: str | None,
    license_file_body: str | None = None,
) -> None:
    """Attach license text path/sha or mark BLOCKED. Never invent a license id."""
    body = harvested_body or license_file_body
    if body and is_pointer_only_license_body(body):
        # Do not treat COPYING / "see LICENSE-*" stubs as redistributable grant text.
        body = None

    expr = entry.get("license_spdx")
    if body and body.strip():
        expr = reconcile_spdx_with_harvested_body(
            str(expr) if expr else None, body
        )
        if expr:
            entry["license_spdx"] = normalize_spdx(expr)
            entry["license_name"] = entry["license_spdx"]
        rel, digest = store_license_body(body)
        entry["license_text_path"] = rel
        entry["license_text_sha256"] = digest
        entry["disclosure_status"] = "ok"
        if not entry.get("license_name") and entry.get("license_spdx"):
            entry["license_name"] = entry["license_spdx"]
        if not entry.get("license_name"):
            entry["license_name"] = "See license text (as published by the licensor)"
        return

    if expr:
        combined = combine_standard_spdx_bodies(str(expr), license_map)
        if combined:
            hrel, digest = store_license_body(combined)
            entry["license_text_path"] = hrel
            entry["license_text_sha256"] = digest
            entry["disclosure_status"] = "ok"
            if not entry.get("license_name"):
                entry["license_name"] = expr
            if not entry.get("notes"):
                entry["notes"] = (
                    "Package-local LICENSE was a pointer or missing; stored published "
                    "SPDX license text(s) for the declared expression."
                )
            return
        primary = primary_spdx_id(str(expr))
        rel = license_map.get(primary)
        if rel:
            path = OUT / rel
            if path.is_file() and path.stat().st_size > 80:
                std = path.read_text(encoding="utf-8")
                if is_pointer_only_license_body(std):
                    entry["license_text_path"] = None
                    entry["license_text_sha256"] = None
                    entry["disclosure_status"] = "BLOCKED"
                    entry["notes"] = (
                        (entry.get("notes") or "")
                        + " SPDX identifier present but full license body was not "
                        "harvested from the package and no complete stored text is "
                        f"available for {primary}."
                    ).strip()
                    return
                hrel, digest = store_license_body(std)
                entry["license_text_path"] = hrel
                entry["license_text_sha256"] = digest
                entry["disclosure_status"] = "ok"
                if not entry.get("license_name"):
                    entry["license_name"] = expr
                return
        entry["license_text_path"] = None
        entry["license_text_sha256"] = None
        entry["disclosure_status"] = "BLOCKED"
        entry["notes"] = (
            (entry.get("notes") or "")
            + f" SPDX expression recorded ({expr}); package-local LICENSE file "
            "not found and no complete stored body for this identifier."
        ).strip()
        return

    entry["license_text_path"] = None
    entry["license_text_sha256"] = None
    entry["disclosure_status"] = "BLOCKED"
    entry["notes"] = (
        (entry.get("notes") or "")
        + " No license identity or license text could be harvested for this package."
    ).strip()


def add_incorporated_assets(entries: list[dict]) -> None:
    flag_src = ROOT / "content" / "language-packs" / "LICENSE-flag-icons.txt"
    if flag_src.is_file():
        body = flag_src.read_text(encoding="utf-8")
        rel, digest = store_license_body(body)
        entries.append(
            {
                "id": "incorporated:flag-icons",
                "name": "flag-icons (lipis/flag-icons)",
                "version": "incorporated SVG set",
                "ecosystem": "incorporated-asset",
                "license_spdx": "MIT",
                "license_name": "MIT License",
                "copyright": "Copyright (c) 2013 Panayiotis Lipiridis",
                "homepage": "https://github.com/lipis/flag-icons",
                "license_text_path": rel,
                "license_text_sha256": digest,
                "source": "core-assets/content/language-packs/LICENSE-flag-icons.txt",
                "notes": "4x3 SVG flags copied into language-pack folders; MIT text retained verbatim.",
                "disclosure_status": "ok",
                "direct": None,
            }
        )

    for rel_src, name, homepage, spdx, license_name in (
        (
            "data/known-default-credentials/defaultcreds/LICENSE.txt",
            "defaultcreds (known-default credentials research list)",
            None,
            "MIT",
            "MIT License",
        ),
        (
            "data/known-default-credentials/seclists-default/LICENSE.txt",
            "SecLists default credentials subset",
            "https://github.com/danielmiessler/SecLists",
            "MIT",
            "MIT License",
        ),
        (
            "data/known-default-credentials/scadapass/LICENSE-ITI-ICS-Security-Tools.md",
            "SCADAPASS / ITI ICS Security Tools attribution",
            None,
            "CC-BY-4.0",
            "Creative Commons Attribution 4.0 International",
        ),
    ):
        src = ROOT / rel_src
        if not src.is_file():
            continue
        body = src.read_text(encoding="utf-8", errors="replace")
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name)[:64]
        hrel, digest = store_license_body(body)
        entries.append(
            {
                "id": f"incorporated:{safe}",
                "name": name,
                "version": "bundled data",
                "ecosystem": "incorporated-asset",
                "license_spdx": spdx,
                "license_name": license_name,
                "copyright": None,
                "homepage": homepage,
                "license_text_path": hrel,
                "license_text_sha256": digest,
                "source": f"core-assets/{rel_src}",
                "notes": "Shipped data catalog; license text copied from the tree, not invented.",
                "disclosure_status": "ok",
                "direct": None,
            }
        )


def npm_production_packages(lock_path: Path, node_modules: Path) -> list[dict]:
    """Every non-dev package in package-lock.json (transitive production graph)."""
    if not lock_path.is_file():
        return []
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    packages = data.get("packages") or {}
    out: list[dict] = []
    for key, meta in packages.items():
        if not key.startswith("node_modules/"):
            continue
        if meta.get("dev") is True:
            continue
        # package name: lockfile "name" (canonical) beats directory leaf (wrap-ansi-cjs → wrap-ansi)
        rest = key[len("node_modules/") :]
        parts = rest.split("/node_modules/")
        leaf = parts[-1]
        pkg_dir = UI / key if (UI / key).is_dir() else node_modules / leaf
        if not pkg_dir.is_dir():
            pkg_dir = (UI / key) if key else pkg_dir

        name = meta.get("name")
        version = meta.get("version") or "unknown"
        lic = meta.get("license")
        if isinstance(lic, dict):
            lic = lic.get("type")
        if pkg_dir.is_dir():
            pj = pkg_dir / "package.json"
            if pj.is_file():
                try:
                    nested = json.loads(pj.read_text(encoding="utf-8"))
                    if not name:
                        name = nested.get("name")
                    if not lic:
                        lic = nested.get("license")
                        if isinstance(lic, dict):
                            lic = lic.get("type")
                    if version == "unknown":
                        version = nested.get("version") or version
                except Exception:
                    pass
        name = name or leaf
        if isinstance(name, str) and name.startswith("@analoginfo-pim/"):
            continue  # first-party AIC packages

        lic_s = str(lic) if lic else None
        if is_commercial_npm_package(str(name), lic_s):
            notice = (
                f"{name}@{version} is distributed under a commercial / proprietary "
                "license. The full license text is not redistributable in this "
                "open-source credits inventory. See the package LICENSE file in "
                "node_modules and your MUI X commercial agreement."
            )
            hrel, digest = store_license_body(notice)
            out.append(
                {
                    "id": f"npm:{name}@{version}",
                    "name": name,
                    "version": str(version),
                    "ecosystem": "npm",
                    "license_spdx": None,
                    "license_name": "Commercial / proprietary (text not redistributable)",
                    "copyright": None,
                    "homepage": meta.get("resolved"),
                    "license_text_path": hrel,
                    "license_text_sha256": digest,
                    "source": "pim-offline-server/ui/package-lock.json (production) + node_modules",
                    "notes": (
                        "Commercial package listed for complete disclosure. "
                        "SPDX 'SEE LICENSE IN LICENSE' is not a valid open-source "
                        "identifier and is not shown. Status is commercial, not Live OSS."
                    ),
                    "direct": False,
                    "disclosure_status": "commercial",
                    "_pkg_dir": None,
                }
            )
            continue

        entry = {
            "id": f"npm:{name}@{version}",
            "name": name,
            "version": str(version),
            "ecosystem": "npm",
            "license_spdx": normalize_spdx(lic_s),
            "license_name": lic_s,
            "copyright": None,
            "homepage": meta.get("resolved"),
            "license_text_path": None,
            "license_text_sha256": None,
            "source": "pim-offline-server/ui/package-lock.json (production) + node_modules",
            "notes": None,
            "direct": False,
            "_pkg_dir": str(pkg_dir) if pkg_dir.is_dir() else None,
        }
        out.append(entry)
    # Deduplicate by id (same name@version may appear nested / via -cjs aliases)
    dedup: dict[str, dict] = {}
    for e in out:
        existing = dedup.get(e["id"])
        if existing is None:
            dedup[e["id"]] = e
            continue
        # Prefer an entry that still has a harvest directory; keep commercial.
        if existing.get("disclosure_status") == "commercial":
            continue
        if e.get("disclosure_status") == "commercial":
            dedup[e["id"]] = e
            continue
        if not existing.get("_pkg_dir") and e.get("_pkg_dir"):
            dedup[e["id"]] = e
    return list(dedup.values())


def sync_to_consumers() -> None:
    consumer_dirs = [
        SERVER / "ui" / "public" / "legal" / "open-source-credits",
        SERVER / "assets" / "legal" / "open-source-credits",
    ]
    for dest_root in consumer_dirs:
        dest_root.mkdir(parents=True, exist_ok=True)
        for src in OUT.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(OUT)
            dest = dest_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = src.read_bytes()
            last_err: OSError | None = None
            for attempt in range(3):
                try:
                    dest.write_bytes(data)
                    last_err = None
                    break
                except OSError as e:
                    last_err = e
                    import time

                    time.sleep(0.25 * (attempt + 1))
            if last_err is not None:
                raise last_err
        print(f"Synced -> {dest_root}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate AIC Server Open Source Credits inventory (complete disclosure)."
    )
    p.add_argument(
        "--require-live",
        action="store_true",
        help="Exit 2 when any third-party package is BLOCKED (fail-closed for deploy/MSI).",
    )
    p.add_argument(
        "--server-root",
        default=None,
        help=(
            "pim-offline-server checkout whose Cargo.lock and package-lock.json "
            "are hashed (default: workspace sibling). Use a worktree so inventory "
            "SHAs match that checkout, not a dirty shared tree."
        ),
    )
    p.add_argument(
        "--check-current",
        action="store_true",
        help=(
            "Exit 0 when committed inventory already matches the canonical "
            "Cargo.lock digest and npm lock SHA and status is Live or Partial. "
            "Exit 1 when stale or missing. Exit 2 when --require-live and BLOCKED. "
            "Does not harvest or rewrite files."
        ),
    )
    p.add_argument(
        "--print-cargo-digest",
        action="store_true",
        help="Print the canonical Cargo.lock digest (hex) and exit 0.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even when the canonical lock digest already matches.",
    )
    return p.parse_args(argv)


def inventory_lock_status(inv_path: Path, cargo_lock: Path, npm_lock: Path) -> str:
    """Return current | stale | blocked | missing.

    current: Live or Partial and canonical cargo digest + npm SHA match.
    blocked: inventory is BLOCKED (digest may still match).
    """
    if not inv_path.is_file() or not cargo_lock.is_file():
        return "missing"
    try:
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "missing"
    status = inv.get("status")
    gen = inv.get("generation") if isinstance(inv.get("generation"), dict) else {}
    inv_cargo = gen.get("cargo_lock_sha256")
    cargo_digest = cargo_lock_canonical_sha256_file(cargo_lock)
    if not inv_cargo or str(inv_cargo).lower() != cargo_digest.lower():
        return "stale"
    if npm_lock.is_file():
        inv_npm = gen.get("npm_lock_sha256")
        disk_npm = sha256_file(npm_lock)
        if not inv_npm or str(inv_npm).lower() != disk_npm.lower():
            return "stale"
    if status == "BLOCKED":
        return "blocked"
    if status in ("Live", "Partial"):
        return "current"
    return "stale"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    global SERVER, UI
    if args.server_root:
        SERVER = Path(args.server_root).expanduser().resolve()
        UI = SERVER / "ui"
    if not SERVER.is_dir():
        print(f"ERROR: expected pim-offline-server at {SERVER}", file=sys.stderr)
        return 1

    cargo_lock = SERVER / "Cargo.lock"
    npm_lock = UI / "package-lock.json"
    inv_path = OUT / "inventory.json"

    if args.print_cargo_digest:
        if not cargo_lock.is_file():
            print(f"ERROR: missing Cargo.lock at {cargo_lock}", file=sys.stderr)
            return 1
        print(cargo_lock_canonical_sha256_file(cargo_lock))
        return 0

    lock_state = inventory_lock_status(inv_path, cargo_lock, npm_lock)
    if args.check_current:
        if lock_state == "current":
            print(f"Open Source Credits: current (canonical digest matches, {inv_path})")
            return 0
        if lock_state == "blocked":
            print(
                "Open Source Credits: inventory is BLOCKED (fail-closed).",
                file=sys.stderr,
            )
            return 2 if args.require_live else 1
        print(
            f"Open Source Credits: {lock_state} (need regen) {inv_path}",
            file=sys.stderr,
        )
        return 1

    if not args.force and lock_state == "current":
        print(
            "Open Source Credits: skip rewrite "
            f"(canonical Cargo.lock digest and npm lock SHA already match, {inv_path})"
        )
        return 0
    if not args.force and lock_state == "blocked" and args.require_live:
        print(
            "ERROR: --require-live refused status=BLOCKED "
            "(inventory already current vs lock digest; harvest unchanged).",
            file=sys.stderr,
        )
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    license_map = write_standard_license_texts_inline()

    lock_packages = parse_cargo_lock(cargo_lock) if cargo_lock.is_file() else []
    regs = registry_roots()
    reg_index = build_registry_index(regs)
    git_index = build_git_checkout_index()
    print("Loading cargo metadata for license/manifest paths…")
    cargo_meta = load_cargo_metadata(SERVER)
    print(f"cargo metadata packages: {len(cargo_meta)}")

    seen: set[tuple[str, str]] = set()
    unique_lock: list[dict] = []
    path_excluded = 0
    first_party_excluded = 0
    for pkg in lock_packages:
        key = (pkg["name"], pkg["version"])
        if key in seen:
            continue
        seen.add(key)
        meta = cargo_meta.get(key) or {}
        meta_lic = meta.get("license") if isinstance(meta.get("license"), str) else None
        if pkg["kind"] == "path":
            # Vendored third-party under vendor/ is disclosed; AIC workspace path crates are not.
            if not is_vendor_third_party_path(meta):
                path_excluded += 1
                continue
            if is_first_party_cargo(pkg["name"], meta_lic, pkg.get("source") or ""):
                path_excluded += 1
                continue
        elif is_first_party_cargo(pkg["name"], meta_lic, pkg.get("source") or ""):
            first_party_excluded += 1
            continue
        unique_lock.append(pkg)

    cargo_entries: list[dict] = []
    cargo_resolved = 0
    cargo_blocked = 0
    for pkg in unique_lock:
        name, ver, kind = pkg["name"], pkg["version"], pkg["kind"]
        meta = cargo_meta.get((name, ver)) or {}
        crate_dir: Path | None = None
        if kind == "registry":
            crate_dir = reg_index.get((name, ver))
        elif kind == "git":
            crate_dir = git_index.get(name)
        elif kind == "path":
            if meta.get("manifest_path"):
                mp = Path(str(meta["manifest_path"]))
                if mp.is_file():
                    crate_dir = mp.parent
        if crate_dir is None and meta.get("manifest_path"):
            mp = Path(str(meta["manifest_path"]))
            if mp.is_file():
                crate_dir = mp.parent

        lic, copyright, license_file_path = (None, None, None)
        harvested = None
        license_file_body = None
        if crate_dir:
            lic, copyright, license_file_path = read_crate_meta(crate_dir)
            harvested = harvest_license_files(crate_dir)
            if license_file_path and license_file_path.is_file():
                try:
                    license_file_body = license_file_path.read_text(
                        encoding="utf-8", errors="replace"
                    )
                except OSError:
                    license_file_body = None
        if not lic and isinstance(meta.get("license"), str):
            lic = meta["license"]

        # Second-pass first-party after reading crate license
        if is_first_party_cargo(name, lic, pkg.get("source") or ""):
            first_party_excluded += 1
            continue

        if kind == "registry":
            src_note = (
                "pim-offline-server/Cargo.lock + local Cargo registry / cargo metadata"
            )
        elif kind == "git":
            src_note = (
                "pim-offline-server/Cargo.lock + local Cargo git checkout / cargo metadata"
            )
        else:
            src_note = (
                "pim-offline-server/Cargo.lock + vendored path crate "
                "(vendor/) / cargo metadata"
            )

        entry = {
            "id": f"cargo:{name}@{ver}",
            "name": name,
            "version": ver,
            "ecosystem": "cargo",
            "license_spdx": normalize_spdx(lic),
            "license_name": normalize_spdx(lic) or lic,
            "copyright": copyright,
            "homepage": f"https://crates.io/crates/{name}" if kind == "registry" else None,
            "license_text_path": None,
            "license_text_sha256": None,
            "source": src_note,
            "notes": None,
            "direct": False,
            "cargo_source_kind": kind,
        }
        finalize_entry_license(entry, license_map, harvested, license_file_body)
        if entry["disclosure_status"] == "ok":
            cargo_resolved += 1
        else:
            cargo_blocked += 1
        cargo_entries.append(entry)

    npm_raw = npm_production_packages(UI / "package-lock.json", UI / "node_modules")
    npm_entries: list[dict] = []
    npm_ok = 0
    npm_blocked = 0
    npm_commercial = 0
    for e in npm_raw:
        if e.get("disclosure_status") == "commercial":
            e.pop("_pkg_dir", None)
            npm_commercial += 1
            npm_entries.append(e)
            continue
        pkg_dir_s = e.pop("_pkg_dir", None)
        harvested = None
        if pkg_dir_s:
            harvested = harvest_license_files(Path(pkg_dir_s))
        finalize_entry_license(e, license_map, harvested, None)
        if e["disclosure_status"] == "ok":
            npm_ok += 1
        else:
            npm_blocked += 1
        npm_entries.append(e)

    incorporated: list[dict] = []
    add_incorporated_assets(incorporated)

    all_entries = (
        incorporated
        + sorted(cargo_entries, key=lambda e: (e["name"].lower(), e["version"]))
        + sorted(npm_entries, key=lambda e: (e["name"].lower(), e["version"]))
    )

    # Commercial / proprietary packages are NOT open source. Keep them in a
    # separate commercial_packages section for operator awareness, but exclude
    # them from the OSS entry list and from Live/BLOCKED status math.
    commercial = [e for e in all_entries if e.get("disclosure_status") == "commercial"]
    oss_entries = [e for e in all_entries if e.get("disclosure_status") != "commercial"]
    all_entries = oss_entries
    oss_blocked = [e for e in all_entries if e.get("disclosure_status") == "BLOCKED"]
    with_text = sum(1 for e in all_entries if e.get("license_text_path"))
    if oss_blocked:
        status = "BLOCKED"
    else:
        status = "Live"
    honesty = (
        "This inventory lists every third-party open-source component incorporated "
        "into AIC Server from the production Cargo graph (registry, git, and "
        "vendored path crates under vendor/), the npm production graph "
        "(package-lock.json, non-dev; lockfile package name preferred over "
        "directory leaf), and incorporated on-disk assets (including "
        "lipis/flag-icons). First-party workspace path crates, AIC-named / "
        "proprietary crates, and @analoginfo-pim/* npm packages are excluded as "
        "AIC-owned code, not third-party open source. Commercial / proprietary "
        "dependencies (for example MUI X Pro/Premium) are excluded from this "
        "open-source inventory and listed separately under commercial_packages; "
        "they do not set Partial/BLOCKED on the OSS disclosure. License bodies "
        "were harvested from local Cargo registry / git / vendor checkouts, "
        "node_modules LICENSE files, and in-tree LICENSE copies; common SPDX "
        "identifiers use the stored published license text when a package-local "
        "file was a pointer or absent. No package or license was invented. "
        + (
            "Every listed open-source package has a license identity and license "
            "text (Live)."
            if status == "Live"
            else (
                f"{len(oss_blocked)} package(s) are BLOCKED because no license "
                "identity and/or redistributable license text could be harvested; "
                "they remain listed and are not silently omitted. "
            )
        )
        + (
            (
                f" {len(commercial)} commercial / proprietary package(s) are noted "
                "separately (not part of the OSS Live status)."
            )
            if commercial
            else ""
        )
    )

    cargo_lock_sha = (
        cargo_lock_canonical_sha256_file(cargo_lock) if cargo_lock.is_file() else None
    )
    npm_lock_sha = sha256_file(npm_lock) if npm_lock.is_file() else None
    sbom_server = SERVER / "sbom" / "pim-offline-server.cdx.json"
    sbom_sha = sha256_file(sbom_server) if sbom_server.is_file() else None

    inventory = OrderedDict(
        [
            ("schema", "aic-open-source-credits"),
            ("schema_version", 2),
            ("status", status),
            ("honesty", honesty),
            ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
            (
                "generation",
                {
                    "tool": "core-assets/scripts/generate-open-source-credits.py",
                    "cargo_lock_path": "pim-offline-server/Cargo.lock",
                    "cargo_lock_digest": "canonical_package_identity_v1",
                    "cargo_lock_sha256": cargo_lock_sha,
                    "npm_lock_path": "pim-offline-server/ui/package-lock.json",
                    "npm_lock_sha256": npm_lock_sha,
                    "sbom_path": "pim-offline-server/sbom/pim-offline-server.cdx.json",
                    "sbom_sha256": sbom_sha,
                    "cargo_third_party_count": len(cargo_entries),
                    "cargo_third_party_with_license_text": cargo_resolved,
                    "cargo_third_party_blocked": cargo_blocked,
                    "cargo_path_packages_excluded_first_party": path_excluded,
                    "cargo_git_or_named_first_party_excluded": first_party_excluded,
                    "cargo_lock_package_count": len(seen),
                    "cargo_registry_roots_used": len(regs),
                    "npm_production_count": len(npm_entries),
                    "npm_production_with_license_text": npm_ok,
                    "npm_production_blocked": npm_blocked,
                    "npm_production_commercial": npm_commercial,
                    "incorporated_count": len(incorporated),
                    "entries_with_license_text": with_text,
                    "blocked_count": len(oss_blocked),
                    "commercial_count": len(commercial),
                },
            ),
            ("entry_count", len(all_entries)),
            ("blocked_count", len(oss_blocked)),
            ("commercial_count", len(commercial)),
            (
                "blocked_packages",
                [
                    {
                        "id": e["id"],
                        "name": e["name"],
                        "version": e["version"],
                        "ecosystem": e["ecosystem"],
                    }
                    for e in oss_blocked
                ],
            ),
            (
                "commercial_packages",
                [
                    {
                        "id": e["id"],
                        "name": e["name"],
                        "version": e["version"],
                        "ecosystem": e["ecosystem"],
                    }
                    for e in commercial
                ],
            ),
            ("entries", all_entries),
            (
                "appendix",
                {
                    "notes": (
                        "Complete third-party disclosure is in entries[]. "
                        f"First-party Cargo path packages excluded: {path_excluded}. "
                        "Vendored third-party path crates under vendor/ are included. "
                        "CycloneDX SBOM remains a companion artifact for hashes/purls."
                    ),
                },
            ),
        ]
    )

    inv_text = json.dumps(inventory, indent=2, ensure_ascii=False) + "\n"
    inv_path.write_text(inv_text, encoding="utf-8", newline="\n")

    # Slim blocked list for operators
    blocked_path = OUT / "blocked-packages.json"
    blocked_path.write_text(
        json.dumps(
            {
                "schema": "aic-open-source-credits-blocked",
                "count": len(oss_blocked),
                "packages": inventory["blocked_packages"],
                "commercial_count": len(commercial),
                "commercial_packages": inventory["commercial_packages"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    readme = OUT / "README.md"
    readme.write_text(
        f"""# Open Source Credits (AIC Server)

Complete third-party open-source disclosure for AIC Server Admin
**About → Open Source Credits**.

## Honesty

Status: **{status}**. Generated by `scripts/generate-open-source-credits.py`
from real lockfiles and harvested LICENSE copies. See `inventory.json`
`honesty` field. Curated-direct-only inventories are a defect.

## Counts

| Metric | Value |
| --- | ---: |
| Entries (third-party) | {len(all_entries)} |
| With license text | {with_text} |
| BLOCKED (OSS gaps) | {len(oss_blocked)} |
| Commercial / proprietary | {len(commercial)} |
| Cargo third-party | {len(cargo_entries)} |
| npm production | {len(npm_entries)} |
| Incorporated assets | {len(incorporated)} |
| Cargo path (first-party, excluded) | {path_excluded} |

## Files

| File | Role |
| --- | --- |
| `inventory.json` | Full entries + honesty + generation SHAs |
| `blocked-packages.json` | BLOCKED package list (if any) |
| `license-texts/` | SPDX texts + `by-sha256/` harvested bodies |

## Regenerate

```text
python scripts/generate-open-source-credits.py
```

Then sync into `pim-offline-server` via this script (auto) or
`scripts/sync-to-projects.ps1`.

Inventory SHA-256: `{sha256_text(inv_text)}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Wrote {inv_path} ({len(all_entries)} entries, status={status})")
    print(
        f"With license text={with_text} oss_blocked={len(oss_blocked)} "
        f"commercial={len(commercial)}"
    )
    print(
        f"Cargo third-party={len(cargo_entries)} ok={cargo_resolved} blocked={cargo_blocked} "
        f"path_excluded={path_excluded}"
    )
    print(
        f"npm production={len(npm_entries)} ok={npm_ok} blocked={npm_blocked} "
        f"commercial={npm_commercial}"
    )
    if oss_blocked:
        print("BLOCKED packages:")
        for e in oss_blocked[:50]:
            print(f"  - {e['id']}")
        if len(oss_blocked) > 50:
            print(f"  ... and {len(oss_blocked) - 50} more")
    if commercial:
        print("Commercial / proprietary packages:")
        for e in commercial[:50]:
            print(f"  - {e['id']}")

    sync_to_consumers()

    # --require-live: fail closed on true OSS BLOCKED gaps. Partial (commercial-only)
    # is shippable honesty — not Live, but not an invented/missing OSS license.
    if args.require_live and oss_blocked:
        print(
            f"ERROR: --require-live refused {len(oss_blocked)} BLOCKED package(s); "
            "disclosure is incomplete (fail-closed).",
            file=sys.stderr,
        )
        return 2
    if args.require_live and status == "BLOCKED":
        print(
            "ERROR: --require-live refused status=BLOCKED.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
