"""Caching layer for QuickUp! CLI using sqlite3.

Provides TTL-based caching for ClickUp API responses to reduce API calls.
"""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import pickle
import sqlite3
import time

# Cache location: ~/.quickup/cache/
CACHE_DIR = Path.home() / ".quickup" / "cache"
CACHE_FILE = CACHE_DIR / "quickup_cache.db"

# TTL values in seconds
TEAMS_TTL = 24 * 60 * 60  # 24 hours
SPACES_TTL = 24 * 60 * 60  # 24 hours
PROJECTS_TTL = 24 * 60 * 60  # 24 hours
LISTS_TTL = 24 * 60 * 60  # 24 hours
TASKS_TTL = 5 * 60  # 5 minutes


class SQLiteCache:
    """SQLite-backed cache with TTL support using pickle serialization."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key        TEXT PRIMARY KEY,
                    value      BLOB NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)

    def __contains__(self, key: str) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute("SELECT expires_at FROM cache WHERE key = ?", (key,)).fetchone()
        return row is not None and row[0] > time.time()

    def get(self, key: str):
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,)).fetchone()
            if row is None:
                return None
            if row[1] <= time.time():
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                return None
        return pickle.loads(row[0])  # noqa: S301 - local self-written cache

    def set(self, key: str, value, expire: int) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, pickle.dumps(value), time.time() + expire),
            )

    def delete(self, key: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))

    def get_all_by_prefix(self, prefix: str) -> list:
        """Return all non-expired values whose keys start with prefix."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key LIKE ?",
                (f"{prefix}%",),
            ).fetchall()
        now = time.time()
        return [
            pickle.loads(value) for value, expires_at in rows if expires_at > now
        ]  # noqa: S301 - local self-written cache

    def get_stale_keys(self, prefix: str) -> list[str]:
        """Return keys matching prefix that have expired but not yet been deleted."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT key FROM cache WHERE key LIKE ? AND expires_at < ?",
                (f"{prefix}%", time.time()),
            ).fetchall()
        return [row[0] for row in rows]

    def clear(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM cache")


def get_cache() -> SQLiteCache:
    """Get or create disk cache instance."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return SQLiteCache(str(CACHE_FILE))


def get_teams_data(clickup) -> list:
    """Get teams data from cache or fetch from API.

    Args:
        clickup: ClickUp client instance.

    Returns:
        List of team objects.
    """
    cache = get_cache()
    cache_key = "teams"

    if cache_key in cache:
        return cache.get(cache_key)  # type: ignore[no-any-return]

    teams = clickup.teams
    cache.set(cache_key, teams, expire=TEAMS_TTL)
    return teams


def get_spaces_data(team) -> list:
    """Get spaces data for a team from cache or fetch from API.

    Args:
        team: Team object.

    Returns:
        List of space objects.
    """
    cache = get_cache()
    cache_key = f"spaces:{team.id}"

    if cache_key in cache:
        return cache.get(cache_key)  # type: ignore[no-any-return]

    spaces = team.spaces
    cache.set(cache_key, spaces, expire=SPACES_TTL)
    return spaces


def get_projects_data(space) -> list:
    """Get projects data for a space from cache or fetch from API.

    Args:
        space: Space object.

    Returns:
        List of project objects.
    """
    cache = get_cache()
    cache_key = f"projects:{space.id}"

    if cache_key in cache:
        return cache.get(cache_key)  # type: ignore[no-any-return]

    projects = space.projects
    cache.set(cache_key, projects, expire=PROJECTS_TTL)
    return projects


def get_lists_data(project) -> list:
    """Get lists data for a project from cache or fetch from API.

    Args:
        project: Project object.

    Returns:
        List of list objects.
    """
    cache = get_cache()
    cache_key = f"lists:{project.id}"

    if cache_key in cache:
        return cache.get(cache_key)  # type: ignore[no-any-return]

    lists = project.lists
    cache.set(cache_key, lists, expire=LISTS_TTL)
    return lists


