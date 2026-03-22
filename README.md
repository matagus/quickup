# QuickUp!

![Python Compatibility](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13|3.14-blue.svg)
[![PyPI Version](https://img.shields.io/pypi/v/quickup.svg)](https://pypi.python.org/pypi/quickup)
[![Tests](https://github.com/matagus/quickup/actions/workflows/tests.yml/badge.svg)](https://github.com/matagus/quickup/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/quickup/badge/?version=latest)](https://quickup.readthedocs.io/en/latest/?badge=latest)

**[Documentation](https://quickup.readthedocs.io/en/latest/)** | [GitHub](https://github.com/matagus/quickup) | [PyPI](https://pypi.python.org/pypi/quickup)

A simple, lightweight, and beautiful console-based client for ClickUp that lets you view, filter, and manage tasks
directly from your command line. View tasks grouped by status, assignee, or priority, update task statuses, and
auto-detect your current sprint. It features interactive mode for easy navigation and caching for fast performance.

![QuickUp! in action](https://raw.githubusercontent.com/matagus/quickup/main/screenshots/demo.gif)

## Features

- **Task Listing**: View all tasks from a ClickUp list with color-coded status groups
- **Filtering**: Filter tasks by assignee, priority, or due date
- **Grouping**: Group tasks by status, assignee, or priority
- **Task Details**: View detailed information about a specific task
- **Task Updates**: Update task status with confirmation display
- **Sprint Detection**: Auto-detect current sprint/iteration lists
- **Interactive Mode**: Navigate through Team → Space → Project → List hierarchy with prompts
- **Caching**: Disk-based caching for improved performance (24h for teams/lists, 5min for tasks)

## Installation

```bash
pip install quickup
```

## Quick Start

Set your ClickUp API token:

```bash
export CLICKUP_TOKEN=your_token_here
```

Or create a `.env` file in your project directory:

```
CLICKUP_TOKEN=your_token_here
```

List tasks from a specific list:

```bash
quickup --team <team_id> --list <list_id>
```

## Commands

### `quickup` (default) - List Tasks

List all tasks from a ClickUp list, grouped by status.

```bash
# Basic usage
quickup --team <team_id> --list <list_id>

# With filters
quickup --team <team_id> --list <list_id> --assignee john --priority high

# Group by assignee
quickup --team <team_id> --list <list_id> --group-by assignee

# Interactive mode
quickup -i

# Bypass cache
quickup --team <team_id> --list <list_id> --no-cache
```

**Options:**
- `--team`: Team ID
- `--space`: Space ID
- `--project`: Project ID
- `--list`: List ID
- `--assignee`: Filter by assignee username (case-insensitive)
- `--priority`: Filter by priority (low, normal, high, urgent)
- `--due-before`: Filter tasks due before date (YYYY-MM-DD)
- `--group-by`: Group by status (default), assignee, or priority
- `--closed`: Include closed/done tasks
- `--no-cache`: Bypass cache and fetch from API
- `-i, --interactive`: Enable interactive mode

### `quickup sprint` - Current Sprint Tasks

Auto-detects the current sprint list by searching for lists containing "sprint" or "iteration" in the name.

```bash
# List tasks from current sprint
quickup sprint --team <team_id>

# With filters
quickup sprint --team <team_id> --assignee jane --group-by priority
```

**Options:**
- `--team`: Team ID
- `--space`: Space ID
- `--project`: Project ID
- `--assignee`: Filter by assignee username
- `--priority`: Filter by priority
- `--due-before`: Filter tasks due before date
- `--group-by`: Group by status, assignee, or priority
- `--closed`: Include closed/done tasks
- `--no-cache`: Bypass cache
- `-i, --interactive`: Enable interactive mode

### `quickup task <task_id>` - Task Details

Show detailed information about a specific task.

```bash
# Show task details
quickup task <task_id>

# With team specification
quickup task <task_id> --team <team_id>
```

**Options:**
- `task_id`: ClickUp task ID
- `--team`: Team ID (required if multiple teams exist)
- `-i, --interactive`: Enable interactive mode

### `quickup update <task_id>` - Update Task Status

Update the status of a specific task.

```bash
# Update task status
quickup update <task_id> --status "In Progress"

# With team specification
quickup update <task_id> --status "Done" --team <team_id>
```

**Options:**
- `task_id`: ClickUp task ID
- `--status`: New status name (e.g., "To Do", "In Progress", "Done")
- `--team`: Team ID (required if multiple teams exist)
- `-i, --interactive`: Enable interactive mode

## Interactive Mode

When multiple teams, spaces, projects, or lists exist, use `-i` flag to enable interactive selection:

```bash
quickup -i
```

This will prompt you to select:
1. Team (if multiple teams exist)
2. Space (if multiple spaces exist)
3. Project (if multiple projects exist)
4. List (if multiple lists exist)

## Output Format

Tasks are displayed with:
- **Bold** task name
- Blue underlined URL
- Priority badge (color-coded)
- Assignee names in parentheses

Status groups are displayed with color-coded headers matching the ClickUp status colors.

At the bottom of the output, a suggestion is shown in gray text with the command to repeat the same query:

```
Run again: quickup --assignee john --priority high --group-by priority
```

This makes it easy to re-run the same filtered/grouped view without typing the full command again.

## Caching

QuickUp! uses disk-based caching to reduce API calls:
- Teams: 24 hours TTL
- Lists: 24 hours TTL
- Tasks: 5 minutes TTL

Cache location: `~/.quickup/cache/`

Use `--no-cache` to bypass cache and fetch fresh data from the API.

## Exit Codes

| Code | Meaning |
|------|---------|
| 1 | Token error or general ClickUp error |
| 2 | Team not found or ambiguous team |
| 3 | List not found |
| 4 | Network error |
| 5 | API error |
| 99 | Unexpected error |

## Requirements

- Python 3.10+
- ClickUp API token

## Dependencies

- [cyclopts](https://github.com/BrianPugh/cyclopts) - CLI framework
- [pyclickup](https://github.com/matagus/pyclickup) - ClickUp API wrapper
- [colorist](https://github.com/TMDBC/colorist) - Terminal colors
- [inquirer](https://github.com/magmax/python-inquirer) - Interactive prompts
- [sqlite3](https://docs.python.org/3/library/sqlite3.html) - Caching layer (Python standard library)
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment loading

## Development

### Running Tests

Run the test suite:

```bash
hatch run test:test
```

Run tests with coverage:

```bash
hatch run test:cov
```

Coverage reports are generated in:
- `coverage.json` - JSON format
- Terminal - Human-readable report

Run tests on a specific Python version:

```bash
hatch run +py=3.11 test:test
```

### Documentation

Build the documentation:

```bash
hatch run docs:build
```

Serve the documentation locally:

```bash
hatch run docs:serve
```

Then open http://localhost:8000 in your browser.

### Debug Environment

For debugging with enhanced tooling:

```bash
hatch run debug:python
```

This environment includes `ipdb` and `line_profiler`.

## License

MIT
