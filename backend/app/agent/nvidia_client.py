"""LLM backend for NVIDIA NIM (build.nvidia.com) — a free-tier alternative to Claude.

NVIDIA hosts open-weight models (Llama, Mixtral, Nemotron, ...) behind an
OpenAI-compatible chat-completions API, so this reuses the `openai` SDK
pointed at NVIDIA's base URL rather than the NVIDIA-specific one. Model
availability on the free tier changes over time — check
https://build.nvidia.com for the current catalog and update NVIDIA_MODEL in
.env if the configured model has been retired.

Same public interface as claude_client.generate_grounded_answer, so
app/agent/router.py can swap between the two based on LLM_PROVIDER without
callers caring which one is active.
"""

import logging

import openai

from app.agent.errors import AgentError
from app.agent.prompts import RAG_SYSTEM_PROMPT, build_context_block, build_user_turn
from app.config import get_settings

logger = logging.getLogger("agent")

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = openai.OpenAI(
            base_url=settings.nvidia_base_url,
            api_key=settings.nvidia_api_key or "unset",
        )
    return _client


def generate_grounded_answer(
    question: str,
    history: list[dict[str, str]],
    retrieved_chunks: list[dict],
) -> str:
    """Ask an NVIDIA-hosted model to answer `question` using only `retrieved_chunks`.

    Same contract as claude_client.generate_grounded_answer: `history` is prior
    turns as [{"role": "user"|"assistant", "content": str}, ...], excluding the
    current turn.
    """
    settings = get_settings()
    if not settings.nvidia_api_key:
        raise AgentError("The support agent isn't configured correctly (missing NVIDIA API key).")

    context_block = build_context_block(retrieved_chunks)
    user_turn = build_user_turn(question, context_block)

    # OpenAI-style chat completions put the system prompt in the messages list
    # itself, unlike Anthropic's separate top-level `system` parameter.
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_turn},
    ]

    try:
        response = _get_client().chat.completions.create(
            model=settings.nvidia_model,
            max_tokens=1024,
            temperature=0.2,
            messages=messages,
        )
    except openai.AuthenticationError as e:
        logger.error("NVIDIA auth error: %s", e)
        raise AgentError("The support agent isn't configured correctly (invalid NVIDIA API key).") from e
    except openai.RateLimitError as e:
        logger.warning("NVIDIA rate limited: %s", e)
        raise AgentError("The support agent is temporarily busy. Please try again shortly.") from e
    except openai.NotFoundError as e:
        logger.error("NVIDIA model not found: %s", e)
        raise AgentError(
            f"The configured model ({settings.nvidia_model}) isn't available. "
            "Check the current catalog at build.nvidia.com and update NVIDIA_MODEL."
        ) from e
    except openai.APIStatusError as e:
        logger.error("NVIDIA API error %s: %s", e.status_code, e.message)
        raise AgentError("The support agent hit an unexpected error.") from e
    except openai.APIConnectionError as e:
        logger.error("NVIDIA connection error: %s", e)
        raise AgentError("Couldn't reach the support agent's backend. Please try again.") from e
    except Exception as e:  # last-resort boundary guard — never let an LLM call 500 the endpoint
        logger.error("Unexpected error calling NVIDIA: %s", e)
        raise AgentError("The support agent hit an unexpected error.") from e

    choice = response.choices[0] if response.choices else None
    if choice is None or not choice.message.content:
        return (
            "I wasn't able to generate an answer for that. If you think this is a "
            "mistake, I can connect you with a human agent."
        )
    return choice.message.content.strip()
