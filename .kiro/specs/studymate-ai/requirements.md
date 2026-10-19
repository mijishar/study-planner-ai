# Requirements Document

## Introduction

StudyMate AI is an AI-powered study assistant for college students and exam-preparing learners.
It solves three common study problems: students struggle to understand difficult technical topics,
struggle to plan their time across a syllabus, and don't know what practice questions to attempt.

The assistant exposes three tools — a Topic Explainer, a Study Planner, and a Quiz Generator —
and uses Strands Decider 2B (tool-selection pattern) to route every student request to the right
tool before the LLM sees it. Amazon Bedrock (Amazon Nova Pro by default) generates the final
student-friendly response. Progress context from previous interactions personalises future
suggestions. The agent will not register for exams, submit assignments, or make purchases; its
scope is learning support and recommendations only.

The system is built in Python using the Strands Agents SDK, the Strands Decider 2B tool-selection
pattern, and the AWS User Group Madurai Strands Decider hackathon kit. It is deployed on Amazon
Bedrock AgentCore Runtime.

---

## Glossary

- **StudyMate_AI**: The overall AI-powered study assistant system delivered by this spec.
- **Decider**: The Strands Decider 2B instance that classifies every incoming student request
  into a tool category before the LLM acts on it.
- **Tool_Selector**: The `ToolSelector` component from `decider_kit.patterns.tool_selection`
  that calls the Decider and narrows the agent's available tools per request.
- **Topic_Explainer**: The Strands `@tool` function that explains a technical concept in plain
  language with examples, given a topic name and optional difficulty level.
- **Study_Planner**: The Strands `@tool` function that breaks a syllabus or study goal into a
  sequenced, time-boxed task list.
- **Quiz_Generator**: The Strands `@tool` function that produces a set of practice questions
  with answers for a given topic and question count.
- **LLM**: The Amazon Bedrock language model (Amazon Nova Pro by default) that generates the
  student-facing natural-language response after a tool has executed.
- **Session**: A single continuous conversation between one student and StudyMate_AI, identified
  by a `session_id` string.
- **Progress_Context**: The accumulated record of topics studied, quizzes taken, and planner
  tasks completed within a session, stored in memory and used to personalise responses.
- **Guardrail**: A boundary rule that prevents the agent from performing actions outside its
  learning-support scope (e.g., exam registration, assignment submission, purchases).
- **Clarification_Request**: A response from StudyMate_AI that asks the student to rephrase or
  narrow their request when the Decider confidence is below the narrowing threshold.

---

## Requirements

### Requirement 1: Tool-Selection Decision

**User Story:** As a student, I want my requests routed to the right study tool automatically,
so that I always get the most relevant response without having to navigate menus.

#### Acceptance Criteria

1. WHEN a student message is received, THE Tool_Selector SHALL call the Decider with the
   message text and the descriptions of Topic_Explainer, Study_Planner, and Quiz_Generator as
   choice options.
2. WHEN the Decider returns a tool choice with confidence at or above 0.60, THE Tool_Selector
   SHALL expose only that single tool to the LLM for the current request.
3. WHEN the Decider returns confidence below 0.60, THE Tool_Selector SHALL expose all three
   tools to the LLM and log a `narrowed: false` entry in the `decisions` list; the LLM SHALL
   then select the tool it uses and that selection SHALL be recorded in the final decision entry.
4. THE Tool_Selector SHALL record the selected tool name, confidence score, full probability
   distribution, `narrowed` boolean, and Decider latency in milliseconds as a dict in the
   `decisions` list returned by `HackathonAgent.chat`; a `none` Decider result SHALL be
   recorded with `tool: "none"`.
5. WHEN the Decider classifies the request as `none` with confidence at or above 0.60, THE
   StudyMate_AI SHALL answer the student directly without invoking any tool.
6. WHEN the Decider call raises an exception or times out, THE Tool_Selector SHALL return a
   safe error response to the student that states the assistant is temporarily unavailable,
   SHALL NOT expose any tool to the LLM, SHALL log `narrowed: false` and `confidence: null`
   in the decision entry, and SHALL NOT surface the internal error details to the student.

---

### Requirement 2: Topic Explainer Tool

**User Story:** As a student, I want difficult technical topics explained in simple language
with examples, so that I can understand concepts I am struggling with.

