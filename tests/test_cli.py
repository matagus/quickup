"""Tests for QuickUp! CLI module."""

import sys
from unittest.mock import Mock, patch

import pytest

from quickup.cli.api_client import get_list_for, get_project_for
from quickup.cli.exceptions import ClickupyError, TokenError
from quickup.cli.main import app, comment_task, list_tasks, run_app, show_task, sprint, update_task


class TestApp:
    """Tests for the CLI app."""

    def test_app_creation(self):
        """Test that app is created with correct name."""
        assert "quickup" in app.name
        assert "console-based client for ClickUp" in app.help

    def test_app_help(self, capsys, monkeypatch):
        """Test that --help works."""
        monkeypatch.setattr(sys, "exit", lambda x: None)
        app(["--help"])
        captured = capsys.readouterr()
        assert "Team ID" in captured.out
        assert "Space ID" in captured.out
        assert "Project ID" in captured.out
        assert "List ID" in captured.out


class TestRunApp:
    """Tests for run_app function."""

    @patch("quickup.cli.main.app")
    def test_successful_execution(self, mock_app):
        """Test successful execution mocks app()."""
        run_app()

        mock_app.assert_called_once()

    @patch("quickup.cli.main.handle_exception")
    @patch("quickup.cli.main.app")
    def test_exception_handling(self, mock_app, mock_handle_exception):
        """Test exception handling mocks ClickupyError and handle_exception."""
        mock_app.side_effect = ClickupyError("Test error")

        run_app()

        mock_handle_exception.assert_called_once()


class TestSprintCommand:
    """Tests for the sprint command."""

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_current_sprint_list")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_with_all_params(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_sprint_list,
        mock_render_list,
    ):
        """Test with all parameters provided."""
        mock_environ.return_value = {"TOKEN": "test-token"}

        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_sprint_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_sprint_list.return_value = mock_sprint_list

        sprint(team="team-123", space="space-456", project="project-789")

        mock_environ.assert_called_once()
        mock_get_sprint_list.assert_called_once_with(mock_team, mock_space)
        mock_render_list.assert_called_once()

    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_token_missing_raises(self, mock_environ, mock_clickup_class):
        """Test token missing scenario raises TokenError."""
        mock_environ.return_value = {}  # No TOKEN

        with pytest.raises(TokenError):
            sprint(team="team-123")


class TestTokenMissingScenarios:
    """Tests for token missing scenarios."""

    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_raises_token_error(self, mock_environ):
        """Test list_tasks raises TokenError when TOKEN not set."""
        mock_environ.return_value = {}  # No TOKEN

        with pytest.raises(TokenError):
            list_tasks()

    @patch("quickup.cli.main.init_environ")
    def test_show_task_raises_token_error(self, mock_environ):
        """Test show_task raises TokenError when TOKEN not set."""
        mock_environ.return_value = {}  # No TOKEN

        with pytest.raises(TokenError):
            show_task(task_id="task-123")

    @patch("quickup.cli.main.init_environ")
    def test_update_task_raises_token_error(self, mock_environ):
        """Test update_task raises TokenError when TOKEN not set."""
        mock_environ.return_value = {}  # No TOKEN

        with pytest.raises(TokenError):
            update_task(task_id="task-123", status="Done")

    @patch("quickup.cli.main.init_environ")
    def test_comment_task_raises_token_error(self, mock_environ):
        """Test comment_task raises TokenError when TOKEN not set."""
        mock_environ.return_value = {}  # No TOKEN

        with pytest.raises(TokenError):
            comment_task(task_id="task-123", text="hello")


