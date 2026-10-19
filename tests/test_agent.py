"""Unit tests for HackathonAgent.

Uses unittest.mock to avoid real Bedrock / Decider network calls.
Requirements: 7.2, 7.4, 7.5, 7.6, 8.1–8.5
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent.agent import HackathonAgent, NAME


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

WORKSPACE = Path(__file__).resolve().parent.parent


def _make_mock_agent(reply: str = "Here is your explanation.") -> MagicMock:
    """Return a mock Strands Agent that returns *reply* when called."""
    mock = MagicMock()
    mock.return_value = reply
    return mock


def _make_mock_decider() -> MagicMock:
    """Return a mock Decider whose .ask() returns a plausible tool-selection result."""
    from decider_kit.client import Decision

    mock_decision = MagicMock(spec=Decision)
    mock_decision.label = "Topic_Explainer"
    mock_decision.confidence = 0.9
    mock_decision.probabilities = {
        "Topic_Explainer": 0.9,
        "Study_Planner": 0.05,
        "Quiz_Generator": 0.03,
        "none": 0.02,
    }

    mock_decider = MagicMock()
    mock_decider.ask.return_value = {"tool": mock_decision}
    mock_decider.last_latency_ms = 42
    return mock_decider


# ===========================================================================
# Constructor tests (Req 7.4)
# ===========================================================================

class TestHackathonAgentConstructor:
    def test_eager_true_does_not_raise(self) -> None:
        HackathonAgent(eager=True)

    def test_eager_false_does_not_raise(self) -> None:
        HackathonAgent(eager=False)

    def test_eager_omitted_does_not_raise(self) -> None:
        HackathonAgent()

    def test_name_constant_is_non_empty_string(self) -> None:
        assert isinstance(NAME, str)
        assert NAME.strip(), "NAME must be a non-empty string"


# ===========================================================================
# chat() return shape (Req 7.2, 7.6)
# ===========================================================================

class TestChatReturnShape:
    """chat() must always return {reply, decisions, model_id, latency_ms}."""

    def _patched_chat(self, message: str = "Explain recursion") -> dict:
        """Run chat() with all network calls patched out."""
        mock_decider = _make_mock_decider()

        with patch("agent.agent.Agent") as MockAgent:
            MockAgent.return_value = _make_mock_agent()
            agent = HackathonAgent(decider=mock_decider, eager=False)
            return agent.chat(message)

    def test_returns_dict(self) -> None:
        result = self._patched_chat()
        assert isinstance(result, dict)

    def test_has_reply_key(self) -> None:
        result = self._patched_chat()
        assert "reply" in result
        assert isinstance(result["reply"], str)

    def test_has_decisions_key(self) -> None:
        result = self._patched_chat()
        assert "decisions" in result
        assert isinstance(result["decisions"], list)

    def test_has_model_id_key(self) -> None:
        result = self._patched_chat()
        assert "model_id" in result
        assert isinstance(result["model_id"], str)

    def test_has_latency_ms_key(self) -> None:
        result = self._patched_chat()
        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], int)
        assert result["latency_ms"] >= 0

    def test_exact_key_set(self) -> None:
        result = self._patched_chat()
        assert set(result.keys()) == {"reply", "decisions", "model_id", "latency_ms"}


class TestChatExceptionBoundary:
    """Req 7.6 — unhandled internal exception returns safe error dict."""

    def test_exception_returns_safe_dict(self) -> None:
        mock_decider = _make_mock_decider()

        with patch("agent.agent.Agent") as MockAgent:
            # Make the Agent call raise
            MockAgent.return_value.side_effect = RuntimeError("simulated internal failure")
            agent = HackathonAgent(decider=mock_decider, eager=False)
            result = agent.chat("Explain recursion")

        assert set(result.keys()) == {"reply", "decisions", "model_id", "latency_ms"}
        assert isinstance(result["reply"], str) and result["reply"].strip()
        assert result["decisions"] == []
        assert isinstance(result["latency_ms"], int) and result["latency_ms"] >= 0

    def test_exception_reply_is_user_friendly(self) -> None:
        mock_decider = _make_mock_decider()

        with patch("agent.agent.Agent") as MockAgent:
            MockAgent.return_value.side_effect = Exception("boom")
            agent = HackathonAgent(decider=mock_decider, eager=False)
            result = agent.chat("anything")

        # Must not contain a raw exception / stack trace hint
        assert "Traceback" not in result["reply"]
        assert "Exception" not in result["reply"]

# ===========================================================================
# eval_cases.jsonl validation (Req 8.1–8.5)
# ===========================================================================

EVAL_CASES_PATH = WORKSPACE / "agent" / "eval_cases.jsonl"
VALID_LABELS = {"explain_topic", "create_study_plan", "generate_quiz", "none"}


@pytest.mark.skipif(not EVAL_CASES_PATH.exists(), reason="eval_cases.jsonl not yet created")
class TestEvalCasesFile:
    def _load_cases(self) -> list[dict]:
        cases = []
        with open(EVAL_CASES_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    cases.append(json.loads(line))
        return cases

    def test_at_least_15_cases(self) -> None:
        cases = self._load_cases()
        assert len(cases) >= 15, f"Expected ≥15 cases, got {len(cases)}"

    def test_each_case_has_state_and_expected(self) -> None:
        for i, case in enumerate(self._load_cases()):
            assert "state" in case, f"Case {i} missing 'state'"
            assert "expected" in case, f"Case {i} missing 'expected'"

    def test_expected_label_is_valid(self) -> None:
        for i, case in enumerate(self._load_cases()):
            label = case["expected"].get("tool")
            assert label in VALID_LABELS, f"Case {i} has invalid label: {label!r}"

    def test_split_values_are_valid_when_present(self) -> None:
        for i, case in enumerate(self._load_cases()):
            if "split" in case:
                assert case["split"] in ("tune", "test"), (
                    f"Case {i} has invalid split: {case['split']!r}"
                )

    def test_at_least_5_tune_cases(self) -> None:
        cases = self._load_cases()
        tune = [c for c in cases if c.get("split") == "tune"]
        assert len(tune) >= 5, f"Expected ≥5 tune cases, got {len(tune)}"

    def test_at_least_10_test_cases(self) -> None:
        cases = self._load_cases()
        test = [c for c in cases if c.get("split", "test") == "test"]
        assert len(test) >= 10, f"Expected ≥10 test cases, got {len(test)}"

    def test_at_least_3_cases_per_label(self) -> None:
        from collections import Counter
        cases = self._load_cases()
        counts = Counter(c["expected"]["tool"] for c in cases)
        for label in VALID_LABELS:
            assert counts[label] >= 3, (
                f"Label '{label}' has only {counts[label]} cases (need ≥3)"
            )
