"""PyInstaller entrypoint for the Tauri sidecar.

Imports the FastAPI app object directly and runs it via uvicorn's
programmatic API instead of the `uvicorn main:app` CLI string form —
PyInstaller can't follow the dynamic "module:attr" string used by the CLI,
so it would miss `main.py` entirely.
"""

import os

import uvicorn

from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
