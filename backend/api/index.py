"""
Vercel serverless entry point.

This module wraps the FastAPI application for deployment on Vercel.
Vercel Python functions use a handler-based interface.

Usage:
    Deploy the backend/ directory to Vercel.
    Set environment variables in Vercel dashboard.
"""

from glean_api.main import app

# Vercel Python handler
# The handler must be a callable that takes (req, res) for Vercel's interface
handler = app
