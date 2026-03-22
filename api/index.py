"""
Vercel serverless entry point.
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add backend paths
_backend = Path(__file__).parent / "backend"
sys.path.insert(0, str(_backend / "apps" / "api"))
sys.path.insert(0, str(_backend / "packages" / "database"))
sys.path.insert(0, str(_backend / "packages" / "core"))
sys.path.insert(0, str(_backend / "packages" / "rss"))
sys.path.insert(0, str(_backend / "packages" / "vector"))

app = FastAPI()

@app.get("/api/test")
def test():
    return JSONResponse({"message": "Python works!", "status": "ok", "phase": "paths_added"})
