import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const MAX_TILT_DEG = 4;

function getSessionId() {
  let id = localStorage.getItem("support_session_id");
  if (!id) {
    id = `sess_${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
    localStorage.setItem("support_session_id", id);
  }
  return id;
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path
        d="M3.4 20.4 21 12 3.4 3.6 3 10l12 2-12 2z"
        fill="currentColor"
      />
    </svg>
  );
}

export default function ChatWidget() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm the Acme support assistant. Ask me about shipping, returns, billing, your account, or troubleshooting.",
      citations: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const sessionId = useRef(getSessionId());
  const scrollRef = useRef(null);
  const widgetRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  function handlePointerMove(e) {
    const el = widgetRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width; // 0..1
    const py = (e.clientY - rect.top) / rect.height; // 0..1
    const rotateY = (px - 0.5) * MAX_TILT_DEG * 2;
    const rotateX = (0.5 - py) * MAX_TILT_DEG * 2;
    setTilt({ x: rotateX, y: rotateY });
  }

  function resetTilt() {
    setTilt({ x: 0, y: 0 });
  }

  async function sendMessage(overrideText) {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text, citations: [] }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionId.current,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations || [],
          escalated: data.escalated,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Something went wrong reaching the support backend (${err.message}). Please make sure the API server is running.`,
          citations: [],
          escalated: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div
      className="chat-widget-wrap"
      onMouseMove={handlePointerMove}
      onMouseLeave={resetTilt}
      style={{ "--tiltX": `${tilt.x}deg`, "--tiltY": `${tilt.y}deg` }}
    >
      <div className="chat-widget" ref={widgetRef}>
        <div className="chat-header">
          <span className="chat-avatar chat-avatar-header">
            <span className="chat-avatar-glow" />
            ✨
          </span>
          <div className="chat-header-text">
            <span className="chat-header-title">Support Assistant</span>
            <span className="chat-header-subtitle">
              <span className="chat-dot" /> Online now
            </span>
          </div>
        </div>

        <div className="chat-messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={`bubble-row ${m.role}`}>
              {m.role === "assistant" && <span className="chat-avatar chat-avatar-msg">✨</span>}
              <div className={`bubble ${m.role} ${m.escalated ? "escalated" : ""}`}>
                <div className="bubble-text">{m.content}</div>
                {m.citations?.length > 0 && (
                  <div className="citations">
                    {m.citations.map((c, j) => (
                      <button
                        key={j}
                        type="button"
                        className="citation-chip"
                        style={{ "--stagger": j }}
                        title={`Ask more about this source (match score ${c.score})`}
                        disabled={loading}
                        onClick={() =>
                          sendMessage(`Tell me more about "${c.heading}" in the ${c.doc}.`)
                        }
                      >
                        <span className="citation-icon">📎</span>
                        {c.doc} <span className="citation-sep">›</span> {c.heading}
                      </button>
                    ))}
                  </div>
                )}
                {m.escalated && (
                  <div className="escalated-tag">🧑‍💼 flagged for a human agent</div>
                )}
              </div>
              {m.role === "user" && <span className="chat-avatar chat-avatar-msg user">🙂</span>}
            </div>
          ))}
          {loading && (
            <div className="bubble-row assistant">
              <span className="chat-avatar chat-avatar-msg">✨</span>
              <div className="bubble assistant typing">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
        </div>

        <div className="chat-input-row">
          <textarea
            rows={1}
            value={input}
            placeholder="Ask a question…"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}
