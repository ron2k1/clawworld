"""ClawWorld Gateway — configuration loader."""

import json
import os
from pathlib import Path
from typing import Any

# Project root is one level up from gateway/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

AGENTS_JSON_PATH = PROJECT_ROOT / "agents.json"


def get_mode() -> str:
    """Return 'mock' or 'live' based on CLAWWORLD_MODE env var."""
    return os.environ.get("CLAWWORLD_MODE", "mock")


def load_agents() -> list[dict[str, Any]]:
    """Load the agent list from agents.json."""
    with open(AGENTS_JSON_PATH, "r") as f:
        data = json.load(f)
    return data["agents"]["list"]


def get_agent_by_id(agent_id: str) -> dict[str, Any] | None:
    """Look up a single agent config by ID."""
    for agent in load_agents():
        if agent["id"] == agent_id:
            return agent
    return None
