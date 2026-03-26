"""Custom exceptions for QuickUp! CLI with exit codes."""

import sys


class ClickupyError(Exception):
    """Base exception for QuickUp! CLI."""

    exit_code = 1

    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\nHint: {self.hint}"
        return self.message


class TokenError(ClickupyError):
    """Raised when API token is invalid or missing."""

    exit_code = 1

    def __init__(self):
        super().__init__(
            "Invalid or missing ClickUp API token.",
            "Run 'quickup login' to authenticate via browser, "
            "or set TOKEN in your .env file with a personal API token.",
        )


class TeamNotFoundError(ClickupyError):
    """Raised when team ID is invalid or no teams exist."""

    exit_code = 2

    def __init__(self, team_id: str | None = None):
        if team_id:
            super().__init__(
                f"Team '{team_id}' not found.",
                "Check that the team ID is correct and you have access to this team.",
            )
        else:
            super().__init__(
                "No teams found in your ClickUp account.",
                "Create at least one team in ClickUp or check your API token permissions.",
            )


class TeamAmbiguousError(ClickupyError):
    """Raised when multiple teams exist but no team ID is specified."""

    exit_code = 2

    def __init__(self, team_names: list[str]):
        super().__init__(
            f"Multiple teams found: {', '.join(team_names)}.",
            "Specify a team using --team <team_id> or use interactive mode.",
        )


class SpaceNotFoundError(ClickupyError):
    """Raised when space is not found."""

    exit_code = 2

    def __init__(self, space_id: str | None = None):
        if space_id:
            super().__init__(
                f"Space '{space_id}' not found.",
                "Check that the space ID is correct and belongs to the selected team.",
            )
        else:
            super().__init__(
                "No spaces found for this team.",
                "Create at least one space in this team or check permissions.",
            )


class ProjectNotFoundError(ClickupyError):
    """Raised when project is not found."""

    exit_code = 2

    def __init__(self, project_id: str | None = None):
        if project_id:
            super().__init__(
                f"Project '{project_id}' not found.",
                "Check that the project ID is correct and belongs to the selected space.",
            )
        else:
            super().__init__(
                "No projects found for this space.",
                "Create at least one project in this space or check permissions.",
            )


class ListNotFoundError(ClickupyError):
    """Raised when list is not found."""

    exit_code = 3

    def __init__(self, list_id: str | None = None, hint: str | None = None):
        if list_id:
            super().__init__(
                f"List '{list_id}' not found.",
                "Check that the list ID is correct and belongs to the selected project.",
            )
        elif hint:
            super().__init__("No lists found.", hint)
        else:
            super().__init__(
                "No lists found for this project.",
                "Create at least one list in this project or check permissions.",
            )


class OAuthError(ClickupyError):
    """Raised when OAuth authentication fails."""

    exit_code = 6

    def __init__(self, message: str = "OAuth authentication failed."):
        super().__init__(message, "Try running 'quickup login' again.")


class NetworkError(ClickupyError):
    """Raised for HTTP/connection failures."""

    exit_code = 4

    def __init__(self, message: str = "Network error occurred."):
        super().__init__(
            message,
            "Check your internet connection and try again. "
            "If the problem persists, ClickUp API may be experiencing issues.",
        )


class APIError(ClickupyError):
    """Raised for ClickUp API errors."""

    exit_code = 5

    def __init__(self, message: str = "ClickUp API error.", status_code: int | None = None):
        hint = None
        if status_code == 401:
            hint = "Authentication failed. Check your API token."
        elif status_code == 403:
            hint = "Access denied. Check your permissions in ClickUp."
        elif status_code == 404:
            hint = "Resource not found. Check the ID and try again."
        elif status_code == 429:
            hint = "Rate limit exceeded. Wait a moment and try again."
        elif status_code and status_code >= 500:
            hint = "ClickUp server error. Try again later."

        super().__init__(message, hint)


def handle_exception(exc: ClickupyError) -> None:
    """Print exception message and exit with appropriate code."""
    print(f"Error: {exc.message}", file=sys.stderr)
    if exc.hint:
        print(f"Hint: {exc.hint}", file=sys.stderr)
    sys.exit(exc.exit_code)
