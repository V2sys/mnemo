"""
mnemo/ui/overlay.py
Owner: Vedansh

CustomTkinter search bar overlay.
This runs on the MAIN thread. It acts like a Mac Spotlight search bar.
For Checkpoint 1, it just needs to open, accept text, and close.
"""

import logging
import customtkinter as ctk
from mnemo.ui.results import ResultsFrame

log = logging.getLogger(__name__)

# Set the overall theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MnemoOverlay(ctk.CTk):
    def __init__(self, on_submit=None, on_action_confirm=None):
        super().__init__()
        self.on_submit = on_submit
        self.on_action_confirm = on_action_confirm
        self.current_action_payload = None

        # --- Window Configuration ---
        self.title("Mnemo Search")
        # Keep window always on top of other apps
        self.attributes("-topmost", True)
        
        # Dimensions - slightly taller and wider for a premium feel
        self.width = 750
        self.height = 75
        
        # Center the window on the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 3) - (self.height // 2)
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

        # --- UI Elements ---
        # Deeper black for the true "floating" feel
        bg_color = "#121212"
        self.configure(fg_color=bg_color)
        
        # Main container frame
        self.frame = ctk.CTkFrame(
            self, 
            corner_radius=0, 
            fg_color=bg_color, 
            border_width=2, 
            border_color="#333333" # Soft grey border
        )
        self.frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Search bar top row
        self.search_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.search_row.pack(fill="x", expand=False, padx=0, pady=0)

        # Icon Label
        self.icon_label = ctk.CTkLabel(
            self.search_row,
            text="✨", # A spark/AI icon
            font=("Segoe UI Emoji", 26),
            text_color="#00a8ff" # A bright accent color
        )
        self.icon_label.pack(side="left", padx=(20, 5), pady=10)

        # The input text box
        self.search_input = ctk.CTkEntry(
            self.search_row, 
            placeholder_text="What would you like to recall?",
            placeholder_text_color="#666666",
            font=("Segoe UI", 24),
            fg_color="transparent",
            border_width=0,
            text_color="#ffffff"
        )
        self.search_input.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=10)
        self.search_input.focus() 

        # The results area below the search bar
        self.results_frame = ResultsFrame(self.frame)

        # --- Key & Event Bindings ---
        self.bind("<Escape>", self.hide_window)
        self.bind("<Return>", self.submit_query)
        
        # Visual Polish: Highlight the border when the user is typing
        self.search_input.bind("<FocusIn>", self.on_focus_in)
        self.search_input.bind("<FocusOut>", self.on_focus_out)

    def on_focus_in(self, event):
        """Highlight the border with an accent color when active."""
        self.frame.configure(border_color="#00a8ff") 

    def on_focus_out(self, event):
        """Restore normal border and hide when clicking away."""
        self.frame.configure(border_color="#333333")
        self.hide_window()

    def submit_query(self, event=None):
        # If we have a pending action, hitting Enter confirms it
        if self.current_action_payload:
            payload = self.current_action_payload
            self.current_action_payload = None
            if self.on_action_confirm:
                self.on_action_confirm(payload)
            self.hide_window()
            return

        query = self.search_input.get().strip()
        if query:
            print(f"\n[UI] User asked: '{query}'")
            if self.on_submit:
                import threading
                # Trigger the callback which will eventually call render_response
                threading.Thread(target=self.on_submit, args=(query,), daemon=True).start()
            
    def show_loading(self):
        """Expand the window and show the loading state."""
        self.geometry(f"{self.width}x{300}")
        self.results_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.results_frame.show_loading()
        
    def render_response(self, response):
        """Render the final answer from the query engine."""
        self.search_input.delete(0, 'end')
        self.results_frame.render(response)
        
        # If it's an action, we store it and wait for Enter to confirm
        if response.get("response_type") == "action":
            self.current_action_payload = response.get("action")

    def show_window(self):
        """Called by the hotkey listener to reveal the UI."""
        self.deiconify() 
        self.search_input.focus()

    def hide_window(self, event=None):
        """Hides the UI without destroying the thread."""
        self.withdraw() 
        self.search_input.delete(0, 'end')
        self.results_frame.pack_forget()
        self.geometry(f"{self.width}x{75}")
        self.current_action_payload = None

if __name__ == "__main__":
    print("Starting UI on main thread. Press 'Escape' to hide it.")
    try:
        app = MnemoOverlay()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nUI closed via terminal.")
