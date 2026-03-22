"""
Vercel serverless entry point.
"""

import sys
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Vercel deployment root is /var/task
# Add backend paths using absolute paths
_backend = "/var/task/backend"
sys.path.insert(0, f"{_backend}/apps/api")
sys.path.insert(0, f"{_backend}/packages/database")
sys.path.insert(0, f"{_backend}/packages/core")
sys.path.insert(0, f"{_backend}/packages/rss")
sys.path.insert(0, f"{_backend}/packages/vector")

app = FastAPI()

@app.get("/api/test")
def test():
    return JSONResponse({
        "message": "Python works!",
        "status": "ok",
        "sys_path": sys.path[:3]
    })
