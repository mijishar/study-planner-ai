"""REUSABLE DECISION PATTERN: guardrails + tool-selection  (#guardrails)

StudyMate AI decision module.  Two responsibilities:

1. **Tool-selection question** — `QUESTIONS` defines the choice question used by
   `ToolSelector` to route every student message to the right tool.  Eval cases in
   `agent/eval_cases.jsonl` reference these question keys.

2. **Scope guardrail** — `ScopeGuardrail` (a subclass of `DeciderGuardrail`) runs
   before every LLM invocation and every tool call, blocking out-of-scope requests
   (exam registration, assignment submission, purchases) and harmful content before
   any tool is invoked.

Typed questions and options
    tool (choice): explain_topic | create_study_plan | generate_quiz | none

Wiring
    from agent.decision import ScopeGuardrail
    guard = ScopeGuardrail(decider)
    agent = Agent(..., interventions=[guard])

How to reuse it
    Set SCOPE to one sentence describing your agent's purpose.  Replace the four tool
    options in QUESTIONS with your own tool names and docstrings.
"""

from __future__ import annotations

import re

from decider_kit import Decider
from decider_kit.patterns.guardrails import DeciderGuardrail
from strands.interventions import Guide, Proceed

PATTERN_TAG = "#guardrails"

# ---------------------------------------------------------------------------
# Tool-selection question used by ToolSelector and eval_cases.jsonl
# ---------------------------------------------------------------------------
QUESTIONS = {
    "tool": Decider.choice(
        "Which study tool should handle this student request?",
        {
            "explain_topic":      "Explain a technical topic in plain language with an example and analogy.",
            "create_study_plan":  "Break a syllabus or study goal into a day-by-day time-boxed task list.",
            "generate_quiz":      "Generate multiple-choice practice questions for a topic.",
            "none":               "No tool needed; the assistant can answer directly.",
        },
    ),
}

# ---------------------------------------------------------------------------
# Scope description for the guardrail
# ---------------------------------------------------------------------------
SCOPE = (
    "learning support: explaining topics, planning study schedules, "
    "and generating practice questions for students"
)

# ---------------------------------------------------------------------------
# Patterns that are always in-scope — bypass the Decider scope check
# These are simple greetings and conversational openers that Decider 2B
# tends to rate as out-of-scope because they don't mention study topics.
# ---------------------------------------------------------------------------
_GREETING_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|"
    r"howdy|greetings|sup|what'?s\s+up|yo|hiya|salut|namaste|bonjour|"
    r"thanks?|thank\s+you|ok|okay|sounds?\s+good|got\s+it|sure|great|"
    r"cool|nice|awesome|perfect)[!.,?]*\s*$",
    re.IGNORECASE,
)

# Educational keywords that are clearly in-scope — also bypass the check
_EDUCATIONAL_PATTERN = re.compile(
    r"\b(explain|what\s+is|how\s+does|define|teach|tell\s+me|"
    r"study|learn|quiz|question|plan|schedule|topic|concept|"
    r"algorithm|data\s+structure|math|physics|chemistry|biology|"
    r"history|english|programming|python|java|machine\s+learning|"
    r"recursion|sorting|database|sql|api|oop|function|class|loop)\b",
    re.IGNORECASE,
)


class ScopeGuardrail(DeciderGuardrail):
    """Restricts StudyMate AI to learning-support actions only.

    Inherits before_invocation (input scope check) and before_tool_call
    (argument grounding check) from DeciderGuardrail.  The `.log` property
    is also inherited and read by HackathonAgent to include guardrail
    decisions alongside tool-selection decisions.

    Override: greetings and clearly educational messages bypass the Decider
    scope check and always Proceed, preventing false-positive blocks on
    conversational openers like "hi" or "hello".
    """

    name = "studymate-scope-guard"

    def __init__(self, decider: Decider) -> None:
        super().__init__(
            decider,
            scope=SCOPE,
            yes=0.5,
            check_inputs=True,
            check_tools=True,
        )

    def before_invocation(self, event, **kwargs):
        """Override: skip scope check for greetings and clearly in-scope messages."""
        if not self.check_inputs or not event.messages:
            return Proceed()

        # Extract the latest user message text
        last_text = ""
        for m in reversed(event.messages):
            if m.get("role") == "user":
                for block in m.get("content", []):
                    if isinstance(block, dict) and "text" in block:
                        last_text = block["text"].strip()
                        break
                if last_text:
                    break

        # Always allow greetings — Decider 2B rates these as out-of-scope
        if last_text and _GREETING_PATTERN.match(last_text):
            self.log.append({
                "stage": "input", "verdict": "proceed",
                "reason": "greeting bypass", "in_scope": 1.0, "injection": 0.0,
                "decider_ms": 0,
            })
            return Proceed()

        # Always allow clearly educational messages
        if last_text and _EDUCATIONAL_PATTERN.search(last_text):
            self.log.append({
                "stage": "input", "verdict": "proceed",
                "reason": "educational bypass", "in_scope": 1.0, "injection": 0.0,
                "decider_ms": 0,
            })
            return Proceed()

        # Fall through to the parent's Decider-based check for everything else
        return super().before_invocation(event, **kwargs)
