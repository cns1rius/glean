"""
Vercel serverless entry point.

Vercel Python runtime requires app to be defined at top level.
This module imports the full Glean backend.
"""

import sys
from pathlib import Path

# Set up paths for backend imports
# Project structure: glean/{api,backend,frontend}/
_project_root = Path(__file__).parent
_backend_path = _project_root / "backend"

# Add backend packages to path
sys.path.insert(0, str(_backend_path / "apps" / "api"))
sys.path.insert(0, str(_backend_path / "packages" / "database"))
sys.path.insert(0, str(_backend_path / "packages" / "core"))
sys.path.insert(0, str(_backend_path / "packages" / "rss"))
sys.path.insert(0, str(_backend_path / "packages" / "vector"))

from glean_api.main import app
