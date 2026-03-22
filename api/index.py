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

# Test importing glean_core
try:
    from glean_core import get_logger
    logger = get_logger(__name__)
    logger.info("glean_core imported successfully")
    import_result = "glean_core OK"
except Exception as e:
    import_result = f"glean_core failed: {e}"

app = FastAPI()

@app.get("/api/test")
def test():
    return JSONResponse({
        "message": "Python works!",
        "status": "ok",
        "import": import_result
    })
