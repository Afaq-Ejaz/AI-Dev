"""
Phase 3 — Intent Classification

Uses Gemini with structured output to classify a customer ticket
into a TicketClassification Pydantic model.
"""

import os
from google import genai
from dotenv import load_dotenv
from ai_dev.contract import TicketInput, TicketClassification

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
CLASSIFICATION_MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = """You are a support ticket classifier for a software company called TicketWise.

Given a customer's support ticket (subject + message), you must classify it into exactly one category and assess its priority.

Categories:
- "bug": Technical issues, crashes, errors, broken features.
- "billing": Payments, charges, refunds, subscriptions, invoices.
- "faq": General questions about product features, how-to, documentation.
- "account": Login problems, password resets, account settings, deletion.
- "escalation": Customer demands a manager, legal threats, security breaches, unresolved issues.

Priority rules:
- "urgent": Security breaches, data loss, payment fraud, explicit manager requests.
- "high": Service outages, repeated billing errors, account lockouts.
- "medium": Bugs affecting workflow, subscription changes, account modifications.
- "low": General questions, feature requests, minor UI issues.

You MUST provide:
1. category — one of the five categories above.
2. confidence — how sure you are (0.0 to 1.0).
3. reasoning — a brief explanation of why you chose this category.
4. priority — one of the four priority levels above.

Be precise. If a ticket mixes multiple issues, classify by the DOMINANT issue."""


def classify_ticket(ticket: TicketInput) -> TicketClassification:
    """
    Send a ticket to Gemini and get back a structured TicketClassification.
    
    Uses Gemini's response_schema to force output into our exact Pydantic model.
    """
    user_message = f"Subject: {ticket.subject}\nMessage: {ticket.message}"

    response = client.models.generate_content(
        model=CLASSIFICATION_MODEL,
        contents=user_message,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=TicketClassification,
            temperature=0.1,  # Low temperature = more deterministic
        ),
    )

    # Parse the JSON response directly into our Pydantic model
    classification = TicketClassification.model_validate_json(response.text)
    return classification


# ── Quick Test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    test_tickets = [
        TicketInput(
            customer_email="alice@example.com",
            subject="Charged twice",
            message="I was charged $29.99 twice this month for my subscription. Please refund the duplicate charge.",
        ),
        TicketInput(
            customer_email="bob@example.com",
            subject="App crashes on startup",
            message="Every time I open the app on my iPhone 15 running iOS 18, it crashes immediately. I've tried reinstalling.",
        ),
        TicketInput(
            customer_email="carol@example.com",
            subject="How to export data?",
            message="I'd like to download all my data. Where can I find the export option?",
        ),
        TicketInput(
            customer_email="dave@example.com",
            subject="I DEMAND A MANAGER",
            message="This is unacceptable. I've been waiting 3 days for a response. I want to speak to your supervisor immediately.",
        ),
        TicketInput(
            customer_email="eve@example.com",
            subject="Can't log in",
            message="I forgot my password and the reset email never arrives. I've checked spam. My account might be locked.",
        ),
    ]

    for ticket in test_tickets:
        print(f"\n{'=' * 50}")
        print(f"Subject: {ticket.subject}")
        print(f"Message: {ticket.message}")
        result = classify_ticket(ticket)
        print(f"  → Category:   {result.category}")
        print(f"  → Confidence: {result.confidence}")
        print(f"  → Priority:   {result.priority}")
        print(f"  → Reasoning:  {result.reasoning}")
