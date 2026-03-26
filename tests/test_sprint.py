"""Tests for QuickUp! sprint command."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from quickup.cli.api_client import get_current_sprint_list
from quickup.cli.exceptions import ListNotFoundError


class TestGetCurrentSprintList:
    """Tests for get_current_sprint_list function."""

    def setup_method(self):
        self.patch_get_projects = patch("quickup.cli.api_client.get_projects_data", side_effect=lambda s: s.projects)
        self.patch_get_lists = patch("quickup.cli.api_client.get_lists_data", side_effect=lambda p: p.lists)
        self.patch_get_projects.start()
        self.patch_get_lists.start()

    def teardown_method(self):
        self.patch_get_projects.stop()
        self.patch_get_lists.stop()

    def test_finds_sprint_list(self):
        """Test finding a sprint list."""
        mock_space = Mock(id="space-123")

        sprint_list = Mock()
        sprint_list.name = "Sprint 5"
        sprint_list.id = "list-005"
        sprint_list.space_id = "space-123"

        other_list = Mock()
        other_list.name = "Backlog"
        other_list.id = "list-001"
        other_list.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [sprint_list, other_list]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_list

    def test_finds_iteration_list(self):
        """Test finding an iteration list."""
        mock_space = Mock(id="space-123")

        iteration_list = Mock()
        iteration_list.name = "Iteration 3"
        iteration_list.id = "list-003"
        iteration_list.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [iteration_list]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == iteration_list

    def test_returns_most_recent_sprint(self):
        """Test returning the most recent sprint by ID."""
        mock_space = Mock(id="space-123")

        sprint_old = Mock()
        sprint_old.name = "Sprint 1"
        sprint_old.id = "list-001"
        sprint_old.space_id = "space-123"

        sprint_new = Mock()
        sprint_new.name = "Sprint 2"
        sprint_new.id = "list-002"
        sprint_new.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [sprint_old, sprint_new]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_new

    def test_filters_by_space(self):
        """Test filtering lists by space."""
        mock_space = Mock(id="space-123")
        mock_other_space = Mock(id="space-456")

        sprint_correct = Mock()
        sprint_correct.name = "Sprint"
        sprint_correct.id = "list-001"
        sprint_correct.space_id = "space-123"

        sprint_other = Mock()
        sprint_other.name = "Sprint Other"
        sprint_other.id = "list-002"
        sprint_other.space_id = "space-456"

        mock_project1 = Mock()
        mock_project1.lists = [sprint_correct]
        mock_space.projects = [mock_project1]

        mock_project2 = Mock()
        mock_project2.lists = [sprint_other]
        mock_other_space.projects = [mock_project2]

        mock_team = Mock()
        mock_team.spaces = [mock_space, mock_other_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_correct

    def test_no_sprint_lists_raises_error(self):
        """Test raising error when no sprint lists found."""
        mock_space = Mock(id="space-123")

        backlog = Mock()
        backlog.name = "Backlog"
        backlog.id = "list-001"
        backlog.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [backlog]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        with pytest.raises(ListNotFoundError):
            get_current_sprint_list(mock_team, mock_space)

    def test_case_insensitive_search(self):
        """Test case-insensitive sprint search."""
        mock_space = Mock(id="space-123")

        sprint_list = Mock()
        sprint_list.name = "SPRINT 5"
        sprint_list.id = "list-005"
        sprint_list.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [sprint_list]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_list

    def test_returns_active_sprint_by_date_range(self):
        """Test returning the sprint whose date range includes today, regardless of ID."""
        mock_space = Mock(id="space-123")
        now = datetime.now(timezone.utc)

        sprint_past = Mock()
        sprint_past.name = "Sprint 1"
        sprint_past.id = "list-005"  # Higher ID, but date range is in the past
        sprint_past.start_date = str(int((now - timedelta(days=14)).timestamp() * 1000))
        sprint_past.due_date = str(int((now - timedelta(days=7)).timestamp() * 1000))
        sprint_past.space_id = "space-123"

        sprint_active = Mock()
        sprint_active.name = "Sprint 2"
        sprint_active.id = "list-002"  # Lower ID, but currently active
        sprint_active.start_date = str(int((now - timedelta(days=3)).timestamp() * 1000))
        sprint_active.due_date = str(int((now + timedelta(days=4)).timestamp() * 1000))
        sprint_active.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [sprint_past, sprint_active]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_active

    def test_falls_back_to_id_sort_when_no_dates(self):
        """Test fallback to ID sort when no start_date/due_date fields are present."""
        mock_space = Mock(id="space-123")

        sprint_old = Mock(spec=["name", "id", "space_id"])
        sprint_old.name = "Sprint 1"
        sprint_old.id = "list-001"
        sprint_old.space_id = "space-123"

        sprint_new = Mock(spec=["name", "id", "space_id"])
        sprint_new.name = "Sprint 2"
        sprint_new.id = "list-002"
        sprint_new.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [sprint_old, sprint_new]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_new  # Highest ID

    def test_falls_back_to_id_sort_when_no_current_sprint(self):
        """Test fallback to ID sort when no sprint's date range includes today."""
        mock_space = Mock(id="space-123")
        now = datetime.now(timezone.utc)

        sprint_past = Mock()
        sprint_past.name = "Sprint 1"
        sprint_past.id = "list-001"
        sprint_past.start_date = str(int((now - timedelta(days=14)).timestamp() * 1000))
        sprint_past.due_date = str(int((now - timedelta(days=7)).timestamp() * 1000))
        sprint_past.space_id = "space-123"

        sprint_future = Mock()
        sprint_future.name = "Sprint 2"
        sprint_future.id = "list-002"
        sprint_future.start_date = str(int((now + timedelta(days=1)).timestamp() * 1000))
        sprint_future.due_date = str(int((now + timedelta(days=7)).timestamp() * 1000))
        sprint_future.space_id = "space-123"

        mock_project = Mock()
        mock_project.lists = [sprint_past, sprint_future]

        mock_space.projects = [mock_project]
        mock_team = Mock()
        mock_team.spaces = [mock_space]

        result = get_current_sprint_list(mock_team, mock_space)
        assert result == sprint_future  # Highest ID since no current sprint
