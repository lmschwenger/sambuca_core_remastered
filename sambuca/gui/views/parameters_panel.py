"""
Parameters Panel View

Panel for configuring bathymetry processing parameters.
"""

import tkinter as tk
from tkinter import ttk


class ParametersPanel:
    """Panel for parameter configuration."""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        self._setup_ui()
        self._setup_sensor_definitions()
        self._load_default_parameters()

    def _setup_ui(self):
        """Set up the parameters panel UI."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Processing Parameters", padding="10")

        # Create notebook for parameter categories
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Physical parameters tab
        self._create_physical_params_tab()

        # Sensor parameters tab
        self._create_sensor_params_tab()

        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

    def _create_physical_params_tab(self):
        """Create the physical parameters tab."""
        physical_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(physical_frame, text="Physical")

        # Depth range
        depth_frame = ttk.LabelFrame(physical_frame, text="Depth Range (m)", padding="5")
        depth_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        depth_frame.columnconfigure(1, weight=1)

        ttk.Label(depth_frame, text="Min:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.depth_min_var = tk.DoubleVar(value=0.0)
        ttk.Entry(depth_frame, textvariable=self.depth_min_var, width=10).grid(
            row=0, column=1, sticky=tk.W, pady=2
        )

        ttk.Label(depth_frame, text="Max:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.depth_max_var = tk.DoubleVar(value=25.0)
        ttk.Entry(depth_frame, textvariable=self.depth_max_var, width=10).grid(
            row=1, column=1, sticky=tk.W, pady=2
        )

        # Water column parameters
        water_frame = ttk.LabelFrame(physical_frame, text="Water Column", padding="5")
        water_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        water_frame.columnconfigure(1, weight=1)

        ttk.Label(water_frame, text="Chlorophyll:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.chl_var = tk.DoubleVar(value=0.5)
        ttk.Entry(water_frame, textvariable=self.chl_var, width=10).grid(
            row=0, column=1, sticky=tk.W, pady=2
        )

        ttk.Label(water_frame, text="NAP:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.nap_var = tk.DoubleVar(value=0.001)
        ttk.Entry(water_frame, textvariable=self.nap_var, width=10).grid(
            row=1, column=1, sticky=tk.W, pady=2
        )

        ttk.Label(water_frame, text="CDOM:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.cdom_var = tk.DoubleVar(value=0.0025)
        ttk.Entry(water_frame, textvariable=self.cdom_var, width=10).grid(
            row=2, column=1, sticky=tk.W, pady=2
        )

        # Substrate parameters
        substrate_frame = ttk.LabelFrame(physical_frame, text="Substrate", padding="5")
        substrate_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        substrate_frame.columnconfigure(1, weight=1)

        ttk.Label(substrate_frame, text="Substrate Fraction:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.substrate_var = tk.DoubleVar(value=1.0)
        ttk.Entry(substrate_frame, textvariable=self.substrate_var, width=10).grid(
            row=0, column=1, sticky=tk.W, pady=2
        )

    def _create_sensor_params_tab(self):
        """Create the sensor parameters tab."""
        sensor_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(sensor_frame, text="Sensor")

        # Sensor information display
        info_frame = ttk.LabelFrame(sensor_frame, text="Sensor Information", padding="5")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)

        ttk.Label(info_frame, text="Selected Sensor:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.sensor_info_var = tk.StringVar(value="Sentinel-2")
        ttk.Label(info_frame, textvariable=self.sensor_info_var, font=('TkDefaultFont', 9, 'bold')).grid(
            row=0, column=1, sticky=tk.W, pady=2
        )

        # Available bands display
        ttk.Label(info_frame, text="Available Bands:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.available_bands_var = tk.StringVar(value="")
        available_label = ttk.Label(info_frame, textvariable=self.available_bands_var, wraplength=300)
        available_label.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        # Band selection
        band_frame = ttk.LabelFrame(sensor_frame, text="Band Configuration", padding="5")
        band_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        band_frame.columnconfigure(1, weight=1)

        ttk.Label(band_frame, text="Bands to Use:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.selected_bands_var = tk.StringVar(value="B2, B3, B4, B5")
        ttk.Entry(band_frame, textvariable=self.selected_bands_var).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=2
        )

        ttk.Label(band_frame, text="Image Band Indices:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.band_indices_var = tk.StringVar(value="1, 2, 3, 4")
        ttk.Entry(band_frame, textvariable=self.band_indices_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=2
        )

        # Help text
        help_text = "Bands to Use: Sensor bands (e.g., B2, B3, B4, B5)\nImage Band Indices: Corresponding indices in your image file (1-based)"
        ttk.Label(band_frame, text=help_text, font=('TkDefaultFont', 8), foreground='gray').grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0)
        )

        # Action buttons
        button_frame = ttk.Frame(sensor_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Button(button_frame, text="Reset to Defaults",
                   command=self._reset_parameters).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Apply Parameters",
                   command=self._apply_parameters).grid(row=0, column=1)

    def _load_default_parameters(self):
        """Load default parameter values."""
        # This could be extended to load from a config file
        pass

    def _setup_sensor_definitions(self):
        """Set up sensor definitions with wavelengths and available bands."""
        # Import from controller to use centralized definitions
        from ..controllers.workflow_controller import SENSOR_DEFINITIONS
        self.sensor_definitions = SENSOR_DEFINITIONS

        # Initialize sensor display with default after definitions are loaded
        self._update_sensor_info("sentinel2")

    def _update_sensor_info(self, sensor_name):
        """Update sensor information display based on selected sensor."""
        if sensor_name in self.sensor_definitions:
            sensor_def = self.sensor_definitions[sensor_name]
            self.sensor_info_var.set(sensor_def['name'])

            # Format available bands
            bands_text = ", ".join([
                f"{band}({wavelength:.0f}nm)"
                for band, wavelength in sensor_def['bands'].items()
            ])
            self.available_bands_var.set(bands_text)
        else:
            self.sensor_info_var.set("Unknown Sensor")
            self.available_bands_var.set("No band information available")

    def update_sensor_selection(self, sensor_name):
        """Update sensor information when sensor selection changes."""
        self._update_sensor_info(sensor_name)

    def get_sensor_wavelengths(self, selected_bands, sensor_name):
        """Get wavelengths for selected bands from sensor definition."""
        from ..controllers.workflow_controller import get_sensor_wavelengths
        return get_sensor_wavelengths(selected_bands, sensor_name)

    def _reset_parameters(self):
        """Reset parameters to default values."""
        self.depth_min_var.set(0.0)
        self.depth_max_var.set(25.0)
        self.chl_var.set(0.5)
        self.nap_var.set(0.001)
        self.cdom_var.set(0.0025)
        self.substrate_var.set(1.0)
        self.selected_bands_var.set("B2, B3, B4, B5")
        self.band_indices_var.set("1, 2, 3, 4")
        # Initialize with default sensor
        self._update_sensor_info("sentinel2")

    def _apply_parameters(self):
        """Apply current parameters to the controller."""
        try:
            params = self.get_parameters()
            self.controller.update_parameters(params)
        except ValueError as e:
            tk.messagebox.showerror("Parameter Error", str(e))

    def get_parameters(self):
        """Get current parameter values as a dictionary."""
        try:
            # Parse selected bands and indices
            selected_bands = [b.strip() for b in self.selected_bands_var.get().split(',')]
            band_indices = [int(i.strip()) for i in self.band_indices_var.get().split(',')]

            if len(selected_bands) != len(band_indices):
                raise ValueError("Number of selected bands must match number of band indices")

            return {
                'depth_range': (self.depth_min_var.get(), self.depth_max_var.get()),
                'fixed_chl': self.chl_var.get(),
                'fixed_nap': self.nap_var.get(),
                'fixed_cdom': self.cdom_var.get(),
                'fixed_substrate_fraction': self.substrate_var.get(),
                'selected_bands': selected_bands,
                'band_indices': band_indices
            }
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid parameter format: {e}")
