# AI Customer Support Agent

A self-hosted AI customer support agent built on FastAPI, ChromaDB, and the Claude API.
Answers customer questions by retrieving grounded context from a markdown knowledge base
and citing its sources — it never answers policy/product questions from general model
knowledge, and it says so honestly (and offers to escalate) when it can't find anything
relevant.

**Status: Phase 1 (knowledge base + RAG chat) is built and working end-to-end.** Tool use
(order lookup, refunds), conversation memory summarization, guardrails, and the admin
dashboard are follow-on phases — see [Roadmap](#roadmap) below.

## Architecture

```
User message
   │
   ▼
[Retrieval Layer] ── embeds query → searches Chroma → returns top-k chunks + similarity score
   │
   ▼
[Confidence gate] ── top score < threshold? → honest "I don't know" + escalated:true, no LLM call
   │  (score OK)
   ▼
[Claude] ── answers ONLY from the retrieved chunks, with inline citations
   │
   ▼
[Response + citations + escalated flag]
   │
   ▼
[Audit log] ── query, retrieved chunks + scores, confidence, answer, latency — every turn
```

The confidence gate is enforced in code (`backend/app/api/chat.py`), not just in the system
prompt — if retrieval doesn't clear `RETRIEVAL_CONFIDENCE_THRESHOLD`, the LLM is never called
and the user gets an honest, deterministic "I don't know, want me to escalate?" response. This
guarantees no hallucination on out-of-scope questions even if a prompt-level instruction were
ever bypassed.

## Project layout

```
backend/
  app/
    main.py            FastAPI app, CORS, startup
    config.py           Settings (env vars)
    db.py / models.py   SQLAlchemy — conversations, messages, audit logs (SQLite; Postgres-ready)
    schemas.py           Pydantic request/response models
    rag/
      chunking.py        Heading-based markdown chunker (not fixed character counts)
      vectorstore.py      Chroma wrapper — swap in Pinecone/Weaviate here later, nowhere else
      ingest.py           Loads knowledge_base/*.md, chunks, embeds, upserts
    agent/
      prompts.py          System prompt: answer only from context, cite sources, resist
                           instructions embedded in retrieved documents
      claude_client.py    Calls the Claude Messages API, maps SDK errors to a graceful
                           AgentError instead of ever 500-ing the endpoint
    api/
      chat.py             POST /chat
      kb.py               GET /kb/docs
  knowledge_base/         6 seed docs: shipping, returns, account, pricing, troubleshooting, privacy
  scripts/ingest.py        CLI: (re)build the vector index
  tests/                   pytest — chunking + chat API (mocked retrieval/LLM, no network needed)
frontend/
  src/ChatWidget.jsx        Embeddable chat widget (citations, escalation banner, typing indicator)
  src/App.jsx                Demo page that mounts the widget
```

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY

python scripts/ingest.py        # builds the Chroma index from knowledge_base/*.md
uvicorn app.main:app --reload --port 8000
```

The first `ingest.py` run downloads a small (~80MB) local embedding model
(`all-MiniLM-L6-v2`, via Chroma's built-in ONNX embedding function) — no external API calls
and no GPU required, so retrieval works fully offline once cached.

Verify it's up:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/kb/docs
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE defaults to http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

## Environment variables (backend/.env)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required** for actual answers. Without it, `/chat` still runs and returns a graceful "not configured" escalation instead of crashing. |
| `AGENT_MODEL` | `claude-sonnet-4-6` | Model used to generate grounded answers. |
| `CLASSIFIER_MODEL` | `claude-haiku-4-5` | Reserved for Phase 4's cheap intent/safety classifier. |
| `DATABASE_URL` | `sqlite:///./support_agent.db` | Swap for a `postgresql://...` URL in production — the schema is driver-agnostic. |
| `CHROMA_DIR` | `./chroma_data` | Where the vector index persists on disk. |
| `KNOWLEDGE_BASE_DIR` | `./knowledge_base` | Folder scanned by the ingestion script. |
| `RETRIEVAL_CONFIDENCE_THRESHOLD` | `0.35` | Below this cosine-similarity score, the agent escalates instead of answering. |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated origins allowed to call the API from a browser. |

## Adding a new knowledge base doc

Drop a markdown file into `backend/knowledge_base/`, structured with `#`/`##` headings (the
chunker splits on headings, not character counts, so each retrieved chunk is a complete,
citable section — not an arbitrary slice of text). Then re-run:

```bash
python scripts/ingest.py
```

Restart isn't required for the API server — only for a fresh `ingest.py` run to pick up the
new/changed file. Ask a question about it right away; the answer will cite the new doc by its
`#` H1 title.

## Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How long do I have to return an item?", "session_id": "demo-1"}'
```

With a valid `ANTHROPIC_API_KEY`, this returns something like:

```json
{
  "conversation_id": "…",
  "answer": "You have 30 days from delivery to return most items for a full refund, as long as they're unused and in original packaging [Returns & Refunds Policy]. ...",
  "citations": [
    {"doc": "Returns & Refunds Policy", "heading": "Return Window", "score": 0.7612}
  ],
  "escalated": false,
  "escalation_reason": null,
  "latency_ms": 1830
}
```

Asking something outside the knowledge base (e.g. "What's the capital of France?") returns
`escalated: true` with `escalation_reason: "low_retrieval_confidence"` and no LLM call is made
— verified in this repo's tests and via manual `curl` runs during development.

## Testing

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v
```

Tests cover the chunking pipeline directly and the `/chat` endpoint with the vector store and
Claude client mocked, so the suite runs offline with no API key and no embedding-model
download required.

## Roadmap

Built so far (**Phase 1**): ingestion pipeline, heading-based chunking, Chroma retrieval,
confidence-gated grounded answering with citations, honest "I don't know" fallback, full
per-turn audit logging, chat widget.

Not yet built — next phases, in the order described in the original project brief:

- **Phase 2 — Tools**: `get_order_status`, `get_account_info` (read-only, auto-run) and
  `create_refund`, `create_support_ticket`, `escalate_to_human` (write actions gated behind a
  "needs confirmation" step in both the API and the chat widget).
- **Phase 3 — Memory**: persist conversation summaries so long threads don't resend full
  transcripts every turn.
- **Phase 4 — Guardrails**: a cheap classifier pass (`CLASSIFIER_MODEL`) for intent/safety
  routing, stronger prompt-injection sanitization of retrieved content, scope refusals, and
  per-session rate limiting.
- **Phase 5 — Admin dashboard**: a React view over the `retrieval_audit_logs` table already
  being populated — live conversations, escalations, KB doc management, deflection-rate
  analytics.
- **Phase 6 — Polish**: streaming responses, clickable inline citations, broader test coverage.

The database schema, vector store wrapper, and audit logging were all designed with these
phases in mind (e.g. `RetrievalAuditLog` already captures everything the Phase 5 dashboard
needs to query), but only Phase 1's functionality is implemented and tested today.