class TestListTasks:
    """Tests for the list_tasks command."""

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_list_for")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_with_all_params(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_list_for,
        mock_render_list,
        capsys,
    ):
        """Test list_tasks with all parameters provided."""
        mock_environ.return_value = {"TOKEN": "test-token"}

        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_list_for.return_value = mock_list

        list_tasks(team="team-123", space="space-456", project="project-789", list_id="list-000")

        mock_environ.assert_called_once()
        mock_clickup_class.assert_called_once_with("test-token")
        mock_get_team.assert_called()
        mock_get_space_for.assert_called()
        mock_get_project_for.assert_called()
        mock_get_list_for.assert_called()
        mock_render_list.assert_called_once_with(
            mock_list,
            mock_team,
            no_cache=False,
            assignee=None,
            priority=None,
            due_before=None,
            group_by="status",
            include_closed=False,
            team="team-123",
            space="space-456",
            project="project-789",
            list_id="list-000",
        )

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_list_for")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_with_team_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_list_for,
        mock_render_list,
    ):
        """Test list_tasks with only team parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_list_for.return_value = mock_list

        list_tasks(team="team-123")

        mock_render_list.assert_called_once()
        call_args = mock_render_list.call_args
        assert call_args[1]["team"] == "team-123"

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_list_for")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_with_space_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_list_for,
        mock_render_list,
    ):
        """Test list_tasks with only space parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_list_for.return_value = mock_list

        list_tasks(space="space-456")

        call_args = mock_render_list.call_args
        assert call_args[1]["space"] == "space-456"

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_list_for")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_with_project_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_list_for,
        mock_render_list,
    ):
        """Test list_tasks with only project parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_list_for.return_value = mock_list

        list_tasks(project="project-789")

        call_args = mock_render_list.call_args
        assert call_args[1]["project"] == "project-789"

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_list_for")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_with_closed_flag(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_list_for,
        mock_render_list,
    ):
        """Test list_tasks passes include_closed=True when --closed is set."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_list_for.return_value = mock_list

        list_tasks(team="team-123", closed=True)

        call_args = mock_render_list.call_args
        assert call_args[1]["include_closed"] is True

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_list_for")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_list_tasks_with_list_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_list_for,
        mock_render_list,
    ):
        """Test list_tasks with only list_id parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_list_for.return_value = mock_list

        list_tasks(list_id="list-000")

        call_args = mock_render_list.call_args
        assert call_args[1]["list_id"] == "list-000"


class TestUpdateTask:
    """Tests for the update_task command."""

    @patch("quickup.cli.main.render_task_update")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_update_task_with_team_id(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_render_task_update,
        capsys,
    ):
        """Test update_task with explicit team ID."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup_class.return_value = mock_clickup

        mock_team = Mock(id="team-123")
        mock_get_team.return_value = mock_team

        mock_task = Mock()
        mock_task.id = "task-86b8z0dn3"
        mock_task.status.status = "To Do"

        mock_clickup._get_all_tasks.return_value = [mock_task]

        update_task(task_id="task-86b8z0dn3", status="In Progress", team="team-123")

        mock_get_team.assert_called()
        mock_render_task_update.assert_called_once_with("task-86b8z0dn3", "To Do", "In Progress")

    @patch("quickup.cli.main.render_task_update")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_update_task_without_team_uses_first_team(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_render_task_update,
        capsys,
    ):
        """Test update_task without team ID uses first team."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup_class.return_value = mock_clickup

        mock_team = Mock(id="team-456")
        mock_clickup.teams = [mock_team]
        mock_get_team.return_value = None

        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.status.status = "To Do"

        mock_clickup._get_all_tasks.return_value = [mock_task]

        update_task(task_id="task-123", status="Done")

        mock_render_task_update.assert_called_once_with("task-123", "To Do", "Done")

    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    @patch("quickup.cli.api_client.get_teams_data")
    def test_update_task_not_found(
        self,
        mock_get_teams_data,
        mock_environ,
        mock_clickup_class,
        capsys,
    ):
        """Test update_task raises error when task not found."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup_class.return_value = mock_clickup

        mock_team = Mock(id="team-123")
        mock_clickup.teams = [mock_team]
        mock_get_teams_data.return_value = [mock_team]
        mock_clickup._get_all_tasks.return_value = []

        with pytest.raises(ClickupyError, match="Task .* not found"):
            update_task(task_id="nonexistent", status="Done")


