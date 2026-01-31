#!/usr/bin/env python3
"""Run Flask app with backend on PYTHONPATH."""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root so "backend" package is found
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.app import app, preload_data

if __name__ == "__main__":
    import os
    preload_data()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
