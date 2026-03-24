"""Agent routing — maps agentId to SOUL.md persona and model config."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

AGENTS_JSON = os.path.join(os.path.dirname(__file__), "..", "agents.json")
WORKSPACES_DIR = os.path.join(os.path.dirname(__file__), "..", "workspaces")


class AgentRouter:
    """Routes agent IDs to their configuration and SOUL.md persona."""

    def __init__(
        self,
        agents_path: Optional[str] = None,
        workspaces_dir: Optional[str] = None,
    ):
        self._agents_path = agents_path or AGENTS_JSON
        self._workspaces_dir = workspaces_dir or WORKSPACES_DIR
        self._agents: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        with open(self._agents_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for agent in data.get("agents", {}).get("list", []):
            self._agents[agent["id"]] = agent

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        return self._agents.get(agent_id)

    def get_soul(self, agent_id: str) -> str | None:
        soul_path = os.path.join(self._workspaces_dir, agent_id, "SOUL.md")
        if os.path.isfile(soul_path):
            with open(soul_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def resolve(self, agent_id: str) -> dict[str, Any] | None:
        """Resolve an agent ID to its config + system_prompt (SOUL.md)."""
        agent = self.get_agent(agent_id)
        if agent is None:
            return None
        soul = self.get_soul(agent_id) or ""
        return {
            "agent": agent,
            "system_prompt": soul,
            "model": agent.get("model", {}).get("primary", ""),
        }

    def list_agents(self) -> list:
        return list(self._agents.keys())
