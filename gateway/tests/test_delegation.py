"""Tests for gateway.delegation module."""

import pytest

from gateway.delegation import (
    ASK_AGENT_TOOL,
    DELEGATION_BLOCKLIST,
    execute_delegation,
)


class FakeMockProvider:
    """Fake provider that yields a canned response."""

    def __init__(self, response: str = "Test response from agent."):
        self._response = response

    async def generate_stream(self, agent_id, messages, **kwargs):
        yield self._response


class FakeErrorProvider:
    """Fake provider that raises an exception."""

    async def generate_stream(self, agent_id, messages, **kwargs):
        raise RuntimeError("connection refused")
        yield  # make it a generator


class FakeEmptyProvider:
    """Fake provider that yields empty string."""

    async def generate_stream(self, agent_id, messages, **kwargs):
        yield ""


class FakeRouter:
    """Fake router with configurable known agents."""

    def __init__(self, known_agents: set[str] | None = None):
        self._known = known_agents or {"analyst", "coder", "lorekeeper", "trader", "jake", "tom", "mira"}

    def resolve(self, agent_id: str):
        if agent_id in self._known:
            return {"agent": {"id": agent_id}, "system_prompt": "", "model": "test/model"}
        return None


@pytest.mark.asyncio
async def test_successful_delegation():
    """Known agent with working provider returns text."""
    provider = FakeMockProvider("The Elder speaks of ancient times.")
    result = await execute_delegation(
        "lorekeeper",
        "Tell me about the ancient war.",
        get_provider_fn=lambda _: provider,
        router=FakeRouter(),
    )
    assert result == "The Elder speaks of ancient times."


@pytest.mark.asyncio
async def test_unknown_agent():
    """Unknown agent returns error string."""
    result = await execute_delegation(
        "nonexistent",
        "Hello?",
        get_provider_fn=lambda _: FakeMockProvider(),
        router=FakeRouter(),
    )
    assert "[delegation error] Unknown agent: nonexistent" in result


@pytest.mark.asyncio
async def test_blocklisted_agent():
    """Blocklisted agent returns error string."""
    router = FakeRouter(known_agents={"assistant", "inspector", "debugger"})
    for agent_id in ["assistant", "inspector", "debugger"]:
        result = await execute_delegation(
            agent_id,
            "Hey",
            get_provider_fn=lambda _: FakeMockProvider(),
            router=router,
        )
        assert "[delegation error] Cannot delegate to" in result


@pytest.mark.asyncio
async def test_provider_exception():
    """Provider that raises returns error string."""
    result = await execute_delegation(
        "analyst",
        "What's the data say?",
        get_provider_fn=lambda _: FakeErrorProvider(),
        router=FakeRouter(),
    )
    assert "[delegation error] analyst failed:" in result
    assert "connection refused" in result


@pytest.mark.asyncio
async def test_empty_response():
    """Provider that returns empty text returns error string."""
    result = await execute_delegation(
        "trader",
        "What's for sale?",
        get_provider_fn=lambda _: FakeEmptyProvider(),
        router=FakeRouter(),
    )
    assert "[delegation error] trader returned empty response" in result


def test_tool_schema_structure():
    """ASK_AGENT_TOOL has required Anthropic tool schema fields."""
    assert ASK_AGENT_TOOL["name"] == "ask_agent"
    assert "input_schema" in ASK_AGENT_TOOL
    schema = ASK_AGENT_TOOL["input_schema"]
    assert schema["type"] == "object"
    assert "agent_id" in schema["properties"]
    assert "question" in schema["properties"]
    assert set(schema["required"]) == {"agent_id", "question"}


def test_blocklist_contains_expected():
    """Blocklist includes assistant and subprocess agents."""
    assert "assistant" in DELEGATION_BLOCKLIST
    assert "inspector" in DELEGATION_BLOCKLIST
    assert "debugger" in DELEGATION_BLOCKLIST
    # Normal agents should NOT be in blocklist
    assert "analyst" not in DELEGATION_BLOCKLIST
    assert "lorekeeper" not in DELEGATION_BLOCKLIST