#### Acceptance Criteria

1. THE Topic_Explainer SHALL accept a `topic` string of 1–500 characters and an optional
   `difficulty` string (`beginner`, `intermediate`, or `advanced`; default `beginner`).
2. WHEN invoked with a valid topic, THE Topic_Explainer SHALL return a dict with keys
   `definition` (str), `example` (str), `analogy` (str), and `difficulty` (str); the
   `analogy` SHALL use vocabulary and example complexity appropriate to the requested
   difficulty level (everyday objects for `beginner`, domain concepts for `intermediate`,
   formal abstractions for `advanced`).
3. WHEN invoked with an empty or whitespace-only `topic` string, THE Topic_Explainer SHALL
   return a structured error dict with key `"error"` whose value identifies the invalid field
   (`topic`) and states the reason (empty or whitespace-only).
4. WHEN invoked with an unrecognised `difficulty` value, THE Topic_Explainer SHALL default to
   `beginner` and include a `"note"` key in the returned dict whose value states that the
   supplied difficulty was unrecognised and `beginner` was used instead.
5. WHEN the Topic_Explainer returns a successful result, THE LLM SHALL produce a response
   consisting of complete prose sentences that incorporate the `definition`, `example`, and
   `analogy` fields in a form appropriate to the `difficulty` level.
6. WHEN the Topic_Explainer returns an error dict, THE LLM SHALL inform the student that the
   explanation could not be generated and ask them to supply a valid topic, without exposing
   the internal error structure.

---

### Requirement 3: Study Planner Tool

**User Story:** As a student, I want my syllabus or study goal broken into a concrete,
time-boxed task list, so that I can manage my time and know what to study each day.

#### Acceptance Criteria

1. THE Study_Planner SHALL accept a `goal` string of 1–2000 characters describing the syllabus
   or study objective and an optional `days_available` integer (minimum 1, maximum 365;
   default 7).
2. WHEN invoked with a valid goal and a `days_available` value between 1 and 365 inclusive,
   THE Study_Planner SHALL return a list of task dicts where each dict contains `day` (int,
   1-indexed), `topic` (non-empty str), `duration_minutes` (int ≥ 5), and `activity`
   (non-empty str); every day number from 1 to `days_available` SHALL appear at least once
   in the list.
3. THE Study_Planner SHALL distribute tasks so that the sum of `duration_minutes` for any
   single `day` value does not exceed 180 minutes.
4. WHEN invoked with an empty or whitespace-only `goal`, THE Study_Planner SHALL return a
   structured error dict with key `"error"` whose value identifies the field (`goal`) and
   states the reason (empty or whitespace-only).
5. WHEN invoked with a `days_available` value less than 1, THE Study_Planner SHALL return a
   structured error dict with key `"error"` whose value identifies the field (`days_available`)
   and states the reason (less than minimum of 1).
6. WHEN invoked with a `days_available` value greater than 365, THE Study_Planner SHALL return
   a structured error dict with key `"error"` whose value identifies the field
   (`days_available`) and states the reason (exceeds maximum of 365).
7. IF the total estimated study workload implied by the `goal` exceeds `days_available`
   multiplied by 180 minutes, THEN THE Study_Planner SHALL return a structured error dict
   with key `"error"` whose value states that the goal cannot be scheduled within the given
   `days_available` at the 180-minute daily cap, and SHALL NOT return a partial or compressed
   task list.
8. WHEN the Study_Planner returns a successful result, THE LLM SHALL format the response as a
   day-by-day schedule where each day appears as a labelled section listing its tasks with
   their topics, durations, and activities.

---

### Requirement 4: Quiz Generator Tool

**User Story:** As a student, I want practice questions generated for any topic I select, so
that I can test my understanding and prepare for exams.

#### Acceptance Criteria

1. THE Quiz_Generator SHALL accept a `topic` string of 1–200 characters and an optional
   `count` integer (minimum 1, maximum 10; default 5).
2. WHEN invoked with a valid topic and a count between 1 and 10 inclusive, THE Quiz_Generator
   SHALL return exactly `count` question dicts, each containing a non-empty `question` (str),
   a `choices` list of exactly four non-empty strings, a `correct_answer` string that exactly
   matches one element of `choices`, and a non-empty `explanation` (str).