class TestShowTask:
    """Tests for the show_task command."""

    @patch("quickup.cli.main.render_task_detail")
    @patch("quickup.cli.main.get_task_data")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_show_task_with_team_id(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_task_data,
        mock_render_task_detail,
        capsys,
    ):
        """Test show_task with explicit team ID."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup_class.return_value = Mock()

        mock_team = Mock(id="team-123")
        mock_get_team.return_value = mock_team

        mock_task = Mock(id="task-86b8z0dn3")
        mock_get_task_data.return_value = mock_task

        show_task(task_id="task-86b8z0dn3", team="team-123")

        mock_get_team.assert_called()
        mock_render_task_detail.assert_called_once_with(mock_task)

    @patch("quickup.cli.main.render_task_detail")
    @patch("quickup.cli.main.get_task_data")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_show_task_without_team_uses_first_team(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_task_data,
        mock_render_task_detail,
        capsys,
    ):
        """Test show_task without team ID uses first team."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup_class.return_value = mock_clickup

        mock_team = Mock(id="team-456")
        mock_clickup.teams = [mock_team]
        mock_get_team.return_value = None

        mock_task = Mock(id="task-123")
        mock_get_task_data.return_value = mock_task

        show_task(task_id="task-123")

        mock_render_task_detail.assert_called_once_with(mock_task)

    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    @patch("quickup.cli.api_client.get_teams_data")
    def test_show_task_not_found(
        self,
        mock_get_teams_data,
        mock_environ,
        mock_clickup_class,
        capsys,
    ):
        """Test show_task raises error when task not found."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_clickup = Mock()
        mock_clickup_class.return_value = mock_clickup

        mock_team = Mock(id="team-123")
        mock_clickup.teams = [mock_team]
        mock_get_teams_data.return_value = [mock_team]
        mock_clickup._get_all_tasks.return_value = []

        with pytest.raises(ClickupyError, match="Task .* not found"):
            show_task(task_id="nonexistent")


class TestSprint:
    """Tests for the sprint command."""

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_current_sprint_list")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_with_all_params(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_sprint_list,
        mock_render_list,
        capsys,
    ):
        """Test sprint with all parameters provided."""
        mock_environ.return_value = {"TOKEN": "test-token"}

        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_sprint_list = Mock(id="sprint-100")

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_sprint_list.return_value = mock_sprint_list

        sprint(team="team-123", space="space-456", project="project-789")

        mock_environ.assert_called_once()
        mock_clickup_class.assert_called_once_with("test-token")
        mock_get_team.assert_called()
        mock_get_space_for.assert_called()
        mock_get_project_for.assert_called()
        mock_get_sprint_list.assert_called_once_with(mock_team, mock_space)
        mock_render_list.assert_called_once()

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_current_sprint_list")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_sprint_with_team_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_sprint_list,
        mock_render_list,
    ):
        """Test sprint with only team parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_sprint_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_sprint_list.return_value = mock_sprint_list

        sprint(team="team-123")

        call_args = mock_render_list.call_args
        assert call_args[1]["team"] == "team-123"

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_current_sprint_list")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_sprint_with_space_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_sprint_list,
        mock_render_list,
    ):
        """Test sprint with only space parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_sprint_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_sprint_list.return_value = mock_sprint_list

        sprint(space="space-456")

        call_args = mock_render_list.call_args
        assert call_args[1]["space"] == "space-456"

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_current_sprint_list")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_sprint_with_project_only(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_sprint_list,
        mock_render_list,
    ):
        """Test sprint with only project parameter."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_sprint_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_sprint_list.return_value = mock_sprint_list

        sprint(project="project-789")

        call_args = mock_render_list.call_args
        assert call_args[1]["project"] == "project-789"

    @patch("quickup.cli.main.render_list")
    @patch("quickup.cli.main.get_current_sprint_list")
    @patch("quickup.cli.main.get_project_for")
    @patch("quickup.cli.main.get_space_for")
    @patch("quickup.cli.main.get_team")
    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_sprint_with_closed_flag(
        self,
        mock_environ,
        mock_clickup_class,
        mock_get_team,
        mock_get_space_for,
        mock_get_project_for,
        mock_get_sprint_list,
        mock_render_list,
    ):
        """Test sprint passes include_closed=True when --closed is set."""
        mock_environ.return_value = {"TOKEN": "test-token"}
        mock_team = Mock()
        mock_space = Mock()
        mock_project = Mock()
        mock_sprint_list = Mock()

        mock_get_team.return_value = mock_team
        mock_get_space_for.return_value = mock_space
        mock_get_project_for.return_value = mock_project
        mock_get_sprint_list.return_value = mock_sprint_list

        sprint(team="team-123", closed=True)

        call_args = mock_render_list.call_args
        assert call_args[1]["include_closed"] is True

    @patch("quickup.cli.main.ClickUp")
    @patch("quickup.cli.main.init_environ")
    def test_token_missing_raises_error(self, mock_environ, mock_clickup_class):
        """Test token missing scenario raises TokenError."""
        mock_environ.return_value = {"TOKEN": None}

        with pytest.raises(TokenError):
            sprint(team="team-123")


