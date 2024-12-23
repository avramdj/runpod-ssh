"""RunPod SSH config manager."""

from pathlib import Path

PKG_PATH = Path(__file__).parent

with open(PKG_PATH / "VERSION", "r") as f:
    __version__ = f.read().strip()