3. WHEN invoked with a `count` outside the range 1 to 10, THE Quiz_Generator SHALL clamp the
   value to the nearest boundary (1 or 10), return the clamped number of question dicts, and
   include a top-level `"note"` key in the result whose value states the original value and
   the boundary it was clamped to.
4. WHEN invoked with an empty or whitespace-only `topic`, THE Quiz_Generator SHALL return a
   structured error dict with key `"error"` whose value identifies the invalid field (`topic`)
   and states the reason (empty or whitespace-only).
5. WHEN the Quiz_Generator returns a successful result, THE LLM SHALL present the questions as
   a numbered list where each question's choices are labelled A through D in order, with the
   correct answer and explanation withheld from the initial presentation.
6. WHEN the Quiz_Generator returns an error dict, THE LLM SHALL inform the student that the
   quiz could not be generated and ask them to supply a valid topic, without exposing the
   internal error structure.

---

### Requirement 5: Progress Context and Personalisation

**User Story:** As a student, I want the assistant to remember what I have studied and what
quizzes I have taken during our conversation, so that its suggestions stay relevant to my
learning progress.

#### Acceptance Criteria

1. THE StudyMate_AI SHALL maintain a Progress_Context object within each Session that records
   the topics explained, study plans created, and quizzes generated during that Session; the
   Progress_Context SHALL hold at most 50 entries, discarding the oldest entry when the cap
   is reached.
2. WHEN a tool is successfully invoked, THE StudyMate_AI SHALL update the Progress_Context
   to include the tool name, topic or goal, and an ISO-8601 UTC timestamp; a failed tool
   invocation SHALL NOT add an entry to the Progress_Context.
3. WHEN generating a response and the Progress_Context contains at least one entry, THE LLM
   SHALL receive the current Progress_Context as part of its system prompt and the response
   SHALL reference at least one previously recorded topic or goal.
4. WHEN a student asks what they have covered so far and the Progress_Context contains at
   least one entry, THE StudyMate_AI SHALL include in its reply a summary listing each
   Progress_Context entry's tool name, topic or goal, and timestamp.
5. WHEN a student asks what they have covered so far and the Progress_Context contains zero
   entries, THE StudyMate_AI SHALL return a response that explicitly states no progress has
   been recorded yet in the current Session.
6. WHEN a new Session identified by a new `session_id` is started, THE StudyMate_AI SHALL
   reset the Progress_Context so that it contains zero entries before processing the first
   message of that Session.

---

### Requirement 6: Safety Guardrails and Scope Boundaries

**User Story:** As an exam-preparing student, I want to be certain the assistant will only
help me learn and will never take administrative actions on my behalf, so that I can use it
safely without risk of unintended consequences.

#### Acceptance Criteria

1. IF a student message explicitly requests any of the following administrative actions —
   registering for an exam, submitting an assignment, or making a purchase — THEN THE
   StudyMate_AI SHALL refuse the request and return a response that (a) states it provides
   learning support only, and (b) does not execute any tool or external call.
2. WHEN a student message could be interpreted as either a learning action or one of the
   administrative actions enumerated in criterion 1, THE StudyMate_AI SHALL treat the
   ambiguity as a potential administrative request (safety-first), issue a
   Clarification_Request that identifies the ambiguity, and SHALL NOT invoke any tool or
   take any further action until the student explicitly confirms a learning intent.
3. THE StudyMate_AI SHALL not invoke any external API endpoint, perform any database write,
   or initiate any financial transaction; all tool results SHALL be generated from in-memory
   or synthesised data only.
4. IF a student message contains content that requests harm to any person or entity, THEN THE
   StudyMate_AI SHALL return a response that (a) declines the request without elaborating on
   the harmful content, and (b) contains no tool invocation.
5. IF a student message is off-topic (not related to studying, learning, or academic subjects)
   but does not request harm, THEN THE StudyMate_AI SHALL return a response that politely
   states it is a study assistant and invites the student to ask a study-related question,
   without invoking any tool.

---

### Requirement 7: Agent Interface Contract

**User Story:** As a developer integrating StudyMate AI into the hackathon kit's demo and
deployment pipeline, I want a stable Python interface, so that the demo UI, benchmarking, and
deployment commands all work without modification.

#### Acceptance Criteria

