"""Tests for QuickUp! OAuth authentication module."""

from io import BytesIO
import json
import sys
from typing import cast
from unittest.mock import Mock, patch

import pytest

from quickup.cli.auth import (
    _exchange_code_for_token,
    _fetch_user_info,
    _OAuthCallbackHandler,
    delete_oauth_token,
    get_oauth_config,
    load_oauth_token,
    perform_oauth_login,
    save_oauth_token,
)
from quickup.cli.config import init_environ


class TestTokenStorage:
    """Tests for OAuth token file read/write/delete."""

    def test_save_and_load_token(self, tmp_path, monkeypatch):
        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", auth_file)
        monkeypatch.setattr("quickup.cli.auth.AUTH_DIR", tmp_path)

        save_oauth_token("test-token-123", {"username": "alice", "email": "a@b.com"})

        assert auth_file.exists()
        data = json.loads(auth_file.read_text())
        assert data["access_token"] == "test-token-123"
        assert data["user"]["username"] == "alice"

        token = load_oauth_token()
        assert token == "test-token-123"

    def test_load_token_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", tmp_path / "nonexistent.json")
        assert load_oauth_token() is None

    def test_load_token_invalid_json(self, tmp_path, monkeypatch):
        auth_file = tmp_path / "auth.json"
        auth_file.write_text("not json")
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", auth_file)
        assert load_oauth_token() is None

    def test_save_token_without_user_info(self, tmp_path, monkeypatch):
        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", auth_file)
        monkeypatch.setattr("quickup.cli.auth.AUTH_DIR", tmp_path)

        save_oauth_token("token-only")
        data = json.loads(auth_file.read_text())
        assert data["access_token"] == "token-only"
        assert "user" not in data

    def test_delete_token_exists(self, tmp_path, monkeypatch):
        auth_file = tmp_path / "auth.json"
        auth_file.write_text('{"access_token": "x"}')
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", auth_file)

        assert delete_oauth_token() is True
        assert not auth_file.exists()

    def test_delete_token_not_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", tmp_path / "nonexistent.json")
        assert delete_oauth_token() is False

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows does not support Unix file permissions")
    def test_save_token_file_permissions(self, tmp_path, monkeypatch):
        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("quickup.cli.auth.AUTH_FILE", auth_file)
        monkeypatch.setattr("quickup.cli.auth.AUTH_DIR", tmp_path)

        save_oauth_token("secret-token")
        stat = auth_file.stat()
        assert stat.st_mode & 0o777 == 0o600


class TestOAuthConfig:
    """Tests for OAuth client config resolution."""

    def test_default_config(self):
        config = get_oauth_config()
        assert len(config) == 2
        assert isinstance(config[0], str)
        assert isinstance(config[1], str)

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv("QUICKUP_CLIENT_ID", "my-id")
        monkeypatch.setenv("QUICKUP_CLIENT_SECRET", "my-secret")
        client_id, client_secret = get_oauth_config()
        assert client_id == "my-id"
        assert client_secret == "my-secret"


class TestCallbackHandler:
    """Tests for the OAuth callback HTTP handler."""

    def _make_handler(self, path: str, expected_state: str = "test-state"):
        _OAuthCallbackHandler.code = None
        _OAuthCallbackHandler.error = None
        _OAuthCallbackHandler.expected_state = expected_state

        # Create a real instance without calling __init__ (which needs a socket)
        handler = _OAuthCallbackHandler.__new__(_OAuthCallbackHandler)
        handler.path = path
        handler.wfile = BytesIO()
        send_response_mock = Mock()
        handler.send_response = send_response_mock  # type: ignore[method-assign]
        handler.send_header = Mock()  # type: ignore[method-assign]
        handler.end_headers = Mock()  # type: ignore[method-assign]

        return handler

    def test_valid_callback(self):
        handler = self._make_handler("/callback?code=abc123&state=test-state")
        send_response_mock = cast(Mock, handler.send_response)
        handler.do_GET()
        assert _OAuthCallbackHandler.code == "abc123"
        assert _OAuthCallbackHandler.error is None
        send_response_mock.assert_called_with(200)

    def test_state_mismatch(self):
        handler = self._make_handler("/callback?code=abc123&state=wrong-state")
        send_response_mock = cast(Mock, handler.send_response)
        handler.do_GET()
        assert _OAuthCallbackHandler.code is None
        assert _OAuthCallbackHandler.error is not None
        send_response_mock.assert_called_with(400)

    def test_missing_code(self):
        handler = self._make_handler("/callback?state=test-state")
        send_response_mock = cast(Mock, handler.send_response)
        handler.do_GET()
        assert _OAuthCallbackHandler.code is None
        assert _OAuthCallbackHandler.error is not None
        send_response_mock.assert_called_with(400)

    def test_error_from_clickup(self):
        handler = self._make_handler("/callback?error=access_denied&error_description=User+denied&state=test-state")
        handler.do_GET()
        assert _OAuthCallbackHandler.code is None
        assert _OAuthCallbackHandler.error is not None
        assert "User denied" in _OAuthCallbackHandler.error


