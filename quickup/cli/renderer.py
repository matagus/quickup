"""Terminal output rendering for QuickUp! CLI."""

from collections import defaultdict
from datetime import datetime

from colorist import BgColorHex, Color, ColorHex, Effect

from .cache import get_tasks_data


def _filter_tasks(task_list, assignee=None, priority=None, due_before=None):
    """Filter tasks based on criteria.

    Args:
        task_list: List of task objects.
        assignee: Filter by assignee username (case-insensitive).
        priority: Filter by priority level (low, normal, high, urgent).
        due_before: Filter tasks due before date (YYYY-MM-DD).

    Returns:
        Filtered list of tasks.
    """
    filtered = task_list

    if assignee:
        assignee_lower = assignee.lower()
        filtered = [t for t in filtered if any(a.username.lower() == assignee_lower for a in t.assignees)]

    if priority:
        priority_map = {"low": 1, "normal": 2, "high": 3, "urgent": 4}
        priority_value = priority_map.get(priority.lower())
        if priority_value:
            filtered = [t for t in filtered if t.priority and t.priority.get("priority") == priority.lower()]

    if due_before:
        try:
            due_date = datetime.strptime(due_before, "%Y-%m-%d")
            filtered = [
                t for t in filtered if t.due_date and datetime.strptime(t.due_date, "%Y-%m-%dT%H:%M:%S.%fZ") < due_date
            ]
        except ValueError:
            pass  # Invalid date format, skip filtering

    return filtered


def _render_task(task):
    """Render a single task line.

    Args:
        task: Task object.
    """
    task_name = f"{Effect.BOLD}{task.name}{Effect.BOLD_OFF}"
    task_url = f"{Color.BLUE}{Effect.UNDERLINE}{task.url}{Effect.UNDERLINE_OFF}{Color.OFF}"
    task_assignees = ", ".join([f"{a.username}" for a in task.assignees])
    task_assignee_str = f"{Effect.DIM}({task_assignees}){Effect.DIM_OFF}" if task_assignees else ""
    task_id_str = f"{Effect.DIM}[id={task.id}]{Effect.DIM_OFF}"

    task_priority = ""
    if task.priority is not None:
        priority_color = ColorHex(task.priority["color"])
        priority_label = task.priority["priority"].capitalize()
        task_priority = f"[{priority_color}{priority_label}{priority_color.OFF}] "

    print(f" ▫ {task_priority}{task_name}: {task_url} {task_assignee_str} {task_id_str}")


def _group_by_status(task_list):
    """Group tasks by status, ordered by color order.

    Args:
        task_list: List of task objects.

    Returns:
        Dict of status name -> tasks, ordered by status orderindex.
    """
    tasks_by_status = defaultdict(list)
    color_for_status = {}
    color_order = {}

    for task in task_list:
        if task.parent is None:
            tasks_by_status[task.status.status].append(task)
            color_for_status[task.status.status] = task.status.color
            color_order[task.status.status] = task.status.orderindex

    ordered_statuses = list(tasks_by_status.keys())
    ordered_statuses.sort(key=lambda x: color_order[x])

    return {s: tasks_by_status[s] for s in ordered_statuses}


def _group_by_assignee(task_list):
    """Group tasks by assignee, alphabetically sorted.

    Args:
        task_list: List of task objects.

    Returns:
        Dict of assignee name -> tasks, sorted alphabetically.
    """
    tasks_by_assignee = defaultdict(list)

    for task in task_list:
        if task.parent is None:
            if task.assignees:
                for assignee in task.assignees:
                    tasks_by_assignee[assignee.username].append(task)
            else:
                tasks_by_assignee["Unassigned"].append(task)

    sorted_assignees = sorted(tasks_by_assignee.keys())
    return {a: tasks_by_assignee[a] for a in sorted_assignees}


