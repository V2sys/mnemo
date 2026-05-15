"""
mnemo/ui/overlay.py
Owner: Vedansh

Spotlight-style search overlay using CustomTkinter.
Runs on the main thread (Tkinter requirement).

Lifecycle:
  - hidden by default
  - hotkey fires → show()
  - user types → on Enter, call query_engine.handle()
  - display results → user clicks one or presses Esc → hide()
"""

import logging
import customtkinter as ctk

from mnemo.ai.query_engine import QueryEngine
from mnemo.actions.router import ActionRouter
from mnemo.schema import QueryRequest, TOP_K_DEFAULT

log = logging.getLogger(__name__)


class OverlayUI:
    def __init__(
        self,
        query_engine: QueryEngine,
        action_router: ActionRouter,
    ) -> None:
        self.query_engine = query_engine
        self.action_router = action_router
        self.root: ctk.CTk | None = None
        self._visible = False

    def build(self) -> None:
        """Construct the Tk window. Call once on main thread before run_main_loop."""
        # TODO(week 4):
        # ctk.set_appearance_mode("dark")
        # ctk.set_default_color_theme("blue")
        # self.root = ctk.CTk()
        # self.root.overrideredirect(True)              # frameless
        # self.root.attributes("-topmost", True)
        # self.root.attributes("-alpha", 0.95)
        # Center on screen, ~600x80 for search bar
        # Add entry widget, bind <Return>, <Escape>, <FocusOut>
        # Add result frame below entry, initially hidden
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def show(self) -> None:
        """Show the overlay and focus the search field."""
        # TODO(week 4): called from hotkey thread via root.after(0, ...)
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def hide(self) -> None:
        # TODO(week 4)
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def _on_submit(self, query: str) -> None:
        """User pressed Enter. Run query in background, render result."""
        # TODO(week 4):
        # Run query_engine.handle on the inference_pool, not the UI thread.
        # On result, use root.after(0, self._render) to come back to UI thread.
        # If response.action is set, call self.action_router.execute(...)
        raise NotImplementedError("Vedansh — week 4 deliverable")

    def run_main_loop(self) -> None:
        """Block here; Tkinter event loop. Call last in main()."""
        if self.root:
            self.root.mainloop()

    def shutdown(self) -> None:
        if self.root:
            self.root.quit()
