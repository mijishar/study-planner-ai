"""Unit tests for StudyMate AI tools.

Tests are pure (no network calls) — all three tools are in-memory.
Requirements: 2.1–2.4, 3.1–3.7, 4.1–4.4
"""

from __future__ import annotations

import pytest

from agent.tools import Quiz_Generator, Study_Planner, Topic_Explainer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_question_shape(q: dict) -> None:
    """Assert that *q* is a well-formed question dict (Req 4.2)."""
    assert isinstance(q["question"], str) and q["question"].strip()
    assert isinstance(q["choices"], list) and len(q["choices"]) == 4
    for c in q["choices"]:
        assert isinstance(c, str) and c.strip()
    assert q["correct_answer"] in q["choices"]
    assert isinstance(q["explanation"], str) and q["explanation"].strip()


# ===========================================================================
# Topic_Explainer
# ===========================================================================

class TestTopicExplainerHappyPath:
    """Req 2.1, 2.2 — valid topic, all three difficulty levels."""

    @pytest.mark.parametrize("difficulty", ["beginner", "intermediate", "advanced"])
    def test_valid_topic_returns_required_keys(self, difficulty: str) -> None:
        result = Topic_Explainer("recursion", difficulty)
        assert "error" not in result, f"Unexpected error: {result}"
        for key in ("definition", "example", "analogy", "difficulty"):
            assert key in result, f"Missing key: {key}"
            assert isinstance(result[key], str) and result[key].strip(), f"Empty value for key: {key}"

    def test_difficulty_echoed_in_output(self) -> None:
        result = Topic_Explainer("machine learning", "intermediate")
        assert result["difficulty"] == "intermediate"

    def test_unknown_topic_uses_fallback(self) -> None:
        result = Topic_Explainer("quantum entanglement", "beginner")
        assert "error" not in result
        assert result["definition"] and result["analogy"]

    def test_no_note_for_valid_difficulty(self) -> None:
        result = Topic_Explainer("api", "advanced")
        assert "note" not in result


class TestTopicExplainerErrorPaths:
    """Req 2.3, 2.4 — invalid inputs."""

    def test_empty_topic_returns_error(self) -> None:
        result = Topic_Explainer("")
        assert result == {"error": "topic: empty or whitespace-only"}

    def test_whitespace_topic_returns_error(self) -> None:
        result = Topic_Explainer("   ")
        assert result == {"error": "topic: empty or whitespace-only"}

    def test_tab_only_topic_returns_error(self) -> None:
        result = Topic_Explainer("\t\n")
        assert result == {"error": "topic: empty or whitespace-only"}

    def test_unrecognised_difficulty_defaults_to_beginner(self) -> None:
        result = Topic_Explainer("database", "expert")
        assert "error" not in result
        assert result["difficulty"] == "beginner"
        assert "note" in result
        assert result["note"].strip()

    def test_note_mentions_original_difficulty(self) -> None:
        result = Topic_Explainer("python", "wizard")
        assert "wizard" in result["note"]


# ===========================================================================
# Study_Planner
# ===========================================================================

def _day_set(schedule: list[dict]) -> set[int]:
    return {t["day"] for t in schedule}


def _max_daily_load(schedule: list[dict]) -> int:
    from collections import defaultdict
    loads: dict[int, int] = defaultdict(int)
    for t in schedule:
        loads[t["day"]] += t["duration_minutes"]
    return max(loads.values()) if loads else 0


class TestStudyPlannerHappyPath:
    """Req 3.2, 3.3 — valid inputs produce correct structure."""

    def test_days_1_covers_day_1(self) -> None:
        result = Study_Planner("Python programming", 1)
        assert isinstance(result, list) and len(result) >= 1
        assert _day_set(result) == {1}

    def test_days_7_covers_all_days(self) -> None:
        result = Study_Planner("algorithms and data structures", 7)
        assert isinstance(result, list)
        assert _day_set(result) == set(range(1, 8))

    def test_days_365_covers_all_days(self) -> None:
        result = Study_Planner("comprehensive CS curriculum", 365)
        assert isinstance(result, list)
        assert _day_set(result) == set(range(1, 366))

    def test_daily_cap_not_exceeded(self) -> None:
        result = Study_Planner("machine learning course", 7)
        assert isinstance(result, list)
        assert _max_daily_load(result) <= 180

    def test_task_dict_has_required_keys(self) -> None:
        result = Study_Planner("calculus", 3)
        assert isinstance(result, list)
        for task in result:
            assert "day" in task
            assert "topic" in task and task["topic"].strip()
            assert "duration_minutes" in task and task["duration_minutes"] >= 5
            assert "activity" in task and task["activity"].strip()


