#!/usr/bin/env python3
"""Generate AIC Server Open Source Credits inventory (honest Partial).

Reads real lockfiles and in-tree LICENSE copies. Looks up SPDX / license
strings from the local Cargo registry cache and npm package.json files when
present. Does not invent packages or licenses.

Output lands under legal/open-source-credits/ (canonical) for sync into the
admin SPA public tree and the server embed path.

Usage (from core-assets repo root):
  python scripts/generate-open-source-credits.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

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

# SPDX id -> filename under license-texts/ (standard SPDX text, US English /
# licensor language as published). Kept short; uncommon IDs fall back to the
# SPDX identifier string only with honesty note on the entry.
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
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_cargo_lock(lock_path: Path) -> list[tuple[str, str]]:
    text = lock_path.read_text(encoding="utf-8")
    packages: list[tuple[str, str]] = []
    for m in re.finditer(
        r"(?m)^\[\[package\]\]\n(?:(?!^\[\[).*\n)*?^name = \"([^\"]+)\"\nversion = \"([^\"]+)\"",
        text,
    ):
        packages.append((m.group(1), m.group(2)))
    return packages


def cargo_direct_names(cargo_toml: Path) -> set[str]:
    data = tomllib.loads(cargo_toml.read_text(encoding="utf-8"))
    names: set[str] = set()
    for section in ("dependencies", "build-dependencies", "dev-dependencies"):
        block = data.get(section) or {}
        names.update(block.keys())
    return names


def build_registry_index(reg_roots: list[Path]) -> dict[tuple[str, str], Path]:
    """Map (crate_name, version) -> Cargo.toml using one shallow walk per root.

    Cargo registry layout is ``registry/src/<index-hash>/<name>-<version>/``.
    Walking only immediate children of each root avoids a full-tree rglob.
    """
    index: dict[tuple[str, str], Path] = {}
    # name-1.2.3 or name-1.2.3-alpha.1 — split on last hyphen before a digit start
    ver_re = re.compile(r"^(.+)-(\d.*)$")
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
            m = ver_re.match(child.name)
            if not m:
                continue
            ct = child / "Cargo.toml"
            if ct.is_file():
                index[(m.group(1), m.group(2))] = ct
    return index


def registry_roots() -> list[Path]:
    home = Path.home() / ".cargo" / "registry" / "src"
    if not home.is_dir():
        return []
    return [p for p in home.iterdir() if p.is_dir()]

def read_crate_meta(ct: Path) -> tuple[str | None, str | None]:
    try:
        data = tomllib.loads(ct.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None, None
    pkg = data.get("package") or {}
    license_spdx = pkg.get("license")
    license_file = pkg.get("license-file")
    authors = pkg.get("authors")
    copyright = None
    if isinstance(authors, list) and authors:
        copyright = "; ".join(str(a) for a in authors)
    elif isinstance(authors, str):
        copyright = authors
    return (str(license_spdx) if license_spdx else None), copyright


def normalize_spdx(raw: str | None) -> str | None:
    if not raw:
        return None
    # Prefer the first SPDX expression token for template lookup; keep full
    # expression on the entry.
    return raw.strip()


def primary_spdx_id(expr: str) -> str:
    # Split on OR / AND / WITH for template selection.
    token = re.split(r"\s+(?:OR|AND|WITH)\s+", expr, maxsplit=1)[0].strip()
    return token.strip("()")


def write_standard_license_texts() -> dict[str, str]:
    """Write common SPDX license texts; return map SPDX -> relative path."""
    LICENSES_DIR.mkdir(parents=True, exist_ok=True)
    texts: dict[str, str] = {
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
        "Apache-2.0": """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

"License" shall mean the terms and conditions for use, reproduction, and
distribution as defined by Sections 1 through 9 of this document.

"Licensor" shall mean the copyright owner or entity authorized by the copyright
owner that is granting the License.

"Legal Entity" shall mean the union of the acting entity and all other entities
that control, are controlled by, or are under common control with that entity.
For the purposes of this definition, "control" means (i) the power, direct or
indirect, to cause the direction or management of such entity, whether by
contract or otherwise, or (ii) ownership of fifty percent (50%) or more of the
outstanding shares, or (iii) beneficial ownership of such entity.

"You" (or "Your") shall mean an individual or Legal Entity exercising
permissions granted by this License.

