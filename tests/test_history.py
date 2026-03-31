"""Tests for QuickUp! command history module."""

import json
import sys
from unittest.mock import patch

import pytest

from quickup.cli.history import MAX_ENTRIES, get_recent, record
from quickup.cli.main import run_app


@pytest.fixture
def history_file(tmp_path):
    """Use a temporary history file."""
    hfile = tmp_path / "history.json"
    with patch("quickup.cli.history.HISTORY_FILE", hfile):
        yield hfile


class TestRecord:
    """Tests for recording command history."""

    def test_record_creates_file(self, history_file):
        record(["quickup", "sprint"])

        data = json.loads(history_file.read_text())
        assert len(data) == 1
        assert data[0]["command"] == "quickup sprint"
        assert "timestamp" in data[0]

    def test_record_normalizes_argv(self, history_file):
        record(["/usr/local/bin/python", "sprint", "--team", "123"])

        data = json.loads(history_file.read_text())
        assert data[0]["command"] == "quickup sprint --team 123"

    def test_record_appends(self, history_file):
        record(["quickup", "sprint"])
        record(["quickup", "--team", "123"])

        data = json.loads(history_file.read_text())
        assert len(data) == 2

    def test_record_caps_at_max(self, history_file):
        for i in range(MAX_ENTRIES + 10):
            record(["quickup", f"cmd-{i}"])

        data = json.loads(history_file.read_text())
        assert len(data) == MAX_ENTRIES
        assert data[-1]["command"] == f"quickup cmd-{MAX_ENTRIES + 9}"


class TestGetRecent:
    """Tests for retrieving recent commands."""

    def test_empty_history(self, history_file):
        assert get_recent() == []

    def test_returns_newest_first(self, history_file):
        record(["quickup", "first"])
        record(["quickup", "second"])

        recent = get_recent(10)
        assert recent[0]["command"] == "quickup second"
        assert recent[1]["command"] == "quickup first"

    def test_respects_limit(self, history_file):
        for i in range(5):
            record(["quickup", f"cmd-{i}"])

        assert len(get_recent(3)) == 3

    def test_corrupted_file(self, history_file):
        history_file.write_text("not json")
        assert get_recent() == []


class TestPickAndRunRecent:
    """Tests for the no-args behavior in run_app."""

    @patch("quickup.cli.main.get_recent", return_value=[])
    def test_no_history(self, mock_recent, capsys, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["quickup"])
        run_app()

        output = capsys.readouterr().out
        assert "No command history" in output

    @patch("quickup.cli.main.inquirer")
    @patch("quickup.cli.main.get_recent")
    def test_prompts_with_recent_commands(self, mock_recent, mock_inquirer, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["quickup"])
        mock_recent.return_value = [
            {"command": "quickup sprint", "timestamp": "2026-03-28T14:32:00+00:00"},
        ]
        mock_inquirer.prompt.return_value = None  # user cancelled

        run_app()

        mock_inquirer.prompt.assert_called_once()
        # Check List was built with the command as a choice value
        list_kwargs = mock_inquirer.List.call_args
        choices = list_kwargs[1]["choices"] if list_kwargs[1] else list_kwargs[0][2]
        assert any("quickup sprint" in val for _, val in choices)

    @patch("quickup.cli.main.app")
    @patch("quickup.cli.main.inquirer")
    @patch("quickup.cli.main.get_recent")
    def test_runs_selected_command(self, mock_recent, mock_inquirer, mock_app, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["quickup"])
        mock_recent.return_value = [
            {"command": "quickup sprint", "timestamp": "2026-03-28T14:32:00+00:00"},
        ]
        mock_inquirer.prompt.return_value = {"cmd": "quickup sprint"}

        run_app()

        assert sys.argv == ["quickup", "sprint"]
        mock_app.assert_called_once()
