"""LLM Providers — abstract base + LiveProvider for Anthropic/xAI APIs."""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import AsyncGenerator

import httpx

from gateway.router import AgentRouter


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers (mock, Anthropic, xAI, etc.)."""

    @abstractmethod
    async def generate_stream(
        self, agent_id: str, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Yield text chunks for a given agent and conversation history."""
        ...


# Model prefix -> (base_url, env var for API key, model name transform)
_PROVIDER_CONFIG = {
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "api_key_env": "ANTHROPIC_API_KEY",
        "api_version": "2023-06-01",
    },
    "xai": {
        "base_url": "https://api.x.ai",
        "api_key_env": "XAI_API_KEY",
        "api_version": "2023-06-01",
    },
}


def _parse_model(model_string: str) -> tuple[str, str]:
    """Parse 'provider/model-name' into (provider, model_name)."""
    if "/" not in model_string:
        return ("anthropic", model_string)
    provider, model = model_string.split("/", 1)
    return (provider, model)


class LiveProvider(BaseLLMProvider):
    """Streams responses from Anthropic/xAI APIs using httpx SSE."""

    def __init__(self, router: AgentRouter):
        self._router = router
        # One asyncio.Lock per session key for rate limiting
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, session_key: str) -> asyncio.Lock:
        """Get or create a per-session lock (max 1 concurrent request per player)."""
        if session_key not in self._locks:
            self._locks[session_key] = asyncio.Lock()
        return self._locks[session_key]

    async def generate_stream(
        self,
        agent_id: str,
        messages: list[dict],
        *,
        session_key: str = "",
        get_provider_fn=None,
        router=None,
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks from the LLM API, with optional tool-use delegation."""
        from gateway.delegation import ASK_AGENT_TOOL, MAX_TOOL_ROUNDS, execute_delegation

        resolved = self._router.resolve(agent_id)
        if resolved is None:
            yield f"[error] Unknown agent: {agent_id}"
            return

        model_string = resolved["model"]
        system_prompt = resolved["system_prompt"]
        provider_name, model_name = _parse_model(model_string)

        config = _PROVIDER_CONFIG.get(provider_name)
        if config is None:
            yield f"[error] Unknown provider: {provider_name}"
            return

        api_key = os.environ.get(config["api_key_env"], "")
        if not api_key:
            yield f"[error] Missing {config['api_key_env']} environment variable"
            return

        # Check if this agent has ask_agent tool enabled
        agent_cfg = resolved["agent"]
        tools_allow = agent_cfg.get("tools", {}).get("allow", [])
        has_tools = "ask_agent" in tools_allow and get_provider_fn is not None

        # Trim to last 20 messages
        trimmed = messages[-20:] if len(messages) > 20 else messages

        headers = {
            "x-api-key": api_key,
            "anthropic-version": config["api_version"],
            "content-type": "application/json",
            "accept": "text/event-stream",
        }

        url = f"{config['base_url']}/v1/messages"
        lock = self._get_lock(session_key) if session_key else asyncio.Lock()

        # Multi-turn loop for tool use (or single pass if no tools)
        api_messages = list(trimmed)

        async with lock:
            for _round in range(MAX_TOOL_ROUNDS if has_tools else 1):
                body = {
                    "model": model_name,
                    "max_tokens": 1024,
                    "stream": True,
                    "messages": api_messages,
                }
                if system_prompt:
                    body["system"] = system_prompt
                if has_tools:
                    body["tools"] = [ASK_AGENT_TOOL]

                # SSE state for this round
                stop_reason = None
                tool_use_id = None
                tool_use_name = None
                tool_use_json = ""
                content_blocks = []  # Collect content blocks for follow-up
                round_text = ""

                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST", url, json=body, headers=headers
                    ) as response:
                        if response.status_code != 200:
                            error_body = await response.aread()
                            yield f"[error] API returned {response.status_code}: {error_body.decode()[:200]}"
                            return

                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data == "[DONE]":
                                break

                            try:
                                event = json.loads(data)
                            except json.JSONDecodeError:
                                continue

                            event_type = event.get("type", "")

                            if event_type == "content_block_start":
                                cb = event.get("content_block", {})
                                if cb.get("type") == "tool_use":
                                    tool_use_id = cb.get("id")
                                    tool_use_name = cb.get("name")
                                    tool_use_json = ""

                            elif event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                delta_type = delta.get("type", "")
                                if delta_type == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        round_text += text
                                        yield text
                                elif delta_type == "input_json_delta":
                                    tool_use_json += delta.get("partial_json", "")

                            elif event_type == "content_block_stop":
                                idx = event.get("index", 0)
                                if tool_use_id and tool_use_name:
                                    content_blocks.append({
                                        "type": "tool_use",
                                        "id": tool_use_id,
                                        "name": tool_use_name,
                                        "input": json.loads(tool_use_json) if tool_use_json else {},
                                    })
                                elif round_text:
                                    content_blocks.append({
                                        "type": "text",
                                        "text": round_text,
                                    })

                            elif event_type == "message_delta":
                                delta = event.get("delta", {})
                                stop_reason = delta.get("stop_reason")

                # If no tool use, we're done
                if stop_reason != "tool_use" or not tool_use_id:
                    break

                # Execute delegation
                try:
                    tool_input = json.loads(tool_use_json) if tool_use_json else {}
                except json.JSONDecodeError:
                    break

                target_id = tool_input.get("agent_id", "")
                question = tool_input.get("question", "")

                # Status indicator to the player
                yield f"\n*[Consulting {target_id}...]*\n"

                delegation_result = await execute_delegation(
                    target_id,
                    question,
                    get_provider_fn=get_provider_fn,
                    router=router or self._router,
                )

                # Build follow-up messages with tool_use + tool_result
                api_messages.append({
                    "role": "assistant",
                    "content": content_blocks,
                })
                api_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": delegation_result,
                    }],
                })

                # Reset for next round
                tool_use_id = None
                tool_use_name = None
                tool_use_json = ""
                content_blocks = []
