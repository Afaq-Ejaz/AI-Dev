# TicketWise — Development Phases & Progress Tracker

## Current Status: PHASE 1
**Immediate Tasks:**
- [x] Design `TicketInput` Pydantic model.
- [x] Design `TicketClassification` Pydantic model.
- [x] Design `TriageResult` Pydantic model.
- [x] Create `kb.json` and populate with 6–8 distinct policy entries.
- [ ] Draft and refine the classification prompt in Google AI Studio.

*Note: Approach task 1 interactively. Discuss field types and validation rules before implementing schemas.*

---

## Phase 1 — Data Contracts & Knowledge Base
*   Learn Pydantic models, field types, and validation rules.
*   Establish input/output boundaries.
*   Create initial JSON knowledge base.
*   Establish reliable classification prompt.

## Phase 2 — First-Principles Semantic Retrieval
*   Generate embeddings for the knowledge base.
*   Understand vector dimensionality and representations.
*   Implement cosine similarity from scratch using NumPy.
*   Test retrieval accuracy (ensure correct policy is retrieved).

## Phase 3 — Intent Classification & Routing
*   Connect Gemini structured outputs with Pydantic.
*   Implement deterministic routing logic.
*   Build `handle_faq()`, `handle_bug()`, and `handle_escalation()`.
*   Combine classification, retrieval, and routing into a unified engine.

## Phase 4 — REST API Integration
*   Build the FastAPI application.
*   Create the `POST /triage` endpoint.
*   Connect endpoint to the triage engine.
*   Implement error handling and request/response validation.

## Phase 5 — Verification Interface & Stress Testing
*   Build the Streamlit UI.
*   Submit test tickets and visualize similarity scores/routing.
*   **Stress Testing Edge Cases:**
    *   *Vague queries:* Insufficient or ambiguous information.
    *   *Aggressive messages:* Emotional tone shouldn't break classification.
    *   *Mixed issues:* Tickets combining billing and technical problems.