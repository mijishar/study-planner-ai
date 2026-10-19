# Implementation Plan: StudyMate AI

## Overview

Replace the kit's example store-support agent with StudyMate AI: three Strands `@tool`
functions (Topic_Explainer, Study_Planner, Quiz_Generator), a `ProgressContext` for
in-session memory, a `ScopeGuardrail` wired through `DeciderGuardrail`, and a `HackathonAgent`
class that satisfies the hackathon kit's interface contract. Evaluation data, a demo script,
and UI updates complete the submission artefacts.

---

## Tasks

- [x] 1. Scaffold project and verify environment
  - Confirm `strands`, `hypothesis`, `pytest`, and `pytest-asyncio` are listed in the project
    dependencies (requirements.txt, pyproject.toml, or setup.py); add any that are missing.
  - Create `tests/__init__.py` (empty) so pytest discovers the tests package.
  - Create `tests/conftest.py` registering the `integration` pytest mark so
    `@pytest.mark.integration` tests can be collected without warnings.
  - Verify that `from decider_kit.patterns.tool_selection import ToolSelector` and
    `from decider_kit.patterns.guardrails import DeciderGuardrail` resolve without error.
  - _Requirements: 7.1, 7.4_

- [x] 2. Implement ProgressContext dataclass and session memory
  - [x] 2.1 Write `ProgressContext` in `agent/tools.py`
    - Define `ProgressEntry` dataclass with fields `tool: str`, `topic_or_goal: str`,
      `timestamp: str` (ISO-8601 UTC).
    - Define `ProgressContext` class with `MAX_ENTRIES = 50`, internal
      `deque(maxlen=50)`, `add(entry: ProgressEntry)` method, and
      `to_prompt_fragment() -> str` method that formats all entries as a bulleted list
      (returns empty string when the deque is empty).
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

  - [ ]* 2.2 Write property test for ProgressContext cap (Property 13)
    - **Property 13: Progress_Context never exceeds 50 entries and discards oldest first**
    - Use `@given(st.integers(min_value=51, max_value=200))` to drive N add() calls and assert
      `len(ctx.entries) == 50` and the retained entries are the N most recent.
    - **Validates: Requirements 5.1**

  - [ ]* 2.3 Write property test for ProgressContext entry shape (Property 14)
    - **Property 14: Successful tool invocation adds a well-formed Progress_Context entry**
    - Generate random tool names and topic strings; call `add()` and assert each retained
      entry has `tool`, `topic_or_goal`, and a string matching the ISO-8601 UTC pattern.
    - **Validates: Requirements 5.2**

  - [ ]* 2.4 Write property test for ProgressContext prompt injection (Property 15)
    - **Property 15: Non-empty Progress_Context is injected into the system prompt**
    - Build a non-empty `ProgressContext` from generated entries; call
      `to_prompt_fragment()` and assert every entry's tool name, topic/goal, and timestamp
      appears in the returned string.
    - **Validates: Requirements 5.3**

  - [ ]* 2.5 Write property test for new session empty context (Property 16)
    - **Property 16: New session starts with an empty Progress_Context**
    - Generate random `session_id` strings; assert that a freshly constructed
      `ProgressContext()` has zero entries before `add()` is called.
    - **Validates: Requirements 5.5, 5.6**

