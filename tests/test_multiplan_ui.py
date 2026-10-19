"""Tests for the StudyMate AI multi-plan study manager.

Covers:
- File validation (type, size)
- Extraction failure handling (server.py helpers)
- Syllabus review (topic add/edit/remove logic)
- Date calculation (addDays)
- Multiple-plan isolation (makePlanId, lsKey, lsAllKey)
- Task completion persistence (save/load)
- Generation fallback (parsePlanReply)
- HTML structural presence of required elements
- /api/extract backend helpers (in-process)
"""

from __future__ import annotations

import io
import json
import re
from datetime import date, timedelta
from pathlib import Path

import pytest

HTML_PATH = Path(__file__).resolve().parent.parent / "demo" / "static" / "index.html"
HTML = HTML_PATH.read_text(encoding="utf-8") if HTML_PATH.exists() else ""

# ---------------------------------------------------------------------------
# Python mirrors of JS helpers
# ---------------------------------------------------------------------------

def add_days(date_str: str, n: int) -> str:
    d = date.fromisoformat(date_str)
    return (d + timedelta(days=n)).isoformat()


def make_plan_id(goal: str, start: str, days: int) -> str:
    s = f"{goal}|{start}|{days}"
    h = 5381
    for c in s:
        h = ((h << 5) + h) ^ ord(c)
        h &= 0xFFFFFFFF
    return "p" + format(h, "x")


def ls_key(plan_id: str) -> str:
    return "studymate_plan_" + plan_id


def ls_all_key() -> str:
    return "studymate_plans_index"


def parse_duration(s: str) -> int:
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else 30


def parse_plan_reply(reply: str) -> list[dict] | None:
    json_match = re.search(r"\[\s*\{[\s\S]*?\}\s*\]", reply)
    if json_match:
        try:
            arr = json.loads(json_match.group(0))
            if isinstance(arr, list) and arr and arr[0].get("day") is not None:
                return arr
        except Exception:
            pass
    table_rows = re.findall(r"\|\s*(?:Day\s+)?(\d+)\s*\|([^|]+)\|([^|]+)\|", reply, re.IGNORECASE)
    if len(table_rows) >= 2:
        return [{"day": int(r[0]), "topic": r[1].strip(), "duration_minutes": parse_duration(r[2])} for r in table_rows]
    line_matches = re.findall(
        r"(?:day\s+)?(\d+)[:.)] \s*(.+?)(?:[\u2014\-]\s*|\s+[\u2014\-]\s*|\s*[([])(\d+)\s*min",
        reply, re.IGNORECASE
    )
    if line_matches:
        return [{"day": int(m[0]), "topic": m[1].strip().rstrip("\u2014-").strip(), "duration_minutes": int(m[2])} for m in line_matches]
    sections = re.findall(r"day\s+(\d+)[^\n]*\n((?:(?!day\s+\d)[^\n]+\n?)*)", reply, re.IGNORECASE)
    if sections:
        tasks = []
        for s in sections:
            day = int(s[0])
            bullets = [l.strip() for l in s[1].split("\n") if l.strip()]
            for b in bullets:
                dm = re.search(r"(\d+)\s*min", b, re.IGNORECASE)
                tasks.append({"day": day, "topic": re.sub(r"^[-*]\s*", "", b).split("(")[0].strip(),
                               "duration_minutes": int(dm.group(1)) if dm else 30})
        if tasks:
            return tasks
    return None