"Source" form shall mean the preferred form for making modifications, including
but not limited to software source code, documentation source, and configuration
files.

"Object" form shall mean any form resulting from mechanical transformation or
translation of a Source form, including but not limited to compiled object code,
generated documentation, and conversions to other media types.

"Work" shall mean the work of authorship, whether in Source or Object form, made
available under the License, as indicated by a copyright notice that is included
in or attached to the work (an example is provided in the Appendix below).

"Derivative Works" shall mean any work, whether in Source or Object form, that is
based on (or derived from) the Work and for which the editorial revisions,
annotations, elaborations, or other modifications represent, as a whole, an
original work of authorship. For the purposes of this License, Derivative Works
shall not include works that remain separable from, or merely link (or bind by
name) to the interfaces of, the Work and Derivative Works thereof.

"Contribution" shall mean any work of authorship, including the original version
of the Work and any modifications or additions to that Work or Derivative Works
thereof, that is intentionally submitted to Licensor for inclusion in the Work
by the copyright owner or by an individual or Legal Entity authorized to submit
on behalf of the copyright owner. For the purposes of this definition,
"submitted" means any form of electronic, verbal, or written communication sent
to the Licensor or its representatives, including but not limited to
communication on electronic mailing lists, source code control systems, and
issue tracking systems that are managed by, or on behalf of, the Licensor for
the purpose of discussing and improving the Work, but excluding communication
that is conspicuously marked or otherwise designated in writing by the copyright
owner as "Not a Contribution."

"Contributor" shall mean Licensor and any individual or Legal Entity on behalf
of whom a Contribution has been received by Licensor and subsequently
incorporated within the Work.

2. Grant of Copyright License. Subject to the terms and conditions of this
License, each Contributor hereby grants to You a perpetual, worldwide,
non-exclusive, no-charge, royalty-free, irrevocable copyright license to
reproduce, prepare Derivative Works of, publicly display, publicly perform,
sublicense, and distribute the Work and such Derivative Works in Source or
Object form.

3. Grant of Patent License. Subject to the terms and conditions of this License,
each Contributor hereby grants to You a perpetual, worldwide, non-exclusive,
no-charge, royalty-free, irrevocable (except as stated in this section) patent
license to make, have made, use, offer to sell, sell, import, and otherwise
transfer the Work, where such license applies only to those patent claims
licensable by such Contributor that are necessarily infringed by their
Contribution(s) alone or by combination of their Contribution(s) with the Work
to which such Contribution(s) was submitted. If You institute patent litigation
against any entity (including a cross-claim or counterclaim in a lawsuit)
alleging that the Work or a Contribution incorporated within the Work
constitutes direct or contributory patent infringement, then any patent licenses
granted to You under this License for that Work shall terminate as of the date
such litigation is filed.

4. Redistribution. You may reproduce and distribute copies of the Work or
Derivative Works thereof in any medium, with or without modifications, and in
Source or Object form, provided that You meet the following conditions:

(a) You must give any other recipients of the Work or Derivative Works a copy of
this License; and

(b) You must cause any modified files to carry prominent notices stating that
You changed the files; and

(c) You must retain, in the Source form of any Derivative Works that You
distribute, all copyright, patent, trademark, and attribution notices from the
Source form of the Work, excluding those notices that do not pertain to any part
of the Derivative Works; and

(d) If the Work includes a "NOTICE" text file as part of its distribution, then
any Derivative Works that You distribute must include a readable copy of the
attribution notices contained within such NOTICE file, excluding those notices
that do not pertain to any part of the Derivative Works, in at least one of the
following places: within a NOTICE text file distributed as part of the
Derivative Works; within the Source form or documentation, if provided along
with the Derivative Works; or, within a display generated by the Derivative
Works, if and wherever such third-party notices normally appear. The contents of
the NOTICE file are for informational purposes only and do not modify the
License. You may add Your own attribution notices within Derivative Works that
You distribute, alongside or as an addendum to the NOTICE text from the Work,
provided that such additional attribution notices cannot be construed as
modifying the License.

You may add Your own copyright statement to Your modifications and may provide
additional or different license terms and conditions for use, reproduction, or
distribution of Your modifications, or for any such Derivative Works as a whole,
provided Your use, reproduction, and distribution of the Work otherwise complies
with the conditions stated in this License.