def _group_by_priority(task_list):
    """Group tasks by priority, ordered urgent->high->normal->low->none.

    Args:
        task_list: List of task objects.

    Returns:
        Dict of priority name -> tasks, ordered by priority level.
    """
    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3, "none": 4}
    tasks_by_priority = defaultdict(list)

    for task in task_list:
        if task.parent is None:
            if task.priority and task.priority.get("priority"):
                priority = task.priority.get("priority").lower()
            else:
                priority = "none"
            tasks_by_priority[priority].append(task)

    sorted_priorities = sorted(tasks_by_priority.keys(), key=lambda x: priority_order.get(x, 99))
    return {p: tasks_by_priority[p] for p in sorted_priorities}


def render_list(
    list_obj,
    team_obj,
    no_cache: bool = False,
    assignee=None,
    priority=None,
    due_before=None,
    group_by="status",
    include_closed: bool = False,
    team=None,
    space=None,
    project=None,
    list_id=None,
):
    """Render tasks from a list grouped by status, assignee, or priority.

    Args:
        list_obj: List object from ClickUp.
        team_obj: Team object from ClickUp.
        no_cache: If True, bypass cache and fetch from API.
        assignee: Filter by assignee username (case-insensitive).
        priority: Filter by priority level (low, normal, high, urgent).
        due_before: Filter tasks due before date (YYYY-MM-DD).
        group_by: Group by "status" (default), "assignee", or "priority".
        include_closed: If True, include closed/done tasks.
        team: Team ID from command line.
        space: Space ID from command line.
        project: Project ID from command line.
        list_id: List ID from command line.
    """
    # Print a header with the list and team names
    styled_list_name = f"{Color.YELLOW}{Effect.BOLD}{list_obj.name}{Effect.BOLD_OFF}{Color.OFF}"
    team_name = f"{Effect.BOLD}{Color.MAGENTA}{team_obj.name}{Color.OFF}{Effect.BOLD_OFF}"

    # Build filter info for header
    filters = []
    if assignee:
        filters.append(f"assignee={assignee}")
    if priority:
        filters.append(f"priority={priority}")
    if due_before:
        filters.append(f"due_before={due_before}")
    if group_by != "status":
        filters.append(f"group_by={group_by}")
    if include_closed:
        filters.append("closed=true")

    filter_info = f" {Effect.DIM}[{', '.join(filters)}]{Effect.DIM_OFF}" if filters else ""
    print(f"{styled_list_name} :: Team: {team_name}{filter_info}")

    if no_cache:
        task_list = team_obj.get_all_tasks(subtasks=False, list_ids=[list_obj.id], include_closed=include_closed)
    else:
        task_list = get_tasks_data(team_obj, list_obj.id, include_closed=include_closed)

    # Apply filters
    task_list = _filter_tasks(task_list, assignee=assignee, priority=priority, due_before=due_before)

    # Group tasks
    if group_by == "assignee":
        grouped = _group_by_assignee(task_list)
    elif group_by == "priority":
        grouped = _group_by_priority(task_list)
    else:
        grouped = _group_by_status(task_list)

    for group_name, tasks in grouped.items():
        if group_by == "status":
            # Find color for status
            if tasks:
                status_color = BgColorHex(tasks[0].status.color)
                print(f"\n{status_color} {group_name.upper()} {status_color.OFF} \n")
        elif group_by == "assignee":
            print(f"\n{Effect.BOLD}{Color.YELLOW}{group_name}{Color.OFF}{Effect.BOLD_OFF}\n")
        elif group_by == "priority":
            priority_colors = {
                "urgent": "#FF0000",
                "high": "#FF8800",
                "normal": "#0088FF",
                "low": "#00AA00",
                "none": "#888888",
            }
            color = priority_colors.get(group_name, "#888888")
            print(f"\n{ColorHex(color)}{Effect.BOLD} {group_name.upper()} {Effect.BOLD_OFF}{Color.OFF}\n")

        for task in tasks:
            _render_task(task)

    # Render suggestion for repeating the command
    print()
    cmd_parts = ["quickup"]
    if team:
        cmd_parts.append(f"--team {team}")
    if space:
        cmd_parts.append(f"--space {space}")
    if project:
        cmd_parts.append(f"--project {project}")
    if list_id:
        cmd_parts.append(f"--list {list_id}")
    if assignee:
        cmd_parts.append(f"--assignee {assignee}")
    if priority:
        cmd_parts.append(f"--priority {priority}")
    if due_before:
        cmd_parts.append(f"--due-before {due_before}")
    if group_by != "status":
        cmd_parts.append(f"--group-by {group_by}")
    if include_closed:
        cmd_parts.append("--closed")
    if no_cache:
        cmd_parts.append("--no-cache")

    suggestion = " ".join(cmd_parts)
    print(f"{Effect.DIM}Run again: {suggestion}{Effect.DIM_OFF}")


