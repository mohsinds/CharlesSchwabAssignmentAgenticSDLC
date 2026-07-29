"""FastAPI control plane."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.routers import audit, health, metrics, pipelines, signals
from services.common.config import configure_langsmith, get_settings
from services.common.logging import configure_logging, get_logger

configure_logging()
settings = get_settings()
_tracing_on = configure_langsmith()
get_logger(__name__).info("langsmith_tracing", enabled=_tracing_on)

app = FastAPI(
    title="Agentic SDLC API",
    version="0.1.0",
    description="Control plane for Temporal/LangGraph SDLC pipelines",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(pipelines.router)
app.include_router(signals.router)
app.include_router(audit.router)
app.include_router(metrics.router)


@app.get("/")
async def root() -> dict:
    return {"service": "agentic-sdlc-api", "docs": "/docs"}
