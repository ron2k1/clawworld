"""Stress tests for the ClawWorld gateway — validates enterprise-readiness."""

import asyncio
import json
import os
import tempfile
import time

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from gateway.session import Session, SessionManager, _safe_key


# ─── Session stress tests ───────────────────────────────────────────

class TestSessionKeySafety:
    """Verify session keys can't collide or break file paths."""

    def test_colon_in_player_name_no_collision(self):
        """Players 'a:b' talking to 'c' should NOT collide with 'a' talking to 'b:c'."""
        key1 = _safe_key("a:b", "c")
        key2 = _safe_key("a", "b:c")
        assert key1 != key2

    def test_special_chars_sanitized(self):
        key = _safe_key("../etc/passwd", "../../secret")
        assert ".." not in key
        assert "/" not in key
        assert "\\" not in key

    def test_empty_names(self):
        key = _safe_key("", "")
        assert isinstance(key, str)
        assert len(key) > 0

    def test_very_long_names_truncated(self):
        key = _safe_key("a" * 500, "b" * 500)
        # Keys should be bounded
        assert len(key) < 300

    def test_unicode_names(self):
        key = _safe_key("プレイヤー", "エージェント")
        assert isinstance(key, str)


class TestSessionConcurrency:
    """Verify sessions handle concurrent access safely."""

    @pytest.mark.asyncio
    async def test_concurrent_appends_no_data_loss(self):
        """Multiple concurrent appends should not lose messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = Session("concurrent_player", "agent1", base_dir=tmpdir)
            n = 50

            async def append_msg(i: int):
                await session.append_async("user", f"message_{i}")

            await asyncio.gather(*[append_msg(i) for i in range(n)])
            history = session.get_history()
            assert len(history) == n

    @pytest.mark.asyncio
    async def test_concurrent_different_sessions(self):
        """Different sessions should not interfere with each other."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = SessionManager(base_dir=tmpdir)
            n = 20

            async def chat(player: str, agent: str, msg: str):
                await mgr.append_async(player, agent, {"role": "user", "content": msg})

            tasks = []
            for i in range(n):
                tasks.append(chat(f"player_{i}", "npc1", f"hello from {i}"))
                tasks.append(chat(f"player_{i}", "npc2", f"hi from {i}"))

            await asyncio.gather(*tasks)

            # Each player-agent pair should have exactly 1 message
            for i in range(n):
                h1 = mgr.get_last_n(f"player_{i}", "npc1", 10)
                h2 = mgr.get_last_n(f"player_{i}", "npc2", 10)
                assert len(h1) == 1
                assert len(h2) == 1


