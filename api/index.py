"""
Vercel serverless entry point.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/test")
def test():
    return JSONResponse({"message": "Python works!", "status": "ok"})