def _render_subtasks(subtasks):
    """Render subtasks (raw dicts from single-task API) grouped by status, same format as list view."""
    by_status = defaultdict(list)
    status_color = {}
    status_order = {}
    for subtask in subtasks:
        status = subtask.get("status", {})
        status_name = status.get("status", "unknown")
        by_status[status_name].append(subtask)
        status_color[status_name] = status.get("color", "#888888")
        status_order[status_name] = status.get("orderindex", 0)

    for status_name in sorted(by_status, key=lambda s: status_order[s]):
        bg = BgColorHex(status_color[status_name])
        print(f"\n{bg} {status_name.upper()} {bg.OFF} \n")
        for subtask in by_status[status_name]:
            task_id = subtask["id"]
            name = f"{Effect.BOLD}{subtask['name']}{Effect.BOLD_OFF}"
            url = f"https://app.clickup.com/t/{task_id}"
            url_str = f"{Color.BLUE}{Effect.UNDERLINE}{url}{Effect.UNDERLINE_OFF}{Color.OFF}"
            assignees = subtask.get("assignees", [])
            assignee_names = ", ".join(a.get("username", "") for a in assignees)
            assignee_str = f"{Effect.DIM}({assignee_names}){Effect.DIM_OFF}" if assignee_names else ""
            id_str = f"{Effect.DIM}[id={task_id}]{Effect.DIM_OFF}"
            priority = subtask.get("priority")
            priority_str = ""
            if priority and isinstance(priority, dict) and priority.get("priority"):
                pc = ColorHex(priority["color"])
                priority_str = f"[{pc}{priority['priority'].capitalize()}{pc.OFF}] "
            print(f" ▫ {priority_str}{name}: {url_str} {assignee_str} {id_str}")