5. Submission of Contributions. Unless You explicitly state otherwise, any
Contribution intentionally submitted for inclusion in the Work by You to the
Licensor shall be under the terms and conditions of this License, without any
additional terms or conditions. Notwithstanding the above, nothing herein shall
supersede or modify the terms of any separate license agreement you may have
executed with Licensor regarding such Contributions.

6. Trademarks. This License does not grant permission to use the trade names,
trademarks, service marks, or product names of the Licensor, except as required
for reasonable and customary use in describing the origin of the Work and
reproducing the content of the NOTICE file.

7. Disclaimer of Warranty. Unless required by applicable law or agreed to in
writing, Licensor provides the Work (and each Contributor provides its
Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied, including, without limitation, any warranties or
conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
PARTICULAR PURPOSE. You are solely responsible for determining the
appropriateness of using or redistributing the Work and assume any risks
associated with Your exercise of permissions under this License.

8. Limitation of Liability. In no event and under no legal theory, whether in
tort (including negligence), contract, or otherwise, unless required by
applicable law (such as deliberate and grossly negligent acts) or agreed to in
writing, shall any Contributor be liable to You for damages, including any
direct, indirect, special, incidental, or consequential damages of any character
arising as a result of this License or out of the use or inability to use the
Work (including but not limited to damages for loss of goodwill, work stoppage,
computer failure or malfunction, or any and all other commercial damages or
losses), even if such Contributor has been advised of the possibility of such
damages.

9. Accepting Warranty or Additional Liability. While redistributing the Work or
Derivative Works thereof, You may choose to offer, and charge a fee for,
acceptance of support, warranty, indemnity, or other liability obligations
and/or rights consistent with this License. However, in accepting such
obligations, You may act only on Your own behalf and on Your sole
responsibility, not on behalf of any other Contributor, and only if You agree to
indemnify, defend, and hold each Contributor harmless for any liability incurred
by, or claims asserted against, such Contributor by reason of your accepting any
such warranty or additional liability.

END OF TERMS AND CONDITIONS
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
        "MPL-2.0": """Mozilla Public License Version 2.0

====================================================================

1. Definitions

1.1. "Contributor"
    means each individual or legal entity that creates, contributes to
    the creation of, or owns Covered Software.

1.2. "Contributor Version"
    means the combination of the Contributions of others (if any) used
    by a Contributor and that particular Contributor's Contribution.

1.3. "Contribution"
    means Covered Software of a particular Contributor.

1.4. "Covered Software"
    means Source Code Form to which the initial Contributor has attached
    the notice in Exhibit A, the Executable Form of such Source Code
    Form, and Modifications of such Source Code Form, in each case
    including portions thereof.

Full text: https://www.mozilla.org/MPL/2.0/
(This inventory stores the SPDX identifier and points operators to the
upstream MPL-2.0 publication for the complete license body.)
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
        "CC0-1.0": """Creative Commons Legal Code

CC0 1.0 Universal

CREATIVE COMMONS CORPORATION IS NOT A LAW FIRM AND DOES NOT PROVIDE
LEGAL SERVICES. DISTRIBUTION OF THIS DOCUMENT DOES NOT CREATE AN
ATTORNEY-CLIENT RELATIONSHIP. CREATIVE COMMONS PROVIDES THIS
INFORMATION ON AN "AS-IS" BASIS. CREATIVE COMMONS MAKES NO WARRANTIES
REGARDING THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS
PROVIDED HEREUNDER, AND DISCLAIMS LIABILITY FOR DAMAGES RESULTING FROM
THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS PROVIDED
HEREUNDER.

Statement of Purpose

The laws of most jurisdictions throughout the world automatically confer
exclusive Copyright and Related Rights (defined below) upon the creator
and subsequent owner(s) (each and all, an "owner") of an original work of
authorship and/or a database (each, a "Work").

Certain owners wish to permanently relinquish those rights to a Work for
the purpose of contributing to a commons of creative, cultural and
scientific works ("Commons") that the public can reliably and without fear
of later claims of infringement build upon, modify, incorporate in other
works, reuse and redistribute as freely as possible in any form whatsoever
and for any purposes, including without limitation commercial purposes.

Full text: https://creativecommons.org/publicdomain/zero/1.0/legalcode
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
    }
    mapping: dict[str, str] = {}
    for spdx, body in texts.items():
        rel = SPDX_TEMPLATES[spdx]
        path = LICENSES_DIR / rel
        path.write_text(body.rstrip() + "\n", encoding="utf-8")
        mapping[spdx] = f"license-texts/{rel}"
    return mapping


