"""Shared local core for Tremotino.

This package owns the vault contract used by both the macOS app and the MCP
adapter. Markdown remains canonical; SQLite and JSON indexes are disposable.
"""

from .core import *  # noqa: F401,F403