1. THE StudyMate_AI SHALL expose a Python class named `HackathonAgent` in `agent/agent.py`
   with a method `chat(message: str, session_id: str = "default") -> dict`; the method SHALL
   also accept an optional `images` parameter consistent with the Strands Agents SDK
   multi-modal signature.
2. WHEN `chat` is called, THE HackathonAgent SHALL return a dict containing exactly the keys
   `reply` (str), `decisions` (list of dicts), `model_id` (str), and `latency_ms` (int);
   `latency_ms` SHALL be the wall-clock time in milliseconds from the start of the `chat`
   call to the return of the dict.
3. THE `decisions` list SHALL contain one entry per Decider call; each entry SHALL include
   `tool` (str), `confidence` (float or null), `narrowed` (bool), `probabilities`
   (dict mapping tool name to float), and `decider_ms` (int); the `stage` field is not
   required.
4. THE HackathonAgent constructor SHALL accept an optional `eager` boolean parameter; WHEN
   `eager=True` is passed, THE constructor SHALL complete without raising an exception.
5. THE `agent/agent.py` module SHALL define a top-level string constant `NAME` containing the
   agent's display name as a non-empty string.
6. WHEN `chat` raises an unhandled internal exception, THE HackathonAgent SHALL return a dict
   with `reply` set to a user-facing error message, `decisions` set to an empty list,
   `model_id` set to the configured model ID, and `latency_ms` set to the elapsed time.

---

### Requirement 8: Benchmark and Evaluation Cases

**User Story:** As a developer preparing the hackathon submission, I want a labelled set of
evaluation cases for the tool-selection decision, so that I can measure Decider accuracy and
report honest benchmark numbers.

#### Acceptance Criteria

1. THE `agent/eval_cases.jsonl` file SHALL contain at least 15 labelled evaluation cases,
   one JSON object per line.
2. EACH evaluation case SHALL be a JSON object with key `state` (str), key `expected` (dict
   mapping the question name used by `questions_for()` to one of the valid answer labels:
   `"explain_topic"`, `"create_study_plan"`, `"generate_quiz"`, or `"none"`), and an optional
   key `split` (str: `"tune"` or `"test"`); omitting `split` is treated as `"test"`.
3. THE evaluation cases SHALL include at least 3 cases whose `expected` value maps to each of
   the four labels: `"explain_topic"`, `"create_study_plan"`, `"generate_quiz"`, and `"none"`.
4. THE `state` field in each evaluation case SHALL use the exact format string produced by
   `ToolSelector.select` when it calls the Decider at runtime, so that the eval case can be
   replayed against the Decider without modification.
5. THE evaluation cases SHALL include at least 5 cases with `split: "tune"` and at least
   10 cases with `split: "test"` (or omitted `split`), so that accuracy numbers reported in
   the submission are computed on held-out data only.

---

### Requirement 9: Demo Script and Web UI

**User Story:** As a hackathon submitter recording the demo video, I want a scripted
conversation that showcases all three tools and the Decider's routing decisions, so that I can
record a complete demo without improvising.

#### Acceptance Criteria

1. THE `agent/demo_script.yaml` SHALL contain at least 6 turns; the turns SHALL collectively
   exercise the Topic_Explainer, Study_Planner, and Quiz_Generator at least once each, and
   compliance with this criterion requires both the minimum turn count and coverage of all
   three tools — meeting the turn count alone is insufficient.
2. EACH turn in the demo script SHALL include a `user` field (the student's message text) and
   a `note` field (neutral narration text for the video); both fields SHALL be non-empty
   strings; if the kit's demo runner uses different field names (e.g., `say` / `narrate`),
   the file SHALL use those names instead and this criterion is satisfied.
3. THE demo web UI SHALL display the `decisions` list from each `chat` response in a live
   decision panel alongside the chat reply; WHEN the `decisions` list is non-empty, the panel
   SHALL show the `tool`, `confidence`, and `probabilities` values for each entry; WHEN the
   `decisions` list is empty or absent, the panel SHALL display a placeholder message
   indicating no routing decision was made.
4. WHEN the demo UI receives a response where any decision entry has `narrowed: true`, THE
   demo UI SHALL render the `tool` value for that entry in a visually distinct style (e.g.,
   bold text or a coloured badge) compared to entries where `narrowed` is false or absent.
