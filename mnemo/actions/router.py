"""
mnemo/actions/router.py
Owner: Vedansh

Execute system actions parsed by the query engine.
Each handler is small and safe — no shell execution of arbitrary strings.
"""

import logging
import os
import subprocess
from pathlib import Path

from mnemo.schema import ActionPayload, ACTION_TYPES

log = logging.getLogger(__name__)


class ActionRouter:
    def execute(self, action: ActionPayload) -> bool:
        """Dispatch the action. Returns True on success."""
        # TODO(week 4):
        # match on action["type"]:
        #   file_open  → self._open_file(action["target"])
        #   app_launch → self._launch_app(action["target"])
        #   system_command → self._system_command(action["target"])
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def _open_file(self, path: str) -> bool:
        """Open a file with its default Windows app."""
        # TODO(week 4):
        # os.startfile(path)
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def _launch_app(self, app_name: str) -> bool:
        """Launch a known application by name (notepad, code, chrome, etc.)."""
        # TODO(week 4):
        # Keep a small allowlist mapping name → executable path
        # Reject anything outside the allowlist for safety
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def _system_command(self, command: str) -> bool:
        """Execute a system command from a strict allowlist."""
        # TODO(week 4):
        # Examples: "lock screen", "sleep", "open settings"
        # NEVER call shell=True with arbitrary input
        raise NotImplementedError("Vedansh — week 4 deliverable")
