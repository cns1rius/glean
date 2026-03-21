"""
Vercel serverless entry point.

This module wraps the FastAPI application for deployment on Vercel.
Vercel expects the api/ directory at the project root.
"""

import sys
from pathlib import Path

# Add backend to path for imports
# Project structure: glean/{api,backend,frontend}/
_backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(_backend_path))
sys.path.insert(0, str(_backend_path / "apps"))
sys.path.insert(0, str(_backend_path / "packages"))

from glean_api.main import app

# Vercel Python handler
handler = app