def render_task_detail(task):
    """Render detailed task information.

    Args:
        task: Task object from ClickUp.
    """
    print(f"{Effect.BOLD}{Color.YELLOW}Task Details{Color.OFF}{Effect.BOLD_OFF}")
    print(f"{'─' * 40}")

    # ID and Name
    print(f"\n{Effect.BOLD}ID:{Effect.BOLD_OFF} {task.id}")
    print(f"{Effect.BOLD}Name:{Effect.BOLD_OFF} {task.name}")

    # Status
    status_color = ColorHex(task.status.color)
    print(f"{Effect.BOLD}Status:{Effect.BOLD_OFF} {status_color}{task.status.status}{status_color.OFF}")

    # URL
    url = getattr(task, "url", None) or f"https://app.clickup.com/t/{task.id}"
    print(f"{Effect.BOLD}URL:{Effect.BOLD_OFF} {Color.BLUE}{Effect.UNDERLINE}{url}{Effect.UNDERLINE_OFF}{Color.OFF}")

    # Assignees
    if task.assignees:
        assignee_names = ", ".join([f"{a.username}" for a in task.assignees])
        print(f"{Effect.BOLD}Assignees:{Effect.BOLD_OFF} {assignee_names}")
    else:
        print(f"{Effect.BOLD}Assignees:{Effect.BOLD_OFF} Unassigned")

    # Priority
    if task.priority:
        priority_color = ColorHex(task.priority["color"])
        priority_label = task.priority["priority"].capitalize()
        print(f"{Effect.BOLD}Priority:{Effect.BOLD_OFF} {priority_color}{priority_label}{priority_color.OFF}")
    else:
        print(f"{Effect.BOLD}Priority:{Effect.BOLD_OFF} None")

    # Due Date
    if task.due_date:
        due_date = task.due_date.split("T")[0] if isinstance(task.due_date, str) else task.due_date.strftime("%Y-%m-%d")
        print(f"{Effect.BOLD}Due Date:{Effect.BOLD_OFF} {due_date}")
    else:
        print(f"{Effect.BOLD}Due Date:{Effect.BOLD_OFF} None")

    # Description (team endpoint uses 'description'; single-task endpoint uses 'text_content')
    description = getattr(task, "description", None) or getattr(task, "text_content", None)
    if description:
        print(f"\n{Effect.BOLD}Description:{Effect.BOLD_OFF}")
        print(f"{description}")

    # Subtasks
    if hasattr(task, "subtasks") and task.subtasks:
        print(f"\n{Effect.BOLD}Subtasks ({len(task.subtasks)}):{Effect.BOLD_OFF}")
        _render_subtasks(task.subtasks)
    else:
        print(f"\n{Effect.BOLD}Subtasks:{Effect.BOLD_OFF} None")


def render_task_update(task_id, old_status, new_status):
    """Render task status update confirmation.

    Args:
        task_id: ClickUp task ID.
        old_status: Previous status name.
        new_status: New status name.
    """
    print(f"{Effect.BOLD}{Color.GREEN}Task Updated{Color.OFF}{Effect.BOLD_OFF}")
    print(f"{'─' * 40}")
    print(f"\n{Effect.BOLD}Task ID:{Effect.BOLD_OFF} {task_id}")
    print(
        f"{Effect.BOLD}Status:{Effect.BOLD_OFF} "
        f"{Color.YELLOW}{old_status}{Color.OFF} → {Color.GREEN}{new_status}{Color.OFF}"
    )
    print(f"\n{Color.GREEN}✓{Color.OFF} Status updated successfully")


def render_task_comments(comments):
    """Render list of comments for a task.

    Args:
        comments: List of comment dicts from the ClickUp API.
    """
    print(f"\n{Effect.BOLD}{Color.YELLOW}Comments ({len(comments)}){Color.OFF}{Effect.BOLD_OFF}")
    print(f"{'─' * 40}")

    if not comments:
        print("\nNo comments")
        return

    for comment in comments:
        user = comment.get("user", {})
        username = user.get("username") or user.get("email") or "Unknown"
        date_ms = comment.get("date")
        date_str = datetime.fromtimestamp(int(date_ms) / 1000).strftime("%Y-%m-%d %H:%M") if date_ms else "Unknown date"
        text = comment.get("comment_text", "")
        print(f"\n{Effect.BOLD}{username}{Effect.BOLD_OFF} · {date_str}")
        print(f"{text}")


def render_comment_posted(task_id, comment_text):
    """Render comment posted confirmation.

    Args:
        task_id: ClickUp task ID.
        comment_text: The comment text that was posted.
    """
    print(f"{Effect.BOLD}{Color.GREEN}Comment Posted{Color.OFF}{Effect.BOLD_OFF}")
    print(f"{'─' * 40}")
    print(f"\n{Effect.BOLD}Task ID:{Effect.BOLD_OFF} {task_id}")
    display_text = comment_text[:80] + "..." if len(comment_text) > 80 else comment_text
    print(f"{Effect.BOLD}Comment:{Effect.BOLD_OFF} {display_text}")
    print(f"\n{Color.GREEN}✓{Color.OFF} Comment posted successfully")
