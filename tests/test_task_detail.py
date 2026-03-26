"""Tests for QuickUp! task detail command."""

from unittest.mock import Mock, patch

from quickup.cli.renderer import render_task_detail


class TestRenderTaskDetail:
    """Tests for render_task_detail function."""

    @patch("builtins.print")
    def test_render_task_detail_basic_info(self, mock_print):
        """Test render_task_detail shows basic task info."""
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.name = "Test Task"
        mock_task.status.status = "In Progress"
        mock_task.status.color = "#FF0000"
        mock_task.url = "https://app.clickup.com/123"
        mock_task.assignees = [Mock(username="john")]
        mock_task.priority = {"priority": "high", "color": "#FF8800"}
        mock_task.due_date = "2024-01-15T10:00:00.000Z"
        mock_task.description = None
        mock_task.subtasks = None

        render_task_detail(mock_task)

        # Verify print was called multiple times
        assert mock_print.called

    @patch("builtins.print")
    def test_render_task_detail_unassigned(self, mock_print):
        """Test render_task_detail shows Unassigned for no assignees."""
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.name = "Test Task"
        mock_task.status.status = "To Do"
        mock_task.status.color = "#123456"
        mock_task.url = "https://app.clickup.com/123"
        mock_task.assignees = []
        mock_task.priority = None
        mock_task.due_date = None
        mock_task.description = None
        mock_task.subtasks = None

        render_task_detail(mock_task)

        # Check that Unassigned was printed
        printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("Unassigned" in arg for arg in printed_args)

    @patch("builtins.print")
    def test_render_task_detail_with_description(self, mock_print):
        """Test render_task_detail shows description."""
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.name = "Test Task"
        mock_task.status.status = "To Do"
        mock_task.status.color = "#123456"
        mock_task.url = "https://app.clickup.com/123"
        mock_task.assignees = []
        mock_task.priority = None
        mock_task.due_date = None
        mock_task.description = "This is a test description"
        mock_task.subtasks = None

        render_task_detail(mock_task)

        printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("This is a test description" in arg for arg in printed_args)

    @patch("builtins.print")
    def test_render_task_detail_with_subtasks(self, mock_print):
        """Test render_task_detail shows subtasks."""
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.name = "Test Task"
        mock_task.status.status = "To Do"
        mock_task.status.color = "#123456"
        mock_task.url = "https://app.clickup.com/123"
        mock_task.assignees = []
        mock_task.priority = None
        mock_task.due_date = None
        mock_task.description = None
        mock_task.subtasks = [
            {
                "id": "sub-1",
                "name": "Subtask 1",
                "status": {"status": "to do", "color": "#aabbcc", "orderindex": 0},
                "assignees": [],
                "priority": None,
            },
            {
                "id": "sub-2",
                "name": "Subtask 2",
                "status": {"status": "to do", "color": "#aabbcc", "orderindex": 0},
                "assignees": [],
                "priority": None,
            },
        ]

        render_task_detail(mock_task)

        printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
        assert any("Subtask 1" in arg for arg in printed_args)
        assert any("Subtask 2" in arg for arg in printed_args)
