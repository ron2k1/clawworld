"""Tests for gateway.stream — JSON-RPC 2.0 encoding helpers."""

from gateway.stream import encode_delta, encode_end


class TestEncodeDelta:
    def test_returns_valid_jsonrpc_notification(self):
        result = encode_delta("Hello")
        assert result["jsonrpc"] == "2.0"
        assert "id" not in result  # notifications have no id

    def test_uses_chat_delta_method(self):
        result = encode_delta("Hello")
        assert result["method"] == "chat.delta"

    def test_includes_text_in_params(self):
        result = encode_delta("Hello")
        assert result["params"]["text"] == "Hello"

    def test_preserves_whitespace(self):
        result = encode_delta("  ")
        assert result["params"]["text"] == "  "

    def test_preserves_newlines(self):
        result = encode_delta("\n")
        assert result["params"]["text"] == "\n"

    def test_preserves_special_characters(self):
        result = encode_delta("héllo 世界")
        assert result["params"]["text"] == "héllo 世界"

    def test_empty_string(self):
        result = encode_delta("")
        assert result["params"]["text"] == ""


class TestEncodeEnd:
    def test_returns_valid_jsonrpc_notification(self):
        result = encode_end()
        assert result["jsonrpc"] == "2.0"
        assert "id" not in result

    def test_uses_chat_end_method(self):
        result = encode_end()
        assert result["method"] == "chat.end"

    def test_has_empty_params(self):
        result = encode_end()
        assert result["params"] == {}
