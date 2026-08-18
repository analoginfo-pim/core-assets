#!/usr/bin/env bash
# Thin wrapper — all logic is in language_packs.py (Python 3 stdlib).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$ROOT/scripts/language-packs/language_packs.py" --root "$ROOT" "$@"
fi
exec python "$ROOT/scripts/language-packs/language_packs.py" --root "$ROOT" "$@"