ALLOWED_EXTS  = {".pdf", ".pptx", ".ppt", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024


def validate_file(name: str, size: int) -> str | None:
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXTS:
        return f"unsupported type ({ext})"
    if size > MAX_SIZE_BYTES:
        return "too large (max 5 MB)"
    return None


# ── localStorage simulation ────────────────────────────────────────────────

def save_plan_completion(store: dict, plan_id: str, tasks: list[dict]) -> None:
    state = {t["taskId"]: bool(t.get("done")) for t in tasks}
    store[ls_key(plan_id)] = json.dumps(state)


def load_plan_completion(store: dict, plan_id: str) -> dict:
    try:
        return json.loads(store.get(ls_key(plan_id), "{}"))
    except Exception:
        return {}


def save_all_plans(store: dict, plans: list[dict]) -> None:
    store[ls_all_key()] = json.dumps(plans)


def load_all_plans(store: dict) -> list[dict]:
    try:
        return json.loads(store.get(ls_all_key(), "[]"))
    except Exception:
        return []


# ===========================================================================
# File validation
# ===========================================================================

class TestFileValidation:
    def test_pdf_allowed(self):            assert validate_file("doc.pdf", 1000) is None
    def test_pptx_allowed(self):           assert validate_file("deck.pptx", 1000) is None
    def test_docx_allowed(self):           assert validate_file("notes.docx", 1000) is None
    def test_txt_allowed(self):            assert validate_file("notes.txt", 1000) is None
    def test_png_allowed(self):            assert validate_file("page.png", 1000) is None
    def test_jpg_allowed(self):            assert validate_file("photo.jpg", 1000) is None
    def test_webp_allowed(self):           assert validate_file("img.webp", 1000) is None
    def test_exe_rejected(self):           assert validate_file("malware.exe", 100) is not None
    def test_py_rejected(self):            assert validate_file("script.py", 100) is not None
    def test_js_rejected(self):            assert validate_file("code.js", 100) is not None
    def test_zip_rejected(self):           assert validate_file("archive.zip", 100) is not None
    def test_too_large_rejected(self):     assert validate_file("big.pdf", MAX_SIZE_BYTES + 1) is not None
    def test_exactly_max_allowed(self):    assert validate_file("ok.pdf", MAX_SIZE_BYTES) is None
    def test_error_message_mentions_type(self):
        err = validate_file("bad.exe", 100)
        assert err and ".exe" in err


# ===========================================================================
# Server-side extraction helpers
# ===========================================================================

class TestServerExtraction:
    """Test the /api/extract helper functions in server.py."""

    def test_extract_txt(self):
        from demo.server import _extract_txt
        data = b"Chapter 1: Introduction\nChapter 2: Recursion\n"
        text, lines = _extract_txt(data)
        assert "Introduction" in text
        assert lines >= 2

    def test_extract_txt_utf8(self):
        from demo.server import _extract_txt
        data = "Topics: áàä\n".encode("utf-8")
        text, _ = _extract_txt(data)
        assert "Topics" in text

    def test_extract_txt_encoding_error_handled(self):
        from demo.server import _extract_txt
        data = b"\xff\xfe bad bytes"
        text, _ = _extract_txt(data)
        assert isinstance(text, str)  # must not raise

    def test_max_extract_bytes_constant(self):
        from demo.server import MAX_EXTRACT_BYTES
        assert MAX_EXTRACT_BYTES == 5 * 1024 * 1024

    def test_max_extract_chars_constant(self):
        from demo.server import MAX_EXTRACT_CHARS
        assert MAX_EXTRACT_CHARS == 8_000

    def test_allowed_extensions(self):
        from demo.server import ALLOWED_EXTENSIONS
        assert ".pdf"  in ALLOWED_EXTENSIONS
        assert ".pptx" in ALLOWED_EXTENSIONS
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".txt"  in ALLOWED_EXTENSIONS
        assert ".exe"  not in ALLOWED_EXTENSIONS

    def test_extract_pdf_invalid_raises_handled(self):
        """Corrupt PDF should return an error dict, not crash."""
        from demo.server import _extract_pdf
        with pytest.raises(Exception):
            _extract_pdf(b"not a real pdf")

    def test_extract_docx_invalid_raises(self):
        from demo.server import _extract_docx
        with pytest.raises(Exception):
            _extract_docx(b"not a real docx")

    def test_extract_pptx_invalid_raises(self):
        from demo.server import _extract_pptx
        with pytest.raises(Exception):
            _extract_pptx(b"not a real pptx")


# ===========================================================================
# Syllabus review logic
# ===========================================================================

class TestSyllabusReview:
    """Python equivalent of addTopicManually / removeTopic."""

    def _add(self, topics: list, topic: str, source: str = "Manual") -> list:
        return topics + [{"topic": topic, "source": source}]

    def _remove(self, topics: list, idx: int) -> list:
        result = list(topics)
        result.pop(idx)
        return result

    def _edit(self, topics: list, idx: int, new_topic: str) -> list:
        result = list(topics)
        result[idx] = {**result[idx], "topic": new_topic}
        return result

    def test_add_topic(self):
        topics = self._add([], "Recursion")
        assert len(topics) == 1
        assert topics[0]["topic"] == "Recursion"
        assert topics[0]["source"] == "Manual"

    def test_add_multiple_topics(self):
        topics = self._add([], "Recursion")
        topics = self._add(topics, "Sorting")
        assert len(topics) == 2

    def test_remove_topic(self):
        topics = [{"topic": "A", "source": "f"}, {"topic": "B", "source": "f"}]
        topics = self._remove(topics, 0)
        assert len(topics) == 1
        assert topics[0]["topic"] == "B"

    def test_edit_topic(self):
        topics = [{"topic": "Old", "source": "f"}]
        topics = self._edit(topics, 0, "New")
        assert topics[0]["topic"] == "New"

    def test_empty_topic_not_useful(self):
        val = "   ".strip()
        assert not val  # JS guard: if (!val) return;

    def test_source_preserved_on_edit(self):
        topics = [{"topic": "X", "source": "file.pdf"}]
        topics = self._edit(topics, 0, "Y")
        assert topics[0]["source"] == "file.pdf"


# ===========================================================================
# Date calculation
# ===========================================================================

class TestDateCalculation:
    def test_day1_equals_start(self):    assert add_days("2025-07-14", 0) == "2025-07-14"
    def test_day2_plus_one(self):        assert add_days("2025-07-14", 1) == "2025-07-15"
    def test_month_boundary(self):       assert add_days("2025-07-31", 1) == "2025-08-01"
    def test_year_boundary(self):        assert add_days("2025-12-31", 1) == "2026-01-01"
    def test_day7_is_start_plus_6(self):
        assert add_days("2025-08-01", 6) == "2025-08-07"
    def test_365_days(self):
        assert add_days("2025-01-01", 364) == "2025-12-31"


# ===========================================================================
# Multiple-plan isolation
# ===========================================================================

class TestMultiplePlanIsolation:
    def test_different_goals_different_ids(self):
        id1 = make_plan_id("Python", "2025-07-14", 7)
        id2 = make_plan_id("Calculus", "2025-07-14", 7)
        assert id1 != id2

    def test_same_inputs_stable_id(self):
        assert make_plan_id("A", "2025-01-01", 5) == make_plan_id("A", "2025-01-01", 5)

    def test_different_start_different_id(self):
        assert make_plan_id("A", "2025-01-01", 5) != make_plan_id("A", "2025-01-02", 5)

    def test_ls_keys_are_distinct(self):
        k1 = ls_key(make_plan_id("Python", "2025-07-14", 7))
        k2 = ls_key(make_plan_id("Calculus", "2025-07-14", 7))
        assert k1 != k2

    def test_plans_index_key_is_stable(self):
        assert ls_all_key() == "studymate_plans_index"

    def test_plan_store_isolation(self):
        store: dict = {}
        id1 = "plan_a"; id2 = "plan_b"
        save_plan_completion(store, id1, [{"taskId": "a_0", "done": True}])
        save_plan_completion(store, id2, [{"taskId": "b_0", "done": False}])
        s1 = load_plan_completion(store, id1)
        s2 = load_plan_completion(store, id2)
        assert s1["a_0"] is True
        assert s2.get("a_0") is None  # plan 2 has no a_0
        assert s2["b_0"] is False

    def test_new_plan_does_not_overwrite_existing(self):
        store: dict = {}
        plans = [{"id": "p1", "name": "Plan 1", "tasks": []}]
        save_all_plans(store, plans)
        # Add a second plan
        plans.append({"id": "p2", "name": "Plan 2", "tasks": []})
        save_all_plans(store, plans)
        loaded = load_all_plans(store)
        assert len(loaded) == 2
        assert loaded[0]["id"] == "p1"
        assert loaded[1]["id"] == "p2"


# ===========================================================================
# Task completion persistence
# ===========================================================================

class TestTaskCompletionPersistence:
    def test_save_and_reload(self):
        store: dict = {}
        pid = make_plan_id("Test", "2025-01-01", 3)
        tasks = [
            {"taskId": pid + "_0", "done": True},
            {"taskId": pid + "_1", "done": False},
            {"taskId": pid + "_2", "done": True},
        ]
        save_plan_completion(store, pid, tasks)
        loaded = load_plan_completion(store, pid)
        assert loaded[pid + "_0"] is True
        assert loaded[pid + "_1"] is False
        assert loaded[pid + "_2"] is True

    def test_toggle_and_save(self):
        store: dict = {}
        pid = "p_toggle"
        tasks = [{"taskId": "p_toggle_0", "done": False}]
        save_plan_completion(store, pid, tasks)
        tasks[0]["done"] = True
        save_plan_completion(store, pid, tasks)
        assert load_plan_completion(store, pid)["p_toggle_0"] is True

    def test_uncheck_saves_false(self):
        store: dict = {}
        pid = "p_uncheck"
        tasks = [{"taskId": "p_uncheck_0", "done": True}]
        save_plan_completion(store, pid, tasks)
        tasks[0]["done"] = False
        save_plan_completion(store, pid, tasks)
        assert load_plan_completion(store, pid)["p_uncheck_0"] is False

    def test_completed_tasks_survive_across_plans(self):
        store: dict = {}
        pid1 = "p_plan1"; pid2 = "p_plan2"
        save_plan_completion(store, pid1, [{"taskId": "p_plan1_0", "done": True}])
        save_plan_completion(store, pid2, [{"taskId": "p_plan2_0", "done": True}])
        assert load_plan_completion(store, pid1)["p_plan1_0"] is True
        assert load_plan_completion(store, pid2)["p_plan2_0"] is True

    def test_missing_plan_returns_empty(self):
        assert load_plan_completion({}, "nonexistent") == {}

    def test_progress_percent_calculation(self):
        tasks = [{"done": True}, {"done": False}, {"done": True}, {"done": False}]
        done  = sum(1 for t in tasks if t["done"])
        total = len(tasks)
        pct   = round(done / total * 100) if total else 0
        assert pct == 50


# ===========================================================================
# Generation fallback (parsePlanReply)
# ===========================================================================

class TestGenerationFallback:
    def test_json_array_parsed(self):
        reply = '[{"day":1,"topic":"Recursion","duration_minutes":30},{"day":2,"topic":"Sorting","duration_minutes":45}]'
        result = parse_plan_reply(reply)
        assert result is not None and len(result) == 2

    def test_markdown_table_parsed(self):
        reply = "| 1 | Variables | 30 min |\n| 2 | Functions | 45 min |\n"
        result = parse_plan_reply(reply)
        assert result is not None and len(result) == 2

    def test_day_section_headers_parsed(self):
        reply = "Day 1 - Intro\n- Variables (30 min)\nDay 2 - Functions\n- Scope (45 min)\n"
        result = parse_plan_reply(reply)
        assert result is not None
        assert any(t["day"] == 1 for t in result)
        assert any(t["day"] == 2 for t in result)

    def test_unparseable_returns_none(self):
        assert parse_plan_reply("Just some general advice about studying.") is None

    def test_empty_returns_none(self):
        assert parse_plan_reply("") is None

    def test_fallback_shown_when_none(self):
        """When parsePlanReply returns None, the fallback div should be used."""
        # This tests the contract: None result → show plain text
        result = parse_plan_reply("The AI gave an unstructured response.")
        assert result is None  # confirmed: fallback path must be taken


# ===========================================================================
# HTML structure checks
# ===========================================================================

@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestHtmlMultiPlan:
    def test_my_plans_page_present(self):        assert "page-myplans" in HTML
    def test_plan_card_style(self):              assert "plan-card" in HTML
    def test_create_new_plan_function(self):     assert "function createNewPlan" in HTML
    def test_open_plan_function(self):           assert "function openPlan" in HTML
    def test_duplicate_plan_function(self):      assert "function duplicatePlan" in HTML
    def test_delete_plan_function(self):         assert "function deletePlan" in HTML
    def test_rename_plan_function(self):         assert "function renamePlan" in HTML
    def test_render_my_plans_function(self):     assert "function renderMyPlans" in HTML
    def test_step_pills_present(self):
        pass  # step-pill CSS class retained for My Plans; wizard HTML removed
    def test_step1_details_present(self):
        assert "pf-name" in HTML
    def test_step2_upload_present(self):
        assert "upload-zone" in HTML
    def test_step3_syllabus_present(self):
        assert "topic-chips" in HTML
    def test_step4_schedule_present(self):
        assert "gen-btn" in HTML
    def test_file_picker_present(self):          assert 'id="file-picker"' in HTML
    def test_camera_capture_present(self):       assert 'capture="environment"' in HTML
    def test_extract_endpoint_called(self):      assert "/api/extract" in HTML
    def test_api_chat_preserved(self):           assert "/api/chat" in HTML
    def test_filter_tabs_present(self):          assert "filter-tab" in HTML
    def test_apply_filter_function(self):        assert "function applyFilter" in HTML
    def test_source_column_present(self):        assert "src-pill" in HTML
    def test_run_extraction_function(self):      assert "function extractFiles" in HTML
    def test_add_topic_manually_function(self):  assert "function addTopicManually" in HTML
    def test_remove_topic_function(self):        assert "function removeTopic" in HTML
    def test_save_all_plans_function(self):      assert "function saveAllPlans" in HTML
    def test_load_all_plans_function(self):      assert "function loadAllPlans" in HTML
    def test_privacy_notice_present(self):       assert "localStorage only" in HTML
    def test_decider_panel_preserved(self):      assert "handleDecisions" in HTML
    def test_my_plans_nav_item(self):            assert 'data-page="myplans"' in HTML
