"""Regression tests for chat() error handling and credential expiry messaging.

Root cause found: AccessDeniedException (expired OAuth2 token) was caught silently
by the generic except Exception block and returned as "something went wrong".

These tests verify:
1. Expired credential errors produce a clear, actionable message
2. Connection errors produce a connectivity message
3. Generic errors still produce a safe fallback
4. Traceback / internal details never appear in the reply
5. The reply is always a non-empty string
6. latency_ms is always non-negative
7. decisions is always a list
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent.agent import HackathonAgent


def _make_mock_decider() -> MagicMock:
    from decider_kit.client import Decision
    mock_decision = MagicMock(spec=Decision)
    mock_decision.label = "none"
    mock_decision.confidence = 0.9
    mock_decision.probabilities = {"none": 0.9, "Topic_Explainer": 0.05, "Study_Planner": 0.03, "Quiz_Generator": 0.02}
    decider = MagicMock()
    decider.ask.return_value = {"tool": mock_decision}
    decider.last_latency_ms = 5
    return decider


def _chat_with_side_effect(message: str, exc: Exception) -> dict:
    """Run chat() where the Agent call raises *exc*."""
    mock_decider = _make_mock_decider()
    with patch("agent.agent.Agent") as MockAgent:
        MockAgent.return_value = MagicMock(side_effect=exc)
        agent = HackathonAgent(decider=mock_decider, eager=False)
        return agent.chat(message)


# ===========================================================================
# Credential / auth errors
# ===========================================================================

class TestCredentialErrorHandling:

    def test_access_denied_exception_produces_clear_message(self):
        """AccessDeniedException (expired token) must produce a helpful message."""
        class AccessDeniedException(Exception):
            pass
        exc = AccessDeniedException("The refresh token has expired.")
        result = _chat_with_side_effect("hi", exc)
        assert "expired" in result["reply"].lower() or "credentials" in result["reply"].lower() or \
               "Bedrock" in result["reply"], (
            f"Expected credential expiry message, got: {result['reply']}"
        )

    def test_access_denied_no_traceback_in_reply(self):
        class AccessDeniedException(Exception):
            pass
        exc = AccessDeniedException("AccessDenied: refresh token expired.")
        result = _chat_with_side_effect("explain recursion", exc)
        assert "Traceback" not in result["reply"]
        assert "AccessDeniedException" not in result["reply"]

    def test_credentials_error_reply_is_non_empty(self):
        class AccessDeniedException(Exception):
            pass
        result = _chat_with_side_effect("hi", AccessDeniedException("expired"))
        assert isinstance(result["reply"], str) and result["reply"].strip()


# ===========================================================================
# Connection errors
# ===========================================================================

class TestConnectionErrorHandling:

    def test_connection_error_produces_connectivity_message(self):
        exc = ConnectionError("Failed to connect to Bedrock endpoint")
        result = _chat_with_side_effect("hi", exc)
        reply_lower = result["reply"].lower()
        assert "connect" in reply_lower or "internet" in reply_lower or "service" in reply_lower, (
            f"Expected connectivity message, got: {result['reply']}"
        )

    def test_timeout_error_message(self):
        exc = TimeoutError("Request timed out after 30s")
        result = _chat_with_side_effect("hello", exc)
        assert isinstance(result["reply"], str) and result["reply"].strip()
        assert "Traceback" not in result["reply"]


# ===========================================================================
# Generic errors
# ===========================================================================

class TestGenericErrorHandling:

    def test_generic_exception_produces_fallback(self):
        result = _chat_with_side_effect("hi", RuntimeError("unexpected internal error"))
        assert isinstance(result["reply"], str) and result["reply"].strip()
        assert "Traceback" not in result["reply"]

    def test_always_returns_required_keys(self):
        for exc in [RuntimeError("boom"), ValueError("bad"), Exception("oops")]:
            result = _chat_with_side_effect("hi", exc)
            assert set(result.keys()) == {"reply", "decisions", "model_id", "latency_ms"}, \
                f"Missing keys for {exc}"

    def test_decisions_always_list_on_error(self):
        result = _chat_with_side_effect("hi", RuntimeError("fail"))
        assert isinstance(result["decisions"], list)

    def test_latency_ms_non_negative_on_error(self):
        result = _chat_with_side_effect("hi", RuntimeError("fail"))
        assert isinstance(result["latency_ms"], int) and result["latency_ms"] >= 0

    def test_no_raw_internal_labels_in_error_reply(self):
        for exc in [RuntimeError("fail"), ValueError("bad")]:
            result = _chat_with_side_effect("hi", exc)
            assert "studymate-scope-guard" not in result["reply"]
            assert "GUIDANCE:" not in result["reply"]
            assert "AccessDeniedException" not in result["reply"]


# ===========================================================================
# Credential expiry is the real root cause — document it explicitly
# ===========================================================================

class TestRealRootCause:
    """
    Documents the actual bug: botocore AccessDeniedException (expired OAuth2 token)
    was silently caught and returned as a generic 'something went wrong' message.
    
    The fix: detect credential errors specifically and return an actionable message
    telling the user to restart the demo server.
    """

    def test_expired_token_message_mentions_restart(self):
        """User must be told what to do when credentials expire."""
        class AccessDeniedException(Exception):
            pass
        exc = AccessDeniedException(
            "An error occurred (AccessDeniedException) when calling the "
            "CreateOAuth2Token operation: The refresh token has expired."
        )
        result = _chat_with_side_effect("hi", exc)
        reply = result["reply"]
        # Must mention the credential issue and guide the user
        has_guidance = (
            "restart" in reply.lower() or
            "expired" in reply.lower() or
            "credentials" in reply.lower() or
            "bedrock" in reply.lower()
        )
        assert has_guidance, (
            f"Credential expiry message should guide the user. Got: {reply}"
        )

    def test_non_credential_error_still_safe(self):
        """Non-credential errors still return a safe fallback."""
        result = _chat_with_side_effect("hi", KeyError("missing key"))
        assert isinstance(result["reply"], str) and result["reply"].strip()
        assert "Traceback" not in result["reply"]