- [x] 3. Implement Topic_Explainer tool
  - [x] 3.1 Write `Topic_Explainer` in `agent/tools.py`
    - Decorate with `@tool`; one-line docstring: `"Explain a technical topic in plain language with an example and analogy."`.
    - Accept `topic: str` and `difficulty: str = "beginner"`.
    - Return `{"error": "topic: empty or whitespace-only"}` for blank topic.
    - Return `{"definition": ..., "example": ..., "analogy": ..., "difficulty": ..., "note": ...}`
      (omit `"note"` when difficulty is valid); default unrecognised difficulty to `"beginner"` and
      include a `"note"` key naming the original value and the fallback.
    - Analogy vocabulary must match difficulty level (everyday objects / domain concepts / formal abstractions).
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 3.2 Write property test for Topic_Explainer success shape (Property 5)
    - **Property 5: Topic_Explainer returns a well-formed success dict**
    - `@given(st.text(min_size=1, max_size=500), st.sampled_from(["beginner","intermediate","advanced"]))`
    - Assert result contains `definition`, `example`, `analogy`, `difficulty` — all non-empty strings.
    - **Validates: Requirements 2.2**

  - [ ]* 3.3 Write property test for whitespace topic rejection (Property 6)
    - **Property 6: Whitespace topic is rejected by both topic-bearing tools**
    - `@given(st.text(alphabet=st.characters(whitelist_categories=("Zs", "Cc")), min_size=0))`
    - Assert `Topic_Explainer(topic=ws)` returns a dict with key `"error"` identifying `"topic"`.
    - (Quiz_Generator half is covered in task 5.3.)
    - **Validates: Requirements 2.3**

  - [ ]* 3.4 Write property test for unrecognised difficulty fallback (Property 7)
    - **Property 7: Unrecognised difficulty defaults gracefully**
    - `@given(st.text().filter(lambda s: s not in {"beginner","intermediate","advanced"}))`
    - Assert result has `difficulty == "beginner"` and a non-empty `"note"` key.
    - **Validates: Requirements 2.4**

- [x] 4. Implement Study_Planner tool
  - [x] 4.1 Write `Study_Planner` in `agent/tools.py`
    - Decorate with `@tool`; one-line docstring: `"Break a syllabus or study goal into a day-by-day time-boxed task list."`.
    - Accept `goal: str` and `days_available: int = 7`.
    - Return structured error dicts for: empty/whitespace goal, `days_available < 1`,
      `days_available > 365`, or total workload exceeding `days_available × 180` minutes.
    - On success, return a list of task dicts with keys `day` (int, 1-indexed), `topic` (str),
      `duration_minutes` (int ≥ 5), `activity` (str); every day 1..days_available must appear
      at least once; sum of `duration_minutes` per day must not exceed 180.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 4.2 Write property test for Study_Planner day coverage (Property 8)
    - **Property 8: Study_Planner covers every requested day**
    - `@given(st.text(min_size=1, max_size=2000), st.integers(min_value=1, max_value=365))`
    - Assert every integer 1..days_available appears as `day` in at least one task dict, and
      every dict has keys `day`, `topic`, `duration_minutes`, `activity`.
    - **Validates: Requirements 3.2**

  - [ ]* 4.3 Write property test for Study_Planner daily cap (Property 9)
    - **Property 9: Daily study load never exceeds 180 minutes**
    - Same strategy as Property 8; group result by `day` and assert sum ≤ 180 for every day.
    - **Validates: Requirements 3.3**

  - [ ]* 4.4 Write property test for Study_Planner invalid inputs (Property 10)
    - **Property 10: Study_Planner rejects invalid inputs**
    - Three sub-strategies: whitespace goals; `st.integers(max_value=0)`; `st.integers(min_value=366)`.
    - Assert each returns a dict with key `"error"` identifying the correct field.
    - **Validates: Requirements 3.4, 3.5, 3.6**

- [x] 5. Implement Quiz_Generator tool
  - [x] 5.1 Write `Quiz_Generator` in `agent/tools.py`
    - Decorate with `@tool`; one-line docstring: `"Generate multiple-choice practice questions for a topic."`.
    - Accept `topic: str` and `count: int = 5`.
    - Return `{"error": "topic: empty or whitespace-only"}` for blank topic.
    - Clamp `count` to [1, 10]; when clamped, add top-level `"note"` key stating original
      value and which boundary was applied.
    - Return a list of exactly `count` (or clamped count) dicts; each dict must contain
      `question` (non-empty str), `choices` (list of exactly 4 non-empty strings),
      `correct_answer` (exactly matches one element of `choices`), `explanation` (non-empty str).
    - Wrap list in a dict when a `"note"` must be included at the top level.
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 5.2 Write property test for Quiz_Generator count and structure (Property 11)
    - **Property 11: Quiz_Generator returns exactly the requested question count with full structure**
    - `@given(st.text(min_size=1, max_size=200), st.integers(min_value=1, max_value=10))`
    - Assert list length == count; every dict has `question`, `choices` (len==4, all non-empty),
      `correct_answer` in `choices`, `explanation` non-empty.
    - **Validates: Requirements 4.2**

  - [ ]* 5.3 Write property test for out-of-range count clamping (Property 12)
    - **Property 12: Out-of-range count is clamped with a note**
    - `@given(st.text(min_size=1, max_size=200), st.integers().filter(lambda n: not (1 <= n <= 10)))`
    - Assert clamped result length equals `max(1, min(10, count))` and a `"note"` key is present.
    - Also cover whitespace topic for Quiz_Generator (Property 6 second half).
    - **Validates: Requirements 4.3, 4.4**

  - [x] 5.4 Update `TOOLS` list in `agent/tools.py`
    - Replace the kit's `[lookup_order, refund_order, cancel_order]` with
      `TOOLS = [Topic_Explainer, Study_Planner, Quiz_Generator]`.
    - _Requirements: 7.1_

