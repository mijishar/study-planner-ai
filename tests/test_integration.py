"""Integration smoke tests for StudyMate AI.

These tests require a live Decider endpoint and a live Amazon Bedrock connection.
They are tagged @pytest.mark.integration and excluded from the default CI run:

    pytest tests/ -m "not integration"    # fast unit + property tests only
    pytest tests/ -m integration          # live end-to-end tests

Requirements: 1.1, 7.2
"""

from __future__ import annotations

import pytest

from agent.agent import HackathonAgent
from decider_kit import Decider
from decider_kit.patterns.tool_selection import ToolSelector
from agent.tools import TOOLS


# ---------------------------------------------------------------------------
# Shared fixture: one HackathonAgent for the whole integration session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def agent() -> HackathonAgent:
    """Live HackathonAgent connected to real Decider + Bedrock."""
    return HackathonAgent()


@pytest.fixture(scope="module")
def decider() -> Decider:
    """Live Decider instance."""
    return Decider()


# ---------------------------------------------------------------------------
# Test 1: ToolSelector calls the Decider with the correct question format
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_tool_selector_question_format(decider: Decider) -> None:
    """ToolSelector must call the Decider with a state string in the expected
    format and return a Selection object with the required fields (Req 1.1)."""
    selector = ToolSelector(decider, TOOLS)
    before = len(selector.log)

    sel = selector.select("Explain what recursion is")

    assert len(selector.log) == before + 1, "Expected exactly one log entry"
    entry = selector.log[-1]

    assert "tool" in entry, "Log entry missing 'tool'"
    assert "confidence" in entry, "Log entry missing 'confidence'"
    assert "narrowed" in entry, "Log entry missing 'narrowed'"
    assert "probabilities" in entry, "Log entry missing 'probabilities'"
    assert "decider_ms" in entry, "Log entry missing 'decider_ms'"

    assert isinstance(entry["confidence"], (int, float))
    assert isinstance(entry["narrowed"], bool)
    assert isinstance(entry["probabilities"], dict)
    assert isinstance(entry["decider_ms"], int)


# ---------------------------------------------------------------------------
# Test 2: Full chat() round-trip — Topic_Explainer
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_chat_topic_explainer(agent: HackathonAgent) -> None:
    """Full HackathonAgent.chat() round-trip for a Topic_Explainer message (Req 7.2)."""
    out = agent.chat("Can you explain what recursion is?", session_id="integration-1")

    assert set(out.keys()) == {"reply", "decisions", "model_id", "latency_ms"}, (
        f"Unexpected keys: {set(out.keys())}"
    )
    assert isinstance(out["reply"], str) and out["reply"].strip()
    assert isinstance(out["decisions"], list)
    assert isinstance(out["model_id"], str)
    assert isinstance(out["latency_ms"], int) and out["latency_ms"] >= 0


# ---------------------------------------------------------------------------
# Test 3: Full chat() round-trip — Study_Planner
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_chat_study_planner(agent: HackathonAgent) -> None:
    """Full HackathonAgent.chat() round-trip for a Study_Planner message (Req 7.2)."""
    out = agent.chat(
        "Create a 3-day study plan for Python programming",
        session_id="integration-2",
    )

    assert set(out.keys()) == {"reply", "decisions", "model_id", "latency_ms"}
    assert isinstance(out["reply"], str) and out["reply"].strip()
    assert isinstance(out["latency_ms"], int) and out["latency_ms"] >= 0


# ---------------------------------------------------------------------------
# Test 4: Full chat() round-trip — Quiz_Generator
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_chat_quiz_generator(agent: HackathonAgent) -> None:
    """Full HackathonAgent.chat() round-trip for a Quiz_Generator message (Req 7.2)."""
    out = agent.chat(
        "Give me 3 quiz questions on sorting algorithms",
        session_id="integration-3",
    )

    assert set(out.keys()) == {"reply", "decisions", "model_id", "latency_ms"}
    assert isinstance(out["reply"], str) and out["reply"].strip()
    assert isinstance(out["latency_ms"], int) and out["latency_ms"] >= 0
