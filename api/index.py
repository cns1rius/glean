"""
Vercel serverless entry point.

This module wraps the FastAPI application for deployment on Vercel.
Vercel expects the api/ directory at the project root.

Usage:
    Deploy the project with vercel.json at root.
    Set environment variables in Vercel dashboard.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from glean_api.main import app

# Vercel Python handler
handler = app
