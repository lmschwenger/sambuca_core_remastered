"""
Progress Dialog Component

A reusable progress dialog for long-running operations.
"""

import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """A modal progress dialog with progress bar and status text."""

    def __init__(self, parent, title="Processing", message="Please wait..."):
        self.parent = parent
        self.dialog = None
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value=message)
        self.cancelled = False

        self._create_dialog(title)

    def _create_dialog(self, title):
        """Create the progress dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)

        # Center on parent
        self._center_dialog()

        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Prevent closing with X button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Status label
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            length=300,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(0, 15))

        # Cancel button
        self.cancel_button = ttk.Button(main_frame, text="Cancel", command=self._on_cancel)
        self.cancel_button.pack()

    def _center_dialog(self):
        """Center the dialog on its parent window."""
        self.dialog.update_idletasks()

        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get dialog size
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _on_cancel(self):
        """Handle cancel button or window close."""
        self.cancelled = True
        self.close()

    def update_progress(self, value, status=None):
        """Update progress bar and optional status message."""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.dialog.update_idletasks()

    def set_status(self, status):
        """Update only the status message."""
        self.status_var.set(status)
        self.dialog.update_idletasks()

    def show(self):
        """Show the dialog."""
        if self.dialog:
            self.dialog.deiconify()
            self.dialog.lift()

    def hide(self):
        """Hide the dialog without closing it."""
        if self.dialog:
            self.dialog.withdraw()

    def close(self):
        """Close and destroy the dialog."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None

    def is_cancelled(self):
        """Check if the operation was cancelled."""
        return self.cancelled
