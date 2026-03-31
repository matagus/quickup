"""Command history tracking for QuickUp! CLI."""

from datetime import datetime, timezone
import json
from pathlib import Path

HISTORY_FILE = Path.home() / ".quickup" / "history.json"
MAX_ENTRIES = 50


def record(argv: list[str]) -> None:
    """Append a command invocation to the history file."""
    # Normalize: replace the full interpreter path with "quickup"
    normalized = ["quickup", *argv[1:]]
    entries = _load()
    entries.append(
        {
            "command": " ".join(normalized),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    # Keep only the most recent entries
    entries = entries[-MAX_ENTRIES:]
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries, indent=2))


def get_recent(n: int = 10) -> list[dict]:
    """Return the most recent n history entries, newest first."""
    entries = _load()
    return list(reversed(entries[-n:]))


def _load() -> list[dict]:
    """Load history entries from disk."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []
