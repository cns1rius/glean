"""
Vercel serverless entry point.

Import Glean backend directly from source paths.
"""

import sys
from pathlib import Path

# Add backend source paths to sys.path
# This allows importing glean modules directly without workspace packages
_backend = Path(__file__).parent / "backend"
sys.path.insert(0, str(_backend / "apps" / "api"))
sys.path.insert(0, str(_backend / "packages" / "database"))
sys.path.insert(0, str(_backend / "packages" / "core"))
sys.path.insert(0, str(_backend / "packages" / "rss"))
sys.path.insert(0, str(_backend / "packages" / "vector"))

from glean_api.main import app
