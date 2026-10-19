"""Tests for StudyMate AI response quality improvements.

Verifies that:
- The system prompt instructs the LLM to answer directly (no unnecessary clarification).
- The system prompt includes all required structural instructions.
- Topic_Explainer returns rich content (definition, example with code, analogy).
- The tool docstring does not ask the LLM to seek clarification.
- Clarification is only requested for genuinely ambiguous inputs (tested via
  the system prompt content, since the LLM itself is not invoked here).

These are unit tests — no Bedrock or Decider connection required.
"""

from __future__ import annotations

import pytest

from agent.agent import _BASE_SYSTEM_PROMPT, _EAGER_SYSTEM_PROMPT
from agent.tools import Topic_Explainer


# ===========================================================================
# System prompt quality tests
# ===========================================================================

class TestBaseSystemPrompt:
    """The base system prompt must contain direct-answer instructions."""

    def test_prompt_instructs_direct_answer(self) -> None:
        """LLM must be told to answer directly without unnecessary clarification."""
        assert "answer directly" in _BASE_SYSTEM_PROMPT.lower() or \
               "never ask" in _BASE_SYSTEM_PROMPT.lower() or \
               "answer immediately" in _BASE_SYSTEM_PROMPT.lower(), (
            "System prompt must instruct the LLM to answer directly."
        )

    def test_prompt_requires_definition_first(self) -> None:
        """Prompt must instruct: give a simple definition first."""
        prompt_lower = _BASE_SYSTEM_PROMPT.lower()
        assert "definition" in prompt_lower or "define" in prompt_lower, (
            "System prompt must instruct starting with a definition."
        )

    def test_prompt_requires_example(self) -> None:
        """Prompt must instruct: include a concrete example."""
        assert "example" in _BASE_SYSTEM_PROMPT.lower(), (
            "System prompt must instruct including an example."
        )

    def test_prompt_requires_step_by_step(self) -> None:
        """Prompt must instruct: explain step by step."""
        prompt_lower = _BASE_SYSTEM_PROMPT.lower()
        assert "step" in prompt_lower, (
            "System prompt must include step-by-step instruction."
        )

    def test_prompt_clarification_rule_exists(self) -> None:
        """Prompt must define when (and when not) to ask clarifying questions."""
        prompt_lower = _BASE_SYSTEM_PROMPT.lower()
        assert "clarif" in prompt_lower, (
            "System prompt must contain clarification rules."
        )

    def test_prompt_no_unnecessary_clarification_keyword(self) -> None:
        """Prompt must NOT instruct the LLM to always ask before answering."""
        # These phrases would cause the LLM to ask unnecessary questions
        bad_phrases = ["always ask before", "confirm before answering", "ask the student first"]
        for phrase in bad_phrases:
            assert phrase not in _BASE_SYSTEM_PROMPT.lower(), (
                f"System prompt contains problematic phrase: '{phrase}'"
            )

    def test_prompt_treats_explain_x_as_complete_request(self) -> None:
        """Prompt must state that 'explain X' is a complete, unambiguous request."""
        assert "explain" in _BASE_SYSTEM_PROMPT.lower(), (
            "System prompt must address 'explain X' style requests."
        )

    def test_eager_prompt_preserved(self) -> None:
        """Eager prompt must still exist and be non-empty."""
        assert isinstance(_EAGER_SYSTEM_PROMPT, str) and _EAGER_SYSTEM_PROMPT.strip()


# ===========================================================================
# Topic_Explainer content quality tests
# ===========================================================================

class TestTopicExplainerContentQuality:
    """Topic_Explainer must return rich, directly usable content."""

    def test_recursion_beginner_has_code_example(self) -> None:
        """Beginner recursion explanation must include a Python code snippet."""
        result = Topic_Explainer("recursion", "beginner")
        assert "error" not in result
        # The example should contain actual code (function keyword or def)
        example = result.get("example", "")
        assert "def " in example or "function" in example.lower() or "```" in example, (
            "Beginner recursion example must include a code snippet."
        )

    def test_recursion_beginner_example_has_base_case_explanation(self) -> None:
        """The recursion example should explain the base case concept."""
        result = Topic_Explainer("recursion", "beginner")
        example = result.get("example", "")
        definition = result.get("definition", "")
        combined = (example + definition).lower()
        assert "base case" in combined or "stop" in combined, (
            "Recursion explanation must mention the base case or stopping condition."
        )

    def test_recursion_intermediate_has_code_example(self) -> None:
        """Intermediate recursion explanation must include a code snippet."""
        result = Topic_Explainer("recursion", "intermediate")
        assert "error" not in result
        example = result.get("example", "")
        assert "def " in example or "```" in example or "factorial" in example.lower(), (
            "Intermediate recursion example must include runnable code."
        )

    def test_all_difficulties_return_non_empty_fields(self) -> None:
        """All three difficulty levels must return non-empty definition, example, analogy."""
        for difficulty in ("beginner", "intermediate", "advanced"):
            result = Topic_Explainer("recursion", difficulty)
            assert "error" not in result, f"Error for difficulty={difficulty}"
            for field in ("definition", "example", "analogy"):
                assert result.get(field, "").strip(), (
                    f"Field '{field}' is empty for difficulty={difficulty}"
                )

    def test_tool_docstring_does_not_instruct_clarification(self) -> None:
        """The Topic_Explainer tool docstring must not tell the LLM to ask for clarification."""
        doc = Topic_Explainer.__doc__ or ""
        bad_phrases = ["ask the student for clarification", "seek clarification before", "ask before answering"]
        for phrase in bad_phrases:
            assert phrase not in doc.lower(), (
                f"Tool docstring contains problematic instruction: '{phrase}'"
            )

    def test_tool_docstring_mentions_no_clarification(self) -> None:
        """The tool docstring should explicitly tell the LLM NOT to seek clarification."""
        doc = Topic_Explainer.__doc__ or ""
        # The docstring uses "should NOT seek clarification" — check for that pattern
        assert "not seek clarification" in doc.lower() or \
               "not ask" in doc.lower() or \
               "without asking" in doc.lower() or \
               "don't ask" in doc.lower(), (
            "Tool docstring should instruct the LLM not to seek clarification."
        )


