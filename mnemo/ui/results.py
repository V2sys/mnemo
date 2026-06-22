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
        super().__init__(parent, fg_color="transparent")
        
        # Loading label
        self.loading_label = ctk.CTkLabel(
            self, text="Thinking...", font=("Segoe UI", 16, "italic"), text_color="#aaaaaa"
        )
        
        # Answer text
        self.text_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 18), 
            text_color="white", justify="left", wraplength=700
        )
        
        # Confidence label
        self.confidence_label = ctk.CTkLabel(
            self, text="Closest I found — low confidence", font=("Segoe UI", 12, "italic"), text_color="#aaaaaa"
        )
        
        # Source chips container
        self.sources_frame = ctk.CTkFrame(self, fg_color="transparent")

    def show_loading(self) -> None:
        """Display a loading state."""
        self._clear()
        self.loading_label.pack(anchor="w", padx=20, pady=20)

    def render(self, response: QueryResponse) -> None:
        """Update the frame to show the given response."""
        self._clear()
        
        if response["response_type"] == "action":
            action = response.get("action", {})
            target = action.get("target", "unknown")
            
            self.text_label.configure(
                text=f"Press Enter to run: {target}", 
                text_color="#00a8ff",
                font=("Segoe UI", 20, "bold")
            )
            self.text_label.pack(anchor="w", padx=20, pady=20)
            
        else:
            # Regular answer
            self.text_label.configure(text=response["text"], font=("Segoe UI", 18))
            
            # Low confidence styling
            if response.get("confidence") == "low":
                self.text_label.configure(text_color="#888888")
                self.text_label.pack(anchor="w", padx=20, pady=(10, 0))
                self.confidence_label.pack(anchor="w", padx=20, pady=(0, 10))
            else:
                self.text_label.configure(text_color="white")
                self.text_label.pack(anchor="w", padx=20, pady=10)
                
            # Render source chips
            sources = response.get("sources", [])
            if sources:
                self.sources_frame.pack(fill="x", padx=20, pady=(5, 10))
                for i, src in enumerate(sources):
                    src_type = src.get("type", "unknown").upper()
                    src_name = src.get("source", "Unknown")
                    
                    chip = ctk.CTkLabel(
                        self.sources_frame, 
                        text=f"[{i+1}] {src_type}: {src_name}",
                        font=("Segoe UI", 11), 
                        fg_color="#333333", 
                        corner_radius=4, 
                        padx=8, 
                        pady=4
                    )
                    chip.pack(side="left", padx=(0, 8))

    def _clear(self) -> None:
        """Clear all widgets from view."""
        self.loading_label.pack_forget()
        self.text_label.pack_forget()
        self.confidence_label.pack_forget()
        self.sources_frame.pack_forget()
        
        for widget in self.sources_frame.winfo_children():
            widget.destroy()
