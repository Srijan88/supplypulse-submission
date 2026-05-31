from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import run_supplypulse_pipeline


class PipelineRunRequest(BaseModel):
    question: str


app = FastAPI(
    title="SupplyPulse V2 API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://supplypulse-submission.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "SupplyPulse V2 API",
        "health": "/api/health",
        "docs": "/docs",
    }


@app.get("/health")
def health_alias() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "SupplyPulse V2 API",
    }


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "SupplyPulse V2 API",
    }


@app.post("/api/pipeline/run")
def run_pipeline(request: PipelineRunRequest) -> Dict[str, Any]:
    result = run_supplypulse_pipeline(request.question)

    return {
        "success": True,
        "pipelineResult": result,
    }
