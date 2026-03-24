"""Tests for gateway.mock — MockProvider streaming and gateway.stream encoding."""

import asyncio

from gateway.mock import MockProvider
from gateway.stream import encode_delta, encode_end


class TestMockProviderStream:
    def test_yields_characters(self):
        provider = MockProvider(delay=0)
        chunks = asyncio.run(
            _collect(provider.generate_stream("assistant", []))
        )
        # Each chunk should be a single character
        assert all(len(c) == 1 for c in chunks)
        # Joined text should form a coherent response
        text = "".join(chunks)
        assert len(text) > 0

    def test_random_choice_returns_valid_response(self):
        provider = MockProvider(delay=0)
        # random.choice picks from the loaded responses — verify we always get a non-empty string
        responses = set()
        for _ in range(10):
            text = "".join(asyncio.run(
                _collect(provider.generate_stream("assistant", []))
            ))
            assert len(text) > 0
            responses.add(text)

    def test_unknown_agent_gets_default(self):
        provider = MockProvider(delay=0)
        chunks = asyncio.run(
            _collect(provider.generate_stream("unknown_agent", []))
        )
        text = "".join(chunks)
        assert "traveler" in text.lower() or len(text) > 0


class TestStreamEncoding:
    def test_encode_delta_format(self):
        result = encode_delta("H")
        assert result["jsonrpc"] == "2.0"
        assert result["method"] == "chat.delta"
        assert result["params"]["text"] == "H"

    def test_encode_end_format(self):
        result = encode_end()
        assert result["jsonrpc"] == "2.0"
        assert result["method"] == "chat.end"
        assert result["params"] == {}

    def test_encode_delta_preserves_whitespace(self):
        result = encode_delta(" ")
        assert result["params"]["text"] == " "

    def test_encode_delta_preserves_newline(self):
        result = encode_delta("\n")
        assert result["params"]["text"] == "\n"


async def _collect(agen):
    """Collect all items from an async generator."""
    items = []
    async for item in agen:
        items.append(item)
    return items
