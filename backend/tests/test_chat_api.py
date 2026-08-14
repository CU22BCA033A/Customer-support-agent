import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app
from app.rag.vectorstore import RetrievedChunk

client = TestClient(app)
init_db()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


@patch("app.api.chat.generate_grounded_answer")
@patch("app.api.chat.get_vector_store")
def test_greeting_skips_retrieval_and_llm_entirely(mock_store, mock_llm):
    resp = client.post("/chat", json={"message": "hi", "session_id": "s3"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["escalated"] is False
    assert body["citations"] == []
    assert "support assistant" in body["answer"].lower()
    mock_store.return_value.query.assert_not_called()
    mock_llm.assert_not_called()


@patch("app.api.chat.get_vector_store")
def test_low_confidence_query_escalates_without_calling_llm(mock_store):
    mock_store.return_value.query.return_value = [
        RetrievedChunk(doc="Shipping Policy", heading="Address Changes", text="...", score=0.05)
    ]
    with patch("app.api.chat.generate_grounded_answer") as mock_llm:
        resp = client.post(
            "/chat",
            json={"message": "unrelated question", "session_id": "s1"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["escalated"] is True
    assert body["escalation_reason"] == "low_retrieval_confidence"
    assert body["citations"] == []
    mock_llm.assert_not_called()


@patch("app.api.chat.generate_grounded_answer")
@patch("app.api.chat.get_vector_store")
def test_confident_query_calls_llm_and_returns_citations(mock_store, mock_llm):
    mock_store.return_value.query.return_value = [
        RetrievedChunk(
            doc="Returns & Refunds Policy",
            heading="Return Window",
            text="Items can be returned within 30 days.",
            score=0.82,
        )
    ]
    mock_llm.return_value = "You can return it within 30 days [Returns & Refunds Policy]."

    resp = client.post(
        "/chat",
        json={"message": "How long do I have to return something?", "session_id": "s1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["escalated"] is False
    assert body["citations"][0]["doc"] == "Returns & Refunds Policy"
    assert "30 days" in body["answer"]
    mock_llm.assert_called_once()


@patch("app.api.chat.generate_grounded_answer")
@patch("app.api.chat.get_vector_store")
def test_conversation_id_persists_history_across_turns(mock_store, mock_llm):
    mock_store.return_value.query.return_value = [
        RetrievedChunk(doc="Pricing & Plans", heading="Plan Overview", text="...", score=0.9)
    ]
    mock_llm.return_value = "Pro is $19/month [Pricing & Plans]."

    first = client.post("/chat", json={"message": "What plans are there?", "session_id": "s2"})
    conv_id = first.json()["conversation_id"]

    second = client.post(
        "/chat",
        json={"message": "And annual billing?", "session_id": "s2", "conversation_id": conv_id},
    )
    assert second.json()["conversation_id"] == conv_id

    history_arg = mock_llm.call_args_list[-1].args[1]
    assert any(m["content"] == "What plans are there?" for m in history_arg)
