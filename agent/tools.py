"""KIT EXAMPLE tools: an online store's order system, with in-memory data so the demo runs anywhere.

Replace with your own tools (/new-agent does this). Keep a clear one-line docstring on each: the
model reads it, and the tool-selection pattern uses it as the option description.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Progress Context — session memory (Requirements 5.1, 5.2, 5.3, 5.6)
# ---------------------------------------------------------------------------
from collections import deque
from dataclasses import dataclass


@dataclass
class ProgressEntry:
    """A single record of a tool invocation within a session."""

    tool: str           # "Topic_Explainer" | "Study_Planner" | "Quiz_Generator"
    topic_or_goal: str  # the topic or goal string passed to the tool
    timestamp: str      # ISO-8601 UTC, e.g. "2025-07-10T14:32:00Z"


class ProgressContext:
    """Accumulates up to MAX_ENTRIES tool-invocation records for a session.

    When the cap is exceeded the oldest entry is discarded automatically
    (deque maxlen behaviour). To_prompt_fragment() serialises the current
    entries as a bulleted list suitable for injection into an LLM system
    prompt; returns an empty string when there are no entries.
    """

    MAX_ENTRIES: int = 50

    def __init__(self) -> None:
        self.entries: deque[ProgressEntry] = deque(maxlen=self.MAX_ENTRIES)

    def add(self, entry: ProgressEntry) -> None:
        """Append *entry* to the context, evicting the oldest if at capacity."""
        self.entries.append(entry)

    def to_prompt_fragment(self) -> str:
        """Return a bulleted-list string of all entries, or '' if empty."""
        if not self.entries:
            return ""
        lines = [
            f"- [{e.timestamp}] {e.tool}: {e.topic_or_goal}"
            for e in self.entries
        ]
        return "Previously studied in this session:\n" + "\n".join(lines)


# ---------------------------------------------------------------------------

from strands import tool

# ---------------------------------------------------------------------------
# Topic_Explainer — Requirements 2.1, 2.2, 2.3, 2.4
# ---------------------------------------------------------------------------

_VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}

# Static content templates keyed by (topic_lower_fragment, difficulty).
# The tool is intentionally template-based (no external API calls) so that
# it is pure and in-memory, suitable for a hackathon demo where the LLM
# renders the final student-facing prose from the structured dict.
#
# Content is organised into three sections:
#   _TOPIC_CONTENT  – curated entries for well-known topics
#   _GENERIC_*      – fallback templates for any other topic string

_TOPIC_CONTENT: dict[str, dict[str, dict[str, str]]] = {
    "recursion": {
        "beginner": {
            "definition": (
                "Recursion is when a function calls itself to solve a smaller version of the same problem. "
                "Every recursive function needs a base case — a condition that stops the calls — "
                "otherwise it would call itself forever."
            ),
            "example": (
                "Here is a Python countdown using recursion:\n\n"
                "```python\n"
                "def countdown(n):\n"
                "    if n <= 0:          # base case: stop here\n"
                "        print('Go!')\n"
                "    else:\n"
                "        print(n)        # print current number\n"
                "        countdown(n - 1)  # call itself with a smaller number\n\n"
                "countdown(3)\n"
                "# Output:\n"
                "# 3\n"
                "# 2\n"
                "# 1\n"
                "# Go!\n"
                "```\n\n"
                "Step by step: countdown(3) prints 3, then calls countdown(2);\n"
                "countdown(2) prints 2, then calls countdown(1);\n"
                "countdown(1) prints 1, then calls countdown(0);\n"
                "countdown(0) hits the base case and prints 'Go!'."
            ),
            "analogy": (
                "Imagine standing between two mirrors facing each other — you see a reflection of a "
                "reflection, each one smaller, until they fade away. Each reflection is like one "
                "recursive call, and the point where the reflections become too small to see is the base case."
            ),
        },
        "intermediate": {
            "definition": (
                "Recursion is a programming technique where a function invokes itself with a reduced "
                "subproblem, relying on a base case to terminate the call stack."
            ),
            "example": (
                "Here is factorial in Python — a classic recursive function:\n\n"
                "```python\n"
                "def factorial(n):\n"
                "    if n == 0:           # base case\n"
                "        return 1\n"
                "    return n * factorial(n - 1)  # recursive case\n\n"
                "print(factorial(5))  # 120\n"
                "```\n\n"
                "Call stack trace for factorial(3):\n"
                "  factorial(3) → 3 * factorial(2)\n"
                "  factorial(2) → 2 * factorial(1)\n"
                "  factorial(1) → 1 * factorial(0)\n"
                "  factorial(0) → 1  (base case)\n"
                "Unwinding: 1→1→2→6"
            ),
            "analogy": (
                "Recursion resembles mathematical induction: prove the base case, then show that "
                "if the statement holds for k it also holds for k+1 — each recursive call is one "
                "inductive step."
            ),
        },
        "advanced": {
            "definition": (
                "Recursion is the application of a function to its own output domain, defined by a "
                "fixed-point equation f = F(f) where F is a higher-order operator and the least "
                "fixed point is computed via repeated unfolding."
            ),
            "example": (
                "In lambda calculus, the Y combinator Y = λf.(λx.f(x x))(λx.f(x x)) encodes "
                "anonymous recursion by applying a self-referential closure. "
                "In Python this looks like:\n\n"
                "```python\n"
                "Y = lambda f: (lambda x: f(lambda v: x(x)(v)))(lambda x: f(lambda v: x(x)(v)))\n"
                "fact = Y(lambda f: lambda n: 1 if n == 0 else n * f(n - 1))\n"
                "print(fact(5))  # 120\n"
                "```"
            ),
            "analogy": (
                "The fixed-point combinator in denotational semantics: the meaning of a recursive "
                "definition is the least upper bound of the ascending Kleene chain "
                "⊥ ⊑ F(⊥) ⊑ F²(⊥) ⊑ … in the CPO of partial functions."
            ),
        },
    },
    "object-oriented programming": {
        "beginner": {
            "definition": (
                "Object-Oriented Programming (OOP) is a way of writing code by grouping related data "
                "and actions together into reusable units called objects."
            ),
            "example": (
                "A 'Dog' object has data like name and breed, and actions like bark() and fetch() "
                "— everything about a dog lives in one tidy package."
            ),
            "analogy": (
                "Think of a cookie cutter (the class) and the cookies it stamps out (objects). Every "
                "cookie has the same shape but can have different toppings."
            ),
        },
        "intermediate": {
            "definition": (
                "OOP is a programming paradigm that organises code around classes — blueprints that "
                "encapsulate state (fields) and behaviour (methods) — and creates instances of those "
                "classes to model domain entities."
            ),
            "example": (
                "A BankAccount class encapsulates a balance field and deposit()/withdraw() methods; "
                "subclasses like SavingsAccount override interest logic through polymorphism."
            ),
            "analogy": (
                "OOP mirrors interface-based contracts in software engineering: a class is a module "
                "with a public API (its interface) and a hidden implementation (encapsulation), "
                "much like a REST service hides its database behind HTTP endpoints."
            ),
        },
        "advanced": {
            "definition": (
                "OOP is a computational model based on message passing between encapsulated agents; "
                "formally, a class defines a type in an algebraic type system, and dynamic dispatch "
                "implements ad-hoc polymorphism through vtable indirection or trait objects."
            ),
            "example": (
                "In Haskell-style type classes, a Functor constraint fmap :: (a -> b) -> f a -> f b "
                "abstracts over any container type f, generalising OOP's polymorphism to higher-kinded "
                "types."
            ),
            "analogy": (
                "OOP dispatch is isomorphic to existential quantification: ∃T. (T, T → String) "
                "packages a value and its method, hiding the concrete type T behind the existential — "
                "exactly what a vtable pointer achieves at runtime."
            ),
        },
    },
    "machine learning": {
        "beginner": {
            "definition": (
                "Machine learning is teaching a computer to learn patterns from examples instead of "
                "giving it explicit step-by-step instructions."
            ),
            "example": (
                "You show a program thousands of photos labelled 'cat' or 'dog'; it learns to "
                "recognise cats and dogs in new photos it has never seen."
            ),
            "analogy": (
                "It's like teaching a child to recognise animals by showing them picture books. "
                "The more pictures they see, the better they get — no one writes out a list of rules "
                "for 'what makes a cat a cat'."
            ),
        },
        "intermediate": {
            "definition": (
                "Machine learning is a subfield of AI where algorithms iteratively adjust internal "
                "parameters (weights) by minimising a loss function computed over a training dataset, "
                "enabling generalisation to unseen inputs."
            ),
            "example": (
                "A logistic regression model trained on labelled email data learns decision boundaries "
                "in feature space that separate spam from non-spam with minimal cross-entropy loss."
            ),
            "analogy": (
                "Training a model is like tuning a radio: you adjust the dial (gradient descent) until "
                "the signal (loss) is as clear as possible on the training station, then check it still "
                "receives other stations (validation set) without static."
            ),
        },
        "advanced": {
            "definition": (
                "Machine learning formalises generalisation as PAC-learning: a hypothesis class ℋ is "
                "efficiently learnable if, for any ε, δ > 0, a polynomial number of samples suffices "
                "to find h ∈ ℋ whose true risk R(h) ≤ min_{h*∈ℋ} R(h*) + ε with probability ≥ 1−δ."
            ),
            "example": (
                "For linear classifiers with VC dimension d, the sample complexity bound is "
                "O((d + log(1/δ)) / ε), meaning a 2-layer perceptron with n neurons requires roughly "
                "O(n log n / ε) examples for ε-accurate learning."
            ),
            "analogy": (
                "The bias–variance trade-off maps directly to the PAC bound's structural risk "
                "minimisation: larger model capacity reduces approximation error (bias) but inflates "
                "the VC-dimension term (variance), making the optimal model the fixed point that "
                "balances both terms."
            ),
        },
    },
    "api": {
        "beginner": {
            "definition": (
                "An API (Application Programming Interface) is a set of rules that lets two programs "
                "talk to each other and share data."
            ),
            "example": (
                "When a weather app on your phone shows today's forecast, it sends a request to a "
                "weather API and gets back temperature and rain data — the app never stores the "
                "weather itself."
            ),
            "analogy": (
                "An API is like a waiter at a restaurant. You (the app) tell the waiter (API) what "
                "you want; the waiter takes your order to the kitchen (server) and brings back your "
                "food (data) — you never go into the kitchen yourself."
            ),
        },
        "intermediate": {
            "definition": (
                "An API defines a contract between a client and a service: a set of endpoints, "
                "accepted request schemas, and guaranteed response schemas, typically exposed over "
                "HTTP using REST or GraphQL conventions."
            ),
            "example": (
                "A REST API endpoint GET /users/{id} accepts a path parameter and returns a JSON "
                "object conforming to a User schema; HTTP status codes (200, 404, 422) communicate "
                "outcome without parsing the body."
            ),
            "analogy": (
                "An API contract is like a typed interface in software: the provider guarantees the "
                "method signature; the consumer depends only on the interface, not the implementation, "
                "enabling independent deployment of both sides."
            ),
        },
        "advanced": {
            "definition": (
                "An API is a formalized interface specification — in REST, described by an OpenAPI "
                "schema; in RPC systems, by an IDL (e.g., Protobuf); the schema induces a category "
                "of request/response types and morphisms (transformations) that must be preserved "
                "across API versions."
            ),
            "example": (
                "GraphQL's type system enforces a strict schema at the query layer, enabling "
                "introspection and client-driven field selection; this is equivalent to projecting a "
                "dependent product type over the server's entity graph."
            ),
            "analogy": (
                "API versioning is analogous to functor mapping in category theory: a backwards-"
                "compatible change is a natural transformation η : F ⇒ G between the old and new "
                "response functors, ensuring existing compositions still commute."
            ),
        },
    },
    "database": {
        "beginner": {
            "definition": (
                "A database is an organised collection of information stored on a computer so it can "
                "be quickly found, updated, and managed."
            ),
            "example": (
                "A school keeps student names, grades, and attendance in a database so teachers can "
                "look up any student's record in seconds."
            ),
            "analogy": (
                "A database is like a filing cabinet: each drawer (table) holds folders (rows) about "
                "one type of thing, and labels (columns) tell you what each piece of paper inside means."
            ),
        },
        "intermediate": {
            "definition": (
                "A relational database stores data in normalised tables linked by foreign keys; a "
                "query engine (SQL) lets users join, filter, and aggregate rows with declarative "
                "syntax rather than procedural loops."
            ),
            "example": (
                "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id "
                "GROUP BY u.name retrieves the order count per user by joining two tables on a "
                "foreign key."
            ),
            "analogy": (
                "Normalisation is like DRY code: instead of repeating a customer's address in every "
                "order row, you store it once in a customers table and reference it by ID, reducing "
                "update anomalies."
            ),
        },
        "advanced": {
            "definition": (
                "A relational database implements the relational algebra over typed tuple spaces; "
                "ACID transactions are enforced through MVCC or locking protocols, and query plans "
                "are optimised using cost-based search over the space of equivalent relational "
                "expressions."
            ),
            "example": (
                "A hash-join between two 10M-row tables runs in O(n) time by building a hash "
                "table on the smaller relation's join key and probing it for each tuple of the "
                "larger relation, outperforming a nested-loop join's O(n²) cost."
            ),
            "analogy": (
                "The query optimiser's problem is isomorphic to join-order enumeration in a DAG: "
                "the Selinger algorithm finds the minimum-cost plan using dynamic programming over "
                "subsets of the join graph, analogous to optimal substructure in shortest-path "
                "algorithms."
            ),
        },
    },
}

# Fallback templates — used when the topic does not match any curated key.
# {topic} is substituted with the original (stripped) topic string.
_FALLBACK_CONTENT: dict[str, dict[str, str]] = {
    "beginner": {
        "definition": (
            "{topic} is a concept that helps solve a specific type of problem by providing a "
            "clear, structured approach that anyone can learn with practice."
        ),
        "example": (
            "For instance, when working with {topic} you might start with a simple, concrete "
            "case — like a small dataset or a minimal example — and gradually add complexity as "
            "you become more comfortable."
        ),
        "analogy": (
            "Think of {topic} like learning to ride a bicycle: at first you need training wheels "
            "(simplified rules), but once the core idea clicks you can balance on your own and "
            "go anywhere."
        ),
    },
    "intermediate": {
        "definition": (
            "{topic} is a structured technique or paradigm that addresses a class of problems "
            "through well-defined abstractions, trade-offs, and composable building blocks used "
            "across many software and engineering domains."
        ),
        "example": (
            "A typical application of {topic} involves identifying the core invariants, selecting "
            "appropriate data structures, and iteratively refining the solution against a suite of "
            "representative test cases."
        ),
        "analogy": (
            "{topic} resembles a design pattern in software engineering: once you recognise the "
            "recurring structure, you apply a known template and adapt it to the specifics of your "
            "problem domain, trading off generality against implementation cost."
        ),
    },
    "advanced": {
        "definition": (
            "{topic} can be formalised as a mathematical structure over an abstract domain, where "
            "the key properties are expressed as invariants, and correctness is proven relative to "
            "a formal specification using axiomatic or denotational semantics."
        ),
        "example": (
            "A rigorous treatment of {topic} involves constructing a proof of correctness — or a "
            "counter-example — by reasoning about the state space, transition relations, and "
            "convergence properties of the associated formal model."
        ),
        "analogy": (
            "{topic} is analogous to a category-theoretic abstraction: the objects are the "
            "entities of the domain, the morphisms are the structure-preserving transformations, "
            "and the key theorems correspond to universal properties that hold regardless of the "
            "concrete representation chosen."
        ),
    },
}


def _get_topic_content(topic: str, difficulty: str) -> dict[str, str]:
    """Return definition/example/analogy for *topic* at *difficulty* level.

    Looks up *topic* in the curated table first (case-insensitive substring
    match on keys); falls back to the generic template when no match is found.
    """
    topic_lower = topic.lower()
    for key, levels in _TOPIC_CONTENT.items():
        if key in topic_lower or topic_lower in key:
            if difficulty in levels:
                return dict(levels[difficulty])
    # Generic fallback
    template = _FALLBACK_CONTENT[difficulty]
    return {k: v.format(topic=topic) for k, v in template.items()}


@tool
def Topic_Explainer(topic: str, difficulty: str = "beginner") -> dict:
    """Explain a technical topic in plain language with an example and analogy.

    Returns a structured dict the LLM should render as:
    1. A plain-language definition.
    2. A concrete example (with code if applicable).
    3. A step-by-step breakdown of the example.
    4. An analogy appropriate to the difficulty level.
    The LLM should NOT seek clarification — just present all four sections directly.
    """
    # --- Input validation ---
    if not topic or not topic.strip():
        return {"error": "topic: empty or whitespace-only"}

    topic = topic.strip()

    # --- Difficulty normalisation ---
    note: str | None = None
    if difficulty not in _VALID_DIFFICULTIES:
        note = (
            f"The difficulty '{difficulty}' was not recognised; "
            f"defaulting to 'beginner'."
        )
        difficulty = "beginner"

    # --- Content generation (pure, in-memory) ---
    content = _get_topic_content(topic, difficulty)

    result: dict = {
        "definition": content["definition"],
        "example": content["example"],
        "analogy": content["analogy"],
        "difficulty": difficulty,
    }
    if note is not None:
        result["note"] = note

    return result


# ---------------------------------------------------------------------------
# Study_Planner — Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
# ---------------------------------------------------------------------------

# Keyword → list of (topic, activity, duration_minutes) tuples.
# Each entry describes one study block that can be assigned to a day.
# duration_minutes must be ≥ 5 and any day's total must not exceed 180.
_TOPIC_ACTIVITIES: list[tuple[str, str, int]] = [
    # Computer Science / Programming
    ("Variables and Data Types", "Read chapter and take notes", 30),
    ("Control Flow (if/else, loops)", "Work through coding exercises", 45),
    ("Functions and Scope", "Write and test small programs", 45),
    ("Recursion", "Study examples and trace call stacks", 60),
    ("Object-Oriented Programming", "Build a simple class hierarchy", 60),
    ("Data Structures: Arrays & Lists", "Implement from scratch", 45),
    ("Data Structures: Stacks & Queues", "Solve practice problems", 45),
    ("Data Structures: Trees & Graphs", "Draw diagrams and trace algorithms", 60),
    ("Sorting Algorithms", "Implement Bubble, Merge, Quick sort", 60),
    ("Searching Algorithms", "Implement Binary Search and BFS/DFS", 45),
    ("Big-O Complexity Analysis", "Analyze time/space of your implementations", 30),
    ("APIs and HTTP", "Read documentation, make sample requests", 30),
    ("Databases and SQL", "Write SELECT, JOIN, GROUP BY queries", 45),
    ("Version Control with Git", "Practice branching and merging", 30),
    ("Testing Fundamentals", "Write unit tests for existing code", 45),
    # Mathematics
    ("Algebra: Linear Equations", "Solve problem sets", 45),
    ("Algebra: Quadratic Equations", "Solve problem sets", 45),
    ("Calculus: Limits", "Read theory and solve examples", 60),
    ("Calculus: Derivatives", "Differentiate functions, apply chain rule", 60),
    ("Calculus: Integrals", "Compute definite and indefinite integrals", 60),
    ("Probability Basics", "Study definitions, solve probability problems", 45),
    ("Statistics: Descriptive Stats", "Calculate mean, median, variance on datasets", 30),
    ("Linear Algebra: Vectors", "Perform vector operations and proofs", 45),
    ("Linear Algebra: Matrices", "Multiply matrices, find determinants", 60),
    ("Discrete Math: Sets & Logic", "Review set theory and truth tables", 45),
    ("Discrete Math: Combinatorics", "Permutations, combinations, counting problems", 45),
    # Sciences
    ("Physics: Kinematics", "Derive and apply kinematic equations", 60),
    ("Physics: Forces and Newton's Laws", "Solve free-body diagram problems", 60),
    ("Chemistry: Periodic Table", "Memorize groups and periodic trends", 30),
    ("Chemistry: Stoichiometry", "Balance equations and compute moles", 45),
    ("Biology: Cell Structure", "Label diagrams and summarise functions", 30),
    ("Biology: Genetics", "Solve Punnett square problems", 45),
    # Languages / Humanities
    ("Grammar and Sentence Structure", "Complete grammar exercises", 30),
    ("Vocabulary Building", "Learn 20 new words with flashcards", 20),
    ("Essay Writing", "Outline and draft a practice essay", 60),
    ("Reading Comprehension", "Read a passage and answer questions", 30),
    ("History: Key Events Timeline", "Create a timeline with notes", 45),
    # General / Exam Prep
    ("Practice Problems", "Timed practice set from past exams", 60),
    ("Concept Review", "Re-read notes and highlight key points", 30),
    ("Flashcard Revision", "Review flashcard deck for the topic", 20),
    ("Mock Exam / Quiz", "Timed full mock exam under exam conditions", 90),
    ("Weak Areas Revisit", "Focus on problem areas from earlier sessions", 45),
    ("Summary and Mind Map", "Draw a mind map of all key concepts", 30),
]

# Keywords that map a goal string to a subset of relevant topic activities.
# Each entry: (keyword_fragment_lower, activity_index_list)
_KEYWORD_MAP: list[tuple[str, list[int]]] = [
    ("python",         [0, 1, 2, 3, 4, 14, 38]),
    ("programm",       [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ("coding",         [0, 1, 2, 4, 8, 9, 14]),
    ("algorithm",      [3, 7, 8, 9, 10, 37]),
    ("data struct",    [5, 6, 7, 8, 9]),
    ("software",       [4, 10, 11, 13, 14]),
    ("database",       [12, 38]),
    ("sql",            [12, 38]),
    ("api",            [11, 38]),
    ("git",            [13, 38]),
    ("math",           [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]),
    ("calculus",       [17, 18, 19]),
    ("algebra",        [15, 16, 22, 23]),
    ("statistic",      [20, 21]),
    ("probabilit",     [20]),
    ("linear algebra", [22, 23]),
    ("discrete",       [24, 25]),
    ("physics",        [26, 27, 39, 40]),
    ("chemistry",      [28, 29, 39, 40]),
    ("biology",        [30, 31, 39, 40]),
    ("science",        [26, 27, 28, 29, 30, 31, 39, 40]),
    ("english",        [32, 33, 34, 35]),
    ("grammar",        [32]),
    ("vocabular",      [33]),
    ("essay",          [34]),
    ("writing",        [34, 35]),
    ("history",        [36]),
    ("exam",           [37, 38, 39, 40, 41]),
    ("quiz",           [37, 40]),
    ("test",           [38, 40]),
    ("review",         [38, 39, 41]),
    ("revision",       [39, 40, 41]),
    ("study",          [38, 39, 40, 41]),
    ("syllabus",       [38, 39, 40, 41]),
    ("course",         [38, 39, 40]),
    ("learn",          [38, 39, 40]),
    ("prepare",        [37, 38, 39, 40, 41]),
]


def _select_activities_for_goal(goal: str) -> list[tuple[str, str, int]]:
    """Return an ordered list of activity tuples matched to *goal* keywords.

    Falls back to the general exam-prep activities when no keyword matches.
    Deduplicates while preserving insertion order.
    """
    goal_lower = goal.lower()
    seen: set[int] = set()
    result: list[tuple[str, str, int]] = []

    for keyword, indices in _KEYWORD_MAP:
        if keyword in goal_lower:
            for idx in indices:
                if idx not in seen:
                    seen.add(idx)
                    result.append(_TOPIC_ACTIVITIES[idx])

    if not result:
        # Generic fallback: general study-prep activities
        fallback_indices = [38, 39, 41, 37, 40]
        for idx in fallback_indices:
            if idx not in seen:
                seen.add(idx)
                result.append(_TOPIC_ACTIVITIES[idx])

    return result


def _build_schedule(
    activities: list[tuple[str, str, int]],
    days_available: int,
) -> list[dict] | None:
    """Distribute *activities* across *days_available* days.

    Returns a list of task dicts on success, or None when the total workload
    exceeds ``days_available × 180`` minutes.

    Distribution strategy:
    - Cycle through the activity list, assigning each to the next day that
      still has room (≤ 180 min).  Every day gets at least one task because
      we seed it with the minimum-duration activity from the list.
    - If the activity pool is smaller than ``days_available``, cycle through
      it repeatedly.
    - After all days have been seeded, remaining capacity is filled greedily.
    """
    DAILY_CAP = 180
    MIN_DURATION = 5

    # Ensure all durations are valid (≥ 5).  The static table already
    # satisfies this, but guard defensively.
    valid_activities = [(t, a, max(d, MIN_DURATION)) for t, a, d in activities]

    if not valid_activities:
        return None

    # Total workload estimate: use each activity once, cycling if needed.
    # We need at least one task per day, so we need ≥ days_available tasks
    # total.  Cycle the activity pool to cover all days.
    pool: list[tuple[str, str, int]] = []
    while len(pool) < max(days_available, 1):
        pool.extend(valid_activities)

    # Check if total workload would exceed the cap.
    # Use exactly days_available * 1 task minimum, each ≤ 180.
    # The real check is: can we schedule at least one task per day
    # without any day exceeding 180 min?  Since each individual task
    # is at most 90 min (from the table), one per day always fits.
    # The overload error fires only when the CALLER provides a workload
    # hint via the goal length heuristic (Requirement 3.7).
    #
    # Heuristic: estimate total workload from the pool slice we will use.
    # We aim for roughly 2–4 tasks per day (60–120 min/day average).
    tasks_per_day = min(3, max(1, DAILY_CAP // 60))
    total_slots = days_available * tasks_per_day

    # Slice the pool to total_slots tasks (cycling as needed).
    extended_pool: list[tuple[str, str, int]] = []
    while len(extended_pool) < total_slots:
        extended_pool.extend(valid_activities)
    extended_pool = extended_pool[:total_slots]

    # Check total estimated minutes vs cap.
    total_minutes = sum(d for _, _, d in extended_pool)
    max_allowed = days_available * DAILY_CAP
    if total_minutes > max_allowed:
        return None

    # Assign tasks to days, ensuring every day appears at least once
    # and no day exceeds 180 min.
    day_load: list[int] = [0] * (days_available + 1)   # 1-indexed
    schedule: list[dict] = []

    pool_index = 0
    pool_len = len(valid_activities)

    # First pass: give each day at least one task (cycled from valid_activities).
    for day in range(1, days_available + 1):
        topic, activity, duration = valid_activities[pool_index % pool_len]
        pool_index += 1
        schedule.append({
            "day": day,
            "topic": topic,
            "duration_minutes": duration,
            "activity": activity,
        })
        day_load[day] += duration

    # Second pass: add extra tasks up to total_slots using remaining capacity.
    extra_needed = total_slots - days_available
    day_ptr = 1
    added = 0
    while added < extra_needed:
        topic, activity, duration = valid_activities[pool_index % pool_len]
        pool_index += 1
        # Find a day that can still accommodate this task.
        tried = 0
        while day_load[day_ptr] + duration > DAILY_CAP and tried < days_available:
            day_ptr = (day_ptr % days_available) + 1
            tried += 1
        if tried >= days_available:
            # No day has room for this task; skip it.
            added += 1
            day_ptr = (day_ptr % days_available) + 1
            continue
        schedule.append({
            "day": day_ptr,
            "topic": topic,
            "duration_minutes": duration,
            "activity": activity,
        })
        day_load[day_ptr] += duration
        day_ptr = (day_ptr % days_available) + 1
        added += 1

    # Sort by day for a clean presentation.
    schedule.sort(key=lambda t: t["day"])
    return schedule


@tool
def Study_Planner(goal: str, days_available: int = 7) -> list | dict:
    """Break a syllabus or study goal into a day-by-day time-boxed task list."""
    # --- Input validation ---
    if not goal or not goal.strip():
        return {"error": "goal: empty or whitespace-only"}

    if days_available < 1:
        return {"error": "days_available: less than minimum of 1"}

    if days_available > 365:
        return {"error": "days_available: exceeds maximum of 365"}

    # --- Activity selection based on goal keywords ---
    activities = _select_activities_for_goal(goal.strip())

    # --- Schedule generation ---
    schedule = _build_schedule(activities, days_available)

    if schedule is None:
        return {
            "error": (
                f"goal cannot be scheduled within {days_available} days "
                f"at the 180-minute daily cap"
            )
        }

    return schedule


# ---------------------------------------------------------------------------
# Study_Planner — Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
# ---------------------------------------------------------------------------

_TOPIC_ACTIVITIES: list[tuple[str, str, int]] = [
    ("Variables and Data Types", "Read chapter and take notes", 30),
    ("Control Flow (if/else, loops)", "Work through coding exercises", 45),
    ("Functions and Scope", "Write and test small programs", 45),
    ("Recursion", "Study examples and trace call stacks", 60),
    ("Object-Oriented Programming", "Build a simple class hierarchy", 60),
    ("Data Structures: Arrays & Lists", "Implement from scratch", 45),
    ("Data Structures: Stacks & Queues", "Solve practice problems", 45),
    ("Data Structures: Trees & Graphs", "Draw diagrams and trace algorithms", 60),
    ("Sorting Algorithms", "Implement Bubble, Merge, Quick sort", 60),
    ("Searching Algorithms", "Implement Binary Search and BFS/DFS", 45),
    ("Big-O Complexity Analysis", "Analyze time/space of your implementations", 30),
    ("APIs and HTTP", "Read documentation, make sample requests", 30),
    ("Databases and SQL", "Write SELECT, JOIN, GROUP BY queries", 45),
    ("Version Control with Git", "Practice branching and merging", 30),
    ("Testing Fundamentals", "Write unit tests for existing code", 45),
    ("Algebra: Linear Equations", "Solve problem sets", 45),
    ("Algebra: Quadratic Equations", "Solve problem sets", 45),
    ("Calculus: Limits", "Read theory and solve examples", 60),
    ("Calculus: Derivatives", "Differentiate functions, apply chain rule", 60),
    ("Calculus: Integrals", "Compute definite and indefinite integrals", 60),
    ("Probability Basics", "Study definitions, solve probability problems", 45),
    ("Statistics: Descriptive Stats", "Calculate mean, median, variance on datasets", 30),
    ("Linear Algebra: Vectors", "Perform vector operations and proofs", 45),
    ("Linear Algebra: Matrices", "Multiply matrices, find determinants", 60),
    ("Discrete Math: Sets & Logic", "Review set theory and truth tables", 45),
    ("Discrete Math: Combinatorics", "Permutations, combinations, counting problems", 45),
    ("Physics: Kinematics", "Derive and apply kinematic equations", 60),
    ("Physics: Forces and Newton's Laws", "Solve free-body diagram problems", 60),
    ("Chemistry: Periodic Table", "Memorize groups and periodic trends", 30),
    ("Chemistry: Stoichiometry", "Balance equations and compute moles", 45),
    ("Biology: Cell Structure", "Label diagrams and summarise functions", 30),
    ("Biology: Genetics", "Solve Punnett square problems", 45),
    ("Grammar and Sentence Structure", "Complete grammar exercises", 30),
    ("Vocabulary Building", "Learn 20 new words with flashcards", 20),
    ("Essay Writing", "Outline and draft a practice essay", 60),
    ("Reading Comprehension", "Read a passage and answer questions", 30),
    ("History: Key Events Timeline", "Create a timeline with notes", 45),
    ("Practice Problems", "Timed practice set from past exams", 60),
    ("Concept Review", "Re-read notes and highlight key points", 30),
    ("Flashcard Revision", "Review flashcard deck for the topic", 20),
    ("Mock Exam / Quiz", "Timed full mock exam under exam conditions", 90),
    ("Weak Areas Revisit", "Focus on problem areas from earlier sessions", 45),
    ("Summary and Mind Map", "Draw a mind map of all key concepts", 30),
]

_KEYWORD_MAP: list[tuple[str, list[int]]] = [
    ("python",         [0, 1, 2, 3, 4, 14, 38]),
    ("programm",       [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ("coding",         [0, 1, 2, 4, 8, 9, 14]),
    ("algorithm",      [3, 7, 8, 9, 10, 37]),
    ("data struct",    [5, 6, 7, 8, 9]),
    ("software",       [4, 10, 11, 13, 14]),
    ("database",       [12, 38]),
    ("sql",            [12, 38]),
    ("api",            [11, 38]),
    ("git",            [13, 38]),
    ("math",           [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]),
    ("calculus",       [17, 18, 19]),
    ("algebra",        [15, 16, 22, 23]),
    ("statistic",      [20, 21]),
    ("probabilit",     [20]),
    ("linear algebra", [22, 23]),
    ("discrete",       [24, 25]),
    ("physics",        [26, 27, 39, 40]),
    ("chemistry",      [28, 29, 39, 40]),
    ("biology",        [30, 31, 39, 40]),
    ("science",        [26, 27, 28, 29, 30, 31, 39, 40]),
    ("english",        [32, 33, 34, 35]),
    ("grammar",        [32]),
    ("vocabular",      [33]),
    ("essay",          [34]),
    ("writing",        [34, 35]),
    ("history",        [36]),
    ("exam",           [37, 38, 39, 40, 41]),
    ("quiz",           [37, 40]),
    ("test",           [38, 40]),
    ("review",         [38, 39, 41]),
    ("revision",       [39, 40, 41]),
    ("study",          [38, 39, 40, 41]),
    ("syllabus",       [38, 39, 40, 41]),
    ("course",         [38, 39, 40]),
    ("learn",          [38, 39, 40]),
    ("prepare",        [37, 38, 39, 40, 41]),
]


def _select_activities_for_goal(goal: str) -> list[tuple[str, str, int]]:
    """Return an ordered list of activity tuples matched to *goal* keywords."""
    goal_lower = goal.lower()
    seen: set[int] = set()
    result: list[tuple[str, str, int]] = []
    for keyword, indices in _KEYWORD_MAP:
        if keyword in goal_lower:
            for idx in indices:
                if idx not in seen:
                    seen.add(idx)
                    result.append(_TOPIC_ACTIVITIES[idx])
    if not result:
        for idx in [38, 39, 41, 37, 40]:
            if idx not in seen:
                seen.add(idx)
                result.append(_TOPIC_ACTIVITIES[idx])
    return result


def _build_schedule(
    activities: list[tuple[str, str, int]],
    days_available: int,
) -> list[dict] | None:
    """Distribute *activities* across *days_available* days (≤ 180 min/day)."""
    DAILY_CAP = 180
    MIN_DURATION = 5
    valid_activities = [(t, a, max(d, MIN_DURATION)) for t, a, d in activities]
    if not valid_activities:
        return None

    tasks_per_day = min(3, max(1, DAILY_CAP // 60))
    total_slots = days_available * tasks_per_day
    pool: list[tuple[str, str, int]] = []
    while len(pool) < total_slots:
        pool.extend(valid_activities)
    pool = pool[:total_slots]

    total_minutes = sum(d for _, _, d in pool)
    max_allowed = days_available * DAILY_CAP
    if total_minutes > max_allowed:
        return None

    day_load: list[int] = [0] * (days_available + 1)
    schedule: list[dict] = []
    pool_index = 0
    pool_len = len(valid_activities)

    for day in range(1, days_available + 1):
        topic, activity, duration = valid_activities[pool_index % pool_len]
        pool_index += 1
        schedule.append({"day": day, "topic": topic, "duration_minutes": duration, "activity": activity})
        day_load[day] += duration

    extra_needed = total_slots - days_available
    day_ptr = 1
    added = 0
    while added < extra_needed:
        topic, activity, duration = valid_activities[pool_index % pool_len]
        pool_index += 1
        tried = 0
        while day_load[day_ptr] + duration > DAILY_CAP and tried < days_available:
            day_ptr = (day_ptr % days_available) + 1
            tried += 1
        if tried < days_available:
            schedule.append({"day": day_ptr, "topic": topic, "duration_minutes": duration, "activity": activity})
            day_load[day_ptr] += duration
        day_ptr = (day_ptr % days_available) + 1
        added += 1

    schedule.sort(key=lambda t: t["day"])
    return schedule


@tool
def Study_Planner(goal: str, days_available: int = 7) -> list | dict:
    """Break a syllabus or study goal into a day-by-day time-boxed task list."""
    if not goal or not goal.strip():
        return {"error": "goal: empty or whitespace-only"}
    if days_available < 1:
        return {"error": "days_available: less than minimum of 1"}
    if days_available > 365:
        return {"error": "days_available: exceeds maximum of 365"}

    activities = _select_activities_for_goal(goal.strip())
    schedule = _build_schedule(activities, days_available)
    if schedule is None:
        return {"error": f"goal cannot be scheduled within {days_available} days at the 180-minute daily cap"}
    return schedule


# ---------------------------------------------------------------------------

ORDERS = {
    "A1001": {"item": "trail running shoes", "amount": 129.00, "status": "delivered", "customer": "Priya"},
    "A1002": {"item": "noise-cancelling headphones", "amount": 249.00, "status": "shipped", "customer": "Arun"},
    "A1003": {"item": "yoga mat", "amount": 35.00, "status": "processing", "customer": "Meena"},
}
ACTIONS: list[dict] = []


@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order's item, amount and status by its order id."""
    o = ORDERS.get(order_id.strip().upper())
    return {"order_id": order_id, **o} if o else {"error": f"no order {order_id}"}


