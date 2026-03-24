"""Tests for gateway.router — agent routing and SOUL.md loading."""

import json
import os
import tempfile

from gateway.router import AgentRouter


def _make_agents_json(tmpdir, agents_list):
    """Helper to create a temporary agents.json."""
    path = os.path.join(tmpdir, "agents.json")
    with open(path, "w") as f:
        json.dump({"agents": {"list": agents_list}}, f)
    return path


def _make_soul(tmpdir, agent_id, content):
    """Helper to create a SOUL.md in a temp workspace."""
    agent_dir = os.path.join(tmpdir, "workspaces", agent_id)
    os.makedirs(agent_dir, exist_ok=True)
    soul_path = os.path.join(agent_dir, "SOUL.md")
    with open(soul_path, "w") as f:
        f.write(content)
    return soul_path


class TestAgentRouting:
    def test_loads_agent_by_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = _make_agents_json(tmpdir, [
                {"id": "assistant", "name": "Personal Assistant", "model": {"primary": "xai/grok-3"}},
            ])
            router = AgentRouter(agents_path=agents_path, workspaces_dir=os.path.join(tmpdir, "workspaces"))
            agent = router.get_agent("assistant")
            assert agent is not None
            assert agent["name"] == "Personal Assistant"

    def test_missing_agent_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = _make_agents_json(tmpdir, [
                {"id": "assistant", "name": "Personal Assistant", "model": {"primary": "xai/grok-3"}},
            ])
            router = AgentRouter(agents_path=agents_path, workspaces_dir=os.path.join(tmpdir, "workspaces"))
            assert router.get_agent("nonexistent") is None

    def test_list_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = _make_agents_json(tmpdir, [
                {"id": "assistant", "name": "Personal Assistant", "model": {}},
                {"id": "analyst", "name": "Analyst", "model": {}},
            ])
            router = AgentRouter(agents_path=agents_path, workspaces_dir=os.path.join(tmpdir, "workspaces"))
            ids = router.list_agents()
            assert "assistant" in ids
            assert "analyst" in ids
            assert len(ids) == 2


class TestSoulLoading:
    def test_loads_correct_soul(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = _make_agents_json(tmpdir, [
                {"id": "assistant", "name": "Personal Assistant", "model": {}},
            ])
            _make_soul(tmpdir, "assistant", "# Personal Assistant\n\nYou are the Personal Assistant.")
            router = AgentRouter(agents_path=agents_path, workspaces_dir=os.path.join(tmpdir, "workspaces"))
            soul = router.get_soul("assistant")
            assert soul is not None
            assert "Personal Assistant" in soul

    def test_missing_soul_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = _make_agents_json(tmpdir, [
                {"id": "ghost", "name": "Ghost", "model": {}},
            ])
            router = AgentRouter(agents_path=agents_path, workspaces_dir=os.path.join(tmpdir, "workspaces"))
            assert router.get_soul("ghost") is None

    def test_loads_real_agents_json(self):
        """Integration test with the actual agents.json and workspaces."""
        router = AgentRouter()
        agent = router.get_agent("assistant")
        assert agent is not None
        soul = router.get_soul("assistant")
        assert soul is not None
        assert "Personal Assistant" in soul
