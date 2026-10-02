"""
Phase 4 — FastAPI Application Entry Point

Foundational REST API application for TicketWise.
Provides API configuration, lifecycle management (lifespan),
health check endpoints, error handling, request/response validation,
and automatic OpenAPI / Swagger documentation.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import uvicorn

from ai_dev.contract import TicketInput, TriageResult
from ai_dev.engine import triage, triage_detailed

# Load environment variables (.env)
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ticketwise.api")


# ── Error Response Model ─────────────────────────────────────────────
class TriageErrorResponse(BaseModel):
    """Structured error body returned when triage fails."""
    error: str
    detail: str
    status_code: int


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
        "description": "Ticket classification, semantic retrieval, and routing endpoints.",
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

# ── CORS Middleware (allows Streamlit UI to call the API) ────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for any unhandled exception that slips through.
    Logs the full traceback and returns a clean 500 response
    instead of leaking internal details to the caller.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=TriageErrorResponse(
            error="internal_server_error",
            detail="An unexpected error occurred. Please try again later.",
            status_code=500,
        ).model_dump(),
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


# ── Triage Endpoint ──────────────────────────────────────────────────
@app.post(
    "/triage",
    tags=["Triage"],
    summary="Triage a customer support ticket",
    response_model=TriageResult,
    responses={
        422: {
            "description": "Validation Error — request body failed Pydantic checks "
                           "(e.g. missing '@' in email, subject > 100 chars).",
        },
        502: {
            "description": "Bad Gateway — the upstream Gemini API call failed "
                           "(network error, invalid key, rate limit).",
            "model": TriageErrorResponse,
        },
        500: {
            "description": "Internal Server Error — an unexpected failure occurred.",
            "model": TriageErrorResponse,
        },
    },
)
async def triage_ticket(ticket: TicketInput):
    """
    Accepts a customer support ticket and runs the full pipeline:
    classification → semantic retrieval → routing.
    """
    try:
        result = triage(ticket)
        return result

    except ValidationError as exc:
        # Pydantic validation failed on the *response* side
        # (e.g. Gemini returned a confidence of 1.5, which violates ge=0/le=1)
        logger.warning(
            "Response validation error for ticket from %s: %s",
            ticket.customer_email,
            exc,
        )
        raise HTTPException(
            status_code=422,
            detail=f"The triage pipeline produced invalid data: {exc.error_count()} validation error(s).",
        )

    except Exception as exc:
        # Catch Gemini / network / embedding errors
        exc_name = type(exc).__name__

        # Google GenAI SDK raises various errors for API issues —
        # treat them all as upstream failures (502 Bad Gateway).
        if "google" in type(exc).__module__.lower() if hasattr(type(exc), "__module__") else False:
            logger.error(
                "Gemini API error while triaging ticket from %s: [%s] %s",
                ticket.customer_email,
                exc_name,
                exc,
            )
            raise HTTPException(
                status_code=502,
                detail=f"Upstream AI service error ({exc_name}). Please try again later.",
            )

        # Anything else is a genuine internal error
        logger.error(
            "Unexpected error while triaging ticket from %s: [%s] %s",
            ticket.customer_email,
            exc_name,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your ticket. Please try again later.",
        )


# ── Detailed Triage Endpoint (for Streamlit UI) ─────────────────────
@app.post(
    "/triage/detail",
    tags=["Triage"],
    summary="Triage with full similarity breakdown",
    description="Returns the standard TriageResult plus similarity scores against ALL KB policies for visualization.",
    responses={
        502: {
            "description": "Bad Gateway — the upstream Gemini API call failed.",
            "model": TriageErrorResponse,
        },
        500: {
            "description": "Internal Server Error — an unexpected failure occurred.",
            "model": TriageErrorResponse,
        },
    },
)
async def triage_ticket_detailed(ticket: TicketInput):
    """
    Extended triage endpoint: runs the full pipeline and returns
    all similarity scores for every KB policy (for Streamlit visualization).
    """
    try:
        detailed = triage_detailed(ticket)
        result = detailed["triage_result"]
        return {
            "ticket_id": result.ticket_id,
            "timestamp": result.timestamp.isoformat(),
            "classification": {
                "category": result.classification.category,
                "confidence": result.classification.confidence,
                "reasoning": result.classification.reasoning,
                "priority": result.classification.priority,
            },
            "matched_policy": result.matched_policy,
            "similarity_score": result.similarity_score,
            "response_message": result.response_message,
            "all_similarity_scores": detailed["all_similarity_scores"],
        }

    except ValidationError as exc:
        logger.warning("Response validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail=f"The triage pipeline produced invalid data: {exc.error_count()} validation error(s).",
        )

    except Exception as exc:
        exc_name = type(exc).__name__
        if "google" in type(exc).__module__.lower() if hasattr(type(exc), "__module__") else False:
            logger.error("Gemini API error: [%s] %s", exc_name, exc)
            raise HTTPException(
                status_code=502,
                detail=f"Upstream AI service error ({exc_name}). Please try again later.",
            )
        logger.error("Unexpected error: [%s] %s", exc_name, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your ticket. Please try again later.",
        )


# ── Server Runner ────────────────────────────────────────────────────
def start():
    """Start the Uvicorn ASGI server with live reloading enabled."""
    uvicorn.run("ai_dev.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    start()

