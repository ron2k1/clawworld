"""ClawWorld Gateway — FastAPI WebSocket server with JSON-RPC 2.0."""

import asyncio
import html
import json
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from gateway.config import get_mode, load_agents
from gateway.mock import MockProvider
from gateway.ollama import OllamaProvider
from gateway.provider import LiveProvider
from gateway.router import AgentRouter
from gateway.session import SessionManager
from gateway.subprocess_provider import SubprocessProvider

# --- Rate limiting ---
def _rate_limit_interval() -> float:
    return float(os.environ.get("CLAWWORLD_RATE_LIMIT", "1.0"))
MAX_MESSAGE_LENGTH = 2000  # max characters per chat message

# Strip control characters (keep newlines/tabs)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_message(text: str) -> str:
    """Sanitize user input: strip control chars, limit length, escape HTML."""
    text = _CONTROL_CHAR_RE.sub("", text)
    text = text[:MAX_MESSAGE_LENGTH]
    text = html.escape(text)
    return text.strip()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    mode = get_mode()
    print(f"Starting ClawWorld Gateway on port 18790 (mode={mode})")
    yield


app = FastAPI(title="ClawWorld Gateway", lifespan=lifespan)
router = AgentRouter()
sessions = SessionManager()

# Providers — in live mode, route per-agent based on model prefix
_mode = get_mode()
_mock_provider = MockProvider()
_live_provider = LiveProvider(router) if _mode == "live" else None
_ollama_provider = OllamaProvider(router) if _mode == "live" else None
_openclaw_provider = None  
_subprocess_provider = SubprocessProvider(router) if _mode == "live" else None


def get_provider(agent_id: str):
    """Pick the right provider for this agent based on mode and model prefix."""
    if _mode != "live":
        return _mock_provider
    # Check if agent has a subprocess runner — always use SubprocessProvider for those
    agent_cfg = router.get_agent(agent_id)
    if agent_cfg and agent_cfg.get("runner", {}).get("type") == "subprocess":
        return _subprocess_provider
    resolved = router.resolve(agent_id)
    if resolved:
        model = resolved.get("model", "")
        if model.startswith("ollama/"):
            return _ollama_provider
        if model.startswith("anthropic/"):
            # Route Anthropic agents directly through LiveProvider (API call)
            # pollution (all agents respond as the main/assistant persona).
            return _live_provider
    return _live_provider


@app.get("/health")
async def health():
    return {"status": "ok", "mode": get_mode()}


def jsonrpc_response(id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def jsonrpc_error(id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}


def jsonrpc_notification(method: str, params: dict) -> dict:
    return {"jsonrpc": "2.0", "method": method, "params": params}


@app.websocket("/gateway-ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    player_name: str | None = None
    last_request_time = 0.0

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json(jsonrpc_error(None, -32700, "Parse error"))
                continue

            if not isinstance(msg, dict):
                await ws.send_json(jsonrpc_error(None, -32600, "Invalid request"))
                continue

            method = msg.get("method")
            params = msg.get("params", {})
            msg_id = msg.get("id")

            if not isinstance(params, dict):
                await ws.send_json(jsonrpc_error(msg_id, -32602, "Invalid params"))
                continue

            # --- hello handshake ---
            if method == "hello":
                player_name = params.get("playerName", "anonymous")
                agent_list = [
                    {"id": a["id"], "name": a["name"]}
                    for a in load_agents()
                ]
                await ws.send_json(jsonrpc_response(msg_id, {
                    "status": "connected",
                    "playerName": player_name,
                    "agentList": agent_list,
                }))

            # --- chat.send ---
            elif method == "chat.send":
                # Rate limiting: 1 request/sec per client for chat
                now = time.monotonic()
                if now - last_request_time < _rate_limit_interval():
                    await ws.send_json(jsonrpc_error(
                        msg_id, -32000, "Rate limited — wait before sending again"
                    ))
                    continue
                last_request_time = now

                if player_name is None:
                    await ws.send_json(jsonrpc_error(
                        msg_id, -32600, "Must send 'hello' before 'chat.send'"
                    ))
                    continue

                agent_id = params.get("agentId")
                raw_message = params.get("message", "")
                if not isinstance(raw_message, str):
                    await ws.send_json(jsonrpc_error(
                        msg_id, -32602, "Message must be a string"
                    ))
                    continue
                message = sanitize_message(raw_message)
                if not message:
                    await ws.send_json(jsonrpc_error(
                        msg_id, -32602, "Message is empty"
                    ))
                    continue

                if not agent_id:
                    await ws.send_json(jsonrpc_error(
                        msg_id, -32602, "Missing agentId"
                    ))
                    continue

                resolved = router.resolve(agent_id)
                if resolved is None:
                    await ws.send_json(jsonrpc_error(
                        msg_id, -32602, f"Unknown agent: {agent_id}"
                    ))
                    continue

                # Persist user message
                await sessions.append_async(player_name, agent_id, {
                    "role": "user",
                    "content": message,
                })

                # Acknowledge the request
                stream_id = str(uuid.uuid4())[:8]
                await ws.send_json(jsonrpc_response(msg_id, {
                    "status": "streaming",
                    "streamId": stream_id,
                }))

                # Get conversation history for context
                history = sessions.get_last_n(player_name, agent_id, 20)

                # Stream response chunks via provider
                full_response = ""
                provider = get_provider(agent_id)
                kwargs = {}
                if isinstance(provider, LiveProvider):
                    kwargs["session_key"] = f"{player_name}:{agent_id}"
                    kwargs["get_provider_fn"] = get_provider
                    kwargs["router"] = router
                try:
                    async for chunk in provider.generate_stream(
                        agent_id, history, **kwargs
                    ):
                        full_response += chunk
                        await ws.send_json(jsonrpc_notification("chat.delta", {
                            "streamId": stream_id,
                            "agentId": agent_id,
                            "delta": chunk,
                        }))
                except Exception as exc:
                    await ws.send_json(jsonrpc_notification("chat.error", {
                        "streamId": stream_id,
                        "agentId": agent_id,
                        "error": str(exc)[:200],
                    }))

                # End of stream
                await ws.send_json(jsonrpc_notification("chat.end", {
                    "streamId": stream_id,
                    "agentId": agent_id,
                    "fullText": full_response,
                }))

                # Persist assistant response
                if full_response:
                    await sessions.append_async(player_name, agent_id, {
                        "role": "assistant",
                        "content": full_response,
                    })

            else:
                await ws.send_json(jsonrpc_error(
                    msg_id, -32601, f"Unknown method: {method}"
                ))

    except WebSocketDisconnect:
        if player_name:
            print(f"Player '{player_name}' disconnected")


def main():
    import uvicorn
    port = int(os.environ.get("CLAWWORLD_PORT", "18790"))
    print(f"Starting ClawWorld Gateway on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
