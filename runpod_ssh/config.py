import os
import stat
import platform
from netrc import netrc, NetrcParseError
from typing import Final
from urllib.parse import urlparse

# Define netrc file locations based on platform
_netrc_paths = [os.path.expanduser('~/netrc'), os.path.expanduser('~/_netrc')] if platform.system() == 'Windows' else [os.path.expanduser('~/.netrc')]
NETRC_FILES: Final[list[str]] = _netrc_paths

NETRC_HOST: Final = "api.runpod.io"


def get_netrc_path() -> str:
    """Return the path to the netrc file."""
    netrc_file = os.environ.get("NETRC")
    if netrc_file:
        return os.path.expanduser(netrc_file)

    for netrc_file in NETRC_FILES:
        home_dir = os.path.expanduser("~")
        if os.path.exists(os.path.join(home_dir, netrc_file)):
            return os.path.join(home_dir, netrc_file)

    netrc_file = ".netrc" if platform.system() != "Windows" else "_netrc"
    return os.path.join(os.path.expanduser("~"), netrc_file)


def get_api_key() -> str | None:
    try:
        auth = netrc().authenticators(NETRC_HOST)
        return auth[2] if auth else None
    except (FileNotFoundError, NetrcParseError):
        return None


def save_api_key(api_key: str) -> None:
    netrc_path = get_netrc_path()
    normalized_host = urlparse(NETRC_HOST).netloc.split(":")[0] or NETRC_HOST
    machine_line = f"machine {normalized_host}"

    orig_lines = None
    try:
        with open(netrc_path) as f:
            orig_lines = f.read().strip().split("\n")
    except OSError:
        pass

    with open(netrc_path, "w") as f:
        if orig_lines:
            skip = 0
            for line in orig_lines:
                if line == "machine " or machine_line in line:
                    skip = 2
                elif skip:
                    skip -= 1
                else:
                    f.write(f"{line}\n")

        # Write the new machine entry
        f.write(f"machine {normalized_host}\n")
        f.write("  login user\n")
        f.write(f"  password {api_key}\n")

    if os.name != "nt":
        os.chmod(netrc_path, stat.S_IRUSR | stat.S_IWUSR)
