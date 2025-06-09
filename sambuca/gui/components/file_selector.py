"""
File Selector Component

A reusable file and directory selection component with validation.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog
from typing import Optional, List, Tuple, Callable


class FileSelector:
    """A reusable file/directory selector with validation and recent paths."""

    def __init__(self, parent, label_text: str, selector_type: str = "file",
                 file_types: Optional[List[Tuple[str, str]]] = None,
                 validation_callback: Optional[Callable] = None):
        """
        Initialize file selector.
        
        Args:
            parent: Parent widget
            label_text: Text for the label
            selector_type: "file", "directory", or "save_file"
            file_types: List of (description, pattern) tuples for file dialogs
            validation_callback: Optional callback to validate selected path
        """
        self.parent = parent
        self.label_text = label_text
        self.selector_type = selector_type
        self.file_types = file_types or [("All files", "*.*")]
        self.validation_callback = validation_callback

        self.path_var = tk.StringVar()
        self.path_var.trace('w', self._on_path_changed)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the file selector UI."""
        # Main frame
        self.frame = ttk.Frame(self.parent)

        # Label
        self.label = ttk.Label(self.frame, text=self.label_text)
        self.label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        # Entry widget
        self.entry = ttk.Entry(self.frame, textvariable=self.path_var)
        self.entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # Browse button
        self.browse_button = ttk.Button(self.frame, text="Browse",
                                        command=self._browse)
        self.browse_button.grid(row=0, column=2)

        # Configure grid weights
        self.frame.columnconfigure(1, weight=1)

    def _browse(self):
        """Open file/directory browser dialog."""
        current_path = self.path_var.get()
        initial_dir = str(Path(current_path).parent) if current_path else None

        if self.selector_type == "file":
            path = filedialog.askopenfilename(
                title=f"Select {self.label_text}",
                filetypes=self.file_types,
                initialdir=initial_dir
            )
        elif self.selector_type == "save_file":
            path = filedialog.asksaveasfilename(
                title=f"Save {self.label_text}",
                filetypes=self.file_types,
                initialdir=initial_dir
            )
        else:  # directory
            path = filedialog.askdirectory(
                title=f"Select {self.label_text}",
                initialdir=initial_dir
            )

        if path:
            self.path_var.set(path)

    def _on_path_changed(self, *args):
        """Handle path changes for validation."""
        if self.validation_callback:
            try:
                is_valid = self.validation_callback(self.path_var.get())
                self._update_validation_state(is_valid)
            except Exception:
                self._update_validation_state(False)

    def _update_validation_state(self, is_valid: bool):
        """Update UI based on validation state."""
        if is_valid:
            self.entry.configure(style="")
        else:
            # You could add a custom style for invalid entries
            pass

    def get_path(self) -> str:
        """Get the current path."""
        return self.path_var.get()

    def set_path(self, path: str):
        """Set the current path."""
        self.path_var.set(path)

    def is_valid(self) -> bool:
        """Check if current path is valid."""
        path = self.get_path()
        if not path:
            return False

        path_obj = Path(path)

        if self.selector_type == "directory":
            return path_obj.exists() and path_obj.is_dir()
        elif self.selector_type == "file":
            return path_obj.exists() and path_obj.is_file()
        else:  # save_file
            return path_obj.parent.exists()

    def grid(self, **kwargs):
        """Grid the file selector frame."""
        self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        """Pack the file selector frame."""
        self.frame.pack(**kwargs)

    def place(self, **kwargs):
        """Place the file selector frame."""
        self.frame.place(**kwargs)
