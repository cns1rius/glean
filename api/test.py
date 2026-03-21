"""
Simple test endpoint to verify Python functions work on Vercel.
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/api/test")
def test():
    return {"message": "Python works!", "status": "ok"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

handler = app
