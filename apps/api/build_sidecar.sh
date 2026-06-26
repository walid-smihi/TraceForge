#!/usr/bin/env bash
# Builds the FastAPI backend into a single-file executable via PyInstaller
# and places it where Tauri expects to find its sidecar binary.
#
# Tauri's sidecar convention requires the binary to be named
# "<name>-<target-triple>" — must be re-run on each OS you want to target
# (PyInstaller does not cross-compile).
set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR="${VENV_DIR:-.sidecar-venv}"
TARGET_TRIPLE="$(rustc -vV | sed -n 's/host: //p')"
OUT_DIR="../desktop/src-tauri/binaries"

if [ -z "$TARGET_TRIPLE" ]; then
  echo "Could not determine target triple — is rustc installed?" >&2
  exit 1
fi

python3 -m venv "$VENV_DIR"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r requirements.txt pyinstaller

pyinstaller --onefile --name traceforge-backend --noconfirm --clean \
  --collect-all pymupdf \
  --collect-all fastapi \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols \
  --hidden-import uvicorn.protocols.http \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan \
  --hidden-import uvicorn.lifespan.on \
  --hidden-import aiosqlite \
  desktop_entrypoint.py

mkdir -p "$OUT_DIR"
EXT=""
[[ "$TARGET_TRIPLE" == *windows* ]] && EXT=".exe"
cp "dist/traceforge-backend$EXT" "$OUT_DIR/traceforge-backend-$TARGET_TRIPLE$EXT"

echo "Sidecar built: $OUT_DIR/traceforge-backend-$TARGET_TRIPLE$EXT"
