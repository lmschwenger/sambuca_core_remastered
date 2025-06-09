"""
Workflow Panel View

Panel for configuring and running bathymetry workflows.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox


class WorkflowPanel:
    """Panel for workflow configuration and execution."""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.parameters_panel = None  # Will be set by main window

        self._setup_ui()
        self._setup_bindings()

    def _setup_ui(self):
        """Set up the workflow panel UI."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Workflow Configuration", padding="10")

        # File selection section
        file_frame = ttk.Frame(self.frame)
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        # SIOP Directory
        ttk.Label(file_frame, text="SIOP Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.siop_dir_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.siop_dir_var, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_siop_dir).grid(
            row=0, column=2, pady=2
        )

        # Input Image
        ttk.Label(file_frame, text="Input Image:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.image_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.image_path_var, state="readonly").grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_image).grid(
            row=1, column=2, pady=2
        )

        # Output Directory
        ttk.Label(file_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.output_dir_var, state="readonly").grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_output_dir).grid(
            row=2, column=2, pady=2
        )

        # Processing options
        options_frame = ttk.Frame(self.frame)
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        # Sensor selection
        ttk.Label(options_frame, text="Sensor:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sensor_var = tk.StringVar(value="sentinel2")
        sensor_combo = ttk.Combobox(options_frame, textvariable=self.sensor_var,
                                    values=["sentinel2", "landsat8"], state="readonly")
        sensor_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        sensor_combo.bind('<<ComboboxSelected>>', self._on_sensor_changed)

        # Processing method
        ttk.Label(options_frame, text="Method:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.method_var = tk.StringVar(value="optimization")
        method_combo = ttk.Combobox(options_frame, textvariable=self.method_var,
                                    values=["optimization", "lut"], state="readonly")
        method_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)

        # Number of processes
        ttk.Label(options_frame, text="Processes:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.n_processes_var = tk.IntVar(value=4)
        processes_spin = ttk.Spinbox(options_frame, from_=1, to=16,
                                     textvariable=self.n_processes_var, width=10)
        processes_spin.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        # Action buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

        self.process_button = ttk.Button(button_frame, text="Process Image",
                                         command=self._process_image, style="Accent.TButton")
        self.process_button.grid(row=0, column=0, pady=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(button_frame, variable=self.progress_var,
                                            length=200, mode='determinate')
        self.progress_bar.grid(row=0, column=1, padx=(10, 0), pady=5)

    def _setup_bindings(self):
        """Set up event bindings."""
        # Set default paths if they exist
        default_siop = Path("../data/siops")
        if default_siop.exists():
            self.siop_dir_var.set(str(default_siop.resolve()))

    def _browse_siop_dir(self):
        """Browse for SIOP directory."""
        directory = filedialog.askdirectory(title="Select SIOP Directory")
        if directory:
            self.siop_dir_var.set(directory)

    def _browse_image(self):
        """Browse for input image file."""
        filename = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[
                ("TIFF files", "*.tif *.tiff"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.image_path_var.set(filename)

    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def _validate_inputs(self):
        """Validate user inputs before processing."""
        if not self.siop_dir_var.get():
            messagebox.showerror("Error", "Please select a SIOP directory")
            return False

        if not self.image_path_var.get():
            messagebox.showerror("Error", "Please select an input image")
            return False

        if not self.output_dir_var.get():
            messagebox.showerror("Error", "Please select an output directory")
            return False

        # Check if paths exist
        if not Path(self.siop_dir_var.get()).exists():
            messagebox.showerror("Error", "SIOP directory does not exist")
            return False

        if not Path(self.image_path_var.get()).exists():
            messagebox.showerror("Error", "Input image does not exist")
            return False

        return True

    def _process_image(self):
        """Process the selected image."""
        if not self._validate_inputs():
            return

        # Disable the process button during processing
        self.process_button.config(state="disabled")
        self.progress_var.set(0)

        try:
            # Prepare parameters
            params = {
                'siop_dir': self.siop_dir_var.get(),
                'image_path': self.image_path_var.get(),
                'output_dir': self.output_dir_var.get(),
                'sensor': self.sensor_var.get(),
                'method': self.method_var.get(),
                'n_processes': self.n_processes_var.get()
            }

            # Start processing (this will be handled by the controller)
            self.controller.process_image(params, self._on_progress, self._on_complete)

        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            self.process_button.config(state="normal")

    def _on_progress(self, progress):
        """Handle progress updates."""
        self.progress_var.set(progress)
        self.parent.update_idletasks()

    def _on_complete(self, success, message):
        """Handle processing completion."""
        self.process_button.config(state="normal")
        self.progress_var.set(100 if success else 0)

        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def _on_sensor_changed(self, event):
        """Handle sensor selection change."""
        if self.parameters_panel:
            self.parameters_panel.update_sensor_selection(self.sensor_var.get())

    def set_parameters_panel(self, parameters_panel):
        """Set reference to parameters panel for sensor updates."""
        self.parameters_panel = parameters_panel
