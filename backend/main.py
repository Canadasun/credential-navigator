"""Credential Navigator API.  Run from backend/:  uvicorn main:app --reload"""
from fastapi import FastAPI

from api import analysis
from core.config import DISCLAIMER

app = FastAPI(title="Credential Navigator", description=DISCLAIMER, version="0.1.0")
app.include_router(analysis.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
