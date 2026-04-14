#!/usr/bin/env python3

"""Helpers for preparing the desktop environment before Qt starts."""

from pathlib import Path
import os

_NULL_LIKE_VALUES = {"", "(null)", "null", "None"}
_DEFAULT_FONTCONFIG_FILE = Path("/etc/fonts/fonts.conf")
_DEFAULT_FONTCONFIG_PATH = _DEFAULT_FONTCONFIG_FILE.parent


def _is_invalid_path(value: str | None, *, expect_dir: bool = False) -> bool:
    """Return True when an environment variable is empty, null-like, or missing on disk."""
    if value is None:
        return True

    cleaned = value.strip()
    if cleaned in _NULL_LIKE_VALUES:
        return True

    path = Path(cleaned).expanduser()
    return not (path.is_dir() if expect_dir else path.is_file())


def ensure_gui_environment() -> None:
    """Normalize GUI-related environment variables for Qt on Linux."""
    home_dir = os.environ.get("HOME", "").strip()
    if home_dir in _NULL_LIKE_VALUES:
        os.environ["HOME"] = str(Path.home())

    if _is_invalid_path(os.environ.get("FONTCONFIG_FILE")):
        if _DEFAULT_FONTCONFIG_FILE.is_file():
            os.environ["FONTCONFIG_FILE"] = str(_DEFAULT_FONTCONFIG_FILE)
        else:
            os.environ.pop("FONTCONFIG_FILE", None)

    if _is_invalid_path(os.environ.get("FONTCONFIG_PATH"), expect_dir=True):
        if _DEFAULT_FONTCONFIG_PATH.is_dir():
            os.environ["FONTCONFIG_PATH"] = str(_DEFAULT_FONTCONFIG_PATH)
        else:
            os.environ.pop("FONTCONFIG_PATH", None)
