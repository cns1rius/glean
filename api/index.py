"""
Vercel serverless entry point - Standalone test.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/test")
def test():
    return JSONResponse({"message": "Python works!", "status": "ok"})

@app.get("/api/health")
def health():
    return JSONResponse({"status": "healthy", "mode": "standalone"})
