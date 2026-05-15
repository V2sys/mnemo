"""
mnemo/ui/results.py
Owner: Vedansh

Renders QueryResponse into the overlay.
Handles: answer text, source chips, low-confidence styling, action confirmations.
"""

import logging
import customtkinter as ctk

from mnemo.schema import QueryResponse

log = logging.getLogger(__name__)


class ResultsFrame(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        # TODO(week 4):
        # Layout: answer text (large), then a row of source chips (small)
        # Low confidence → grey out + show "Closest I found — low confidence" label
        # Action response → show "Press Enter to run: {target}" prompt

    def render(self, response: QueryResponse) -> None:
        """Update the frame to show the given response."""
        # TODO(week 4):
        # Clear previous content
        # Switch rendering based on response_type
        raise NotImplementedError("Vedansh — week 4 deliverable")