def add_incorporated_assets(entries: list[dict], license_map: dict[str, str]) -> None:
    """First-party incorporated third-party content with on-disk LICENSE copies."""
    flag_src = ROOT / "content" / "language-packs" / "LICENSE-flag-icons.txt"
    if flag_src.is_file():
        body = flag_src.read_text(encoding="utf-8")
        dest = LICENSES_DIR / "flag-icons-MIT.txt"
        dest.write_text(body, encoding="utf-8")
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
                "license_text_path": "license-texts/flag-icons-MIT.txt",
                "license_text_sha256": sha256_file(dest),
                "source": "core-assets/content/language-packs/LICENSE-flag-icons.txt",
                "notes": "4x3 SVG flags copied into language-pack folders; MIT text retained verbatim.",
            }
        )

    for rel, name, homepage in (
        (
            "data/known-default-credentials/defaultcreds/LICENSE.txt",
            "defaultcreds (known-default credentials research list)",
            None,
        ),
        (
            "data/known-default-credentials/seclists-default/LICENSE.txt",
            "SecLists default credentials subset",
            "https://github.com/danielmiessler/SecLists",
        ),
        (
            "data/known-default-credentials/scadapass/LICENSE-ITI-ICS-Security-Tools.md",
            "SCADAPASS / ITI ICS Security Tools attribution",
            None,
        ),
    ):
        src = ROOT / rel
        if not src.is_file():
            continue
        body = src.read_text(encoding="utf-8", errors="replace")
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name)[:64]
        dest = LICENSES_DIR / f"incorporated-{safe}.txt"
        dest.write_text(body, encoding="utf-8")
        entries.append(
            {
                "id": f"incorporated:{safe}",
                "name": name,
                "version": "bundled data",
                "ecosystem": "incorporated-asset",
                "license_spdx": None,
                "license_name": "See license text (as published by the data licensor)",
                "copyright": None,
                "homepage": homepage,
                "license_text_path": f"license-texts/{dest.name}",
                "license_text_sha256": sha256_file(dest),
                "source": f"core-assets/{rel}",
                "notes": "Shipped data catalog; license text copied from the tree, not invented.",
            }
        )


def npm_direct_packages(package_json: Path, lock_path: Path, node_modules: Path) -> list[dict]:
    """Only packages named in package.json dependencies / optionalDependencies.

    DevDependencies are build-time and are not claimed as shipping credits
    unless they appear in the production bundle; we still list production
    dependencies honestly. Full lock enumeration stays out of the curated list.
    """
    if not package_json.is_file():
        return []
    pj = json.loads(package_json.read_text(encoding="utf-8"))
    wanted: set[str] = set()
    for section in ("dependencies", "optionalDependencies"):
        block = pj.get(section) or {}
        wanted.update(block.keys())

    lock_meta: dict[str, dict] = {}
    if lock_path.is_file():
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        packages = data.get("packages") or {}
        for key, meta in packages.items():
            if key.startswith("node_modules/") and "node_modules/" not in key[len("node_modules/") :]:
                lock_meta[key[len("node_modules/") :]] = meta

    out: list[dict] = []
    for name in sorted(wanted, key=str.lower):
        meta = lock_meta.get(name) or {}
        version = meta.get("version") or "unknown"
        lic = meta.get("license")
        if isinstance(lic, dict):
            lic = lic.get("type")
        if not lic:
            pkg_path = node_modules / name / "package.json"
            if pkg_path.is_file():
                try:
                    nested = json.loads(pkg_path.read_text(encoding="utf-8"))
                    lic = nested.get("license")
                    if isinstance(lic, dict):
                        lic = lic.get("type")
                    if version == "unknown":
                        version = nested.get("version") or version
                except Exception:
                    pass
            # file: workspace packages often omit license in lock
            if not lic and str(pj.get("dependencies", {}).get(name, "")).startswith("file:"):
                # Read sibling package.json when path-local
                pass
        out.append(
            {
                "id": f"npm:{name}@{version}",
                "name": name,
                "version": version,
                "ecosystem": "npm",
                "license_spdx": normalize_spdx(str(lic) if lic else None),
                "license_name": str(lic) if lic else None,
                "copyright": None,
                "homepage": meta.get("resolved"),
                "license_text_path": None,
                "license_text_sha256": None,
                "source": "ui/package.json dependencies + package-lock.json / node_modules",
                "notes": None
                if lic
                else "License string not found in package-lock or node_modules package.json.",
                "direct": True,
            }
        )
    return out

def attach_license_text(entry: dict, license_map: dict[str, str]) -> None:
    expr = entry.get("license_spdx")
    if not expr:
        return
    primary = primary_spdx_id(expr)
    rel = license_map.get(primary)
    if rel:
        entry["license_text_path"] = rel
        path = OUT / rel
        if path.is_file():
            entry["license_text_sha256"] = sha256_file(path)
        if not entry.get("license_name"):
            entry["license_name"] = primary
    else:
        entry["notes"] = (
            (entry.get("notes") or "")
            + f" SPDX expression recorded from package metadata ({expr}); "
            "full license body not embedded for this uncommon SPDX id in this Partial inventory."
        ).strip()


def main() -> int:
    if not SERVER.is_dir():
        print(f"ERROR: expected sibling pim-offline-server at {SERVER}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    license_map = write_standard_license_texts()

    cargo_lock = SERVER / "Cargo.lock"
    cargo_toml = SERVER / "Cargo.toml"
    lock_packages = parse_cargo_lock(cargo_lock) if cargo_lock.is_file() else []
    direct = cargo_direct_names(cargo_toml) if cargo_toml.is_file() else set()
    regs = registry_roots()
    reg_index = build_registry_index(regs)

    # Deduplicate lock by name@version
    seen: set[tuple[str, str]] = set()
    unique_lock: list[tuple[str, str]] = []
    for name, ver in lock_packages:
        key = (name, ver)
        if key in seen:
            continue
        seen.add(key)
        unique_lock.append(key)

    cargo_entries: list[dict] = []
    resolved = 0
    unresolved = 0
    for name, ver in unique_lock:
        if name not in direct:
            continue
        ct = reg_index.get((name, ver))
        lic, copyright = (None, None)
        if ct:
            lic, copyright = read_crate_meta(ct)
        if lic:
            resolved += 1
        else:
            unresolved += 1
        entry = {
            "id": f"cargo:{name}@{ver}",
            "name": name,
            "version": ver,
            "ecosystem": "cargo",
            "license_spdx": normalize_spdx(lic),
            "license_name": lic,
            "copyright": copyright,
            "homepage": f"https://crates.io/crates/{name}",
            "license_text_path": None,
            "license_text_sha256": None,
            "source": "pim-offline-server/Cargo.lock + local Cargo registry Cargo.toml license field",
            "notes": None
            if lic
            else "License string not found in local Cargo registry cache for this crate/version.",
            "direct": True,
        }
        attach_license_text(entry, license_map)
        cargo_entries.append(entry)

    npm_entries = npm_direct_packages(UI / "package.json", UI / "package-lock.json", UI / "node_modules")
    for e in npm_entries:
        attach_license_text(e, license_map)

    incorporated: list[dict] = []
    add_incorporated_assets(incorporated, license_map)

    # Curated operator list: incorporated + cargo direct + npm top-level
    curated = incorporated + sorted(cargo_entries, key=lambda e: e["name"].lower()) + sorted(
        npm_entries, key=lambda e: e["name"].lower()
    )

    # Full transitive cargo appendix (names/versions only from lock — no invented licenses)
    appendix_cargo = [
        {"name": n, "version": v, "purl": f"pkg:cargo/{n}@{v}"} for n, v in unique_lock
    ]

    cargo_lock_sha = sha256_file(cargo_lock) if cargo_lock.is_file() else None
    npm_lock = UI / "package-lock.json"
    npm_lock_sha = sha256_file(npm_lock) if npm_lock.is_file() else None
    sbom_server = SERVER / "sbom" / "pim-offline-server.cdx.json"
    sbom_sha = sha256_file(sbom_server) if sbom_server.is_file() else None

    inventory = OrderedDict(
        [
            ("schema", "aic-open-source-credits"),
            ("schema_version", 1),
            ("status", "Partial"),
            (
                "honesty",
                "This inventory is Partial. It lists (1) first-party incorporated "
                "third-party assets with on-disk LICENSE copies, (2) direct Cargo "
                "dependencies of pim-offline-server with license SPDX strings read "
                "from the local Cargo registry cache when present, and (3) direct "
                "npm production dependencies from ui/package.json. The full "
                "transitive Cargo graph is enumerated in appendix.cargo_lock_packages "
                "(names and versions only) and in the committed CycloneDX SBOM under "
                "pim-offline-server/sbom/. No package or license was invented. "
                "Crates or npm packages without a resolved license string are labeled "
                "accordingly. License bodies for common SPDX identifiers are the "
                "standard published license text; uncommon SPDX expressions keep the "
                "identifier only until a full body is harvested. Transitive npm "
                "packages are not expanded in this curated list.",
            ),
            ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
            (
                "generation",
                {
                    "tool": "core-assets/scripts/generate-open-source-credits.py",
                    "cargo_lock_path": "pim-offline-server/Cargo.lock",
                    "cargo_lock_sha256": cargo_lock_sha,
                    "npm_lock_path": "pim-offline-server/ui/package-lock.json",
                    "npm_lock_sha256": npm_lock_sha,
                    "sbom_path": "pim-offline-server/sbom/pim-offline-server.cdx.json",
                    "sbom_sha256": sbom_sha,
                    "cargo_direct_resolved_licenses": resolved,
                    "cargo_direct_unresolved_licenses": unresolved,
                    "cargo_lock_package_count": len(unique_lock),
                    "cargo_registry_roots_used": len(regs),
                },
            ),
            ("entry_count", len(curated)),
            ("entries", curated),
            (
                "appendix",
                {
                    "cargo_lock_packages": appendix_cargo,
                    "notes": (
                        "Complete Cargo.lock package name/version list for the server "
                        "crate lockfile. License text for every transitive crate is "
                        "not claimed here. Cross-check the CycloneDX SBOM for hashes "
                        "and purls."
                    ),
                },
            ),
        ]
    )

    inv_path = OUT / "inventory.json"
    inv_text = json.dumps(inventory, indent=2, ensure_ascii=False) + "\n"
    inv_path.write_text(inv_text, encoding="utf-8")

    # Slim downloadable appendix (full lock names) as sibling for operators
    appendix_path = OUT / "appendix-cargo-lock.json"
    appendix_path.write_text(
        json.dumps(
            {
                "schema": "aic-open-source-credits-appendix",
                "cargo_lock_sha256": cargo_lock_sha,
                "packages": appendix_cargo,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    readme = OUT / "README.md"
    readme.write_text(
        f"""# Open Source Credits (AIC Server)

Canonical Partial inventory of open-source and incorporated third-party
components credited in the AIC Server Admin **About → Open Source Credits**
page.

## Honesty

Status: **Partial**. Generated by `scripts/generate-open-source-credits.py`
from real lockfiles and in-tree LICENSE copies. See `inventory.json`
`honesty` field. Do not claim this list is a complete license harvest of
every transitive crate.

## Files

| File | Role |
| --- | --- |
| `inventory.json` | Curated entries + honesty metadata + generation SHAs |
| `appendix-cargo-lock.json` | Full Cargo.lock name/version list |
| `license-texts/` | SPDX standard texts + incorporated LICENSE copies |

## Regenerate

```text
python scripts/generate-open-source-credits.py
```

Then sync into `pim-offline-server/ui/public/legal/open-source-credits/`
via `scripts/sync-to-projects.ps1` (map entry) or copy for local lab.

Inventory SHA-256: `{sha256_text(inv_text)}`
Entries: {len(curated)}
Cargo.lock packages (appendix): {len(unique_lock)}
""",
        encoding="utf-8",
    )

    print(f"Wrote {inv_path} ({len(curated)} curated entries)")
    print(f"Cargo direct licenses resolved={resolved} unresolved={unresolved}")
    print(f"Cargo.lock packages={len(unique_lock)} npm top-level={len(npm_entries)}")

    # Sync copies into the server tree (canonical remains core-assets).
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
            dest.write_bytes(src.read_bytes())
        print(f"Synced -> {dest_root}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