class TestSessionEviction:
    """Verify session cache doesn't grow unbounded."""

    def test_eviction_triggers_at_max(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = SessionManager(base_dir=tmpdir)
            # Fill to max
            for i in range(501):
                mgr.append(f"p{i}", "a", {"role": "user", "content": "x"})
            # Should have evicted down to ~80% of 500 = 400
            assert len(mgr._sessions) <= 500


# ─── Sanitization stress tests ──────────────────────────────────────

class TestSanitization:
    """Verify input sanitization handles adversarial inputs."""

    def test_empty_message_after_sanitize(self):
        from gateway.server import sanitize_message
        assert sanitize_message("") == ""
        assert sanitize_message("   ") == ""
        assert sanitize_message("\x00\x01\x02") == ""

    def test_html_injection_escaped(self):
        from gateway.server import sanitize_message
        result = sanitize_message("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_very_long_message_truncated(self):
        from gateway.server import sanitize_message, MAX_MESSAGE_LENGTH
        result = sanitize_message("a" * 10000)
        assert len(result) <= MAX_MESSAGE_LENGTH

    def test_control_chars_stripped(self):
        from gateway.server import sanitize_message
        result = sanitize_message("hello\x00world\x7f!")
        assert "\x00" not in result
        assert "\x7f" not in result
        assert "hello" in result


# ─── Router stress tests ────────────────────────────────────────────

class TestRouterEdgeCases:
    """Verify agent routing handles edge cases."""

    def test_resolve_unknown_agent(self):
        from gateway.router import AgentRouter
        router = AgentRouter()
        assert router.resolve("nonexistent_agent_12345") is None

    def test_resolve_returns_model(self):
        from gateway.router import AgentRouter
        router = AgentRouter()
        result = router.resolve("jake")
        assert result is not None
        assert result["model"].startswith("ollama/")

    def test_new_agents_loaded(self):
        """Inspector and debugger should be in the agent list."""
        from gateway.router import AgentRouter
        router = AgentRouter()
        assert router.resolve("inspector") is not None
        assert router.resolve("debugger") is not None
        assert "openai/" in router.resolve("inspector")["model"]
        assert "openai/" in router.resolve("debugger")["model"]

    def test_all_agents_have_soul(self):
        """Every agent should have a SOUL.md or at least resolve."""
        from gateway.router import AgentRouter
        router = AgentRouter()
        for agent_id in router.list_agents():
            resolved = router.resolve(agent_id)
            assert resolved is not None, f"Agent {agent_id} failed to resolve"


# ─── Provider routing stress tests ──────────────────────────────────

class TestProviderRouting:
    """Verify provider selection logic."""

    def test_ollama_agents_get_ollama_provider(self):
        from gateway.server import get_provider, _mode
        if _mode != "live":
            pytest.skip("Live mode only")
        from gateway.ollama import OllamaProvider
        provider = get_provider("jake")
        assert isinstance(provider, OllamaProvider)

    def test_anthropic_agents_get_live_provider(self):
        from gateway.server import get_provider, _mode
        if _mode != "live":
            pytest.skip("Live mode only")
        from gateway.provider import LiveProvider
        provider = get_provider("analyst")
        assert isinstance(provider, LiveProvider)

    def test_unknown_agent_gets_fallback(self):
        from gateway.server import get_provider, _mode
        if _mode != "live":
            pytest.skip("Live mode only")
        provider = get_provider("nonexistent_99999")
        # Should fall back to LiveProvider, not crash
        assert provider is not None


# ─── Ollama provider stress tests ───────────────────────────────────

class TestOllamaThinkingFilter:
    """Verify thinking text is properly stripped."""

    def test_think_tags_stripped(self):
        from gateway.ollama import OllamaProvider
        from gateway.router import AgentRouter
        provider = OllamaProvider(AgentRouter())
        result = provider._strip_thinking("<think>I need to respond as Jake.</think>Hey there!")
        assert "I need to respond" not in result
        assert "Hey there!" in result

    def test_unclosed_think_stripped(self):
        from gateway.ollama import OllamaProvider
        from gateway.router import AgentRouter
        provider = OllamaProvider(AgentRouter())
        result = provider._strip_thinking("<think>This is my reasoning...\nStill thinking...")
        assert result == ""

    def test_meta_reasoning_stripped(self):
        from gateway.ollama import OllamaProvider
        from gateway.router import AgentRouter
        provider = OllamaProvider(AgentRouter())
        # Meta-reasoning paragraph followed by actual dialogue
        text = "The user is testing me. I need to stay in character.\n\nHey! Welcome to the village!"
        result = provider._strip_thinking(text)
        assert "The user is testing" not in result
        assert "Welcome to the village" in result

    def test_actual_dialogue_preserved(self):
        from gateway.ollama import OllamaProvider
        from gateway.router import AgentRouter
        provider = OllamaProvider(AgentRouter())
        text = "Hey there, traveler! The fields look great this season. Have you seen the new bridge?"
        result = provider._strip_thinking(text)
        assert result == text

    def test_empty_after_strip_returns_raw(self):
        """If everything is stripped, fallback to raw response."""
        from gateway.ollama import OllamaProvider
        from gateway.router import AgentRouter
        provider = OllamaProvider(AgentRouter())
        # All meta-reasoning — strip returns empty, caller should use raw
        text = "The user is testing me."
        result = provider._strip_thinking(text)
        # Empty result means the caller in generate_stream yields raw fallback
        assert result == ""

    def test_stray_close_think_stripped(self):
        from gateway.ollama import OllamaProvider
        from gateway.router import AgentRouter
        provider = OllamaProvider(AgentRouter())
        text = "Some leaked reasoning</think> Actual response here."
        result = provider._strip_thinking(text)
        assert "Actual response" in result
        assert "leaked reasoning" not in result



class TestJSONRPCProtocol:
    """Verify JSON-RPC 2.0 compliance."""

    def test_error_response_format(self):
        from gateway.server import jsonrpc_error
        err = jsonrpc_error(1, -32600, "Invalid request")
        assert err["jsonrpc"] == "2.0"
        assert err["id"] == 1
        assert err["error"]["code"] == -32600
        assert err["error"]["message"] == "Invalid request"

    def test_response_format(self):
        from gateway.server import jsonrpc_response
        resp = jsonrpc_response(2, {"status": "ok"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 2
        assert resp["result"]["status"] == "ok"

    def test_notification_format(self):
        from gateway.server import jsonrpc_notification
        notif = jsonrpc_notification("chat.delta", {"text": "hi"})
        assert notif["jsonrpc"] == "2.0"
        assert "id" not in notif
        assert notif["method"] == "chat.delta"


# ─── Integration: full message flow ─────────────────────────────────

class TestMessageFlow:
    """Test the full message processing pipeline."""

    def test_sanitize_then_session_roundtrip(self):
        """Message goes through sanitization, then session persistence, then retrieval."""
        from gateway.server import sanitize_message
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = SessionManager(base_dir=tmpdir)
            raw = "  <b>Hello!</b>  \x00 "
            clean = sanitize_message(raw)
            assert "\x00" not in clean
            assert "<b>" not in clean

            mgr.append("p1", "a1", {"role": "user", "content": clean})
            history = mgr.get_last_n("p1", "a1", 10)
            assert len(history) == 1
            assert history[0]["content"] == clean
            assert history[0]["role"] == "user"

    def test_rate_limit_interval_configurable(self):
        from gateway.server import _rate_limit_interval
        interval = _rate_limit_interval()
        assert isinstance(interval, float)
        assert interval >= 0