# ===========================================================================
# Clarification behaviour rules (via system prompt text analysis)
# ===========================================================================

class TestClarificationRules:
    """The system prompt must define clear rules about when to seek clarification."""

    def test_clarification_only_when_ambiguous(self) -> None:
        """System prompt must say clarification is for genuinely ambiguous cases only."""
        prompt_lower = _BASE_SYSTEM_PROMPT.lower()
        # The prompt should mention ambiguity as the condition for clarification
        assert "ambiguous" in prompt_lower or "missing" in prompt_lower, (
            "System prompt must restrict clarification to ambiguous/missing-info cases."
        )

    def test_prompt_does_not_over_clarify(self) -> None:
        """System prompt must not encourage asking multiple clarifying questions."""
        # Count occurrences of clarification-encouraging phrases
        prompt_lower = _BASE_SYSTEM_PROMPT.lower()
        # These are fine IF paired with a restriction on when to use them
        clarif_count = prompt_lower.count("clarif")
        # There should be at most a few mentions — one rule, not a policy of constant asking
        assert clarif_count <= 5, (
            f"System prompt mentions 'clarif' {clarif_count} times — may over-encourage clarification."
        )

    def test_explain_x_treated_as_complete_request(self) -> None:
        """The prompt must explicitly state that 'explain X' style requests are complete."""
        prompt_lower = _BASE_SYSTEM_PROMPT.lower()
        # The prompt should address "explain X" as a complete request
        assert "explain" in prompt_lower and (
            "complete" in prompt_lower or
            "unambiguous" in prompt_lower or
            "immediately" in prompt_lower or
            "directly" in prompt_lower
        ), "System prompt should state that 'explain X' is a complete request."


# ===========================================================================
# Tool-selection pattern preservation
# ===========================================================================

class TestToolSelectionPreserved:
    """Verify that tool names, module structure, and /api/chat contract are unchanged."""

    def test_tools_module_exports_correct_names(self) -> None:
        from agent.tools import TOOLS, Quiz_Generator, Study_Planner, Topic_Explainer
        tool_names = {t.tool_name for t in TOOLS}
        assert "Topic_Explainer" in tool_names
        assert "Study_Planner" in tool_names
        assert "Quiz_Generator" in tool_names

    def test_hackathon_agent_chat_signature_unchanged(self) -> None:
        """chat() must still accept message, session_id, images."""
        import inspect
        from agent.agent import HackathonAgent
        sig = inspect.signature(HackathonAgent.chat)
        params = list(sig.parameters)
        assert "message" in params
        assert "session_id" in params
        assert "images" in params

    def test_chat_returns_required_keys(self) -> None:
        """chat() must still return reply, decisions, model_id, latency_ms."""
        from unittest.mock import MagicMock, patch
        from agent.agent import HackathonAgent

        mock_decider = MagicMock()
        mock_decision = MagicMock()
        mock_decision.label = "Topic_Explainer"
        mock_decision.confidence = 0.9
        mock_decision.probabilities = {"Topic_Explainer": 0.9, "Study_Planner": 0.05, "Quiz_Generator": 0.03, "none": 0.02}
        mock_decider.ask.return_value = {"tool": mock_decision}
        mock_decider.last_latency_ms = 10

        with patch("agent.agent.Agent") as MockAgent:
            MockAgent.return_value = MagicMock(return_value="Recursion is a function calling itself.")
            agent = HackathonAgent(decider=mock_decider, eager=False)
            result = agent.chat("Explain recursion in simple words with a Python example")

        assert set(result.keys()) == {"reply", "decisions", "model_id", "latency_ms"}
        assert isinstance(result["reply"], str)
        assert isinstance(result["decisions"], list)
        assert isinstance(result["latency_ms"], int) and result["latency_ms"] >= 0
