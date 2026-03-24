"""Tests for LiveProvider — unit tests with mocked HTTP responses."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.provider import LiveProvider, _parse_model


# --- helpers ---

async def _collect(agen):
    items = []
    async for item in agen:
        items.append(item)
    return items


def _make_sse_lines(texts: list[str]) -> list[str]:
    """Build SSE lines that mimic Anthropic content_block_delta events."""
    lines = []
    for text in texts:
        event = {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": text},
        }
        lines.append(f"data: {json.dumps(event)}")
    lines.append("data: [DONE]")
    return lines


# --- _parse_model ---

class TestParseModel:
    def test_anthropic_model(self):
        provider, model = _parse_model("anthropic/claude-sonnet-4-6")
        assert provider == "anthropic"
        assert model == "claude-sonnet-4-6"

    def test_xai_model(self):
        provider, model = _parse_model("xai/grok-3")
        assert provider == "xai"
        assert model == "grok-3"

    def test_bare_model_defaults_to_anthropic(self):
        provider, model = _parse_model("claude-haiku-4-5-20251001")
        assert provider == "anthropic"
        assert model == "claude-haiku-4-5-20251001"


# --- LiveProvider ---

class TestLiveProviderStream:
    def _make_router(self, model="anthropic/claude-sonnet-4-6", soul="You are a test NPC."):
        router = MagicMock()
        router.resolve.return_value = {
            "agent": {"id": "test", "name": "Test"},
            "system_prompt": soul,
            "model": model,
        }
        return router

    def test_unknown_agent_yields_error(self):
        router = MagicMock()
        router.resolve.return_value = None
        provider = LiveProvider(router)
        chunks = asyncio.run(
            _collect(provider.generate_stream("unknown", []))
        )
        assert len(chunks) == 1
        assert "[error]" in chunks[0]

    def test_missing_api_key_yields_error(self):
        router = self._make_router()
        provider = LiveProvider(router)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False):
            chunks = asyncio.run(
                _collect(provider.generate_stream("test", []))
            )
        assert len(chunks) == 1
        assert "Missing" in chunks[0]

    def test_unknown_provider_yields_error(self):
        router = self._make_router(model="openai/gpt-4")
        provider = LiveProvider(router)
        with patch.dict("os.environ", {}, clear=False):
            chunks = asyncio.run(
                _collect(provider.generate_stream("test", []))
            )
        assert len(chunks) == 1
        assert "Unknown provider" in chunks[0]

    def test_streams_text_chunks(self):
        """Test that SSE content_block_delta events are parsed into text chunks."""
        router = self._make_router()
        provider = LiveProvider(router)

        sse_lines = _make_sse_lines(["Hello", " world", "!"])

        # Mock the httpx streaming response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(sse_lines))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"}):
            with patch("httpx.AsyncClient", return_value=mock_client):
                chunks = asyncio.run(
                    _collect(provider.generate_stream("test", [
                        {"role": "user", "content": "hi"}
                    ]))
                )

        assert chunks == ["Hello", " world", "!"]

    def test_per_session_locking(self):
        """Test that the same session_key reuses the same lock."""
        router = self._make_router()
        provider = LiveProvider(router)
        lock1 = provider._get_lock("player1:npc1")
        lock2 = provider._get_lock("player1:npc1")
        lock3 = provider._get_lock("player1:npc2")
        assert lock1 is lock2
        assert lock1 is not lock3

    def test_trims_messages_to_20(self):
        """Test that messages are trimmed to last 20."""
        router = self._make_router()
        provider = LiveProvider(router)

        messages = [{"role": "user", "content": f"msg{i}"} for i in range(30)]

        sse_lines = _make_sse_lines(["ok"])

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(sse_lines))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"}):
            with patch("httpx.AsyncClient", return_value=mock_client):
                asyncio.run(
                    _collect(provider.generate_stream("test", messages))
                )

        # Verify the API was called with trimmed messages
        call_args = mock_client.stream.call_args
        body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert len(body["messages"]) == 20
        assert body["messages"][0]["content"] == "msg10"


async def _async_iter(items):
    for item in items:
        yield item
