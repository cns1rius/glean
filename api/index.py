"""
Vercel serverless entry point.

Import Glean backend directly from source paths.
"""

import sys
from pathlib import Path
import traceback

# Add backend source paths to sys.path
_backend = Path(__file__).parent / "backend"
sys.path.insert(0, str(_backend / "apps" / "api"))
sys.path.insert(0, str(_backend / "packages" / "database"))
sys.path.insert(0, str(_backend / "packages" / "core"))
sys.path.insert(0, str(_backend / "packages" / "rss"))
sys.path.insert(0, str(_backend / "packages" / "vector"))

try:
    from glean_api.main import app
except Exception as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    raise
