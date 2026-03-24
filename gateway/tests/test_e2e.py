"""End-to-end tests — WebSocket connection lifecycle and chat flow."""

import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from gateway.server import app


class TestHealthEndpoint:
    def test_returns_ok(self):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "mode" in data


class TestWebSocketHello:
    def test_hello_handshake(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_json({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "hello",
                "params": {"playerName": "testplayer"},
            })
            resp = ws.receive_json()
            assert resp["jsonrpc"] == "2.0"
            assert resp["id"] == 1
            assert resp["result"]["status"] == "connected"
            assert resp["result"]["playerName"] == "testplayer"
            assert isinstance(resp["result"]["agentList"], list)

    def test_hello_defaults_to_anonymous(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_json({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "hello",
                "params": {},
            })
            resp = ws.receive_json()
            assert resp["result"]["playerName"] == "anonymous"

    def test_invalid_json_returns_parse_error(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_text("not json{{{")
            resp = ws.receive_json()
            assert resp["error"]["code"] == -32700
            assert "Parse error" in resp["error"]["message"]

    def test_unknown_method_returns_error(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_json({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "nonexistent",
                "params": {},
            })
            resp = ws.receive_json()
            assert resp["error"]["code"] == -32601
            assert "Unknown method" in resp["error"]["message"]


class TestWebSocketChat:
    def test_chat_before_hello_returns_error(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_json({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "chat.send",
                "params": {"agentId": "assistant", "message": "hi"},
            })
            resp = ws.receive_json()
            assert resp["error"]["code"] == -32600
            assert "hello" in resp["error"]["message"].lower()

    def test_chat_missing_agent_id(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            # Handshake first
            ws.send_json({
                "jsonrpc": "2.0", "id": 1,
                "method": "hello",
                "params": {"playerName": "p1"},
            })
            ws.receive_json()
            # Chat without agentId
            ws.send_json({
                "jsonrpc": "2.0", "id": 2,
                "method": "chat.send",
                "params": {"message": "hi"},
            })
            resp = ws.receive_json()
            assert resp["error"]["code"] == -32602
            assert "agentId" in resp["error"]["message"]

    def test_chat_unknown_agent(self):
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_json({
                "jsonrpc": "2.0", "id": 1,
                "method": "hello",
                "params": {"playerName": "p1"},
            })
            ws.receive_json()
            ws.send_json({
                "jsonrpc": "2.0", "id": 2,
                "method": "chat.send",
                "params": {"agentId": "nonexistent_agent", "message": "hi"},
            })
            resp = ws.receive_json()
            assert resp["error"]["code"] == -32602
            assert "Unknown agent" in resp["error"]["message"]

    def test_full_chat_flow(self):
        """Test hello -> chat.send -> streaming deltas -> end notification."""
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            # 1. Hello
            ws.send_json({
                "jsonrpc": "2.0", "id": 1,
                "method": "hello",
                "params": {"playerName": "e2e_player"},
            })
            hello_resp = ws.receive_json()
            assert hello_resp["result"]["status"] == "connected"

            # 2. Chat with a known mock agent (assistant)
            ws.send_json({
                "jsonrpc": "2.0", "id": 2,
                "method": "chat.send",
                "params": {"agentId": "assistant", "message": "Hello!"},
            })

            # 3. Should get streaming ack first
            ack = ws.receive_json()
            assert ack["result"]["status"] == "streaming"
            stream_id = ack["result"]["streamId"]
            assert len(stream_id) > 0

            # 4. Collect delta notifications
            deltas = []
            while True:
                msg = ws.receive_json()
                if msg.get("method") == "chat.delta":
                    deltas.append(msg["params"]["delta"])
                    assert msg["params"]["streamId"] == stream_id
                    assert msg["params"]["agentId"] == "assistant"
                elif msg.get("method") == "chat.end":
                    assert msg["params"]["streamId"] == stream_id
                    full_text = msg["params"]["fullText"]
                    break

            # 5. Verify deltas reconstruct the full text
            assert len(deltas) > 0
            assert "".join(deltas) == full_text

    def test_multiple_messages_accumulate(self):
        """Test that sending multiple messages works in sequence."""
        client = TestClient(app)
        with client.websocket_connect("/gateway-ws") as ws:
            ws.send_json({
                "jsonrpc": "2.0", "id": 1,
                "method": "hello",
                "params": {"playerName": "multi_player"},
            })
            ws.receive_json()

            # Send two messages in sequence
            for msg_id in [2, 3]:
                ws.send_json({
                    "jsonrpc": "2.0", "id": msg_id,
                    "method": "chat.send",
                    "params": {"agentId": "assistant", "message": f"Message {msg_id}"},
                })
                # Consume ack
                ack = ws.receive_json()
                assert ack["result"]["status"] == "streaming"
                # Consume all deltas + end
                while True:
                    msg = ws.receive_json()
                    if msg.get("method") == "chat.end":
                        break
