"""Tests for gateway.session — conversation persistence."""

import json
import os
import tempfile

from gateway.session import Session


class TestSessionCreate:
    def test_new_session_has_empty_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("player1", "assistant", base_dir=tmpdir)
            assert s.get_history() == []

    def test_new_session_sets_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("player1", "assistant", base_dir=tmpdir)
            assert s.player_id == "player1"
            assert s.agent_id == "assistant"


class TestSessionAppend:
    def test_append_single_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("player1", "assistant", base_dir=tmpdir)
            s.append("user", "Hello!")
            history = s.get_history()
            assert len(history) == 1
            assert history[0] == {"role": "user", "content": "Hello!"}

    def test_append_multiple_messages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("player1", "assistant", base_dir=tmpdir)
            s.append("user", "Hi")
            s.append("assistant", "Hello there!")
            s.append("user", "How are you?")
            assert len(s.get_history()) == 3

    def test_history_returns_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("player1", "assistant", base_dir=tmpdir)
            s.append("user", "Hi")
            h = s.get_history()
            h.clear()
            assert len(s.get_history()) == 1


class TestSessionPersistence:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s1 = Session("player1", "assistant", base_dir=tmpdir)
            s1.append("user", "Hello")
            s1.append("assistant", "Hi back")

            # Load same session from disk
            s2 = Session("player1", "assistant", base_dir=tmpdir)
            assert s2.get_history() == [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi back"},
            ]

    def test_file_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("player1", "assistant", base_dir=tmpdir)
            s.append("user", "Test")
            filepath = os.path.join(tmpdir, "player1__assistant.json")
            assert os.path.isfile(filepath)
            with open(filepath, "r") as f:
                data = json.load(f)
            assert "messages" in data

    def test_load_nonexistent_session_is_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Session("ghost", "nobody", base_dir=tmpdir)
            assert s.get_history() == []
