"""Deterministic handling for greetings/thanks/farewells.

These aren't policy questions, so routing them through the retrieval
confidence gate makes the bot escalate on a plain "hi" -- treating a
greeting like an out-of-scope question. Matching is intentionally exact
(after light normalization), not substring/fuzzy, so a real question that
happens to start with "hi" (e.g. "hi, how long is shipping?") still goes
through retrieval as normal instead of being swallowed here.
"""

import re

_GREETINGS = {
    "hi", "hello", "hey", "hi there", "hello there", "hey there",
    "good morning", "good afternoon", "good evening", "yo", "sup", "howdy",
}
_THANKS = {
    "thanks", "thank you", "ty", "thx", "appreciate it", "appreciated",
    "thanks a lot", "thank you so much",
}
_FAREWELLS = {"bye", "goodbye", "see ya", "see you", "later", "cya", "bye bye"}

GREETING_REPLY = (
    "Hi! I'm the support assistant. Ask me about shipping, returns, billing, "
    "your account, or troubleshooting."
)
THANKS_REPLY = "You're welcome! Let me know if there's anything else I can help with."
FAREWELL_REPLY = "Take care! Feel free to come back anytime you have a question."


def smalltalk_reply(message: str) -> str | None:
    """Return a canned reply for a plain greeting/thanks/farewell, else None."""
    normalized = re.sub(r"[!.?]+$", "", message.strip().lower())
    if normalized in _GREETINGS:
        return GREETING_REPLY
    if normalized in _THANKS:
        return THANKS_REPLY
    if normalized in _FAREWELLS:
        return FAREWELL_REPLY
    return None
