"""MockProvider — scripted responses with simulated streaming."""

import asyncio
import json
import random
from pathlib import Path
from typing import AsyncGenerator

from gateway.provider import BaseLLMProvider

_MOCK_DIR = Path(__file__).parent / "mock_responses"


class MockProvider(BaseLLMProvider):
    """Loads scripted responses from JSON files and streams them char-by-char."""

    def __init__(self, delay: float = 0.03):
        self._delay = delay
        self._responses: dict[str, list[str]] = {}

    def _load(self, agent_id: str) -> list[str]:
        """Load and cache responses for *agent_id*."""
        if agent_id not in self._responses:
            path = _MOCK_DIR / f"{agent_id}.json"
            if path.exists():
                self._responses[agent_id] = json.loads(path.read_text())
            else:
                self._responses[agent_id] = [
                    f"[{agent_id}] I don't have scripted responses yet."
                ]
        return self._responses[agent_id]

    async def generate_stream(
        self, agent_id: str, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Yield one character at a time with a 30 ms delay."""
        responses = self._load(agent_id)
        text = random.choice(responses)
        for char in text:
            yield char
            await asyncio.sleep(self._delay)
