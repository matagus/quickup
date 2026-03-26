"""Configuration and environment loading for QuickUp! CLI."""

import dotenv

from .auth import load_oauth_token


def init_environ():
    """Load environment variables and resolve authentication token.

    Token resolution order:
    1. TOKEN from .env file (personal API token, backward compatible)
    2. OAuth token from ~/.quickup/auth.json

    Returns:
        dict: Environment variables as a dictionary.
    """
    dotenv.load_dotenv(".env")
    env = dotenv.dotenv_values()

    if not env.get("TOKEN"):
        oauth_token = load_oauth_token()
        if oauth_token:
            env["TOKEN"] = oauth_token

    return env
