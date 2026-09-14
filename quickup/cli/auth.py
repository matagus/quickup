"""OAuth2 authentication flow for QuickUp! CLI."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
import webbrowser

import dotenv

from .exceptions import OAuthConfigError

AUTH_DIR = Path.home() / ".quickup"
AUTH_FILE = AUTH_DIR / "auth.json"

CLICKUP_AUTH_URL = "https://app.clickup.com/api"
CLICKUP_TOKEN_URL = "https://api.clickup.com/api/v2/oauth/token"
CLICKUP_USER_URL = "https://api.clickup.com/api/v2/user"

_CALLBACK_PORT = 4242
_REDIRECT_URI = f"http://localhost:{_CALLBACK_PORT}"
_CALLBACK_TIMEOUT = 120  # seconds


def get_oauth_config() -> tuple[str, str]:
    """Return the (client_id, client_secret) of the ClickUp OAuth app to use.

    Credentials are never bundled with the package: they come from
    ``QUICKUP_CLIENT_ID`` / ``QUICKUP_CLIENT_SECRET`` in the environment or in a
    local ``.env`` file. Register your own app at
    https://app.clickup.com/settings/apps with redirect URI
    ``http://localhost:4242``.

    Raises:
        OAuthConfigError: if either credential is missing or blank.
    """
    # Pick up a local .env without overriding variables already in the environment.
    dotenv.load_dotenv(".env")

    credentials = {
        "QUICKUP_CLIENT_ID": os.environ.get("QUICKUP_CLIENT_ID", "").strip(),
        "QUICKUP_CLIENT_SECRET": os.environ.get("QUICKUP_CLIENT_SECRET", "").strip(),
    }
    missing = [name for name, value in credentials.items() if not value]
    if missing:
        raise OAuthConfigError(missing)

    return credentials["QUICKUP_CLIENT_ID"], credentials["QUICKUP_CLIENT_SECRET"]


def load_oauth_token() -> str | None:
    """Load the OAuth access token from ~/.quickup/auth.json."""
    try:
        data = json.loads(AUTH_FILE.read_text())
        return data.get("access_token")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def save_oauth_token(token: str, user_info: dict | None = None) -> None:
    """Save the OAuth access token to ~/.quickup/auth.json with restricted permissions."""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(AUTH_DIR, 0o700)

    data: dict[str, object] = {"access_token": token}
    if user_info:
        data["user"] = user_info

    # Write via a 0600 temp file and publish atomically: the token is never
    # world/group-readable, not even for the instant between create and chmod.
    tmp_file = AUTH_FILE.with_suffix(AUTH_FILE.suffix + ".tmp")
    fd = os.open(tmp_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.chmod(tmp_file, 0o600)  # O_CREAT mode is filtered by umask
        os.replace(tmp_file, AUTH_FILE)
    except BaseException:
        tmp_file.unlink(missing_ok=True)
        raise


def delete_oauth_token() -> bool:
    """Delete the stored OAuth token. Returns True if a token was removed."""
    try:
        AUTH_FILE.unlink()
        return True
    except FileNotFoundError:
        return False


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the OAuth2 callback."""

    code: str | None = None
    error: str | None = None
    expected_state: str = ""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Validate state parameter
        state = params.get("state", [None])[0]
        if state != self.expected_state:
            self._respond(400, "State mismatch — possible CSRF attack. Please try again.")
            self.__class__.error = "State parameter mismatch"
            return

        # Check for error from ClickUp
        if "error" in params:
            error_msg = params.get("error_description", params["error"])[0]
            self._respond(400, f"Authorization failed: {error_msg}")
            self.__class__.error = error_msg
            return

        # Extract authorization code
        code = params.get("code", [None])[0]
        if not code:
            self._respond(400, "No authorization code received.")
            self.__class__.error = "No authorization code in callback"
            return

        self.__class__.code = code
        self._respond(
            200,
            "Authentication successful! You can close this tab and return to the terminal.",
        )

    def _respond(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        # NOTE: keep the emoji choice out of the f-string. pyupgrade corrupts
        # multi-line f-strings that embed `{'x' if cond else 'y'}` with non-ASCII
        # literals: it re-emits the literal with shifted offsets and appends junk
        # to the closing quote on every run (pyupgrade 3.21.2, all --pyNN-plus tiers).
        icon = "✅" if status == 200 else "❌"
        html = f"""<!DOCTYPE html>
<html><head><title>QuickUp! Login</title></head>
<body style="font-family: system-ui, sans-serif; display: flex; justify-content: center;
align-items: center; height: 100vh; margin: 0; background: #f5f5f5;">
<div style="text-align: center; padding: 2rem; background: white; border-radius: 12px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<h2>{icon} {message}</h2>
</div></body></html>"""
        self.wfile.write(html.encode())

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default request logging."""
        pass


def _exchange_code_for_token(code: str, client_id: str, client_secret: str) -> str:
    """Exchange authorization code for an access token."""
    data = json.dumps(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        }
    ).encode()

    req = Request(
        CLICKUP_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:
        result = json.loads(resp.read())

    token = result.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {result}")
    return token


def _fetch_user_info(token: str) -> dict:
    """Fetch the authenticated user's info from ClickUp."""
    req = Request(CLICKUP_USER_URL, headers={"Authorization": token})
    with urlopen(req) as resp:
        result = json.loads(resp.read())
    return result.get("user", {})


def perform_oauth_login() -> tuple[str, dict]:
    """Run the full OAuth2 login flow.

    Opens the browser for authorization, starts a local server for the callback,
    exchanges the code for an access token, and fetches user info.

    Returns:
        Tuple of (access_token, user_info dict).

    Raises:
        OAuthConfigError: If the OAuth app credentials are not configured.
        RuntimeError: If the OAuth flow fails at any step.
    """
    client_id, client_secret = get_oauth_config()
    state = secrets.token_urlsafe(32)

    auth_url = f"{CLICKUP_AUTH_URL}?client_id={client_id}&redirect_uri={_REDIRECT_URI}&state={state}"

    # Reset handler state
    _OAuthCallbackHandler.code = None
    _OAuthCallbackHandler.error = None
    _OAuthCallbackHandler.expected_state = state

    server = HTTPServer(("127.0.0.1", _CALLBACK_PORT), _OAuthCallbackHandler)
    server.timeout = _CALLBACK_TIMEOUT

    webbrowser.open(auth_url)

    # Handle a single request (blocks until callback or timeout)
    server.handle_request()
    server.server_close()

    if _OAuthCallbackHandler.error:
        raise RuntimeError(_OAuthCallbackHandler.error)

    code = _OAuthCallbackHandler.code
    if not code:
        raise RuntimeError("No authorization code received — did the login time out?")

    access_token = _exchange_code_for_token(code, client_id, client_secret)
    user_info = _fetch_user_info(access_token)

    return access_token, user_info
