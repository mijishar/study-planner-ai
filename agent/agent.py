"""StudyMate AI — HackathonAgent

An AI-powered study assistant built on the Strands Agents SDK with Strands Decider 2B
for tool-selection routing.  Three @tool functions handle the three study domains:

    Topic_Explainer  — explains a concept with examples and analogies
    Study_Planner    — breaks a syllabus into a day-by-day task list
    Quiz_Generator   — produces multiple-choice practice questions

The Decider pre-filters every message so the LLM sees only the relevant tool(s).
A ScopeGuardrail blocks out-of-scope and harmful requests.
A ProgressContext accumulates what the student has studied for personalised follow-ups.

Interface (Requirements 7.1–7.6):
    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("Explain recursion to me", session_id="s1")
    out["reply"], out["decisions"], out["model_id"], out["latency_ms"]
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking
from decider_kit.patterns.tool_selection import ToolSelector

from .decision import ScopeGuardrail
from .tools import (
    TOOLS,
    ProgressContext,
    ProgressEntry,
    Quiz_Generator,
    Study_Planner,
    Topic_Explainer,
)

# ---------------------------------------------------------------------------
# Module-level constant (Requirement 7.5)
# ---------------------------------------------------------------------------
NAME: str = "StudyMate AI"

# ---------------------------------------------------------------------------
# Reply sanitization — strip internal guidance/system text that leaks through
# ---------------------------------------------------------------------------
# Patterns that indicate raw internal Strands/Decider output leaked into reply
_GUIDANCE_PATTERNS = [
    re.compile(r"GUIDANCE:\s*\[.*?\].*", re.DOTALL),
    re.compile(r"\[studymate-scope-guard\].*", re.DOTALL),
    re.compile(r"This request is outside what you are for.*", re.DOTALL | re.IGNORECASE),
    re.compile(r"Say so politely and offer what you can help with\.?\s*", re.IGNORECASE),
]

_FRIENDLY_GREETING = (
    "Hello! 👋 I'm StudyMate AI, your study companion. "
    "I can help you understand topics, build a study plan, or practice with quizzes. "
    "What would you like to learn today?"
)

_FRIENDLY_SCOPE_LIMIT = (
    "I'm StudyMate AI, focused on educational support. "
    "I can help you explain concepts, create study schedules, or generate practice questions. "
    "What topic would you like to study?"
)


def _sanitize_reply(reply: str, original_message: str) -> str:
    """Replace raw internal guidance text with a user-friendly response."""
    # Check if any guidance pattern appears in the reply
    for pattern in _GUIDANCE_PATTERNS:
        if pattern.search(reply):
            # If the original message was a greeting, use a greeting response
            from .decision import _GREETING_PATTERN
            if _GREETING_PATTERN.match(original_message.strip()):
                return _FRIENDLY_GREETING
            return _FRIENDLY_SCOPE_LIMIT
    return reply

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
_BASE_SYSTEM_PROMPT = """You are StudyMate AI, a friendly and knowledgeable study assistant for students.
You help students understand difficult topics, plan their study schedules, and practice with quizzes.
You only provide learning support — you cannot register for exams, submit assignments, or make purchases.

## How to answer educational questions

When a student asks you to explain a concept, always answer directly and completely. Never ask
unnecessary clarifying questions. If the topic and level are clear from the message, provide the
full explanation immediately.

Structure every explanation like this:
1. **Simple definition first** — one or two plain-language sentences.
2. **Example** — a concrete, runnable code snippet or real-world scenario. If the student
   mentions Python (or any language), use that language.
3. **Step-by-step breakdown** — walk through the example line by line or step by step.
4. **Analogy** — relate the concept to something everyday (for beginners) or domain-specific
   (for intermediate/advanced students).
5. **Follow-up invitation** — end with one short, open question inviting the student to go deeper
   (e.g. "Want me to show a recursive tree example next?").

## Clarification rules

Only ask a clarifying question when ALL of the following are true:
- The topic is genuinely ambiguous (e.g. the word "transformation" with no context).
- AND the student has not given any indication of the subject area.
- AND you cannot make a reasonable assumption.

If the student says "explain X" or "explain X in simple words", treat that as a complete,
unambiguous request and answer immediately at a beginner level.

## Tone

Be warm, encouraging, and direct. Keep explanations concise but complete. Never pad responses
with filler phrases like "Great question!" or "Certainly!"."""

_EAGER_SYSTEM_PROMPT = """You are StudyMate AI, a friendly and knowledgeable study assistant.
You help students understand difficult topics, plan their study schedules, and practice with quizzes.
Act immediately and always invoke the most relevant tool without asking clarifying questions first."""

# Tool names used for ProgressContext entries
_TOOL_NAMES = {
    "Topic_Explainer",
    "Study_Planner",
    "Quiz_Generator",
}

# ---------------------------------------------------------------------------
# Helper: current UTC timestamp in ISO-8601 format
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# HackathonAgent (Requirements 7.1–7.6)
# ---------------------------------------------------------------------------

class HackathonAgent:
    """One Strands Agent per session, with ToolSelector, ScopeGuardrail, and ProgressContext."""

    def __init__(
        self,
        decider: Decider | None = None,
        model_id: str | None = None,
        eager: bool | None = None,
    ) -> None:
        import os

        self.decider = decider or Decider()
        self.eager = eager if eager is not None else os.environ.get("DEMO_EAGER") == "1"
        self.model_id = model_id or default_model_id()

        # sessions: session_id → (Agent, ToolSelector, ScopeGuardrail, ProgressContext)
        self.sessions: dict[str, tuple[Agent, ToolSelector, ScopeGuardrail, ProgressContext]] = {}

    # ------------------------------------------------------------------
    # Session management (Requirements 5.1, 5.3, 5.6, 7.4)
    # ------------------------------------------------------------------

    def _session(
        self, session_id: str, progress_fragment: str = ""
    ) -> tuple[Agent, ToolSelector, ScopeGuardrail, ProgressContext]:
        """Return (or create) a session tuple for *session_id*.

        A new session_id always gets a fresh ProgressContext with zero entries (Req 5.6).
        The system prompt is rebuilt on every chat() call to include the latest context.
        """
        if session_id not in self.sessions:
            guard = ScopeGuardrail(self.decider)
            selector = ToolSelector(self.decider, TOOLS)
            ctx = ProgressContext()
            # Initial agent creation (tools refined per-call; interventions fixed)
            base_prompt = _EAGER_SYSTEM_PROMPT if self.eager else _BASE_SYSTEM_PROMPT
            system_prompt = f"{base_prompt}\n\n{progress_fragment}" if progress_fragment else base_prompt
            agent = Agent(
                model=agent_model(self.model_id),
                system_prompt=system_prompt,
                tools=TOOLS,
                interventions=[guard],
                callback_handler=None,
            )
            self.sessions[session_id] = (agent, selector, guard, ctx)
        return self.sessions[session_id]

    # ------------------------------------------------------------------
    # chat() (Requirements 7.2, 7.3, 7.6)
    # ------------------------------------------------------------------

    def chat(
        self,
        message: str,
        session_id: str = "default",
        images: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Process *message* and return {reply, decisions, model_id, latency_ms}.

        Parameters
        ----------
        message:    Student message text.
        session_id: Identifies the conversation session.  A new value starts a
                    fresh session with an empty ProgressContext.
        images:     Optional list of image paths/bytes for multi-modal input.
        """
        t0 = time.perf_counter()

        try:
            # 1. Get / create session state
            agent, selector, guard, ctx = self._session(session_id)

            # 2. Rebuild system prompt with current ProgressContext (Req 5.3)
            base_prompt = _EAGER_SYSTEM_PROMPT if self.eager else _BASE_SYSTEM_PROMPT
            fragment = ctx.to_prompt_fragment()
            system_prompt = f"{base_prompt}\n\n{fragment}" if fragment else base_prompt

            # 3. Snapshot log lengths before this turn
            guard_before = len(guard.log)
            selector_before = len(selector.log)

            # 4. Use ToolSelector to narrow tools for this message (Req 1.1–1.6)
            narrowed_tools = selector.tools_for(message)

            # 5. Invoke the Agent with the (possibly narrowed) tool set
            agent_with_tools = Agent(
                model=agent_model(self.model_id),
                system_prompt=system_prompt,
                tools=narrowed_tools,
                interventions=[guard],
                callback_handler=None,
            )
            result = agent_with_tools(
                [*image_blocks(images), {"text": message}] if images else message,
                invocation_state={"images": list(images or [])},
            )
            reply = strip_thinking(str(result))
            reply = _sanitize_reply(reply, message)

            # 6. Collect decision log entries for this turn (Req 1.4, 7.3)
            selector_entries = selector.log[selector_before:]
            guard_entries = guard.log[guard_before:]

            # Convert selector entries to the required schema
            decisions: list[dict[str, Any]] = []
            for entry in selector_entries:
                decisions.append({
                    "tool":         entry.get("tool", "none"),
                    "confidence":   entry.get("confidence"),
                    "narrowed":     entry.get("narrowed", False),
                    "probabilities": entry.get("probabilities", {}),
                    "decider_ms":   entry.get("decider_ms", 0),
                })

            # 7. Update ProgressContext on successful tool invocation (Req 5.2)
            #    Detect which tool ran by inspecting the selector's last entry
            if selector_entries:
                last_sel = selector_entries[-1]
                tool_name = last_sel.get("tool", "none")
                if tool_name in _TOOL_NAMES:
                    # Extract topic/goal from the message heuristically
                    ctx.add(ProgressEntry(
                        tool=tool_name,
                        topic_or_goal=message[:200],
                        timestamp=_utc_now(),
                    ))

            latency_ms = round((time.perf_counter() - t0) * 1000)
            return {
                "reply":      reply,
                "decisions":  decisions,
                "model_id":   self.model_id,
                "latency_ms": latency_ms,
            }

        except Exception as exc:
            # Requirement 7.6: safe error dict, never surface stack trace
            import logging
            logging.getLogger(__name__).error(
                "HackathonAgent.chat() failed for message=%r: %s: %s",
                message[:100], type(exc).__name__, exc,
            )
            latency_ms = round((time.perf_counter() - t0) * 1000)

            # Produce a more informative user-facing message for known error classes
            exc_name = type(exc).__name__
            exc_str  = str(exc)
            if "AccessDeniedException" in exc_name or "expired" in exc_str.lower() or "credentials" in exc_str.lower():
                user_msg = (
                    "StudyMate AI cannot reach Amazon Bedrock right now — "
                    "the session credentials have expired. "
                    "Please restart the demo server to refresh them."
                )
            elif "ConnectionError" in exc_name or "timeout" in exc_str.lower() or "connect" in exc_str.lower():
                user_msg = (
                    "StudyMate AI cannot reach the AI service right now. "
                    "Please check your internet connection and try again."
                )
            else:
                user_msg = "I'm sorry, something went wrong. Please try again."

            return {
                "reply":      user_msg,
                "decisions":  [],
                "model_id":   self.model_id,
                "latency_ms": latency_ms,
            }


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    agent = HackathonAgent()
    msgs = sys.argv[1:] or [
        "Explain recursion to me please.",
        "Create a 3-day study plan for Python programming.",
        "Give me 3 quiz questions on sorting algorithms.",
    ]
    for msg in msgs:
        print(json.dumps(agent.chat(msg), indent=2))