class TestGetProjectFor:
    """Tests for get_project_for hidden-folder filtering."""

    def _make_project(self, pid, name, hidden=False):
        p = Mock()
        p.id = pid
        p.name = name
        p.hidden = hidden
        return p

    @patch("quickup.cli.api_client.get_projects_data")
    def test_hidden_project_excluded_from_interactive_choices(self, mock_get_projects, monkeypatch):
        """Hidden projects must not appear in the inquirer choices."""
        monkeypatch.setattr("sys.argv", ["quickup"])  # no --project arg

        visible = self._make_project("p1", "My Project")
        hidden = self._make_project("p2", "hidden", hidden=True)
        mock_get_projects.return_value = [visible, hidden]

        captured_choices = []

        def fake_prompt(questions):
            captured_choices.extend(questions[0].choices)
            return {"project": f"{visible.name} [{visible.id}]"}

        with patch("quickup.cli.api_client.inquirer.prompt", side_effect=fake_prompt):
            result = get_project_for(Mock(), [], interactive=True)

        assert result is visible
        assert not any("hidden" in c for c in captured_choices)

    @patch("quickup.cli.api_client.get_projects_data")
    def test_single_non_hidden_project_returned_without_prompt(self, mock_get_projects, monkeypatch):
        """When only one non-hidden project exists, return it without prompting."""
        monkeypatch.setattr("sys.argv", ["quickup"])

        visible = self._make_project("p1", "My Project")
        hidden = self._make_project("p2", "hidden", hidden=True)
        mock_get_projects.return_value = [visible, hidden]

        with patch("quickup.cli.api_client.inquirer.prompt") as mock_prompt:
            result = get_project_for(Mock(), [], interactive=True)

        assert result is visible
        mock_prompt.assert_not_called()

    @patch("quickup.cli.api_client.get_projects_data")
    def test_all_projects_hidden_falls_back_to_showing_all(self, mock_get_projects, monkeypatch):
        """When every project is hidden, fall back to returning the first one."""
        monkeypatch.setattr("sys.argv", ["quickup"])

        h1 = self._make_project("p1", "hidden", hidden=True)
        mock_get_projects.return_value = [h1]

        result = get_project_for(Mock(), [], interactive=False)

        assert result is h1


class TestGetListFor:
    """Tests for get_list_for hidden-folder list merging."""

    def _make_list(self, lid, name):
        li = Mock()
        li.id = lid
        li.name = name
        return li

    def _make_project(self, pid, hidden=False, lists=None):
        p = Mock()
        p.id = pid
        p.hidden = hidden
        p.lists = lists or []
        return p

    @patch("quickup.cli.api_client.get_projects_data")
    @patch("quickup.cli.api_client.get_lists_data")
    def test_hidden_sibling_lists_merged_in_interactive(self, mock_get_lists, mock_get_projects, monkeypatch):
        """Lists from hidden sibling projects appear in the interactive choices."""
        monkeypatch.setattr("sys.argv", ["quickup"])  # no --list arg

        list_a = self._make_list("l1", "Sprint 1")
        list_b = self._make_list("l2", "Backlog")  # lives in the hidden folder

        selected_project = self._make_project("p1")
        hidden_project = self._make_project("p2", hidden=True)

        mock_space = Mock()
        selected_project.space = mock_space
        mock_get_projects.return_value = [selected_project, hidden_project]
        mock_get_lists.side_effect = lambda p: [list_a] if p is selected_project else [list_b]

        captured_choices = []

        def fake_prompt(questions):
            captured_choices.extend(questions[0].choices)
            return {"list": f"{list_a.name} [{list_a.id}]"}

        with patch("quickup.cli.api_client.inquirer.prompt", side_effect=fake_prompt):
            result = get_list_for(selected_project, [], interactive=True)

        assert result is list_a
        assert any(list_b.name in c for c in captured_choices), "hidden folder lists not merged"

    @patch("quickup.cli.api_client.get_projects_data")
    @patch("quickup.cli.api_client.get_lists_data")
    def test_list_id_from_hidden_project_resolved_via_cli_arg(self, mock_get_lists, mock_get_projects, monkeypatch):
        """A --list ID belonging to a hidden sibling project is resolved correctly."""
        hidden_list = self._make_list("l99", "Folderless List")
        selected_project = self._make_project("p1")
        hidden_project = self._make_project("p2", hidden=True)

        monkeypatch.setattr("sys.argv", ["quickup", "--list", "l99"])

        mock_space = Mock()
        selected_project.space = mock_space
        mock_get_projects.return_value = [selected_project, hidden_project]
        mock_get_lists.side_effect = lambda p: [] if p is selected_project else [hidden_list]

        result = get_list_for(selected_project, ["--list", "l99"])

        assert result is hidden_list

    @patch("quickup.cli.api_client.get_lists_data")
    def test_no_space_attribute_does_not_crash(self, mock_get_lists, monkeypatch):
        """If the project has no .space, list fetch completes without merging."""
        monkeypatch.setattr("sys.argv", ["quickup"])

        only_list = self._make_list("l1", "Only List")
        project_no_space = self._make_project("p1")
        del project_no_space.space  # simulate missing attribute

        mock_get_lists.return_value = [only_list]

        result = get_list_for(project_no_space, [], interactive=False)

        assert result is only_list
