"""API client wrapper for ClickUp API interactions."""

import sys

from colorist import Color
import inquirer

from .cache import get_lists_data, get_projects_data, get_spaces_data, get_teams_data
from .exceptions import (
    ListNotFoundError,
    ProjectNotFoundError,
    SpaceNotFoundError,
    TeamAmbiguousError,
    TeamNotFoundError,
)


def get_team(clickup, argv, interactive=False):
    """Get team from CLI args or interactive selection.

    Args:
        clickup: ClickUp client instance.
        argv: Command line arguments.
        interactive: If True, prompt user to select team when multiple exist.

    Returns:
        Team object.

    Raises:
        TeamNotFoundError: If team ID is invalid or no teams exist.
        TeamAmbiguousError: If multiple teams exist but interactive=False.
    """
    try:
        team_id = sys.argv[sys.argv.index("--team") + 1]
        teams = get_teams_data(clickup)
        team = next((t for t in teams if str(t.id) == team_id), None)
        if team is None:
            raise TeamNotFoundError(team_id=team_id)
        return team

    except ValueError:
        teams = get_teams_data(clickup)
        if len(teams) == 0:
            raise TeamNotFoundError()

        if len(teams) > 1:
            if interactive:
                questions = [
                    inquirer.List(
                        "team",
                        message=f"Select a {Color.MAGENTA}Team{Color.OFF}",
                        choices=[f"{t.name} [{t.id}]" for t in teams],
                    )
                ]
                answers = inquirer.prompt(questions)
                if answers:
                    for t in teams:
                        if f"{t.name} [{t.id}]" == answers["team"]:
                            return t

            raise TeamAmbiguousError([t.name for t in teams])

        return teams[0]

    except (TeamNotFoundError, TeamAmbiguousError):
        raise
    except Exception:
        raise TeamNotFoundError(team_id=argv[argv.index("--team") + 1] if "--team" in argv else None)


def get_space_for(team, argv, interactive=False):
    """Get space from CLI args or interactive selection.

    Args:
        team: Team object.
        argv: Command line arguments.
        interactive: If True, prompt user to select space when multiple exist.

    Returns:
        Space object.

    Raises:
        SpaceNotFoundError: If space is not found.
    """
    try:
        space_id = sys.argv[sys.argv.index("--space") + 1]
        spaces = get_spaces_data(team)
        return next(s for s in spaces if str(s.id) == space_id)

    except ValueError:
        spaces = get_spaces_data(team)
        if len(spaces) == 0:
            raise SpaceNotFoundError()

        if len(spaces) > 1:
            if interactive:
                questions = [
                    inquirer.List(
                        "space",
                        message=f"Select a {Color.CYAN}Space{Color.OFF}",
                        choices=[f"{space.name} [{space.id}]" for space in spaces],
                    )
                ]

                answers = inquirer.prompt(questions)

                if answers:
                    for space in spaces:
                        if f"{space.name} [{space.id}]" == answers["space"]:
                            return space

        return spaces[0]

    except SpaceNotFoundError:
        raise
    except Exception:
        raise SpaceNotFoundError(space_id=argv[argv.index("--space") + 1] if "--space" in argv else None)


def get_project_for(space, argv, interactive=False):
    """Get project from CLI args or interactive selection.

    Args:
        space: Space object.
        argv: Command line arguments.
        interactive: If True, prompt user to select project when multiple exist.

    Returns:
        Project object.

    Raises:
        ProjectNotFoundError: If project is not found.
    """
    try:
        project_id = sys.argv[sys.argv.index("--project") + 1]
        projects = get_projects_data(space)
        return next(p for p in projects if str(p.id) == project_id)

    except ValueError:
        projects = get_projects_data(space)
        if len(projects) == 0:
            raise ProjectNotFoundError()

        visible = [p for p in projects if not getattr(p, "hidden", False)]
        if not visible:
            visible = projects

        if len(visible) > 1:
            if interactive:
                questions = [
                    inquirer.List(
                        "project",
                        message=f"Select a {Color.GREEN}Project{Color.OFF}",
                        choices=[f"{project.name} [{project.id}]" for project in visible],
                    )
                ]

                answers = inquirer.prompt(questions)

                if answers:
                    for project in visible:
                        if f"{project.name} [{project.id}]" == answers["project"]:
                            return project

        return visible[0]

    except ProjectNotFoundError:
        raise
    except Exception:
        raise ProjectNotFoundError(project_id=argv[argv.index("--project") + 1] if "--project" in argv else None)


def get_list_for(space_obj, argv, interactive=False):
    """Get list from CLI args or interactive selection.

    Args:
        space_obj: Space object.
        argv: Command line arguments.
        interactive: If True, prompt user to select list when multiple exist.

    Returns:
        List object.

    Raises:
        ListNotFoundError: If list is not found.
    """
    try:
        index = sys.argv.index("--list")
        list_id = sys.argv[index + 1]
        lists = get_lists_data(space_obj)
        # Also include lists from hidden (folderless) sibling projects
        if hasattr(space_obj, "space"):
            for p in get_projects_data(space_obj.space):
                if getattr(p, "hidden", False) and p.id != space_obj.id:
                    lists = lists + get_lists_data(p)
        return next(li for li in lists if str(li.id) == list_id)

    except ValueError:
        lists = get_lists_data(space_obj)
        # Also include lists from hidden (folderless) sibling projects
        if hasattr(space_obj, "space"):
            for p in get_projects_data(space_obj.space):
                if getattr(p, "hidden", False) and p.id != space_obj.id:
                    lists = lists + get_lists_data(p)

        if len(lists) == 0:
            raise ListNotFoundError()

        if len(lists) > 1:
            if interactive:
                questions = [
                    inquirer.List(
                        "list",
                        message=f"Select a {Color.YELLOW}List{Color.OFF}",
                        choices=[f"{li.name} [{li.id}]" for li in lists],
                    )
                ]

                answers = inquirer.prompt(questions)

                if answers:
                    for li in lists:
                        if f"{li.name} [{li.id}]" == answers["list"]:
                            return li

        return lists[0]

    except ListNotFoundError:
        raise
    except Exception:
        raise ListNotFoundError(list_id=argv[argv.index("--list") + 1] if "--list" in argv else None)


def get_current_sprint_list(team, space):
    """Auto-detect current sprint list from team's lists.

    Searches for lists containing "sprint" or "iteration" in the name (case-insensitive).
    Prefers the sprint explicitly marked as "started" (active). Falls back to sorting by ID
    descending (most recent first) if no started sprint is found.

    Args:
        team: Team object.
        space: Space object (used to filter lists by space).

    Returns:
        List object for the current sprint.

    Raises:
        ListNotFoundError: If no sprint lists are found.
    """
    # Get all lists for the team by iterating through spaces -> projects -> lists
    all_lists = []
    spaces = get_spaces_data(team) if not space else [space]
    for sp in spaces:
        for proj in get_projects_data(sp):
            all_lists.extend(get_lists_data(proj))

    # Find sprint/iteration lists
    sprint_lists = [li for li in all_lists if "sprint" in li.name.lower() or "iteration" in li.name.lower()]

    if not sprint_lists:
        raise ListNotFoundError(hint="No lists found with 'sprint' or 'iteration' in the name")

    # Prefer the sprint explicitly marked as started (currently active)
    active_sprints = [li for li in sprint_lists if getattr(li, "status", None) == "started"]
    if active_sprints:
        return active_sprints[0]

    # Fallback: sort by ID descending (most recent first)
    sprint_lists.sort(key=lambda x: x.id, reverse=True)

    return sprint_lists[0]
