import os
from pathlib import Path
from typing import Final
from platformdirs import user_config_dir
from dotenv import load_dotenv

# Load .env file if it exists (for development)
load_dotenv()

APP_NAME: Final = "runpod-ssh"
CONFIG_DIR: Final = Path(user_config_dir(APP_NAME))
CREDENTIALS_FILE: Final = CONFIG_DIR / "credentials"


def get_api_key() -> str | None:
    """Get API key from environment or config file."""
    # First try environment variable
    api_key = os.getenv("RUNPOD_API_KEY")
    if api_key:
        return api_key

    # Then try config file
    if CREDENTIALS_FILE.exists():
        return CREDENTIALS_FILE.read_text().strip()

    return None


def save_api_key(api_key: str) -> None:
    """Save API key to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(api_key)
