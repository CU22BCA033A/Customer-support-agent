class AgentError(Exception):
    """Raised when the LLM call fails outright (auth, network, rate limit, ...)."""