@tool
def refund_order(order_id: str, amount: float) -> dict:
    """Refund an order (irreversible): sends the money back to the customer."""
    o = ORDERS.get(order_id.strip().upper())
    if not o:
        return {"error": f"no order {order_id}"}
    if amount > o["amount"]:
        return {"error": f"refund {amount} exceeds the order amount {o['amount']}"}
    ACTIONS.append({"action": "refund", "order_id": order_id, "amount": amount})
    return {"refunded": amount, "order_id": order_id}


@tool
def cancel_order(order_id: str) -> dict:
    """Cancel an order that has not shipped yet (irreversible)."""
    o = ORDERS.get(order_id.strip().upper())
    if not o:
        return {"error": f"no order {order_id}"}
    if o["status"] != "processing":
        return {"error": f"order {order_id} is {o['status']} and cannot be cancelled"}
    o["status"] = "cancelled"
    ACTIONS.append({"action": "cancel", "order_id": order_id})
    return {"cancelled": order_id}


# ---------------------------------------------------------------------------
# Quiz_Generator — Requirements 4.1, 4.2, 4.3, 4.4
# ---------------------------------------------------------------------------

_QUIZ_BANK: dict[str, list[dict]] = {
    "recursion": [
        {"question": "What is the base case in a recursive function?",
         "choices": ["The case that stops the recursion", "The first recursive call", "The return type", "The function name"],
         "correct_answer": "The case that stops the recursion",
         "explanation": "A base case is a condition that terminates the recursion, preventing infinite loops."},
        {"question": "What happens if a recursive function has no base case?",
         "choices": ["It runs forever and causes a stack overflow", "It returns None", "It raises a SyntaxError", "It loops exactly 100 times"],
         "correct_answer": "It runs forever and causes a stack overflow",
         "explanation": "Without a base case, the function keeps calling itself until the call stack is exhausted."},
        {"question": "Which data structure is used internally to track recursive calls?",
         "choices": ["Call stack", "Queue", "Heap", "Hash table"],
         "correct_answer": "Call stack",
         "explanation": "Each recursive call pushes a new frame onto the call stack; the base case pops them off."},
        {"question": "What is tail recursion?",
         "choices": ["Recursion where the recursive call is the last operation", "Recursion without a base case", "Recursion using two functions", "Recursion over a list tail"],
         "correct_answer": "Recursion where the recursive call is the last operation",
         "explanation": "Tail recursion allows some compilers/interpreters to optimise away stack frames."},
        {"question": "What is the time complexity of computing Fibonacci(n) with naive recursion?",
         "choices": ["O(2^n)", "O(n)", "O(n log n)", "O(1)"],
         "correct_answer": "O(2^n)",
         "explanation": "Naive Fibonacci recomputes many sub-problems; memoisation reduces this to O(n)."},
    ],
    "sorting": [
        {"question": "What is the average-case time complexity of QuickSort?",
         "choices": ["O(n log n)", "O(n²)", "O(n)", "O(log n)"],
         "correct_answer": "O(n log n)",
         "explanation": "On average, QuickSort partitions the array into two roughly equal halves at each step."},
        {"question": "Which sorting algorithm is stable by default?",
         "choices": ["Merge Sort", "Quick Sort", "Heap Sort", "Selection Sort"],
         "correct_answer": "Merge Sort",
         "explanation": "Merge Sort preserves the relative order of equal elements, making it stable."},
        {"question": "What is the worst-case time complexity of Bubble Sort?",
         "choices": ["O(n²)", "O(n log n)", "O(n)", "O(1)"],
         "correct_answer": "O(n²)",
         "explanation": "Bubble Sort compares adjacent elements repeatedly; in the worst case it does n*(n-1)/2 comparisons."},
        {"question": "Which algorithm sorts by building a sorted subarray one element at a time?",
         "choices": ["Insertion Sort", "Quick Sort", "Merge Sort", "Radix Sort"],
         "correct_answer": "Insertion Sort",
         "explanation": "Insertion Sort places each element into its correct position in the already-sorted portion."},
        {"question": "What is the space complexity of Merge Sort?",
         "choices": ["O(n)", "O(1)", "O(log n)", "O(n²)"],
         "correct_answer": "O(n)",
         "explanation": "Merge Sort requires auxiliary space proportional to the input size for the merge step."},
    ],
    "python": [
        {"question": "What does the `len()` function return for a list?",
         "choices": ["The number of elements", "The size in bytes", "The last index", "The sum of elements"],
         "correct_answer": "The number of elements",
         "explanation": "`len()` returns the count of items in a sequence or collection."},
        {"question": "Which keyword is used to define a function in Python?",
         "choices": ["def", "func", "function", "define"],
         "correct_answer": "def",
         "explanation": "Python uses `def` followed by the function name to declare a function."},
        {"question": "What is a list comprehension?",
         "choices": ["A concise way to create lists using a loop expression", "A type of sorted list", "A built-in function for filtering", "A class for list manipulation"],
         "correct_answer": "A concise way to create lists using a loop expression",
         "explanation": "`[x*2 for x in range(5)]` creates [0,2,4,6,8] in a single readable expression."},
        {"question": "What is the output of `type(3.14)` in Python?",
         "choices": ["<class 'float'>", "<class 'int'>", "<class 'str'>", "<class 'double'>"],
         "correct_answer": "<class 'float'>",
         "explanation": "3.14 is a floating-point literal; Python's type() returns the class object."},
        {"question": "How do you handle exceptions in Python?",
         "choices": ["try/except", "if/error", "catch/throw", "begin/rescue"],
         "correct_answer": "try/except",
         "explanation": "Python uses `try` to wrap risky code and `except` to catch and handle exceptions."},
    ],
    "machine learning": [
        {"question": "What is overfitting in machine learning?",
         "choices": ["When a model performs well on training data but poorly on new data", "When a model trains too slowly", "When training data is too large", "When the model has too few parameters"],
         "correct_answer": "When a model performs well on training data but poorly on new data",
         "explanation": "Overfitting occurs when a model memorises training examples instead of learning general patterns."},
        {"question": "What does a train/test split achieve?",
         "choices": ["It evaluates generalisation on unseen data", "It speeds up training", "It removes outliers", "It balances class labels"],
         "correct_answer": "It evaluates generalisation on unseen data",
         "explanation": "Keeping a held-out test set prevents the model from being evaluated on data it trained on."},
        {"question": "Which algorithm minimises a loss function by updating weights iteratively?",
         "choices": ["Gradient descent", "Decision tree", "K-means", "Naive Bayes"],
         "correct_answer": "Gradient descent",
         "explanation": "Gradient descent computes the gradient of the loss and steps in the negative gradient direction."},
        {"question": "What is a hyperparameter?",
         "choices": ["A parameter set before training, not learned from data", "A weight learned during training", "A feature in the dataset", "A type of activation function"],
         "correct_answer": "A parameter set before training, not learned from data",
         "explanation": "Examples include learning rate and number of layers — they control the training process itself."},
        {"question": "What does 'epoch' mean in neural network training?",
         "choices": ["One full pass through the entire training dataset", "One weight update step", "One layer of the network", "One batch of data"],
         "correct_answer": "One full pass through the entire training dataset",
         "explanation": "An epoch completes when the model has seen every training sample once."},
    ],
    "database": [
        {"question": "What does SQL stand for?",
         "choices": ["Structured Query Language", "Standard Query Logic", "Simple Question Language", "Sequential Query List"],
         "correct_answer": "Structured Query Language",
         "explanation": "SQL is the standard language for querying and manipulating relational databases."},
        {"question": "Which SQL clause filters rows based on a condition?",
         "choices": ["WHERE", "GROUP BY", "ORDER BY", "HAVING"],
         "correct_answer": "WHERE",
         "explanation": "WHERE applies a predicate to filter individual rows before grouping or ordering."},
        {"question": "What is a primary key?",
         "choices": ["A column that uniquely identifies each row", "The first column in a table", "A foreign reference to another table", "An indexed column"],
         "correct_answer": "A column that uniquely identifies each row",
         "explanation": "Primary keys enforce entity integrity by ensuring no two rows have the same identifier."},
        {"question": "What does a JOIN do in SQL?",
         "choices": ["Combines rows from two tables based on a related column", "Deletes duplicate rows", "Creates a new table", "Sorts the result set"],
         "correct_answer": "Combines rows from two tables based on a related column",
         "explanation": "JOINs are used to retrieve data spread across multiple related tables."},
        {"question": "What is normalisation in databases?",
         "choices": ["Organising data to reduce redundancy and improve integrity", "Sorting data alphabetically", "Compressing data for storage", "Indexing all columns"],
         "correct_answer": "Organising data to reduce redundancy and improve integrity",
         "explanation": "Normalisation splits data into related tables to avoid update and insertion anomalies."},
    ],
}