class TestExchangeCodeForToken:
    """Tests for the token exchange HTTP call."""

    @patch("quickup.cli.auth.urlopen")
    def test_successful_exchange(self, mock_urlopen):
        mock_resp = Mock()
        mock_resp.read.return_value = json.dumps({"access_token": "tok_123"}).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        token = _exchange_code_for_token("code123", "cid", "csecret")
        assert token == "tok_123"

    @patch("quickup.cli.auth.urlopen")
    def test_missing_token_in_response(self, mock_urlopen):
        mock_resp = Mock()
        mock_resp.read.return_value = json.dumps({"error": "bad"}).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with pytest.raises(RuntimeError, match="No access_token"):
            _exchange_code_for_token("code123", "cid", "csecret")


class TestFetchUserInfo:
    """Tests for fetching user info."""

    @patch("quickup.cli.auth.urlopen")
    def test_successful_fetch(self, mock_urlopen):
        mock_resp = Mock()
        mock_resp.read.return_value = json.dumps({"user": {"username": "alice", "email": "a@b.com"}}).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        info = _fetch_user_info("tok_123")
        assert info["username"] == "alice"


class TestPerformOAuthLogin:
    """Tests for the full OAuth login flow."""

    @patch("quickup.cli.auth._fetch_user_info")
    @patch("quickup.cli.auth._exchange_code_for_token")
    @patch("quickup.cli.auth.webbrowser.open")
    @patch("quickup.cli.auth.HTTPServer")
    def test_successful_login(self, mock_server_cls, mock_browser, mock_exchange, mock_user_info):
        # Simulate the callback setting the code
        def fake_handle_request():
            _OAuthCallbackHandler.code = "auth-code-xyz"

        mock_server = Mock()
        mock_server.handle_request.side_effect = fake_handle_request
        mock_server_cls.return_value = mock_server

        mock_exchange.return_value = "access-token-abc"
        mock_user_info.return_value = {"username": "bob", "email": "b@c.com"}

        token, user_info = perform_oauth_login()

        assert token == "access-token-abc"
        assert user_info["username"] == "bob"
        mock_browser.assert_called_once()
        mock_exchange.assert_called_once()
        mock_server.server_close.assert_called_once()

    @patch("quickup.cli.auth.webbrowser.open")
    @patch("quickup.cli.auth.HTTPServer")
    def test_login_timeout(self, mock_server_cls, mock_browser):
        mock_server = Mock()
        # Simulate timeout — code stays None
        mock_server.handle_request.return_value = None
        mock_server_cls.return_value = mock_server

        _OAuthCallbackHandler.code = None
        _OAuthCallbackHandler.error = None

        with pytest.raises(RuntimeError, match="No authorization code"):
            perform_oauth_login()


class TestInitEnvironOAuthFallback:
    """Tests for token resolution order in init_environ."""

    @patch("dotenv.load_dotenv")
    @patch("dotenv.dotenv_values")
    def test_env_token_takes_precedence(self, mock_values, mock_load):
        mock_values.return_value = {"TOKEN": "env-token"}
        result = init_environ()
        assert result["TOKEN"] == "env-token"

    @patch("quickup.cli.config.load_oauth_token", return_value="oauth-token")
    @patch("dotenv.load_dotenv")
    @patch("dotenv.dotenv_values")
    def test_oauth_fallback_when_no_env_token(self, mock_values, mock_load, mock_oauth):
        mock_values.return_value = {}
        result = init_environ()
        assert result["TOKEN"] == "oauth-token"

    @patch("quickup.cli.config.load_oauth_token", return_value=None)
    @patch("dotenv.load_dotenv")
    @patch("dotenv.dotenv_values")
    def test_no_token_at_all(self, mock_values, mock_load, mock_oauth):
        mock_values.return_value = {}
        result = init_environ()
        assert result.get("TOKEN") is None
