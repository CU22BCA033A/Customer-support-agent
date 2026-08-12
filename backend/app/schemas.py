from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=128)
    conversation_id: str | None = None


class Citation(BaseModel):
    doc: str
    heading: str
    score: float


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[Citation]
    escalated: bool
    escalation_reason: str | None = None
    latency_ms: int
