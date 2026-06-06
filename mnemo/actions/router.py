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

from mnemo.schema import ActionPayload

log = logging.getLogger(__name__)


class ActionRouter:
    def __init__(self):
        self._dynamic_app_map = self._build_start_menu_map()

    def _build_start_menu_map(self) -> dict[str, str]:
        """Scans the Start Menu and builds a safe map of App Name -> Shortcut Path."""
        app_map = {}
        try:
            # The two main locations for Windows Start Menu shortcuts
            common_start_menu = Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            user_start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            
            for start_menu in [common_start_menu, user_start_menu]:
                if not start_menu.exists():
                    continue
                    
                for lnk_path in start_menu.rglob("*.lnk"):
                    # e.g. "Google Chrome.lnk" -> "google chrome"
                    app_name = lnk_path.stem.lower()
                    app_map[app_name] = str(lnk_path)
                    
            log.info(f"Built dynamic app launcher map with {len(app_map)} applications.")
        except Exception as e:
            log.warning(f"Failed to build dynamic start menu map: {e}")
            
        return app_map

    def execute(self, action: ActionPayload) -> bool:
        """Dispatch the action. Returns True on success."""
        try:
            action_type = action.get("type")
            target = action.get("target", "")
            
            log.info(f"Routing action: {action_type} on '{target}'")
            if action_type == "file_open":
                return self._open_file(target)
            elif action_type == "app_launch":
                return self._launch_app(target)
            elif action_type == "system_command":
                return self._system_command(target)
            else:
                log.warning(f"Unknown action type: {action_type}")
                return False
        except Exception as e:
            log.error(f"Action execution failed: {e}")
            return False

    def _open_file(self, path: str) -> bool:
        """Open a file with its default Windows app."""
        # Note: os.startfile is Windows-only, which matches the project requirements.
        # Ensure we only try if there's actually a path
        if not path:
            return False
        os.startfile(path)
        return True

    def _launch_app(self, app_name: str) -> bool:
        """Launch an application using the dynamic Start Menu map or strict fallbacks."""
        # 1. Check our dynamically built map of Start Menu shortcuts
        lnk_path = self._dynamic_app_map.get(app_name.lower())
        if lnk_path:
            os.startfile(lnk_path)
            return True
            
        # 2. Fallback to strict allowlist for system apps that might not have a clean shortcut
        allowlist = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe"
        }
        exe = allowlist.get(app_name.lower())
        if exe:
            os.startfile(exe)
            return True
        
        log.warning(f"App '{app_name}' not found in Start Menu or strict allowlist.")
        return False

    def _system_command(self, command: str) -> bool:
        """Execute a system command from a strict allowlist."""
        # Special case for opening command prompt if Phi-3 misclassifies it
        if "cmd" in command.lower() or "command prompt" in command.lower():
            os.startfile("cmd.exe")
            return True
            
        # Strict allowlist to prevent arbitrary shell execution (security requirement)
        allowlist = {
            "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
            "lock screen": ["rundll32.exe", "user32.dll,LockWorkStation"],
            "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
        }
        cmd_args = allowlist.get(command.lower())
        if cmd_args:
            subprocess.Popen(cmd_args, shell=False)
            return True
            
        log.warning(f"System command '{command}' not in strict allowlist.")
        return False
