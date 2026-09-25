# TicketWise — Development Phases & Progress Tracker

## Current Status: PHASE 4 (next up)

---

## Phase 1 — Data Contracts & Knowledge Base
- [x] Learn Pydantic models, field types, and validation rules.
- [x] Design `TicketInput` Pydantic model.
- [x] Design `TicketClassification` Pydantic model.
- [x] Design `TriageResult` Pydantic model.
- [x] Establish input/output boundaries.
- [x] Create `kb.json` and populate with 6–8 distinct policy entries.
- [x] Draft and refine the classification prompt in `classifier.py`.

## Phase 2 — First-Principles Semantic Retrieval
- [x] Generate embeddings for the knowledge base.
- [x] Understand vector dimensionality and representations.
- [x] Implement cosine similarity from scratch using NumPy.
- [x] Test retrieval accuracy (ensure correct policy is retrieved).

## Phase 3 — Intent Classification & Routing
- [x] Connect Gemini structured outputs with Pydantic.
- [x] Implement deterministic routing logic.
- [x] Build `handle_faq()`, `handle_bug()`, and `handle_escalation()`.
- [x] Combine classification, retrieval, and routing into a unified engine.

## Phase 4 — REST API Integration
- [x] Build the FastAPI application.
- [x] Create the `POST /triage` endpoint.
- [ ] Connect endpoint to the triage engine.
- [ ] Implement error handling and request/response validation.

## Phase 5 — Verification Interface & Stress Testing
- [ ] Build the Streamlit UI.
- [ ] Submit test tickets and visualize similarity scores/routing.
- [ ] Stress test: vague queries (insufficient or ambiguous information).
- [ ] Stress test: aggressive messages (emotional tone shouldn't break classification).
- [ ] Stress test: mixed issues (tickets combining billing and technical problems).