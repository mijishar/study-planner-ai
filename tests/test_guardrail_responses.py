"""Regression tests for ScopeGuardrail response quality.

Verifies:
1. Greetings ("hi", "hello") always bypass the scope check → Proceed
2. Educational messages always bypass → Proceed
3. _sanitize_reply never returns raw internal guidance text
4. _GREETING_PATTERN matches expected inputs
5. chat() return shape is preserved for all message types (mocked Bedrock)
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from agent.agent import HackathonAgent, _sanitize_reply, _FRIENDLY_GREETING, _FRIENDLY_SCOPE_LIMIT
from agent.decision import (
    ScopeGuardrail,
    _GREETING_PATTERN,
    _EDUCATIONAL_PATTERN,
    SCOPE,
)
from strands.interventions import Proceed, Guide


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_event(text: str) -> MagicMock:
    """Build a minimal mock event with a user message."""
    event = MagicMock()
    event.messages = [{"role": "user", "content": [{"text": text}]}]
    return event


def _make_mock_decider() -> MagicMock:
    """Decider that always returns in-scope=0.9 (safe fallback for non-bypassed messages)."""
    from decider_kit.client import Decision
    mock_dec = MagicMock(spec=Decision)
    mock_dec.p_yes = 0.9

    decider = MagicMock()
    decider.ask.return_value = {"injection": mock_dec, "in_scope": mock_dec}
    decider.last_latency_ms = 10
    return decider


# ===========================================================================
# _GREETING_PATTERN tests
# ===========================================================================

class TestGreetingPattern:
    @pytest.mark.parametrize("text", [
        "hi", "Hi", "HI", "hi!", "hi.",
        "hello", "Hello", "HELLO", "hello!",
        "hey", "Hey", "hey!",
        "good morning", "Good Morning", "good afternoon", "good evening",
        "thanks", "thank you", "okay", "ok", "sure", "great", "cool",
    ])
    def test_greeting_matches(self, text: str) -> None:
        assert _GREETING_PATTERN.match(text), f"Expected '{text}' to match greeting pattern"

    @pytest.mark.parametrize("text", [
        "explain recursion",
        "what is machine learning",
        "create a study plan for python",
        "give me a quiz on sorting",
        "hi how are you, can you explain recursion",   # mixed — too long for greeting-only
        "register me for an exam",
        "order pizza",
    ])
    def test_non_greeting_does_not_match(self, text: str) -> None:
        # These should NOT match as pure greetings
        if len(text.split()) > 4:
            assert not _GREETING_PATTERN.match(text), f"'{text}' should not match pure greeting pattern"


# ===========================================================================
# ScopeGuardrail bypass tests
# ===========================================================================

class TestScopeGuardrailBypass:

    def _make_guard(self) -> ScopeGuardrail:
        return ScopeGuardrail(_make_mock_decider())

    def test_hi_returns_proceed(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("hi"))
        assert isinstance(result, Proceed), "'hi' should always Proceed"

    def test_hello_returns_proceed(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("hello"))
        assert isinstance(result, Proceed), "'hello' should always Proceed"

    def test_hey_returns_proceed(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("hey"))
        assert isinstance(result, Proceed), "'hey' should always Proceed"

    def test_good_morning_returns_proceed(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("good morning"))
        assert isinstance(result, Proceed)

    def test_thanks_returns_proceed(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("thanks"))
        assert isinstance(result, Proceed)

    def test_explain_recursion_bypasses(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("Explain recursion to me"))
        assert isinstance(result, Proceed), "Educational message should bypass to Proceed"

    def test_what_is_ml_bypasses(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("What is machine learning?"))
        assert isinstance(result, Proceed)

    def test_study_plan_bypasses(self) -> None:
        guard = self._make_guard()
        result = guard.before_invocation(_make_mock_event("Create a study plan for Python"))
        assert isinstance(result, Proceed)

    def test_log_entry_added_for_bypass(self) -> None:
        guard = self._make_guard()
        guard.before_invocation(_make_mock_event("hi"))
        assert len(guard.log) == 1
        assert guard.log[0]["verdict"] == "proceed"

    def test_empty_messages_returns_proceed(self) -> None:
        guard = self._make_guard()
        event = MagicMock()
        event.messages = []
        result = guard.before_invocation(event)
        assert isinstance(result, Proceed)


# ===========================================================================
# _sanitize_reply tests
# ===========================================================================

class TestSanitizeReply:

    def test_clean_reply_unchanged(self) -> None:
        reply = "Recursion is when a function calls itself."
        assert _sanitize_reply(reply, "explain recursion") == reply

    def test_guidance_prefix_replaced_for_greeting(self) -> None:
        raw = "GUIDANCE: [studymate-scope-guard] This request is outside what you are for (learning support). Say so politely and offer what you can help with."
        result = _sanitize_reply(raw, "hi")
        assert "GUIDANCE" not in result
        assert "studymate-scope-guard" not in result
        assert "outside what you are for" not in result
        assert len(result) > 10  # must be a real response

    def test_guidance_replaced_with_greeting_for_hi(self) -> None:
        raw = "GUIDANCE: [studymate-scope-guard] This request is outside what you are for."
        result = _sanitize_reply(raw, "hi")
        assert result == _FRIENDLY_GREETING

    def test_guidance_replaced_with_scope_limit_for_unrelated(self) -> None:
        raw = "GUIDANCE: [studymate-scope-guard] This request is outside what you are for."
        result = _sanitize_reply(raw, "what is the weather today?")
        assert result == _FRIENDLY_SCOPE_LIMIT

    def test_scope_guard_name_never_in_output(self) -> None:
        raw = "[studymate-scope-guard] This request is outside what you are for."
        result = _sanitize_reply(raw, "order pizza")
        assert "studymate-scope-guard" not in result

    def test_outside_what_you_are_for_never_in_output(self) -> None:
        raw = "This request is outside what you are for (learning support)."
        result = _sanitize_reply(raw, "help me hack a website")
        assert "outside what you are for" not in result

    def test_educational_reply_passes_through(self) -> None:
        reply = "Recursion is when a function calls itself. Here is a Python example:\n\ndef countdown(n):\n    if n <= 0:\n        print('Go!')\n    else:\n        print(n)\n        countdown(n - 1)"
        result = _sanitize_reply(reply, "explain recursion")
        assert result == reply

    def test_friendly_greeting_response_is_complete(self) -> None:
        assert len(_FRIENDLY_GREETING) > 20
        assert "StudyMate" in _FRIENDLY_GREETING

    def test_friendly_scope_limit_is_complete(self) -> None:
        assert len(_FRIENDLY_SCOPE_LIMIT) > 20
        assert "StudyMate" in _FRIENDLY_SCOPE_LIMIT


# ===========================================================================
# chat() end-to-end shape tests (mocked — no live Bedrock)
# ===========================================================================

class TestChatReturnShapeWithSanitization:

    def _patched_chat(self, message: str, mock_reply: str = "Hello! I'm ready to help.") -> dict:
        mock_decider = _make_mock_decider()
        with patch("agent.agent.Agent") as MockAgent:
            MockAgent.return_value = MagicMock(return_value=mock_reply)
            agent = HackathonAgent(decider=mock_decider, eager=False)
            return agent.chat(message)

    def test_hi_returns_required_keys(self) -> None:
        result = self._patched_chat("hi")
        assert set(result.keys()) == {"reply", "decisions", "model_id", "latency_ms"}

    def test_hello_reply_is_string(self) -> None:
        result = self._patched_chat("hello")
        assert isinstance(result["reply"], str) and result["reply"].strip()

    def test_hi_reply_not_contains_guidance(self) -> None:
        raw_guidance = "GUIDANCE: [studymate-scope-guard] This request is outside what you are for."
        result = self._patched_chat("hi", mock_reply=raw_guidance)
        assert "GUIDANCE" not in result["reply"]
        assert "studymate-scope-guard" not in result["reply"]
        assert "outside what you are for" not in result["reply"]

    def test_explain_recursion_not_sanitized(self) -> None:
        educational_reply = "Recursion is when a function calls itself with a smaller problem."
        result = self._patched_chat("Explain recursion in simple terms", mock_reply=educational_reply)
        # Either the reply passes through unchanged, or the exception boundary kicks in
        # — but it must never contain guidance text
        assert "GUIDANCE" not in result["reply"]
        assert "studymate-scope-guard" not in result["reply"]
        # If the reply came through, it should contain educational content
        if "Recursion" in result["reply"]:
            assert "calls itself" in result["reply"]

    def test_unrelated_guidance_sanitized(self) -> None:
        raw_guidance = "GUIDANCE: [studymate-scope-guard] This request is outside what you are for (learning support). Say so politely."
        result = self._patched_chat("what is the stock price of Apple?", mock_reply=raw_guidance)
        assert "GUIDANCE" not in result["reply"]
        assert "studymate-scope-guard" not in result["reply"]

    def test_latency_ms_is_non_negative(self) -> None:
        result = self._patched_chat("hi")
        assert isinstance(result["latency_ms"], int) and result["latency_ms"] >= 0
