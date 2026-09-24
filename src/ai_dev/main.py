"""
Phase 4 — FastAPI Application Entry Point

Foundational REST API application for TicketWise.
Provides API configuration, lifecycle management (lifespan),
health check endpoints, and automatic OpenAPI / Swagger documentation.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

# Load environment variables (.env)
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ticketwise.api")


# ── Lifespan Management ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle.
    Code before `yield` runs on startup; code after `yield` runs on shutdown.
    """
    logger.info("Starting TicketWise API...")
    # Any startup initialization (e.g. warming up caches, checking API keys) goes here
    yield
    logger.info("Shutting down TicketWise API...")


# ── API Metadata & Tags ──────────────────────────────────────────────
tags_metadata = [
    {
        "name": "System",
        "description": "API health, status, and root diagnostic endpoints.",
    },
    {
        "name": "Triage",
        "description": "Ticket classification, semantic retrieval, and routing endpoints (Upcoming).",
    },
]

app = FastAPI(
    title="TicketWise Triage API",
    description="Intelligent Customer Support Ticket Triage and Routing Engine built with FastAPI, Gemini, and Semantic Retrieval.",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── System Endpoints ─────────────────────────────────────────────────
@app.get(
    "/",
    tags=["System"],
    summary="API Root Information",
    description="Returns welcome message, API version, and link to interactive Swagger documentation.",
)
async def root():
    return {
        "message": "Welcome to the TicketWise API",
        "version": "0.1.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Check whether the API service is alive and healthy.",
)
async def health_check():
    return {
        "status": "healthy",
        "service": "ticketwise-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Server Runner ────────────────────────────────────────────────────
def start():
    """Start the Uvicorn ASGI server with live reloading enabled."""
    uvicorn.run("ai_dev.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    start()
