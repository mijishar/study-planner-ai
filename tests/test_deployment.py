"""Deployment verification tests for StudyMate AI.

Run AFTER `./kit deploy` to confirm submission/deployment.json is valid
and the deployed AgentCore endpoint responds correctly.

    pytest tests/test_deployment.py -m integration -v

Requirements: 7.1 (deployment contract)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

WORKSPACE = Path(__file__).resolve().parent.parent
DEPLOYMENT_JSON = WORKSPACE / "submission" / "deployment.json"


# ---------------------------------------------------------------------------
# Test 1: deployment.json schema
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_deployment_json_exists() -> None:
    """submission/deployment.json must exist after ./kit deploy."""
    assert DEPLOYMENT_JSON.exists(), (
        f"deployment.json not found at {DEPLOYMENT_JSON}. "
        "Run `./kit deploy` first."
    )


@pytest.mark.integration
def test_deployment_json_is_valid_json() -> None:
    """deployment.json must be parseable JSON."""
    assert DEPLOYMENT_JSON.exists(), "Run `./kit deploy` first."
    text = DEPLOYMENT_JSON.read_text(encoding="utf-8")
    data = json.loads(text)  # raises on invalid JSON
    assert isinstance(data, dict), "deployment.json must be a JSON object"


@pytest.mark.integration
def test_deployment_json_has_arn_key() -> None:
    """deployment.json must contain an ARN key (agentcore_arn or arn)."""
    assert DEPLOYMENT_JSON.exists(), "Run `./kit deploy` first."
    data = json.loads(DEPLOYMENT_JSON.read_text(encoding="utf-8"))
    arn_value = data.get("agentcore_arn") or data.get("arn")
    assert arn_value, (
        "deployment.json must have a non-empty 'agentcore_arn' or 'arn' key. "
        f"Got keys: {list(data.keys())}"
    )
    assert isinstance(arn_value, str) and arn_value.strip()


# ---------------------------------------------------------------------------
# Test 2: Live AgentCore round-trip (requires DEMO_TARGET=agentcore + ARN)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_agentcore_chat_returns_valid_response() -> None:
    """A chat() call against the deployed AgentCore agent must return a valid dict."""
    import os

    assert DEPLOYMENT_JSON.exists(), "Run `./kit deploy` first."
    data = json.loads(DEPLOYMENT_JSON.read_text(encoding="utf-8"))
    arn = data.get("agentcore_arn") or data.get("arn")
    assert arn, "No ARN in deployment.json"

    # Point the demo server at AgentCore
    os.environ["DEMO_TARGET"] = "agentcore"
    os.environ["AGENTCORE_ARN"] = arn

    from agent.agent import HackathonAgent

    agent = HackathonAgent()
    out = agent.chat("Explain what a binary search tree is", session_id="deploy-verify")

    assert set(out.keys()) == {"reply", "decisions", "model_id", "latency_ms"}, (
        f"Unexpected keys from deployed agent: {set(out.keys())}"
    )
    assert isinstance(out["reply"], str) and out["reply"].strip(), "Empty reply from deployed agent"
    assert isinstance(out["latency_ms"], int) and out["latency_ms"] >= 0
