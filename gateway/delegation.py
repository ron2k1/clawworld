"""Multi-agent delegation — allows one NPC to consult another."""

import json
from typing import Callable

from gateway.router import AgentRouter

# Anthropic Messages API tool schema for ask_agent
ASK_AGENT_TOOL = {
    "name": "ask_agent",
    "description": (
        "Ask another NPC agent a question. Use this when a player asks about "
        "a topic outside your direct expertise. The target agent will answer "
        "the question and you can synthesize the response in your own voice."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "agent_id": {
                "type": "string",
                "description": (
                    "The ID of the agent to consult (e.g. 'analyst', "
                    "'coder', 'lorekeeper', 'trader', 'jake', 'tom', 'mira')."
                ),
            },
            "question": {
                "type": "string",
                "description": "The question to ask the target agent.",
            },
        },
        "required": ["agent_id", "question"],
    },
}

# Agents that cannot be delegation targets (self-referential or too slow)
DELEGATION_BLOCKLIST = frozenset({
    "assistant",              # Can't delegate to yourself
    "inspector",          # Subprocess — too slow
    "debugger",           # Subprocess — too slow
    "hermes-agent",       # Local model, not reliable for delegation
})

MAX_TOOL_ROUNDS = 3


async def execute_delegation(
    target_agent_id: str,
    question: str,
    *,
    get_provider_fn: Callable,
    router: AgentRouter,
) -> str:
    """Execute a one-shot delegation call to another agent. Returns text response."""
    # Validate target exists
    if router.resolve(target_agent_id) is None:
        return f"[delegation error] Unknown agent: {target_agent_id}"

    # Validate target not blocklisted
    if target_agent_id in DELEGATION_BLOCKLIST:
        return f"[delegation error] Cannot delegate to {target_agent_id}"

    # Get the correct provider for this target
    provider = get_provider_fn(target_agent_id)

    # Build ephemeral one-shot messages (no session history)
    messages = [{"role": "user", "content": question}]

    try:
        collected = ""
        async for chunk in provider.generate_stream(target_agent_id, messages):
            collected += chunk

        if not collected.strip():
            return f"[delegation error] {target_agent_id} returned empty response"

        return collected.strip()
    except Exception as exc:
        return f"[delegation error] {target_agent_id} failed: {str(exc)[:200]}"
