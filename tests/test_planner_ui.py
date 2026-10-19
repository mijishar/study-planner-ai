"""Tests for the Study Planner timetable JavaScript logic.

These tests exercise the Python-equivalent of the JS functions in index.html:
- addDays()           — date arithmetic
- fmtDate()           — display formatting
- parsePlanReply()    — AI response parsing (JSON, markdown table, numbered list, Day N sections)
- makePlanId()        — stable plan identifier
- lsKey()             — localStorage key
- saveCompletion() /
  loadCompletion()    — persistence layer (mocked)
- renderTimetable()   — task row generation helpers
- updateOverallProgress() — progress % calculation
- Fallback behaviour  — when parsing fails
- Validation          — missing goal / date / invalid days

All pure logic is re-implemented in Python so it can be tested without a browser.
The JS source is also checked for the presence of required functions/elements.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Locate the HTML file
# ---------------------------------------------------------------------------
HTML_PATH = Path(__file__).resolve().parent.parent / "demo" / "static" / "index.html"


# ---------------------------------------------------------------------------
# Python re-implementations of the JS helpers (mirrors the JS exactly)
# ---------------------------------------------------------------------------

def add_days(date_str: str, n: int) -> str:
    """Python mirror of JS addDays()."""
    d = date.fromisoformat(date_str)
    return (d + timedelta(days=n)).isoformat()


def fmt_date(date_str: str) -> str:
    """Python mirror of JS fmtDate() — abbreviated weekday + day + month."""
    d = date.fromisoformat(date_str)
    return d.strftime("%a %-d %b") if hasattr(date, "strftime") else d.strftime("%a %d %b")


def parse_duration(s: str) -> int:
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else 30


def parse_plan_reply(reply: str) -> list[dict] | None:
    """Python mirror of JS parsePlanReply()."""
    # Strategy 1: JSON array
    json_match = re.search(r"\[\s*\{[\s\S]*?\}\s*\]", reply)
    if json_match:
        try:
            arr = json.loads(json_match.group(0))
            if isinstance(arr, list) and arr and arr[0].get("day") is not None:
                return arr
        except Exception:
            pass

    # Strategy 2: markdown table rows
    table_rows = re.findall(r"\|\s*(?:Day\s+)?(\d+)\s*\|([^|]+)\|([^|]+)\|", reply, re.IGNORECASE)
    if len(table_rows) >= 2:
        return [{"day": int(r[0]), "topic": r[1].strip(), "duration_minutes": parse_duration(r[2].strip())} for r in table_rows]

    # Strategy 3: numbered / bulleted lines with "N min"
    line_matches = re.findall(r"(?:day\s+)?(\d+)[:\.\)]\s*(.+?)(?:[—\-–]\s*|\s+[–\-—]\s*|\s*[\(\[])(\d+)\s*min", reply, re.IGNORECASE)
    if line_matches:
        return [{"day": int(m[0]), "topic": m[1].strip().rstrip("–-—").strip(), "duration_minutes": int(m[2])} for m in line_matches]

    # Strategy 4: "Day N" section headers with bullets
    # Non-greedy: stop at the next "Day N" header so each section is isolated
    sections = re.findall(r"day\s+(\d+)[^\n]*\n((?:(?!day\s+\d)[^\n]+\n?)*)", reply, re.IGNORECASE)
    if sections:
        tasks = []
        for s in sections:
            day = int(s[0])
            bullets = [l.strip() for l in s[1].split("\n") if l.strip()]
            for b in bullets:
                dm = re.search(r"(\d+)\s*min", b, re.IGNORECASE)
                tasks.append({
                    "day": day,
                    "topic": re.sub(r"^[-•*]\s*", "", b).split("(")[0].strip(),
                    "duration_minutes": int(dm.group(1)) if dm else 30,
                })
        if tasks:
            return tasks

    return None


def make_plan_id(goal: str, start: str, days: int) -> str:
    """Python mirror of JS makePlanId() — djb2 hash."""
    s = f"{goal}|{start}|{days}"
    h = 5381
    for c in s:
        h = ((h << 5) + h) ^ ord(c)
        h &= 0xFFFFFFFF
    return "p" + format(h, "x")


def ls_key(plan_id: str) -> str:
    return "studymate_plan_" + plan_id


def update_overall_progress(tasks: list[dict]) -> dict:
    """Returns {done, total, pct} — mirrors updateOverallProgress()."""
    total = len(tasks)
    done  = sum(1 for t in tasks if t.get("done"))
    pct   = round(done / total * 100) if total else 0
    return {"done": done, "total": total, "pct": pct}


# ---------------------------------------------------------------------------
# Tests: addDays / date arithmetic
# ---------------------------------------------------------------------------

class TestAddDays:
    def test_add_zero(self) -> None:
        assert add_days("2025-07-14", 0) == "2025-07-14"

    def test_add_one(self) -> None:
        assert add_days("2025-07-14", 1) == "2025-07-15"

    def test_add_six(self) -> None:
        assert add_days("2025-07-14", 6) == "2025-07-20"

    def test_month_boundary(self) -> None:
        assert add_days("2025-07-31", 1) == "2025-08-01"

    def test_year_boundary(self) -> None:
        assert add_days("2025-12-31", 1) == "2026-01-01"

    def test_day_n_minus_1_formula(self) -> None:
        """Day 1 → start date, Day 7 → start + 6."""
        start = "2025-08-01"
        assert add_days(start, 1 - 1) == "2025-08-01"
        assert add_days(start, 7 - 1) == "2025-08-07"

    def test_365_days(self) -> None:
        result = add_days("2025-01-01", 364)
        assert result == "2025-12-31"


# ---------------------------------------------------------------------------
# Tests: parsePlanReply
# ---------------------------------------------------------------------------

class TestParsePlanReply:

    # ── Strategy 1: JSON array ──────────────────────────────────────────────
    def test_json_array_parsed(self) -> None:
        reply = 'Here is your plan:\n[{"day":1,"topic":"Variables","duration_minutes":30},{"day":1,"topic":"Loops","duration_minutes":45}]'
        result = parse_plan_reply(reply)
        assert result is not None
        assert len(result) == 2
        assert result[0]["day"] == 1
        assert result[0]["topic"] == "Variables"
        assert result[0]["duration_minutes"] == 30

    def test_json_missing_day_not_used(self) -> None:
        # Array without 'day' key should not be used by strategy 1
        reply = '[{"topic":"A","duration_minutes":30}]'
        result = parse_plan_reply(reply)
        # Should fall through to other strategies or return None — either is acceptable
        # The point is it shouldn't crash
        assert result is None or isinstance(result, list)

    # ── Strategy 2: markdown table ──────────────────────────────────────────
    def test_markdown_table_parsed(self) -> None:
        reply = (
            "| Day | Topic | Duration |\n"
            "|-----|-------|----------|\n"
            "| 1 | Variables and Data Types | 30 min |\n"
            "| 1 | Control Flow | 45 min |\n"
            "| 2 | Functions | 45 min |\n"
        )
        result = parse_plan_reply(reply)
        assert result is not None
        assert len(result) == 3
        assert result[0]["day"] == 1
        assert "Variables" in result[0]["topic"]

    def test_markdown_table_duration_extracted(self) -> None:
        reply = (
            "| 1 | Topic A | 60 min |\n"
            "| 2 | Topic B | 90 min |\n"
        )
        result = parse_plan_reply(reply)
        assert result is not None
        assert result[0]["duration_minutes"] == 60
        assert result[1]["duration_minutes"] == 90

    # ── Strategy 3: numbered list ───────────────────────────────────────────
    def test_numbered_list_parsed(self) -> None:
        reply = (
            "Day 1: Variables and Data Types — 30 min\n"
            "Day 1: Control Flow — 45 min\n"
            "Day 2: Functions — 45 min\n"
        )
        result = parse_plan_reply(reply)
        assert result is not None
        assert len(result) >= 2

    # ── Strategy 4: Day N section headers ───────────────────────────────────
    def test_day_section_headers_parsed(self) -> None:
        # Plain "Day N" headers (no bold)
        reply = (
            "Day 1 — Introduction\n"
            "- Variables and Data Types (30 min)\n"
            "- Control Flow (45 min)\n"
            "\nDay 2 — Functions\n"
            "- Functions and Scope (45 min)\n"
        )
        result = parse_plan_reply(reply)
        assert result is not None
        assert any(t["day"] == 1 for t in result)
        assert any(t["day"] == 2 for t in result)

    # ── Fallback ─────────────────────────────────────────────────────────────
    def test_unparseable_returns_none(self) -> None:
        reply = "This is a great plan! You should study hard every day."
        result = parse_plan_reply(reply)
        assert result is None

    def test_empty_string_returns_none(self) -> None:
        assert parse_plan_reply("") is None

    def test_single_sentence_returns_none(self) -> None:
        assert parse_plan_reply("Study Python for 3 days.") is None


# ---------------------------------------------------------------------------
# Tests: makePlanId (stability and differentiation)
# ---------------------------------------------------------------------------

class TestMakePlanId:

    def test_same_inputs_same_id(self) -> None:
        id1 = make_plan_id("Python", "2025-07-14", 7)
        id2 = make_plan_id("Python", "2025-07-14", 7)
        assert id1 == id2

    def test_different_goal_different_id(self) -> None:
        assert make_plan_id("Python", "2025-07-14", 7) != make_plan_id("Java", "2025-07-14", 7)

    def test_different_start_different_id(self) -> None:
        assert make_plan_id("Python", "2025-07-14", 7) != make_plan_id("Python", "2025-07-15", 7)

    def test_different_days_different_id(self) -> None:
        assert make_plan_id("Python", "2025-07-14", 7) != make_plan_id("Python", "2025-07-14", 10)

    def test_id_starts_with_p(self) -> None:
        assert make_plan_id("Python", "2025-07-14", 7).startswith("p")

    def test_id_is_alphanumeric(self) -> None:
        pid = make_plan_id("Calculus", "2025-08-01", 14)
        assert re.match(r"^p[0-9a-f]+$", pid)


# ---------------------------------------------------------------------------
# Tests: lsKey
# ---------------------------------------------------------------------------

class TestLsKey:
    def test_key_contains_plan_id(self) -> None:
        pid = make_plan_id("Python", "2025-07-14", 7)
        assert pid in ls_key(pid)

    def test_key_has_prefix(self) -> None:
        assert ls_key("abc123").startswith("studymate_plan_")


# ---------------------------------------------------------------------------
# Tests: updateOverallProgress / completion tracking
# ---------------------------------------------------------------------------

class TestUpdateOverallProgress:

    def test_zero_tasks(self) -> None:
        r = update_overall_progress([])
        assert r == {"done": 0, "total": 0, "pct": 0}

    def test_none_done(self) -> None:
        tasks = [{"done": False}, {"done": False}, {"done": False}]
        r = update_overall_progress(tasks)
        assert r == {"done": 0, "total": 3, "pct": 0}

    def test_all_done(self) -> None:
        tasks = [{"done": True}, {"done": True}]
        r = update_overall_progress(tasks)
        assert r == {"done": 2, "total": 2, "pct": 100}

    def test_half_done(self) -> None:
        tasks = [{"done": True}, {"done": False}]
        r = update_overall_progress(tasks)
        assert r == {"done": 1, "total": 2, "pct": 50}

    def test_one_of_three(self) -> None:
        tasks = [{"done": True}, {"done": False}, {"done": False}]
        r = update_overall_progress(tasks)
        assert r["pct"] == 33

    def test_toggle_updates_count(self) -> None:
        tasks = [{"done": False}, {"done": False}]
        assert update_overall_progress(tasks)["done"] == 0
        tasks[0]["done"] = True
        assert update_overall_progress(tasks)["done"] == 1
        tasks[0]["done"] = False  # uncheck
        assert update_overall_progress(tasks)["done"] == 0


# ---------------------------------------------------------------------------
# Tests: Task date assignment
# ---------------------------------------------------------------------------

class TestTaskDateAssignment:

    def test_day_1_gets_start_date(self) -> None:
        start = "2025-07-14"
        tasks = [{"day": 1, "topic": "Variables", "duration_minutes": 30}]
        for t in tasks:
            t["date"] = add_days(start, t["day"] - 1)
        assert tasks[0]["date"] == "2025-07-14"

    def test_day_7_gets_start_plus_6(self) -> None:
        start = "2025-07-14"
        tasks = [{"day": 7, "topic": "Review", "duration_minutes": 30}]
        for t in tasks:
            t["date"] = add_days(start, t["day"] - 1)
        assert tasks[0]["date"] == "2025-07-20"

    def test_multi_task_same_day_same_date(self) -> None:
        start = "2025-08-01"
        tasks = [
            {"day": 3, "topic": "A", "duration_minutes": 30},
            {"day": 3, "topic": "B", "duration_minutes": 45},
        ]
        for t in tasks:
            t["date"] = add_days(start, t["day"] - 1)
        assert tasks[0]["date"] == tasks[1]["date"] == "2025-08-03"


# ---------------------------------------------------------------------------
# Tests: Persistence helpers (saveCompletion / loadCompletion equivalent)
# ---------------------------------------------------------------------------

class TestPersistenceHelpers:
    """These test the Python logic that mirrors the JS localStorage helpers."""

    def _save(self, store: dict, plan_id: str, tasks: list[dict]) -> None:
        state = {t["taskId"]: t.get("done", False) for t in tasks}
        store[ls_key(plan_id)] = json.dumps(state)

    def _load(self, store: dict, plan_id: str) -> dict:
        try:
            return json.loads(store.get(ls_key(plan_id), "{}"))
        except Exception:
            return {}

    def test_save_and_load_roundtrip(self) -> None:
        store: dict = {}
        pid = "ptest1"
        tasks = [{"taskId": "ptest1_0", "done": True}, {"taskId": "ptest1_1", "done": False}]
        self._save(store, pid, tasks)
        loaded = self._load(store, pid)
        assert loaded["ptest1_0"] is True
        assert loaded["ptest1_1"] is False

    def test_new_plan_clears_old_state(self) -> None:
        store: dict = {}
        old_pid = "pold"
        new_pid = "pnew"
        self._save(store, old_pid, [{"taskId": "pold_0", "done": True}])
        # Simulated: when new plan is generated, old key is removed
        store.pop(ls_key(old_pid), None)
        assert self._load(store, old_pid) == {}

    def test_load_missing_key_returns_empty(self) -> None:
        assert self._load({}, "nonexistent") == {}

    def test_completion_survives_refresh(self) -> None:
        store: dict = {}
        pid = "prefresh"
        tasks = [{"taskId": "prefresh_0", "done": True}, {"taskId": "prefresh_1", "done": False}]
        self._save(store, pid, tasks)
        # "Refresh": reload from same store
        loaded = self._load(store, pid)
        assert loaded.get("prefresh_0") is True


# ---------------------------------------------------------------------------
# Tests: HTML source contains required elements and functions
# ---------------------------------------------------------------------------

class TestHtmlStructure:
    html = HTML_PATH.read_text(encoding="utf-8") if HTML_PATH.exists() else ""

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_date_picker_present(self) -> None:
        assert 'type="date"' in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_timetable_table_present(self) -> None:
        assert "sp-table" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_task_checkbox_present(self) -> None:
        assert "task-cb" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_overall_progress_present(self) -> None:
        assert "sp-overall" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_fallback_div_present(self) -> None:
        assert "sp-fallback" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_add_days_function_present(self) -> None:
        assert "function addDays" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_parse_plan_reply_function_present(self) -> None:
        assert "function parsePlanReply" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_make_plan_id_function_present(self) -> None:
        assert "function makePlanId" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_render_timetable_function_present(self) -> None:
        assert "function renderTimetable" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_on_task_toggle_function_present(self) -> None:
        assert "function onTaskToggle" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_update_overall_progress_function_present(self) -> None:
        assert "function updateOverallProgress" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_save_completion_function_present(self) -> None:
        assert "function saveCompletion" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_load_completion_function_present(self) -> None:
        assert "function loadCompletion" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_api_chat_call_preserved(self) -> None:
        assert '/api/chat' in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_decider_panel_preserved(self) -> None:
        assert "handleDecisions" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_validation_messages_present(self) -> None:
        assert "showPlanMsg" in self.html
        assert "Please enter a study goal" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_day_header_row_present(self) -> None:
        assert "day-header" in self.html

    @pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
    def test_done_class_for_completed_tasks(self) -> None:
        assert "task-row.done" in self.html or 'classList.toggle("done"' in self.html
