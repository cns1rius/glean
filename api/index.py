"""
Vercel serverless entry point.
"""

import sys
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Vercel deployment root is /var/task
_backend = "/var/task/backend"
sys.path.insert(0, f"{_backend}/apps/api")
sys.path.insert(0, f"{_backend}/packages/database")
sys.path.insert(0, f"{_backend}/packages/core")
sys.path.insert(0, f"{_backend}/packages/rss")
sys.path.insert(0, f"{_backend}/packages/vector")

# Test import
try:
    from glean_api.main import app as glean_app
    import_result = "glean_api.main imported OK"
except Exception as e:
    import_result = f"import failed: {type(e).__name__}: {e}"

app = FastAPI()

@app.get("/api/test")
def test():
    return JSONResponse({
        "message": "Python works!",
        "status": "ok",
        "import": import_result
    })