def get_tasks_data(team, list_id: str, include_closed: bool = False) -> list:
    """Get tasks data for a list from cache or fetch from API.

    Args:
        team: Team object.
        list_id: ClickUp list ID.
        include_closed: If True, include closed/done tasks.

    Returns:
        List of task objects.
    """
    cache = get_cache()
    cache_key = f"tasks:{list_id}:closed" if include_closed else f"tasks:{list_id}"

    if cache_key in cache:
        return cache.get(cache_key)  # type: ignore[no-any-return]

    tasks = team.get_all_tasks(subtasks=False, list_ids=[list_id], include_closed=include_closed)
    cache.set(cache_key, tasks, expire=TASKS_TTL)
    cache.set(f"team_for_list:{list_id}", team.id, expire=TEAMS_TTL)
    return tasks


def find_task_in_cache(task_id: str):
    """Search all cached task lists for a task by ID.

    Args:
        task_id: ClickUp task ID.

    Returns:
        Task object if found in cache, None otherwise.
    """
    cache = get_cache()
    cache_key = f"task:{task_id}"
    if cache_key in cache:
        return cache.get(cache_key)
    for task_list in cache.get_all_by_prefix("tasks:"):
        for task in task_list:
            if task.id == task_id:
                return task
    return None


def get_task_data(clickup, team_id: str, task_id: str):
    """Get a single task from cache or fetch from API.

    Checks the per-task cache key first, then searches cached list entries,
    then falls back to fetching the task directly via the single-task endpoint
    (which includes subtasks). Always caches the result under 'task:{task_id}'.

    Args:
        clickup: ClickUp client instance.
        team_id: Team ID to scope the API call.
        task_id: ClickUp task ID.

    Returns:
        Task object, or None if not found.
    """
    from pyclickup.models import Task

    cache = get_cache()
    cache_key = f"task:{task_id}"

    task = find_task_in_cache(task_id)
    if task is not None:
        cache.set(cache_key, task, expire=TASKS_TTL)
        return task

    task_data = clickup.get(f"task/{task_id}?include_subtasks=true")
    if isinstance(task_data, dict) and "id" in task_data:
        task = Task(task_data, client=clickup)
        cache.set(cache_key, task, expire=TASKS_TTL)
        return task
    return None


def force_refresh_tasks(team, list_id: str) -> list:
    """Fetch tasks unconditionally from API and overwrite cache."""
    tasks = team.get_all_tasks(subtasks=False, list_ids=[list_id])
    cache = get_cache()
    cache.set(f"tasks:{list_id}", tasks, expire=TASKS_TTL)
    return tasks


def maybe_warmup(token: str) -> None:
    """Refresh any expired task cache entries before the command runs."""
    if os.environ.get("QUICKUP_WARMUP", "true").lower() == "false":
        return

    cache = get_cache()
    stale_keys = cache.get_stale_keys("tasks:")
    if not stale_keys:
        return

    # Collect team mappings BEFORE clearing cache
    list_team_pairs = []
    for key in stale_keys:
        list_id = key.removeprefix("tasks:")
        team_id = cache.get(f"team_for_list:{list_id}")
        if team_id:
            list_team_pairs.append((list_id, team_id))

    if not list_team_pairs:
        return

    # Clear everything — hierarchy will be lazily re-fetched from API on next use
    cache.clear()

    from colorist import Effect
    from pyclickup import ClickUp

    clickup = ClickUp(token)
    teams = {t.id: t for t in get_teams_data(clickup)}

    print(f"{Effect.DIM}Warming cache...{Effect.DIM_OFF}", end="", flush=True)

    def _refresh(pair: tuple[str, str]) -> None:
        list_id, team_id = pair
        team = teams.get(team_id)
        if team:
            force_refresh_tasks(team, list_id)

    with ThreadPoolExecutor(max_workers=min(4, len(list_team_pairs))) as pool:
        list(pool.map(_refresh, list_team_pairs))

    print(f"\r{' ' * 20}\r", end="", flush=True)


def invalidate_tasks_cache(list_id: str) -> None:
    """Invalidate cache for a specific list.

    Args:
        list_id: ClickUp list ID.
    """
    cache = get_cache()
    cache.delete(f"tasks:{list_id}")


def clear_cache() -> None:
    """Clear all cached data."""
    cache = get_cache()
    cache.clear()