- [x] 6. Implement ScopeGuardrail in `agent/decision.py`
  - [x] 6.1 Rewrite `agent/decision.py` to define `ScopeGuardrail`
    - Remove `IS_KIT_EXAMPLE = True` and all order-action-specific code.
    - Subclass `DeciderGuardrail` from `decider_kit.patterns.guardrails`.
    - Set `scope` to:
      `"learning support: explaining topics, planning study schedules, and generating practice questions for students"`.
    - Constructor: `def __init__(self, decider: Decider): super().__init__(decider, scope=SCOPE)`.
    - Expose a `log` property (inherited from `DeciderGuardrail`) so `HackathonAgent` can
      read guardrail decision entries alongside tool-selection entries.
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

- [x] 7. Implement HackathonAgent in `agent/agent.py`
  - [x] 7.1 Write `ProgressContext`-aware session management
    - Change `self.sessions` type to `dict[str, tuple[Agent, ToolSelector, ProgressContext]]`.
    - In `_session()`, construct a new `ProgressContext` for each new `session_id`; prepend
      `ctx.to_prompt_fragment()` to `SYSTEM_PROMPT` when the context is non-empty before each
      `Agent` construction (or refresh the system prompt string on each `chat()` call using
      the current context state).
    - _Requirements: 5.1, 5.3, 5.6_

  - [x] 7.2 Wire `ToolSelector` and `ScopeGuardrail` into the Agent
    - Import `ToolSelector` from `decider_kit.patterns.tool_selection`.
    - In `_session()`, construct `ToolSelector(decider, TOOLS)` and `ScopeGuardrail(decider)`.
    - Pass `interventions=[scope_guard]` to the Strands `Agent`; use
      `selector.tools_for(message)` at call time to obtain the narrowed tool list and
      re-instantiate or reconfigure the Agent per call (or use `selector.agent_for()`).
    - Set module-level `NAME = "StudyMate AI"`.
    - Update `SYSTEM_PROMPT` to describe a study assistant (remove store-support text).
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.5_

  - [x] 7.3 Implement `chat()` return dict and decision log
    - After the agent call, collect `selector.log` entries appended since the start of this
      `chat()` call and place them in `decisions`.
    - Each entry must carry `tool`, `confidence`, `narrowed`, `probabilities`, `decider_ms`
      (the `stage` field from `ToolSelector` may be present but is not required by spec).
    - Return `{"reply": ..., "decisions": ..., "model_id": ..., "latency_ms": ...}`.
    - `latency_ms` must be the wall-clock milliseconds for the whole `chat()` call.
    - _Requirements: 1.4, 7.2, 7.3_

  - [x] 7.4 Add exception boundary and ProgressContext update logic
    - Wrap the body of `chat()` in `try/except Exception`; on exception return the safe
      error dict: `{"reply": "<user-facing message>", "decisions": [], "model_id": ..., "latency_ms": ...}`.
    - After a successful tool execution (non-error dict result), append a `ProgressEntry`
      to the session's `ProgressContext` with the tool name, topic/goal, and
      `datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")`.
    - _Requirements: 5.2, 7.6_

  - [ ]* 7.5 Write property test for chat() return shape (Property 17)
    - **Property 17: chat() always returns the required dict structure**
    - `@given(st.text())` with a mocked Agent; also inject a mock that raises an exception.
    - Assert result always contains keys `reply` (str), `decisions` (list), `model_id` (str),
      `latency_ms` (int, ≥ 0).
    - **Validates: Requirements 7.2, 7.6**

  - [ ]* 7.6 Write property tests for ToolSelector integration (Properties 1–4)
    - **Property 1: Narrowing collapses the tool set**
      - `@given(st.floats(min_value=0.60, max_value=1.0), st.sampled_from(["Topic_Explainer","Study_Planner","Quiz_Generator","none"]))`
      - Mock Decider to return that confidence and label; assert `tools_for()` returns a
        list of exactly one tool (or empty for `"none"`).
    - **Property 2: Below-threshold falls back to the full tool set**
      - `@given(st.floats(min_value=0.0, max_value=0.599))`
      - Assert `tools_for()` returns all three tools and log entry has `narrowed=False`.
    - **Property 3: Decision log entry is structurally complete**
      - Any confidence and label; assert log entry contains `tool`, `confidence`, `narrowed`,
        `probabilities`, `decider_ms`.
    - **Property 4: Decider exception triggers safe fallback**
      - Mock Decider to raise; assert `tools_for()` returns all three tools and
        log entry has `narrowed=False`, `confidence=None`.
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 1.6**

