#!/usr/bin/env python3
"""Find typographic characters standing in for ASCII syntax.

A word processor, a chat client, or a model that has read too much prose will
"improve" a hyphen into an en-dash and a straight quote into a curly one. In
prose that is correct typography. In a command line it is a defect, and on
Windows PowerShell it is a defect with three distinct failure modes, none of
which names the real cause:

1.  A .ps1 saved as UTF-8 WITHOUT a BOM is read by Windows PowerShell 5.1 as
    Windows-1252. The three bytes of an em-dash (E2 80 94) decode as three
    CP1252 characters, the last of which is a right double quotation mark. A
    string literal containing an em-dash therefore terminates early, and the
    parser reports "The string is missing the terminator" plus "Missing closing
    '}'" pointing at a line far below the real one. Verified on this host; it is
    the shape that broke Stage-MaxMindGeoLiteDefaults.ps1 and
    Prove-JumpFleetCapacity.ps1.

2.  PowerShell's own tokenizer NORMALIZES U+2013, U+2014, and U+2015 when they
    prefix a parameter, so `Get-Item -Force` and `Get-Item \u2013Force` both bind.
    That is the trap: the defect passes a local smoke test and ships.

3.  External executables do no such normalization. `git \u2013\u2013version` exits 1 with
    "'\u2013\u2013version' is not a git command". curl.exe exits 6 and prints "The
    argument starts with a Unicode character. Maybe ASCII was intended?" - a
    warning it carries precisely because this defect is so common.

Beyond PowerShell the cost is searchability. An en-dash inside "NIST SP 800-53"
produces "800\u201353", which an assessor searching a binder export does not match
and a crosswalk keyed on the identifier silently drops. That already happened in
the shipped locale catalogs; see language-packs/_audit_endash_identifiers.py.

DETECTION IS ASYMMETRIC BY DESIGN. In a script or a source file a typographic
dash is always wrong, so it fails the run. In a shipped locale catalog it may be
the target language's orthography -- German and French prose legitimately use an
em-dash as punctuation -- so those hits are REPORTED and never failed on, and
--fix never touches them. The one exception is a dash inside an identifier,
which no orthography requires: that stays a hard hit in any language.

Usage:
  assert-ascii-syntax.py PATH [PATH ...]           report; exit 1 on hard hits
  assert-ascii-syntax.py PATH --fix                rewrite hard hits to ASCII
  assert-ascii-syntax.py PATH --ext .ps1 .rs       restrict the extension set
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

DEFAULT_EXTENSIONS = (
    ".ps1",
    ".psm1",
    ".rs",
    ".ts",
    ".tsx",
    ".py",
    ".json",
    ".toml",
    ".yml",
)

# Each banned codepoint maps to the ASCII character it was substituted for.
BANNED: dict[str, tuple[str, str]] = {
    "\u2010": ("-", "HYPHEN"),
    "\u2011": ("-", "NON-BREAKING HYPHEN"),
    "\u2012": ("-", "FIGURE DASH"),
    "\u2013": ("-", "EN DASH"),
    "\u2014": ("-", "EM DASH"),
    "\u2015": ("-", "HORIZONTAL BAR"),
    "\u2212": ("-", "MINUS SIGN"),
    "\u2018": ("'", "LEFT SINGLE QUOTATION MARK"),
    "\u2019": ("'", "RIGHT SINGLE QUOTATION MARK"),
    "\u201c": ('"', "LEFT DOUBLE QUOTATION MARK"),
    "\u201d": ('"', "RIGHT DOUBLE QUOTATION MARK"),
    "\u00a0": (" ", "NO-BREAK SPACE"),
}

BANNED_RE = re.compile("[" + "".join(BANNED) + "]")

# Mojibake: a UTF-8 byte sequence that was decoded as Windows-1252 and then
# re-encoded as UTF-8. Repairing only the trailing smart quote of "\u00e2\u20ac\u201d" would
# leave "\u00e2\u20ac-" behind, so these sequences are matched whole and first.
# Real example in the tree: Prove-WinrmPrivilegeJob.ps1 ships both an em-dash
# and a rightwards arrow that went through this round trip.
MOJIBAKE: dict[str, tuple[str, str]] = {
    "\u00e2\u20ac\u201d": ("-", "EM DASH via CP1252 (E2 80 94)"),
    "\u00e2\u20ac\u201c": ("-", "EN DASH via CP1252 (E2 80 93)"),
    "\u00e2\u20ac\u2122": ("'", "APOSTROPHE via CP1252 (E2 80 99)"),
    "\u00e2\u20ac\u0153": ('"', "LEFT QUOTE via CP1252 (E2 80 9C)"),
    "\u00e2\u2020\u2019": ("->", "RIGHTWARDS ARROW via CP1252 (E2 86 92)"),
    "\u00c2\u00a0": (" ", "NO-BREAK SPACE via CP1252 (C2 A0)"),
}

MOJIBAKE_RE = re.compile("|".join(re.escape(k) for k in MOJIBAKE))

# Identifier families this product cites. A dash here is a corrupted identifier
# in any language, so it is a hard hit even inside translated prose.
CONTROL_FAMILIES = "AC|AT|AU|CA|CM|CP|IA|IR|MA|MP|PE|PL|PM|PS|PT|RA|SA|SC|SI|SR"
STANDARDS = "CVE|ISO|IEC|RFC|FIPS|NIST|SP|CIS|CCI"
IDENTIFIER_DASH = re.compile(
    r"(?:\b800"
    rf"|\b(?:{CONTROL_FAMILIES})"
    rf"|\b(?:{STANDARDS})"
    r"|\bL\d)"
    r"([\u2010-\u2015\u2212])"
    r"(?=[0-9A-Za-z])"
)

# Directory names that mean "shipped translation", where typographic
# punctuation may be the target language's own orthography.
PROSE_DIRS = frozenset({"locales", "locales-ui", "i18n", "language-packs"})


def is_prose_catalog(path: Path) -> bool:
    """True when the file is a shipped locale catalog rather than source."""
    if path.suffix.lower() != ".json":
        return False
    return bool(PROSE_DIRS.intersection(p.lower() for p in path.parts))


def read_text(path: Path) -> tuple[str, bool]:
    """Return (text, has_utf8_bom). Decodes as UTF-8, replacing bad bytes."""
    raw = path.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    return raw.decode("utf-8-sig" if bom else "utf-8", errors="replace"), bom


def scan_line(line: str, prose: bool) -> list[tuple[int, str, str, bool]]:
    """Return (col, label, replacement, is_hard) for each hit on a line."""
    out: list[tuple[int, str, str, bool]] = []

    # Mojibake first, and record its span so its component codepoints are not
    # also reported individually.
    covered: set[int] = set()
    for match in MOJIBAKE_RE.finditer(line):
        seq = match.group(0)
        ascii_out, label = MOJIBAKE[seq]
        covered.update(range(match.start(), match.end()))
        out.append((match.start() + 1, label, ascii_out, True))

    identifier_cols = {m.start(1) for m in IDENTIFIER_DASH.finditer(line)}
    for match in BANNED_RE.finditer(line):
        if match.start() in covered:
            continue
        char = match.group(0)
        ascii_out, name = BANNED[char]
        # Outside a translation, every hit is hard. Inside one, only a dash
        # sitting in an identifier is -- the rest is the language's own comma.
        hard = (not prose) or (match.start() in identifier_cols)
        out.append(
            (match.start() + 1, f"U+{ord(char):04X} {name}", ascii_out, hard)
        )
    return sorted(out)


def repair_line(line: str, prose: bool) -> str:
    """Rewrite only the hard hits on a line, leaving prose punctuation alone."""
    line = MOJIBAKE_RE.sub(lambda m: MOJIBAKE[m.group(0)][0], line)
    if not prose:
        return BANNED_RE.sub(lambda m: BANNED[m.group(0)][0], line)
    return IDENTIFIER_DASH.sub(lambda m: m.group(0)[:-1] + "-", line)


def write_bytes_retrying(path: Path, payload: bytes, attempts: int = 4) -> None:
    """Write with bounded backoff.

    Rewriting hundreds of files back to back races Defender's on-access scanner
    on this host and surfaces as OSError [Errno 22] Invalid argument. The write
    is idempotent, so retrying is safe; giving up silently would not be.
    """
    for attempt in range(1, attempts + 1):
        try:
            path.write_bytes(payload)
            return
        except OSError as exc:
            if attempt == attempts:
                raise OSError(f"failed to write {path} after {attempts} attempts") from exc
            time.sleep(0.2 * attempt)


def iter_files(roots: list[Path], extensions: tuple[str, ...]):
    for root in roots:
        if root.is_file():
            if root.suffix.lower() in extensions:
                yield root
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in extensions:
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report typographic characters used where ASCII syntax is required."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--ext",
        nargs="+",
        default=list(DEFAULT_EXTENSIONS),
        help=f"extensions to scan (default: {' '.join(DEFAULT_EXTENSIONS)})",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="rewrite hard hits to ASCII; prose punctuation is never touched",
    )
    args = parser.parse_args()

    extensions = tuple(
        e.lower() if e.startswith(".") else "." + e.lower() for e in args.ext
    )

    hard: list[tuple[Path, bool, list[tuple[int, int, str, str]]]] = []
    prose_only: list[tuple[Path, list[str]]] = []
    scanned = 0

    for path in iter_files([p.resolve() for p in args.paths], extensions):
        scanned += 1
        text, bom = read_text(path)
        if not (BANNED_RE.search(text) or MOJIBAKE_RE.search(text)):
            continue
        prose = is_prose_catalog(path)
        hard_hits: list[tuple[int, int, str, str]] = []
        soft_names: list[str] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            for col, label, ascii_out, is_hard in scan_line(line, prose):
                if is_hard:
                    hard_hits.append((line_no, col, label, ascii_out))
                else:
                    soft_names.append(label)
        if hard_hits:
            hard.append((path, bom, hard_hits))
        if soft_names:
            prose_only.append((path, soft_names))

    print(f"scanned {scanned} file(s) for {len(BANNED)} banned codepoint(s)\n")

    if hard:
        total = sum(len(h) for _, _, h in hard)
        print(f"HARD: {total} hit(s) in {len(hard)} file(s)")
        for path, bom, hits in hard:
            flag = "" if bom else "   [no BOM: PowerShell 5.1 misparses this]"
            print(f"\n  {path}{flag}")
            for line, col, label, ascii_out in hits:
                print(f"    {path.name}:{line}:{col}  {label} -> {ascii_out!r}")
    else:
        print("HARD: none")

    if prose_only:
        total = sum(len(n) for _, n in prose_only)
        print(
            f"\nPROSE: {total} hit(s) in {len(prose_only)} locale file(s) "
            "-- reported only, target-language orthography, never rewritten"
        )
        for path, names in prose_only:
            kinds = ", ".join(sorted(set(names)))
            print(f"  {path}  {len(names)} hit(s): {kinds}")

    if not args.fix:
        if hard:
            print("\n(report only -- pass --fix to rewrite the hard hits to ASCII)")
        return 1 if hard else 0

    rewritten = 0
    for path, bom, _ in hard:
        text, _ = read_text(path)
        prose = is_prose_catalog(path)
        fixed = "".join(
            repair_line(chunk, prose) for chunk in text.splitlines(keepends=True)
        )
        if fixed == text:
            continue
        # UTF-8 out; the BOM is preserved only when the file already carried one,
        # and splitlines(keepends=True) leaves CRLF or LF exactly as found.
        encoded = fixed.encode("utf-8")
        write_bytes_retrying(path, (b"\xef\xbb\xbf" + encoded) if bom else encoded)
        rewritten += 1
    print(f"\nrewrote {rewritten} file(s) to ASCII syntax")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