_QUIZ_FALLBACK_TEMPLATE = [
    {"question": "What is the most fundamental concept in {topic}?",
     "choices": ["The core principle that all other ideas build upon", "The most advanced technique", "The historical origin of the field", "The most common mistake beginners make"],
     "correct_answer": "The core principle that all other ideas build upon",
     "explanation": "In any subject, understanding the foundational concept first makes learning everything else much easier."},
    {"question": "How would you best describe {topic} to a beginner?",
     "choices": ["A structured approach to solving a specific class of problems", "A programming language feature", "A hardware component", "A software framework"],
     "correct_answer": "A structured approach to solving a specific class of problems",
     "explanation": "{topic} provides a systematic method that can be learned and applied to real problems."},
    {"question": "What is the primary benefit of mastering {topic}?",
     "choices": ["Ability to solve problems in that domain efficiently", "Faster typing speed", "Access to advanced hardware", "Automatic code generation"],
     "correct_answer": "Ability to solve problems in that domain efficiently",
     "explanation": "Mastery of {topic} lets you recognise patterns and apply well-tested solutions quickly."},
    {"question": "Which approach is recommended when first learning {topic}?",
     "choices": ["Start with simple examples and gradually increase complexity", "Read the most advanced textbook first", "Memorise all terminology before practising", "Skip theory and only practise coding"],
     "correct_answer": "Start with simple examples and gradually increase complexity",
     "explanation": "Building understanding incrementally from simple to complex helps solidify concepts before tackling edge cases."},
    {"question": "What should you do after studying {topic}?",
     "choices": ["Practice with exercises and build a small project", "Move on immediately to the next topic", "Read the same material again", "Watch a video without taking notes"],
     "correct_answer": "Practice with exercises and build a small project",
     "explanation": "Active practice and project work reinforce learning far more effectively than passive review alone."},
]


