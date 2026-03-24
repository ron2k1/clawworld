"""JSON-RPC 2.0 streaming helpers for chat deltas."""


def encode_delta(text_chunk: str) -> dict:
    """Return a JSON-RPC 2.0 notification for a streaming text chunk."""
    return {
        "jsonrpc": "2.0",
        "method": "chat.delta",
        "params": {"text": text_chunk},
    }


def encode_end() -> dict:
    """Return a JSON-RPC 2.0 notification signalling stream end."""
    return {
        "jsonrpc": "2.0",
        "method": "chat.end",
        "params": {},
    }
