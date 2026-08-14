from app.agent.smalltalk import (
    FAREWELL_REPLY,
    GREETING_REPLY,
    THANKS_REPLY,
    smalltalk_reply,
)


def test_greeting_variants_match():
    for msg in ["hi", "Hi", "hello!", "hey there", "Good morning."]:
        assert smalltalk_reply(msg) == GREETING_REPLY


def test_thanks_variants_match():
    for msg in ["thanks", "Thank you!", "thx", "appreciate it"]:
        assert smalltalk_reply(msg) == THANKS_REPLY


def test_farewell_variants_match():
    for msg in ["bye", "goodbye", "see ya"]:
        assert smalltalk_reply(msg) == FAREWELL_REPLY


def test_real_question_does_not_match():
    assert smalltalk_reply("How long do I have to return an item?") is None
    assert smalltalk_reply("hi, how long is shipping to Canada?") is None
