#!/usr/bin/env python3
"""
config_reader.py

A tiny, self‑contained class that reads a “list_of_nodes.conf”‑style
configuration file, skips comment lines (those that start with '#')
and empty lines, and yields the remaining lines one‑by‑one.

Typical usage
-------------
    from config_reader import ConfigReader

    reader = ConfigReader("list_of_nodes.conf")
    for entry in reader:
        print(entry)               # or any custom processing

The class also offers a convenience method `as_list()` if you just want
a Python list with all valid entries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator, List
from loguru import logger

# ------------------------------------------------------------------------- #
class ConfigReader:
    """
    Read a configuration file line‑by‑line, automatically ignoring:

        * lines that are blank (after stripping whitespace)
        * lines that start with the comment character '#'

    The class implements the iterator protocol, so you can simply:

        for line in ConfigReader("my.conf"):
            ...

    If you prefer a concrete list instead of an iterator, call
    ``as_list()``.
    """

    #: default comment marker – can be overridden per instance
    COMMENT_PREFIX: str = "#"

    #------------------------------------------------------------------------- #
    def __init__(self, filename: str | Path) -> None:
        """
        Parameters
        ----------
        filename:
            Path (as a string or :class:`pathlib.Path`) of the file to read.
        """
        self.path = Path(filename)
        if not self.path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {self.path}")

    # --------------------------------------------------------------------- #
    # Helper utilities
    # --------------------------------------------------------------------- #
    @staticmethod
    def _is_comment_or_blank(line: str, comment_prefix: str = "#") -> bool:
        """
        Return ``True`` if *line* should be ignored:

        * after ``strip()`` the line is empty, or
        * it begins with *comment_prefix*.
        """
        stripped = line.strip()
        return not stripped or stripped.startswith(comment_prefix)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def __iter__(self) -> Iterator[str]:
        """
        Make the class itself an iterator over the *valid* lines.
        """
        with self.path.open("r", encoding="utf-8") as fh:
            for raw_line in fh:
                # Remove only the trailing newline – keep any other whitespace
                line = raw_line.rstrip("\n")

                if self._is_comment_or_blank(line, self.COMMENT_PREFIX):
                    continue          # skip comment / blank lines

                yield line            # <-- a line that the caller cares about

    # --------------------------------------------------------------------- #
    def as_list(self) -> List[str]:
        """
        Return a list with all non‑comment, non‑blank lines.
        """
        return list(self)          # ``self`` is iterable, re‑using __iter__

    # --------------------------------------------------------------------- #
    # Optional convenience: parsing the “node_name 'description'” format
    # --------------------------------------------------------------------- #
    @staticmethod
    def parse_entry(entry: str) -> tuple[str, str]:
        """
        Small helper that splits a line of the form::

            node_name 'description'

        into a tuple ``(node_name, description)``.
        The description may contain spaces and is allowed to be quoted
        with either single‑ or double‑quotes.

        Raises
        ------
        ValueError
            If the line cannot be parsed.
        """
        import shlex

        # shlex respects quotes, so it will correctly treat the description
        # as one token even if it contains spaces.
        parts = shlex.split(entry)
        if len(parts) != 2:
            raise ValueError(f"Unable to parse entry: {entry!r}")
        return parts[0], parts[1]


# ------------------------------------------------------------------------- #
# Example usage when the file is executed directly
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Change this path if your config lives elsewhere
    cfg = ConfigReader("config/list_of_nodes.conf")

    logger.info("=== Raw lines (no processing) ===")
    for line in cfg:
        logger.success(line)

    logger.info("\n=== Parsed as (node, description) tuples ===")
    for raw in cfg:
        try:
            node, desc = ConfigReader.parse_entry(raw)
            logger.success(f"{node!r:12} -> {desc}")
        except ValueError as exc:
            logger.error(f"⚠️  {exc}")