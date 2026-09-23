from typing import Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid


class TicketInput(BaseModel):
    """What the customer actually submits."""
    customer_email: str

    @field_validator("customer_email")
    @classmethod
    def must_include_at(cls, v: str):
        if "@" not in v:
            raise ValueError("Email must contain '@'")
        return v

    subject: str = Field(max_length=100)
    message: str = Field(max_length=1000)


class TicketClassification(BaseModel):
    """What the LLM returns after classifying the ticket."""
    category: Literal["bug", "billing", "faq", "account", "escalation"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    priority: Literal["low", "medium", "high", "urgent"]


class TriageResult(BaseModel):
    """Final output the API returns after the full pipeline runs."""
    ticket_id: str = Field(default_factory=lambda: f"T-{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    classification: TicketClassification
    matched_policy: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    response_message: str