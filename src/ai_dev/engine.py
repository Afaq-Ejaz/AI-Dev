"""
Phase 3 — Unified Triage Engine

The single entry point that combines:
  1. Classification (classifier.py) — LLM decides what type of ticket it is
  2. Retrieval (retrieval.py)      — finds the most relevant KB policy
  3. Routing (router.py)           — deterministic handler produces the response

Input:  TicketInput
Output: TriageResult
"""

from ai_dev.contract import TicketInput, TicketClassification, TriageResult
from ai_dev.classifier import classify_ticket
from ai_dev.retrieval import load_kb, generate_kb_embeddings, retrieve_top_match
from ai_dev.router import route_ticket


# ── Pre-load KB and embeddings once at module level ──────────────────
_policies = load_kb()
_kb_embeddings = generate_kb_embeddings(_policies)


def triage(ticket: TicketInput) -> TriageResult:
    """
    The full pipeline:
    
    TicketInput → classify → retrieve policy → route → TriageResult
    """
    # Step 1: Classify the ticket using Gemini
    classification: TicketClassification = classify_ticket(ticket)

    # Step 2: Retrieve the best matching policy from the KB
    query = f"{ticket.subject} {ticket.message}"
    matched_policy, similarity_score = retrieve_top_match(query, _policies, _kb_embeddings)

    # Step 3: Route to the correct handler and get the response
    response_message = route_ticket(ticket, classification, matched_policy)

    # Step 4: Package everything into the final result
    result = TriageResult(
        classification=classification,
        matched_policy=matched_policy["title"],
        similarity_score=similarity_score,
        response_message=response_message,
    )

    return result


# ── Quick Test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    test_tickets = [
        TicketInput(
            customer_email="alice@example.com",
            subject="Charged twice",
            message="I was charged $29.99 twice this month. Please refund.",
        ),
        TicketInput(
            customer_email="bob@example.com",
            subject="App crashes",
            message="App crashes every time I open it on Android 15.",
        ),
        TicketInput(
            customer_email="carol@example.com",
            subject="How do I export my data?",
            message="Where is the export option? I can't find it anywhere.",
        ),
        TicketInput(
            customer_email="dave@example.com",
            subject="GIVE ME A MANAGER NOW",
            message="I have been ignored for 5 days. This is completely unacceptable. I want a supervisor.",
        ),
        TicketInput(
            customer_email="eve@example.com",
            subject="Locked out",
            message="My account is locked and the password reset email isn't coming through.",
        ),
    ]

    for ticket in test_tickets:
        print(f"\n{'=' * 70}")
        print(f"TICKET: {ticket.subject}")
        print(f"FROM:   {ticket.customer_email}")
        print(f"MSG:    {ticket.message}")
        print("-" * 70)

        result = triage(ticket)

        print(f"TICKET ID:    {result.ticket_id}")
        print(f"CATEGORY:     {result.classification.category}")
        print(f"CONFIDENCE:   {result.classification.confidence}")
        print(f"PRIORITY:     {result.classification.priority}")
        print(f"REASONING:    {result.classification.reasoning}")
        print(f"MATCHED:      {result.matched_policy}")
        print(f"SIMILARITY:   {result.similarity_score:.4f}")
        print(f"RESPONSE:\n{result.response_message}")