def _get_quiz_questions(topic: str, count: int) -> list[dict]:
    """Return *count* question dicts for *topic* (in-memory, no API)."""
    topic_lower = topic.lower()
    bank: list[dict] | None = None
    for key, questions in _QUIZ_BANK.items():
        if key in topic_lower or topic_lower in key:
            bank = questions
            break

    if bank is None:
        # Use template fallback, substituting the actual topic string
        bank = [
            {
                "question": q["question"].format(topic=topic),
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"].format(topic=topic),
            }
            for q in _QUIZ_FALLBACK_TEMPLATE
        ]

    # Cycle the bank to meet the requested count
    result: list[dict] = []
    while len(result) < count:
        result.extend(bank)
    return result[:count]


@tool
def Quiz_Generator(topic: str, count: int = 5) -> list | dict:
    """Generate multiple-choice practice questions for a topic."""
    # --- Input validation ---
    if not topic or not topic.strip():
        return {"error": "topic: empty or whitespace-only"}

    topic = topic.strip()

    # --- Count clamping ---
    original_count = count
    clamped = False
    boundary: str | None = None
    if count < 1:
        count = 1
        clamped = True
        boundary = "minimum of 1"
    elif count > 10:
        count = 10
        clamped = True
        boundary = "maximum of 10"

    questions = _get_quiz_questions(topic, count)

    if clamped:
        return {
            "questions": questions,
            "note": (
                f"count {original_count} was outside the allowed range [1, 10]; "
                f"clamped to {boundary} ({count})."
            ),
        }
    return questions


# ---------------------------------------------------------------------------

TOOLS = [Topic_Explainer, Study_Planner, Quiz_Generator]
