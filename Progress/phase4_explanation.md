# Phase 4 — REST API Integration

## Overview
Phase 4 connects the core TicketWise engine (`engine.py`) to an external REST API using **FastAPI**. It exposes HTTP endpoints for health monitoring and ticket triaging, backed by automated validation and error handling.

---

## What Was Built

### 1. Application Setup & Lifespan (`main.py`)
- Initialized FastAPI app with OpenAPI tags and interactive documentation at `/docs` and `/redoc`.
- Added an asynchronous `lifespan` context manager to handle startup and shutdown events cleanly.

### 2. Diagnostic & Health Endpoints
- `GET /`: Returns service metadata, status, version, and documentation link.
- `GET /health`: Returns service health status and UTC timestamp for monitoring and uptime probes.

### 3. Triage Endpoint (`POST /triage`)
- Accepts customer tickets matching the `TicketInput` contract (email, subject, message).
- Passes the validated ticket directly to `triage(ticket)` from `engine.py`.
- Returns the complete `TriageResult` (ticket ID, timestamp, classification, matched policy, similarity score, and formatted response).

### 4. Request & Response Validation
- **Request Validation**: Automatically enforced by FastAPI using Pydantic's `TicketInput`. If an email is missing `@` or fields exceed character limits, FastAPI immediately returns HTTP `422 Unprocessable Entity`.
- **Response Validation**: Enforced by `response_model=TriageResult`, ensuring only defined fields are returned and types are strictly preserved.

### 5. Multi-Layer Error Handling
- **Structured Error Model (`TriageErrorResponse`)**: Standardized error schema containing `error`, `detail`, and `status_code`.
- **Upstream AI Failures (HTTP 502 Bad Gateway)**: Catches Google GenAI API errors (network interruptions, invalid keys, or rate limits) so callers receive a clear retryable status code instead of an opaque crash.
- **Pipeline Data Violations (HTTP 422)**: Catches any internal `ValidationError` if the LLM output violates Pydantic constraints.
- **Global Safety Net (HTTP 500)**: Catches unhandled exceptions via `@app.exception_handler(Exception)`, logs full tracebacks to the server log, and returns a safe error response without leaking internal code details.

---

## System Flow

```
Incoming Request (POST /triage)
         │
         ▼
[ FastAPI / Pydantic Validation ] ── (Invalid) ──► HTTP 422 Validation Error
         │ (Valid TicketInput)
         ▼
[ Unified Engine (engine.py) ]
  ├── 1. Gemini Classifier (classifier.py)
  ├── 2. Semantic Retrieval (retrieval.py)
  └── 3. Deterministic Router (router.py)
         │
         ├── Upstream AI Failure  ──────────────► HTTP 502 Bad Gateway
         ├── Internal Error       ──────────────► HTTP 500 Server Error
         │
         ▼ (Success)
HTTP 200 OK + TriageResult JSON
```

---

## Quick Testing

### Run the API Server
```bash
uv run ai-dev
# or
uv run uvicorn ai_dev.main:app --reload
```

### 1. Test Healthy Triage
```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "alice@example.com",
    "subject": "Charged twice",
    "message": "I was charged $29.99 twice this month. Please refund."
  }'
```
*Expected: HTTP 200 with structured `TriageResult` JSON.*

### 2. Test Input Validation
```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "invalid-email-address",
    "subject": "Help",
    "message": "Need support"
  }'
```
*Expected: HTTP 422 stating "Email must contain '@'".*
