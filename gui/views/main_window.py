"""
Main Window View

The primary window interface for the Sambuca Core GUI.
"""

import tkinter as tk
from tkinter import ttk

from ..controllers.workflow_controller import WorkflowController
from .workflow_panel import WorkflowPanel
from .results_panel import ResultsPanel
from .parameters_panel import ParametersPanel


class MainWindow:
    """Main window view for the Sambuca Core GUI."""
    
    def __init__(self, root):
        self.root = root
        self.controller = WorkflowController()
        
        self._setup_layout()
        self._setup_panels()
        
    def _setup_layout(self):
        """Set up the main window layout."""
        # Create main container with padding
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
    def _setup_panels(self):
        """Set up the main GUI panels."""
        # Left panel for workflow and parameters
        left_frame = ttk.Frame(self.main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Right panel for results
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Create panels
        self.workflow_panel = WorkflowPanel(left_frame, self.controller)
        self.parameters_panel = ParametersPanel(left_frame, self.controller)
        self.results_panel = ResultsPanel(right_frame, self.controller)
        
        # Connect panels for communication
        self.workflow_panel.set_parameters_panel(self.parameters_panel)
        
        # Position panels
        self.workflow_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        self.parameters_panel.frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        self.results_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure weights
        left_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
