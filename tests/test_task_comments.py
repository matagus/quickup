"""Tests for --comments flag on the task command."""

from unittest.mock import Mock, patch

import pytest

from quickup.cli.exceptions import ClickupyError
from quickup.cli.main import show_task
from quickup.cli.renderer import render_task_comments

SAMPLE_COMMENTS = [
    {
        "comment_text": "First comment",
        "user": {"username": "alice"},
        "date": "1700000000000",
    },
    {
        "comment_text": "Second comment",
        "user": {"username": "bob"},
        "date": "1700000060000",
    },
]


class TestRenderTaskComments:
    """Tests for render_task_comments function."""

    @patch("builtins.print")
    def test_renders_comments(self, mock_print):
        render_task_comments(SAMPLE_COMMENTS)
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("alice" in arg for arg in printed)
        assert any("First comment" in arg for arg in printed)
        assert any("bob" in arg for arg in printed)
        assert any("Second comment" in arg for arg in printed)

    @patch("builtins.print")
    def test_shows_comment_count(self, mock_print):
        render_task_comments(SAMPLE_COMMENTS)
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("2" in arg for arg in printed)

    @patch("builtins.print")
    def test_no_comments_message(self, mock_print):
        render_task_comments([])
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("No comments" in arg for arg in printed)

    @patch("builtins.print")
    def test_handles_missing_user(self, mock_print):
        render_task_comments([{"comment_text": "Anon comment", "date": "1700000000000"}])
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("Anon comment" in arg for arg in printed)
        assert any("Unknown" in arg for arg in printed)


class TestShowTaskComments:
    """Tests for --comments flag on show_task command."""

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.render_task_comments")
    @patch("quickup.cli.main.render_task_detail")
    @patch("quickup.cli.main.get_task_data")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comments_flag_fetches_and_renders(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_task_data,
        mock_render_detail,
        mock_render_comments,
        mock_requests,
    ):
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup.teams = [Mock(id="team-1")]
        mock_clickup_class.return_value = mock_clickup
        mock_get_team.return_value = None
        mock_get_task_data.return_value = Mock()
        mock_requests.get.return_value = Mock(ok=True, json=lambda: {"comments": SAMPLE_COMMENTS})

        show_task(task_id="task-abc", comments=True)

        mock_requests.get.assert_called_once_with(
            "https://api.clickup.com/api/v2/task/task-abc/comment",
            headers=mock_clickup.headers,
        )
        mock_render_comments.assert_called_once_with(SAMPLE_COMMENTS)

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.render_task_comments")
    @patch("quickup.cli.main.render_task_detail")
    @patch("quickup.cli.main.get_task_data")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comments_flag_empty_list(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_task_data,
        mock_render_detail,
        mock_render_comments,
        mock_requests,
    ):
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup.teams = [Mock(id="team-1")]
        mock_clickup_class.return_value = mock_clickup
        mock_get_team.return_value = None
        mock_get_task_data.return_value = Mock()
        mock_requests.get.return_value = Mock(ok=True, json=lambda: {"comments": []})

        show_task(task_id="task-abc", comments=True)

        mock_render_comments.assert_called_once_with([])

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.render_task_detail")
    @patch("quickup.cli.main.get_task_data")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comments_flag_api_error_raises(
        self, mock_environ, mock_clickup_class, mock_get_team, mock_get_task_data, mock_render_detail, mock_requests
    ):
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup.teams = [Mock(id="team-1")]
        mock_clickup_class.return_value = mock_clickup
        mock_get_team.return_value = None
        mock_get_task_data.return_value = Mock()
        mock_response = Mock(ok=False, status_code=403)
        mock_response.json.return_value = {"err": "Forbidden"}
        mock_response.text = '{"err": "Forbidden"}'
        mock_requests.get.return_value = mock_response

        with pytest.raises(ClickupyError, match="Failed to fetch comments"):
            show_task(task_id="task-abc", comments=True)

    @patch("quickup.cli.main.render_task_comments")
    @patch("quickup.cli.main.render_task_detail")
    @patch("quickup.cli.main.get_task_data")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_without_comments_flag_skips_fetch(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_task_data,
        mock_render_detail,
        mock_render_comments,
    ):
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.teams = [Mock(id="team-1")]
        mock_clickup_class.return_value = mock_clickup
        mock_get_team.return_value = None
        mock_get_task_data.return_value = Mock()

        show_task(task_id="task-abc")

        mock_render_comments.assert_not_called()
