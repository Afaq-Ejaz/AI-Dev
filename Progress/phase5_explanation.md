# Phase 5 — Verification Interface & Stress Testing

## Overview
Phase 5 adds a **Streamlit dashboard** (`dashboard.py`) that connects directly to the Phase 4 FastAPI backend. It provides a visual interface to submit tickets, inspect the full triage pipeline output, visualize similarity scores across all KB policies, and run pre-built stress test suites to verify system robustness.

---

## What Was Built

### 1. Backend Enhancements (`main.py` + `engine.py`)
- **CORS Middleware**: Added `CORSMiddleware` to FastAPI so the Streamlit UI (running on a different port) can call the API without cross-origin errors.
- **`POST /triage/detail` Endpoint**: A new extended endpoint that returns the standard `TriageResult` *plus* all similarity scores against every KB policy — enabling the dashboard to render the full retrieval landscape.
- **`triage_detailed()` in `engine.py`**: An extended pipeline function that computes similarity scores against all 8 KB policies (not just the top match) and returns them alongside the regular triage result.

### 2. Streamlit Dashboard (`dashboard.py`)
- **Ticket Submission Form**: Email, subject, and message fields with real-time validation. Sends the ticket to `/triage/detail` and renders the result.
- **Classification Display**: Category, priority, confidence, and similarity score shown as color-coded metric cards with gradient backgrounds.
- **AI Reasoning & Response**: Shows the LLM's reasoning for its classification decision and the deterministic router's response message side-by-side.
- **Interactive Similarity Chart**: A horizontal Plotly bar chart showing cosine similarity scores for all 8 KB policies, with the matched policy highlighted. Lets you visually verify retrieval accuracy.

### 3. Stress Test Suite
Three built-in test suites with **12 total test tickets**, runnable individually or as a batch:

| Suite | Purpose | Test Cases |
|---|---|---|
| 🌫️ **Vague Queries** | Insufficient or ambiguous information | Minimal info, off-topic, ambiguous intent, single-word |
| 😡 **Aggressive Messages** | Emotional tone shouldn't break classification | Angry billing, frustrated bug, threatening escalation, ALL CAPS rage |
| 🔀 **Mixed Issues** | Multi-category tickets should pick the dominant issue | Billing+Bug, Account+Escalation, FAQ+Billing, Bug+Account+Billing |

### 4. Session History Tracker
- Tracks every triaged ticket in the session with a summary table.
- Sidebar shows real-time category and priority breakdowns.
- Each historical result is expandable for full detail + similarity chart.

---

## System Flow (Phase 5 Complete Architecture)

```
                    ┌────────────────────────────┐
                    │   Streamlit Dashboard       │
                    │   (dashboard.py :8501)      │
                    │                             │
                    │  ┌─ Submit Ticket ─────┐    │
                    │  │  Email / Subject /   │    │
                    │  │  Message form        │    │
                    │  └──────────┬───────────┘    │
                    │             │                │
                    │  ┌─ Stress Tests ──────┐    │
                    │  │  Vague / Aggressive / │   │
                    │  │  Mixed issue suites   │   │
                    │  └──────────┬───────────┘    │
                    └─────────────┼────────────────┘
                                  │ HTTP POST
                                  │ /triage/detail
                                  ▼
                    ┌────────────────────────────┐
                    │   FastAPI Server            │
                    │   (main.py :8000)           │
                    │                             │
                    │   CORS ─► Validation ─►     │
                    │   Engine Pipeline ─►         │
                    │   Detailed Response          │
                    └─────────────┬────────────────┘
                                  │
                    ┌─────────────▼────────────────┐
                    │   Unified Engine (engine.py)  │
                    │                               │
                    │   1. Gemini Classifier         │
                    │   2. Semantic Retrieval (all)  │
                    │   3. Deterministic Router      │
                    └───────────────────────────────┘
```

---

## How to Run

### Step 1: Start the FastAPI server (Terminal 1)
```bash
uv run ai-dev
```

### Step 2: Start the Streamlit dashboard (Terminal 2)
```bash
uv run streamlit run src/ai_dev/dashboard.py
```

The dashboard opens at `http://localhost:8501`.

---

## Key Design Decisions

### Why call the API instead of importing engine directly?
The dashboard calls the FastAPI server over HTTP rather than importing `engine.py` directly. This:
1. **Tests the real deployment path** — the same path a production frontend or mobile app would use.
2. **Validates error handling** — CORS, HTTP status codes, and error responses are exercised.
3. **Proves the API layer works end-to-end** — classification → retrieval → routing → serialization → HTTP response → deserialization.

### Why a `/triage/detail` endpoint?
The original `POST /triage` returns only the top-matched policy. For verification, we need to see *all* similarity scores to confirm the retrieval system ranked policies correctly. The detail endpoint adds this without modifying the original contract.

### Why are stress tests hardcoded in the dashboard?
They serve as a **regression test suite** — predetermined edge cases that you can re-run after any code change to verify nothing broke. The labels ("Angry billing complaint", "Mixed Bug+Billing") make it clear what each test is validating.
