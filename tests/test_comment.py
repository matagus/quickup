"""Tests for QuickUp! comment command."""

from io import StringIO
from unittest.mock import Mock, patch

import pytest

from quickup.cli.exceptions import ClickupyError, TokenError
from quickup.cli.main import comment_task
from quickup.cli.renderer import render_comment_posted


class TestRenderCommentPosted:
    """Tests for render_comment_posted function."""

    @patch("builtins.print")
    def test_render_comment_posted_basic(self, mock_print):
        """Test render_comment_posted shows confirmation."""
        render_comment_posted("task-123", "This is a comment")
        assert mock_print.called

    @patch("builtins.print")
    def test_render_comment_posted_shows_task_id(self, mock_print):
        """Test render_comment_posted includes the task ID."""
        render_comment_posted("task-456", "Hello")
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("task-456" in arg for arg in printed)

    @patch("builtins.print")
    def test_render_comment_posted_shows_comment_text(self, mock_print):
        """Test render_comment_posted includes the comment text."""
        render_comment_posted("task-789", "My comment text")
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("My comment text" in arg for arg in printed)

    @patch("builtins.print")
    def test_render_comment_posted_shows_success_message(self, mock_print):
        """Test render_comment_posted shows success indicator."""
        render_comment_posted("task-123", "text")
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("successfully" in arg.lower() for arg in printed)

    @patch("builtins.print")
    def test_render_comment_posted_truncates_long_text(self, mock_print):
        """Test render_comment_posted truncates comments longer than 80 chars."""
        long_text = "x" * 100
        render_comment_posted("task-123", long_text)
        printed = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        # Should show truncated text with "..."
        assert any("..." in arg for arg in printed)
        # Should NOT show the full 100-char string
        assert not any(long_text in arg for arg in printed)


class TestCommentTask:
    """Tests for comment_task CLI command."""

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.render_comment_posted")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comment_task_posts_and_renders(self, mock_environ, mock_clickup_class, mock_render, mock_requests):
        """Test that comment_task calls post and renders confirmation."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup_class.return_value = mock_clickup
        mock_requests.post.return_value = Mock(ok=True)

        comment_task(task_id="task-abc", text="Hello world")

        mock_requests.post.assert_called_once_with(
            "https://api.clickup.com/api/v2/task/task-abc/comment",
            headers=mock_clickup.headers,
            json={"comment_text": "Hello world", "notify_all": False},
        )
        mock_render.assert_called_once_with("task-abc", "Hello world")

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.render_comment_posted")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comment_task_with_notify_all(self, mock_environ, mock_clickup_class, mock_render, mock_requests):
        """Test that --notify-all passes notify_all=True to the API."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup_class.return_value = mock_clickup
        mock_requests.post.return_value = Mock(ok=True)

        comment_task(task_id="task-abc", text="Ping everyone", notify_all=True)

        mock_requests.post.assert_called_once_with(
            "https://api.clickup.com/api/v2/task/task-abc/comment",
            headers=mock_clickup.headers,
            json={"comment_text": "Ping everyone", "notify_all": True},
        )

    @patch("quickup.cli.main.init_environ")
    def test_comment_task_raises_token_error_when_missing(self, mock_environ):
        """Test TokenError is raised when TOKEN is not set."""
        mock_environ.return_value = {}

        with pytest.raises(TokenError):
            comment_task(task_id="task-abc", text="test")

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comment_task_raises_on_api_error(self, mock_environ, mock_clickup_class, mock_requests):
        """Test ClickupyError is raised when API returns an error response."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup_class.return_value = mock_clickup
        mock_response = Mock(ok=False, status_code=404)
        mock_response.json.return_value = {"err": "Task not found"}
        mock_response.text = '{"err": "Task not found"}'
        mock_requests.post.return_value = mock_response

        with pytest.raises(ClickupyError, match="Failed to post comment"):
            comment_task(task_id="bad-task", text="test")

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comment_task_raises_on_non_json_error(self, mock_environ, mock_clickup_class, mock_requests):
        """Test ClickupyError is raised when API returns a non-JSON error response."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup_class.return_value = mock_clickup
        mock_response = Mock(ok=False, status_code=500)
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "Internal Server Error"
        mock_requests.post.return_value = mock_response

        with pytest.raises(ClickupyError, match="Failed to post comment"):
            comment_task(task_id="task-abc", text="test")

    @patch("quickup.cli.main.requests")
    @patch("quickup.cli.main.render_comment_posted")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_comment_task_reads_from_stdin(self, mock_environ, mock_clickup_class, mock_render, mock_requests):
        """Test that comment_task reads from stdin when --text is omitted."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup.headers = {"Authorization": "Bearer test-token"}
        mock_clickup_class.return_value = mock_clickup
        mock_requests.post.return_value = Mock(ok=True)

        with patch("quickup.cli.main.sys") as mock_sys:
            mock_sys.stdin = StringIO("piped comment text")
            mock_sys.stdin.isatty = lambda: False
            comment_task(task_id="task-abc")

        mock_requests.post.assert_called_once_with(
            "https://api.clickup.com/api/v2/task/task-abc/comment",
            headers=mock_clickup.headers,
            json={"comment_text": "piped comment text", "notify_all": False},
        )

    def test_comment_task_raises_when_no_text_and_tty(self):
        """Test ClickupyError when no --text and stdin is a TTY."""
        with pytest.raises(ClickupyError, match="No comment text provided"), patch("quickup.cli.main.sys") as mock_sys:
            mock_sys.stdin.isatty.return_value = True
            comment_task(task_id="task-abc")