class TestStudyPlannerErrorPaths:
    """Req 3.4, 3.5, 3.6 — invalid inputs return structured errors."""

    def test_empty_goal_returns_error(self) -> None:
        result = Study_Planner("")
        assert "error" in result
        assert "goal" in result["error"]

    def test_whitespace_goal_returns_error(self) -> None:
        result = Study_Planner("   ")
        assert "error" in result
        assert "goal" in result["error"]

    def test_days_zero_returns_error(self) -> None:
        result = Study_Planner("Python", 0)
        assert "error" in result
        assert "days_available" in result["error"]

    def test_days_negative_returns_error(self) -> None:
        result = Study_Planner("Python", -5)
        assert "error" in result
        assert "days_available" in result["error"]

    def test_days_366_returns_error(self) -> None:
        result = Study_Planner("Python", 366)
        assert "error" in result
        assert "days_available" in result["error"]

    def test_days_1000_returns_error(self) -> None:
        result = Study_Planner("Python", 1000)
        assert "error" in result
        assert "days_available" in result["error"]


# ===========================================================================
# Quiz_Generator
# ===========================================================================

class TestQuizGeneratorHappyPath:
    """Req 4.1, 4.2 — valid topic and count within [1, 10]."""

    def test_count_1_returns_one_question(self) -> None:
        result = Quiz_Generator("recursion", 1)
        assert isinstance(result, list) and len(result) == 1
        _assert_question_shape(result[0])

    def test_count_5_returns_five_questions(self) -> None:
        result = Quiz_Generator("sorting", 5)
        assert isinstance(result, list) and len(result) == 5
        for q in result:
            _assert_question_shape(q)

    def test_count_10_returns_ten_questions(self) -> None:
        result = Quiz_Generator("python", 10)
        assert isinstance(result, list) and len(result) == 10
        for q in result:
            _assert_question_shape(q)

    def test_unknown_topic_uses_fallback(self) -> None:
        result = Quiz_Generator("quantum computing", 3)
        assert isinstance(result, list) and len(result) == 3
        for q in result:
            _assert_question_shape(q)


class TestQuizGeneratorClamping:
    """Req 4.3 — count outside [1, 10] is clamped with a note."""

    def test_count_0_clamped_to_1(self) -> None:
        result = Quiz_Generator("database", 0)
        assert isinstance(result, dict)
        assert "questions" in result
        assert len(result["questions"]) == 1
        assert "note" in result
        assert result["note"].strip()

    def test_count_11_clamped_to_10(self) -> None:
        result = Quiz_Generator("machine learning", 11)
        assert isinstance(result, dict)
        assert "questions" in result
        assert len(result["questions"]) == 10
        assert "note" in result

    def test_count_negative_clamped_to_1(self) -> None:
        result = Quiz_Generator("python", -3)
        assert isinstance(result, dict)
        assert len(result["questions"]) == 1

    def test_note_mentions_original_count(self) -> None:
        result = Quiz_Generator("sorting", 99)
        assert "99" in result["note"]


class TestQuizGeneratorErrorPaths:
    """Req 4.4 — empty/whitespace topic returns structured error."""

    def test_empty_topic_returns_error(self) -> None:
        result = Quiz_Generator("")
        assert result == {"error": "topic: empty or whitespace-only"}

    def test_whitespace_topic_returns_error(self) -> None:
        result = Quiz_Generator("   ")
        assert result == {"error": "topic: empty or whitespace-only"}

    def test_tab_topic_returns_error(self) -> None:
        result = Quiz_Generator("\t")
        assert result == {"error": "topic: empty or whitespace-only"}
