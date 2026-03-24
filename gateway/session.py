"""Per-player-per-NPC conversation session persistence."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
MAX_SESSIONS = 500  # max cached sessions before eviction
SESSION_TTL = 3600  # seconds before idle session is evicted from cache

# Sanitize player names for safe file paths
_UNSAFE_CHARS = re.compile(r"[^a-zA-Z0-9_\-]")


def _safe_key(player_id: str, agent_id: str) -> str:
    """Build a collision-safe session key by sanitizing inputs."""
    safe_player = _UNSAFE_CHARS.sub("_", player_id)[:100]
    safe_agent = _UNSAFE_CHARS.sub("_", agent_id)[:100]
    return f"{safe_player}__{safe_agent}"


class Session:
    """Manages conversation history for a player-NPC pair."""

    def __init__(self, player_id: str, agent_id: str, base_dir: str | None = None):
        self.player_id = player_id
        self.agent_id = agent_id
        self._base_dir = base_dir or SESSIONS_DIR
        self._messages: list[dict[str, str]] = []
        self._lock = asyncio.Lock()
        self.last_access = time.monotonic()
        self._load()

    @property
    def _filepath(self) -> str:
        key = _safe_key(self.player_id, self.agent_id)
        return os.path.join(self._base_dir, f"{key}.json")

    def _load(self) -> None:
        try:
            if os.path.isfile(self._filepath):
                with open(self._filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._messages = data.get("messages", [])
        except (json.JSONDecodeError, OSError):
            self._messages = []

    def save(self) -> None:
        try:
            os.makedirs(self._base_dir, exist_ok=True)
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump({"messages": self._messages}, f, indent=2)
        except OSError:
            pass  # fail silently on disk errors — session is still in memory

    async def append_async(self, role: str, content: str) -> None:
        """Thread-safe append with async lock."""
        async with self._lock:
            self._messages.append({"role": role, "content": content})
            self.last_access = time.monotonic()
            self.save()

    def append(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        self.last_access = time.monotonic()
        self.save()

    def get_history(self) -> list[dict[str, str]]:
        self.last_access = time.monotonic()
        return list(self._messages)


class SessionManager:
    """Manages multiple Session instances keyed by (player_id, agent_id)."""

    def __init__(self, base_dir: str | None = None):
        self._base_dir = base_dir or SESSIONS_DIR
        self._sessions: dict[str, Session] = {}

    def _get_session(self, player_id: str, agent_id: str) -> Session:
        key = _safe_key(player_id, agent_id)
        if key not in self._sessions:
            # Evict oldest sessions if cache is full
            if len(self._sessions) >= MAX_SESSIONS:
                self._evict_oldest()
            self._sessions[key] = Session(player_id, agent_id, self._base_dir)
        return self._sessions[key]

    def _evict_oldest(self) -> None:
        """Remove the least recently accessed sessions down to 80% capacity."""
        target = int(MAX_SESSIONS * 0.8)
        sorted_keys = sorted(
            self._sessions.keys(),
            key=lambda k: self._sessions[k].last_access,
        )
        while len(self._sessions) > target and sorted_keys:
            del self._sessions[sorted_keys.pop(0)]

    def append(self, player_id: str, agent_id: str, message: dict) -> None:
        session = self._get_session(player_id, agent_id)
        session.append(message["role"], message["content"])

    async def append_async(self, player_id: str, agent_id: str, message: dict) -> None:
        session = self._get_session(player_id, agent_id)
        await session.append_async(message["role"], message["content"])

    def get_last_n(self, player_id: str, agent_id: str, n: int = 20) -> list[dict[str, str]]:
        session = self._get_session(player_id, agent_id)
        history = session.get_history()
        return history[-n:] if len(history) > n else history