- [x] 8. Write unit tests in `tests/test_tools.py` and `tests/test_agent.py`
  - [x] 8.1 Write unit tests for the three tools in `tests/test_tools.py`
    - `Topic_Explainer` happy paths: one test per difficulty level; confirm all four output
      keys are present and non-empty.
    - `Topic_Explainer` error paths: empty string, whitespace-only string, unrecognised
      difficulty (confirm `"note"` present and `difficulty == "beginner"`).
    - `Study_Planner` with `days_available=1` and `days_available=365`; confirm every day
      appears and daily cap holds.
    - `Study_Planner` error paths: empty goal, `days_available=0`, `days_available=366`.
    - `Quiz_Generator` with `count=1` and `count=10`; confirm list length and dict structure.
    - `Quiz_Generator` clamp paths: `count=0` → 1 question + note; `count=11` → 10 questions
      + note.
    - `Quiz_Generator` error path: whitespace topic.
    - _Requirements: 2.1–2.4, 3.1–3.7, 4.1–4.4_

  - [x] 8.2 Write unit tests for HackathonAgent in `tests/test_agent.py`
    - `HackathonAgent(eager=True)` constructs without raising (`eager` param accepted).
    - `HackathonAgent(eager=False)` constructs without raising.
    - Module-level `NAME` constant is a non-empty string.
    - `agent/eval_cases.jsonl` has ≥ 15 entries; every entry has `state`, `expected` keys;
      `split` is `"tune"` or `"test"` when present; there are ≥ 5 `"tune"` and ≥ 10
      `"test"` (or omitted) cases; each expected value maps to one of the four valid labels.
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 7.4, 7.5_

- [x] 9. Checkpoint — ensure all unit and property tests pass
  - Run `pytest tests/test_tools.py tests/test_agent.py tests/test_properties.py -x`
    (exclude `@pytest.mark.integration`). Ensure all tests pass, ask the user if questions arise.

- [x] 10. Write `agent/eval_cases.jsonl`
  - [x] 10.1 Author ≥ 15 labelled evaluation cases
    - Write one JSON object per line with keys `state` (str), `expected` (dict mapping the
      question name used by `questions_for()` — `"tool"` — to one of `"explain_topic"`,
      `"create_study_plan"`, `"generate_quiz"`, `"none"`), and optional `split`
      (`"tune"` or `"test"`).
    - Include ≥ 3 cases per label across all four labels.
    - Include ≥ 5 cases with `split: "tune"` and ≥ 10 with `split: "test"` or omitted.
    - Use the exact `state` format that `ToolSelector.select()` produces:
      `"User request: <message>"` (or with optional conversation prefix).
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 11. Write `agent/demo_script.yaml`
  - [x] 11.1 Author ≥ 6-turn demo script
    - Each turn has `user` (student message text) and `note` (video narration text);
      both non-empty strings.
    - Collectively the turns must exercise Topic_Explainer, Study_Planner, and
      Quiz_Generator at least once each.
    - At least one turn should trigger a narrowed decision (confidence ≥ 0.60) and at least
      one should remain broad so the decision panel shows both states on camera.
    - _Requirements: 9.1, 9.2_

