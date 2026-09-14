"""Tests for QuickUp! exceptions."""

import pytest

from quickup.cli.exceptions import (
    APIError,
    ClickupyError,
    ListNotFoundError,
    NetworkError,
    OAuthConfigError,
    ProjectNotFoundError,
    SpaceNotFoundError,
    TeamAmbiguousError,
    TeamNotFoundError,
    TokenError,
    handle_exception,
)


class TestClickupyError:
    """Tests for base ClickupyError."""

    def test_default_message(self):
        """Test default message."""
        exc = ClickupyError("Test error")
        assert str(exc) == "Test error"
        assert exc.exit_code == 1

    def test_message_with_hint(self):
        """Test message with hint."""
        exc = ClickupyError("Test error", "Fix this")
        assert "Test error" in str(exc)
        assert "Hint: Fix this" in str(exc)


class TestTokenError:
    """Tests for TokenError."""

    def test_message(self):
        """Test exception message."""
        exc = TokenError()
        assert "Invalid or missing ClickUp API token" in exc.message
        assert exc.exit_code == 1


class TestTeamNotFoundError:
    """Tests for TeamNotFoundError."""

    def test_no_team_id(self):
        """Test with no team ID."""
        exc = TeamNotFoundError()
        assert "No teams found" in exc.message
        assert exc.exit_code == 2

    def test_with_team_id(self):
        """Test with specific team ID."""
        exc = TeamNotFoundError(team_id="abc123")
        assert "Team 'abc123' not found" in exc.message
        assert exc.exit_code == 2


class TestTeamAmbiguousError:
    """Tests for TeamAmbiguousError."""

    def test_message(self):
        """Test exception message."""
        exc = TeamAmbiguousError(["Team A", "Team B"])
        assert "Multiple teams found: Team A, Team B" in exc.message
        assert exc.exit_code == 2


class TestSpaceNotFoundError:
    """Tests for SpaceNotFoundError."""

    def test_no_space_id(self):
        """Test with no space ID."""
        exc = SpaceNotFoundError()
        assert "No spaces found" in exc.message
        assert exc.exit_code == 2

    def test_with_space_id(self):
        """Test with specific space ID."""
        exc = SpaceNotFoundError(space_id="xyz789")
        assert "Space 'xyz789' not found" in exc.message


class TestProjectNotFoundError:
    """Tests for ProjectNotFoundError."""

    def test_no_project_id(self):
        """Test with no project ID."""
        exc = ProjectNotFoundError()
        assert "No projects found" in exc.message
        assert exc.exit_code == 2

    def test_with_project_id(self):
        """Test with specific project ID."""
        exc = ProjectNotFoundError(project_id="proj-abc")
        assert "Project 'proj-abc' not found" in exc.message
        assert exc.exit_code == 2


class TestListNotFoundError:
    """Tests for ListNotFoundError."""

    def test_no_list_id(self):
        """Test with no list ID."""
        exc = ListNotFoundError()
        assert "No lists found" in exc.message
        assert exc.exit_code == 3

    def test_with_list_id(self):
        """Test with specific list ID."""
        exc = ListNotFoundError(list_id="list-000")
        assert "List 'list-000' not found" in exc.message


class TestOAuthConfigError:
    """Tests for OAuthConfigError."""

    def test_single_missing_credential(self):
        """Test message when only one credential is missing."""
        exc = OAuthConfigError(["QUICKUP_CLIENT_SECRET"])
        assert exc.message == "Missing OAuth app credential: QUICKUP_CLIENT_SECRET."
        assert "QUICKUP_CLIENT_ID" not in exc.message
        assert exc.exit_code == 6

    def test_multiple_missing_credentials(self):
        """Test message when both credentials are missing."""
        exc = OAuthConfigError(["QUICKUP_CLIENT_ID", "QUICKUP_CLIENT_SECRET"])
        assert exc.message == "Missing OAuth app credentials: QUICKUP_CLIENT_ID, QUICKUP_CLIENT_SECRET."

    def test_hint_explains_setup(self):
        """Test the hint tells the user how to configure the OAuth app."""
        exc = OAuthConfigError(["QUICKUP_CLIENT_ID"])
        assert "app.clickup.com/settings/apps" in str(exc)
        assert "http://localhost:4242" in str(exc)
        assert "QUICKUP_CLIENT_SECRET" in str(exc)


class TestNetworkError:
    """Tests for NetworkError."""

    def test_default_message(self):
        """Test default message."""
        exc = NetworkError()
        assert "Network error occurred" in exc.message
        assert exc.exit_code == 4


class TestAPIError:
    """Tests for APIError."""

    def test_default(self):
        """Test default API error."""
        exc = APIError()
        assert exc.exit_code == 5

    def test_401(self):
        """Test 401 status code."""
        exc = APIError(status_code=401)
        assert exc.hint
        assert "Authentication failed" in exc.hint

    def test_403(self):
        """Test 403 status code."""
        exc = APIError(status_code=403)
        assert exc.hint
        assert "Access denied" in exc.hint

    def test_429(self):
        """Test 429 status code."""
        exc = APIError(status_code=429)
        assert exc.hint
        assert "Rate limit" in exc.hint

    def test_404(self):
        """Test 404 status code."""
        exc = APIError(status_code=404)
        assert exc.hint
        assert "Resource not found" in exc.hint

    def test_500(self):
        """Test 500 status code."""
        exc = APIError(status_code=500)
        assert exc.hint
        assert "ClickUp server error" in exc.hint

    def test_503(self):
        """Test 503 status code."""
        exc = APIError(status_code=503)
        assert exc.hint
        assert "ClickUp server error" in exc.hint


class TestHandleException:
    """Tests for handle_exception function."""

    def test_exit_code(self):
        """Test that correct exit code is used."""
        exc = ListNotFoundError()

        with pytest.raises(SystemExit) as exc_info:
            handle_exception(exc)

        assert exc_info.value.code == 3

    def test_prints_hint_to_stderr(self, capsys):
        """Test that hint is printed to stderr."""
        exc = TokenError()

        with pytest.raises(SystemExit):
            handle_exception(exc)

        captured = capsys.readouterr()
        assert "Hint:" in captured.err

    def test_no_hint_does_not_print(self, capsys):
        """Test that hint is not printed when exception has no hint."""
        exc = ClickupyError("Error without hint")

        with pytest.raises(SystemExit):
            handle_exception(exc)

        captured = capsys.readouterr()
        assert "Hint:" not in captured.err
        assert "Error: Error without hint" in captured.err
