"""
Main GUI Application

Entry point for the Sambuca Core GUI application.
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from .views.main_window import MainWindow


class SambucaGuiApp:
    """Main GUI application class for Sambuca Core."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sambuca Core - Bathymetry Processing GUI")
        self.root.geometry("1000x700")
        
        # Set up styling
        self._setup_styling()
        
        # Initialize main window
        self.main_window = MainWindow(self.root)
        
    def _setup_styling(self):
        """Configure the GUI theme and styling."""
        style = ttk.Style()
        
        # Use a modern theme if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
            
    def run(self):
        """Start the GUI application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()


def main():
    """Main entry point for the GUI."""
    app = SambucaGuiApp()
    app.run()


if __name__ == "__main__":
    main()