- [x] 12. Update demo UI in `demo/static/index.html`
  - [x] 12.1 Add live decision panel for tool-selection entries
    - When the `/api/chat` response includes a non-empty `decisions` list, render each
      entry's `tool`, `confidence`, and `probabilities` in the existing decision panel
      (`#dec`).
    - When `decisions` is empty or absent, display a placeholder message:
      "No routing decision was made for this turn."
    - _Requirements: 9.3_

  - [x] 12.2 Highlight narrowed decisions with a badge
    - For any decision entry where `narrowed: true`, render the `tool` value in a visually
      distinct style — a coloured badge (e.g., amber/green with `border-radius: 99px`
      and a contrasting background) distinct from entries where `narrowed` is false.
    - Update the page `<title>` and `<h1>` to "StudyMate AI".
    - _Requirements: 9.4_

- [x] 13. Write integration smoke tests in `tests/test_integration.py`
  - [x] 13.1 Author integration tests tagged `@pytest.mark.integration`
    - Test 1: `ToolSelector` calls the Decider with the correct question format for one
      sample study-domain message; assert the returned `Selection` object has the required
      fields.
    - Test 2: Full `HackathonAgent.chat()` round-trip for a Topic_Explainer message;
      assert returned dict has `reply`, `decisions`, `model_id`, `latency_ms` keys and
      `latency_ms >= 0`.
    - Test 3: Full `HackathonAgent.chat()` round-trip for a Study_Planner message.
    - Test 4: Full `HackathonAgent.chat()` round-trip for a Quiz_Generator message.
    - _Requirements: 7.2, 1.1_

- [x] 14. Deployment verification artefacts
  - [x] 14.1 Verify `submission/deployment.json` schema after `./kit deploy`
    - After running `./kit deploy`, confirm that `submission/deployment.json` exists and
      contains at least `agentcore_arn` (or `arn`) and `decider_mode` keys; write a
      pytest fixture or script that loads the file and asserts the keys are present and
      non-empty strings.
    - Verify that re-running the demo server with `DEMO_TARGET=agentcore` and the ARN
      from the deployment file returns a valid `chat()` response dict.
    - _Requirements: 7.1 (deployment contract)_

- [x] 15. Final checkpoint — ensure all tests pass
  - Run `pytest tests/ -m "not integration" -x` and confirm zero failures.
  - Run `pytest tests/ -m integration -x` against a live environment to confirm deployed
    agent returns valid responses.
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP.
- Each task references specific requirements for traceability.
- Property tests (tasks 2.2–2.5, 3.2–3.4, 4.2–4.4, 5.2–5.3, 7.5–7.6) use `hypothesis`
  with `@given(...)` and `@settings(max_examples=100)`. Each test includes the comment:
  `# Feature: studymate-ai, Property N: <property text>`.
- The design's 17 properties are each covered by exactly one property-based test.
- Integration tests (task 13) require a live Decider and Bedrock endpoint; they are
  excluded from CI by default via `-m "not integration"`.
- Checkpoints (tasks 9 and 15) are the only tasks that run the test suite; no other
  task should invoke the test runner.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4", "5.1"] },
    { "id": 5, "tasks": ["5.2", "5.3", "5.4"] },
    { "id": 6, "tasks": ["6.1"] },
    { "id": 7, "tasks": ["7.1"] },
    { "id": 8, "tasks": ["7.2"] },
    { "id": 9, "tasks": ["7.3"] },
    { "id": 10, "tasks": ["7.4"] },
    { "id": 11, "tasks": ["7.5", "7.6", "8.1"] },
    { "id": 12, "tasks": ["8.2"] },
    { "id": 13, "tasks": ["10.1", "11.1"] },
    { "id": 14, "tasks": ["12.1"] },
    { "id": 15, "tasks": ["12.2", "13.1"] },
    { "id": 16, "tasks": ["14.1"] }
  ]
}
```
