import logging

import anthropic

from app.agent.prompts import RAG_SYSTEM_PROMPT, build_context_block, build_user_turn
from app.config import get_settings

logger = logging.getLogger("agent")

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        settings = get_settings()
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    return _client


class AgentError(Exception):
    """Raised when the LLM call fails outright (auth, network, rate limit, ...)."""


def generate_grounded_answer(
    question: str,
    history: list[dict[str, str]],
    retrieved_chunks: list[dict],
) -> str:
    """Ask Claude to answer `question` using only `retrieved_chunks` as context.

    `history` is prior turns as [{"role": "user"|"assistant", "content": str}, ...],
    excluding the current turn.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise AgentError("The support agent isn't configured correctly (missing API key).")

    context_block = build_context_block(retrieved_chunks)
    user_turn = build_user_turn(question, context_block)

    messages = [*history, {"role": "user", "content": user_turn}]

    try:
        response = _get_client().messages.create(
            model=settings.agent_model,
            max_tokens=1024,
            system=RAG_SYSTEM_PROMPT,
            messages=messages,
        )
    except anthropic.AuthenticationError as e:
        logger.error("Anthropic auth error: %s", e)
        raise AgentError("The support agent isn't configured correctly (invalid API key).") from e
    except anthropic.RateLimitError as e:
        logger.warning("Anthropic rate limited: %s", e)
        raise AgentError("The support agent is temporarily busy. Please try again shortly.") from e
    except anthropic.APIStatusError as e:
        logger.error("Anthropic API error %s: %s", e.status_code, e.message)
        raise AgentError("The support agent hit an unexpected error.") from e
    except anthropic.APIConnectionError as e:
        logger.error("Anthropic connection error: %s", e)
        raise AgentError("Couldn't reach the support agent's backend. Please try again.") from e
    except Exception as e:  # last-resort boundary guard — never let an LLM call 500 the endpoint
        logger.error("Unexpected error calling Anthropic: %s", e)
        raise AgentError("The support agent hit an unexpected error.") from e

    if response.stop_reason == "refusal":
        return (
            "I'm not able to help with that request. If you think this is a mistake, "
            "I can connect you with a human agent."
        )

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "".join(text_parts).strip()
