"""
Phase 3 — Deterministic Routing

Routes a classified ticket to the correct handler based on its category.
Each handler takes the classification + matched policy and produces a response message.
"""

from ai_dev.contract import TicketInput, TicketClassification


def handle_faq(ticket: TicketInput, classification: TicketClassification, policy: dict) -> str:
    """Handle FAQ tickets — return the relevant policy info directly."""
    return (
        f"Thanks for reaching out! Here's what we found regarding your question:\n\n"
        f"{policy['content']}\n\n"
        f"If this doesn't answer your question, feel free to reply and we'll connect you with a team member."
    )


def handle_bug(ticket: TicketInput, classification: TicketClassification, policy: dict) -> str:
    """Handle bug reports — acknowledge and collect info per policy."""
    return (
        f"We've received your bug report and logged it as {classification.priority} priority.\n\n"
        f"Our policy: {policy['content']}\n\n"
        f"A member of our engineering team will follow up at {ticket.customer_email}. "
        f"Please have your device info and steps to reproduce ready."
    )


def handle_billing(ticket: TicketInput, classification: TicketClassification, policy: dict) -> str:
    """Handle billing issues — apply refund/subscription policy."""
    return (
        f"We understand billing issues are frustrating. Here's our policy:\n\n"
        f"{policy['content']}\n\n"
        f"We're reviewing your case and will reach out to {ticket.customer_email} "
        f"within 1–2 business days with a resolution."
    )


def handle_account(ticket: TicketInput, classification: TicketClassification, policy: dict) -> str:
    """Handle account issues — login, password, deletion."""
    return (
        f"We're looking into your account issue. Here's what applies:\n\n"
        f"{policy['content']}\n\n"
        f"If you need immediate access, try the password reset link. "
        f"We'll follow up at {ticket.customer_email} if further action is needed."
    )


def handle_escalation(ticket: TicketInput, classification: TicketClassification, policy: dict) -> str:
    """Handle escalations — flag for human agent review."""
    return (
        f"We hear you, and we're taking this seriously. Your ticket has been escalated "
        f"to a senior support agent for immediate review.\n\n"
        f"Escalation policy: {policy['content']}\n\n"
        f"A team lead will contact you at {ticket.customer_email} within the next 2 hours."
    )


# ── Router ───────────────────────────────────────────────────────────
ROUTE_MAP = {
    "faq": handle_faq,
    "bug": handle_bug,
    "billing": handle_billing,
    "account": handle_account,
    "escalation": handle_escalation,
}


def route_ticket(
    ticket: TicketInput,
    classification: TicketClassification,
    policy: dict,
) -> str:
    """
    Deterministic routing: pick the handler based on category, call it.
    
    No AI here — just a clean if/else (via dict lookup).
    If confidence is too low, auto-escalate regardless of category.
    """
    # Auto-escalate if LLM isn't confident enough
    if classification.confidence < 0.5:
        handler = handle_escalation
    else:
        handler = ROUTE_MAP.get(classification.category, handle_escalation)

    return handler(ticket, classification, policy)
