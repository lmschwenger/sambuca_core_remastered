"""Management of Spectral Inherent Optical Properties (SIOPs) for different sensors."""

import os
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from numpy.typing import NDArray
from scipy.interpolate import interp1d
import pandas as pd


class SIOPManager:
    """Manager for Spectral Inherent Optical Properties with sensor-specific interpolation.

    This class manages the loading, storage, and interpolation of spectral libraries
    for different sensors or custom wavelength configurations.
    """

    def __init__(self, siop_directory: Optional[str] = None):
        """Initialize the SIOP manager.

        Args:
            siop_directory: Optional path to directory containing spectral libraries.
                If provided, libraries will be loaded immediately.
        """
        self.siop_directory = siop_directory
        self.raw_libraries = {}  # Original spectral libraries
        self.sensor_configs = {}  # Registered sensor wavelengths

        if siop_directory:
            self.load_libraries(siop_directory)

    def load_libraries(self, directory: str) -> None:
        """Load all spectral libraries from a directory.

        Args:
            directory: Path to directory containing spectral libraries.
        """
        self.siop_directory = directory

        # Direct CSV loading approach
        self.raw_libraries = self._load_csv_libraries(directory)

        print(f"Loaded {len(self.raw_libraries)} spectral libraries from {directory}")

    def _load_csv_libraries(self, directory: str) -> Dict[str, Tuple[NDArray, NDArray]]:
        """Load CSV spectral libraries directly.

        Args:
            directory: Path to directory containing CSV files.

        Returns:
            Dictionary of (wavelengths, values) tuples.
        """
        libraries = {}

        # Walk through directory and subdirectories
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.csv'):
                    filepath = os.path.join(root, file)
                    try:
                        # Extract library type from directory and file name
                        rel_path = os.path.relpath(filepath, directory)
                        parts = rel_path.split(os.sep)

                        # Create library name from file name and parent directory
                        file_base = os.path.splitext(parts[-1])[0]

                        # Load CSV
                        df = pd.read_csv(filepath)

                        # Check number of columns
                        if len(df.columns) == 2:
                            # Simple two-column format
                            wavelength_col = df.columns[0]
                            value_col = df.columns[1]

                            # Use file name without extension as library name
                            library_name = file_base.lower()

                            libraries[library_name] = (
                                df[wavelength_col].values,
                                df[value_col].values
                            )
                            print(f"Loaded {library_name} from {rel_path}")
                        else:
                            # Multi-column format
                            wavelength_col = df.columns[0]

                            for col in df.columns[1:]:
                                library_name = f"{file_base}_{col}".lower()
                                libraries[library_name] = (
                                    df[wavelength_col].values,
                                    df[col].values
                                )
                                print(f"Loaded {library_name} from {rel_path}")
                    except Exception as e:
                        print(f"Error loading {file}: {e}")

        return libraries

    def register_sensor(self, sensor_name: str, wavelengths: List[float]) -> None:
        """Register a sensor with its central wavelengths.

        Args:
            sensor_name: Name of the sensor.
            wavelengths: Central wavelengths of the sensor's bands in nanometers.
        """
        self.sensor_configs[sensor_name] = np.array(wavelengths)
        print(f"Registered sensor '{sensor_name}' with {len(wavelengths)} bands")

    def get_siops_for_sensor(self, sensor_name: str) -> Dict[str, Any]:
        """Get all SIOPs interpolated for a registered sensor.

        Args:
            sensor_name: Name of a previously registered sensor.

        Returns:
            Dictionary with interpolated SIOPs for the specified sensor.

        Raises:
            KeyError: If the sensor has not been registered.
        """
        if sensor_name not in self.sensor_configs:
            raise KeyError(f"Sensor '{sensor_name}' not registered")

        target_wavelengths = self.sensor_configs[sensor_name]
        return self.get_siops_for_wavelengths(target_wavelengths)

    def get_siops_for_wavelengths(self, target_wavelengths: Union[List[float], NDArray]) -> Dict[str, Any]:
        """Get all SIOPs interpolated to match specified wavelengths.

        Args:
            target_wavelengths: Target wavelengths for interpolation.

        Returns:
            Dictionary with interpolated SIOPs for the specified wavelengths.
        """
        if not isinstance(target_wavelengths, np.ndarray):
            target_wavelengths = np.array(target_wavelengths)

        result = {
            'wavelengths': target_wavelengths,
            'num_bands': len(target_wavelengths)
        }

        # Process each spectral library
        for name, (src_wavelengths, src_values) in self.raw_libraries.items():
            # Check if wavelength ranges overlap enough
            if min(src_wavelengths) > max(target_wavelengths) or \
               max(src_wavelengths) < min(target_wavelengths):
                print(f"Warning: Spectral library '{name}' does not cover the target wavelength range")
                continue

            # Create interpolator
            interpolator = interp1d(
                src_wavelengths,
                src_values,
                bounds_error=False,
                fill_value="extrapolate"
            )

            # Interpolate to target wavelengths
            result[name] = interpolator(target_wavelengths)

        return result

    def list_available_libraries(self) -> List[str]:
        """List all available spectral library names.

        Returns:
            List of spectral library names.
        """
        return list(self.raw_libraries.keys())

    def get_common_library_types(self) -> Dict[str, List[str]]:
        """Group libraries by common types (absorption, backscatter, substrate).

        Returns:
            Dictionary with grouped library names.
        """
        types = {
            'absorption': [],
            'backscatter': [],
            'substrate': [],
            'other': []
        }

        for name in self.raw_libraries.keys():
            if 'absorption' in name:
                types['absorption'].append(name)
            elif 'backscatter' in name:
                types['backscatter'].append(name)
            elif 'substrate' in name:
                types['substrate'].append(name)
            else:
                types['other'].append(name)

        return types

    def get_standard_siops(self, sensor_name: str) -> Dict[str, Any]:
        """Get a standard set of SIOPs needed for the forward model.

        This method tries to automatically select the appropriate libraries
        for typical forward model parameters.

        Args:
            sensor_name: Name of a registered sensor.

        Returns:
            Dictionary with standard SIOPs for the forward model.

        Raises:
            KeyError: If required libraries cannot be found.
        """
        if sensor_name not in self.sensor_configs:
            raise KeyError(f"Sensor '{sensor_name}' not registered")

        # Get all interpolated libraries
        all_siops = self.get_siops_for_sensor(sensor_name)

        # Try to find standard libraries by common naming patterns
        standard_siops = {
            'wavelengths': all_siops['wavelengths'],
            'num_bands': all_siops['num_bands']
        }

        # Find water absorption
        water_abs_keys = [k for k in all_siops.keys() if 'water_absorption' in k]
        if water_abs_keys:
            standard_siops['a_water'] = all_siops[water_abs_keys[0]]
        else:
            raise KeyError("Could not find water absorption spectrum")

        # Find phytoplankton absorption
        ph_abs_keys = [k for k in all_siops.keys() if 'phytoplankton_absorption' in k]
        if ph_abs_keys:
            standard_siops['a_ph_star'] = all_siops[ph_abs_keys[0]]
        else:
            raise KeyError("Could not find phytoplankton absorption spectrum")

        # Find sand substrate (primary substrate)
        sand_keys = [k for k in all_siops.keys() if 'sand_substrate' in k]
        if sand_keys:
            standard_siops['substrate1'] = all_siops[sand_keys[0]]
        else:
            # Try any substrate
            substrate_keys = [k for k in all_siops.keys() if 'substrate' in k]
            if substrate_keys:
                standard_siops['substrate1'] = all_siops[substrate_keys[0]]
            else:
                raise KeyError("Could not find substrate spectrum")

        # Find secondary substrate if available
        seagrass_keys = [k for k in all_siops.keys() if 'seagrass_substrate' in k]
        if seagrass_keys:
            standard_siops['substrate2'] = all_siops[seagrass_keys[0]]

        return standard_siops

    def plot_siops(self, sensor_name=None, save_path=None, figsize=(15, 12)):
        """
        Plot the Spectral Inherent Optical Properties (SIOPs) from a SIOPManager.

        Parameters:
        -----------
        siop_manager : SIOPManager
            The SIOPManager instance containing the SIOPs
        sensor_name : str, optional
            Name of a registered sensor to plot interpolated SIOPs for.
            If None, raw libraries will be plotted.
        save_path : str, optional
            Path to save the figure. If None, the figure is displayed but not saved.
        figsize : tuple, optional
            Figure size (width, height) in inches

        Returns:
        --------
        fig : matplotlib.figure.Figure
            The created figure object
        """
        import matplotlib.pyplot as plt
        import numpy as np

        # Get SIOPs - either raw or for a specific sensor
        if sensor_name:
            if sensor_name not in self.sensor_configs:
                raise ValueError(f"Sensor '{sensor_name}' not registered in self.siop_manager")
            siops = self.get_siops_for_sensor(sensor_name)
            wavelengths = siops['wavelengths']
            title_suffix = f" (interpolated for {sensor_name})"
        else:
            siops = self.raw_libraries
            title_suffix = " (raw data)"

        # Create figure
        fig = plt.figure(figsize=figsize)

        # Group libraries by type
        absorption_libs = [k for k in siops.keys() if 'absorption' in k.lower() and k != 'wavelengths']
        backscatter_libs = [k for k in siops.keys() if 'backscatter' in k.lower()]
        substrate_libs = [k for k in siops.keys() if 'substrate' in k.lower()]

        # 1. Plot absorption coefficients
        if absorption_libs:
            ax1 = plt.subplot(2, 2, 1)
            for lib in absorption_libs:
                if sensor_name:
                    plt.plot(wavelengths, siops[lib], label=lib)
                else:
                    plt.plot(siops[lib][0], siops[lib][1], label=lib)
            plt.title(f"Absorption Coefficients{title_suffix}")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Absorption (m⁻¹)")
            plt.grid(True, alpha=0.3)
            plt.legend()

        # 2. Plot backscattering coefficients
        if backscatter_libs:
            ax2 = plt.subplot(2, 2, 2)
            for lib in backscatter_libs:
                if sensor_name:
                    plt.plot(wavelengths, siops[lib], label=lib)
                else:
                    plt.plot(siops[lib][0], siops[lib][1], label=lib)
            plt.title(f"Backscattering Coefficients{title_suffix}")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Backscattering (m⁻¹)")
            plt.grid(True, alpha=0.3)
            plt.legend()

        # 3. Plot substrate reflectance
        if substrate_libs:
            ax3 = plt.subplot(2, 2, 3)
            for lib in substrate_libs:
                if sensor_name:
                    plt.plot(wavelengths, siops[lib], label=lib)
                else:
                    plt.plot(siops[lib][0], siops[lib][1], label=lib)
            plt.title(f"Substrate Reflectance{title_suffix}")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Reflectance")
            plt.grid(True, alpha=0.3)
            plt.legend()

        # 4. Plot example forward model
        if 'water_absorption' in siops and sensor_name:
            ax4 = plt.subplot(2, 2, 4)

            # Get standard SIOP values
            try:
                std_siops = self.get_standard_siops(sensor_name)

                # Run a simple forward model for demonstration
                import sambuca_core as sbc

                # Example parameters for shallow and deep water
                shallow_results = sbc.forward_model(
                    chl=1.0, cdom=0.3, nap=1.0, depth=2.0,
                    substrate1=std_siops.get('substrate1', np.ones_like(wavelengths) * 0.3),
                    wavelengths=wavelengths,
                    a_water=std_siops.get('a_water', siops.get('water_absorption')),
                    a_ph_star=std_siops.get('a_ph_star', siops.get('phytoplankton_absorption')),
                    num_bands=len(wavelengths)
                )

                deep_results = sbc.forward_model(
                    chl=1.0, cdom=0.3, nap=1.0, depth=30.0,  # Deep water
                    substrate1=std_siops.get('substrate1', np.ones_like(wavelengths) * 0.3),
                    wavelengths=wavelengths,
                    a_water=std_siops.get('a_water', siops.get('water_absorption')),
                    a_ph_star=std_siops.get('a_ph_star', siops.get('phytoplankton_absorption')),
                    num_bands=len(wavelengths)
                )

                # Plot example spectra
                plt.plot(wavelengths, shallow_results.rrs, 'b-', label='Shallow water (2m)')
                plt.plot(wavelengths, deep_results.rrs, 'r-', label='Deep water (30m)')

                # Highlight sensor bands if available
                if hasattr(self, 'sensor_configs') and sensor_name in self.sensor_configs:
                    sensor_bands = self.sensor_configs[sensor_name]
                    plt.plot(sensor_bands, np.interp(sensor_bands, wavelengths, shallow_results.rrs),
                             'bo', markersize=8, label=f'{sensor_name} bands')
                    plt.plot(sensor_bands, np.interp(sensor_bands, wavelengths, deep_results.rrs),
                             'ro', markersize=8)

                plt.title(f"Example Spectra for {sensor_name}")
                plt.xlabel("Wavelength (nm)")
                plt.ylabel("Rrs (sr⁻¹)")
                plt.grid(True, alpha=0.3)
                plt.legend()
            except Exception as e:
                plt.text(0.5, 0.5, f"Error generating example spectra:\n{str(e)}",
                         ha='center', va='center', transform=ax4.transAxes)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure saved to {save_path}")

        return fig

    def plot_full_siop_library(self, save_path=None, figsize=(15, 15)):
        """
        Plot the full SIOP library from the given directory, showing all available spectral files
        with their original resolution and grouping by type.

        Parameters:
        -----------
        siop_directory : str
            Path to the directory containing SIOP files
        save_path : str, optional
            Path to save the figure. If None, the figure is displayed but not saved.
        figsize : tuple, optional
            Figure size (width, height) in inches

        Returns:
        --------
        fig : matplotlib.figure.Figure
            The created figure object
        """
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import os

        # Define categories and their associated keywords
        categories = {
            'Water Absorption': ['water_absorption', 'water_abs'],
            'Phytoplankton Absorption': ['phytoplankton_absorption', 'ph_absorption', 'chl_absorption'],
            'CDOM Absorption': ['cdom_absorption', 'cdom_abs', 'gelbstoff'],
            'Tripton/NAP Absorption': ['nap_absorption', 'tripton_absorption', 'nap_abs'],
            'Water Backscattering': ['water_backscatter', 'water_bb'],
            'Phytoplankton Backscattering': ['phytoplankton_backscatter', 'ph_backscatter', 'chl_backscatter'],
            'Tripton/NAP Backscattering': ['nap_backscatter', 'tripton_backscatter', 'nap_bb'],
            'Substrate Reflectance': ['substrate', 'bottom', 'sand', 'seagrass', 'coral', 'algae', 'mud']
        }

        # Create a figure with subplots based on the number of categories we find
        fig = plt.figure(figsize=figsize)

        # Initialize counters and keep track of which subplot to use
        subplot_count = 0
        num_categories_found = 0
        subplot_mapping = {}

        # First pass to determine how many subplots we need
        for root, _, files in os.walk(self.siop_directory):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    file_lower = file.lower()
                    file_category = None

                    # Determine category
                    for category, keywords in categories.items():
                        if any(keyword in file_lower for keyword in keywords):
                            file_category = category
                            break

                    if file_category:
                        if file_category not in subplot_mapping:
                            subplot_mapping[file_category] = num_categories_found
                            num_categories_found += 1

        # Calculate grid dimensions - try to make it close to square
        grid_size = int(np.ceil(np.sqrt(num_categories_found)))
        rows = grid_size
        cols = int(np.ceil(num_categories_found / grid_size))

        # Second pass to actually plot the data
        for root, _, files in os.walk(self.siop_directory):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    file_lower = file.lower()
                    file_category = None

                    # Determine category
                    for category, keywords in categories.items():
                        if any(keyword in file_lower for keyword in keywords):
                            file_category = category
                            break

                    if file_category:
                        # Get this file's subplot index
                        subplot_idx = subplot_mapping[file_category] + 1

                        # Get or create the subplot
                        ax = plt.subplot(rows, cols, subplot_idx)

                        try:
                            # Read CSV file
                            df = pd.read_csv(file_path)
                            if len(df.columns) >= 2:
                                # Assume first column is wavelength and second is value
                                wavelength_col = df.columns[0]
                                value_col = df.columns[1]

                                # Generate nice label from filename
                                label = os.path.splitext(os.path.basename(file_path))[0]
                                label = label.replace('_', ' ').title()

                                # Plot the data
                                ax.plot(df[wavelength_col], df[value_col], label=label)

                                # Set axes labels for the first time we plot in this category
                                if file_category == 'Water Absorption' and 'abs_label_set' not in locals():
                                    ax.set_xlabel('Wavelength (nm)')
                                    ax.set_ylabel('Absorption (m⁻¹)')
                                    locals()['abs_label_set'] = True
                                elif 'Backscattering' in file_category and 'bb_label_set' not in locals():
                                    ax.set_xlabel('Wavelength (nm)')
                                    ax.set_ylabel('Backscattering (m⁻¹)')
                                    locals()['bb_label_set'] = True
                                elif 'Substrate' in file_category and 'substrate_label_set' not in locals():
                                    ax.set_xlabel('Wavelength (nm)')
                                    ax.set_ylabel('Reflectance')
                                    locals()['substrate_label_set'] = True
                                else:
                                    ax.set_xlabel('Wavelength (nm)')
                                    if 'Absorption' in file_category:
                                        ax.set_ylabel('Absorption (m⁻¹)')
                                    elif 'Backscattering' in file_category:
                                        ax.set_ylabel('Backscattering (m⁻¹)')
                                    elif 'Substrate' in file_category:
                                        ax.set_ylabel('Reflectance')
                                    else:
                                        ax.set_ylabel('Value')

                        except Exception as e:
                            print(f"Error plotting {file_path}: {e}")

                        # Set title and enable grid and legend
                        ax.set_title(file_category)
                        ax.grid(True, alpha=0.3)
                        ax.legend(fontsize='small')

        plt.tight_layout()

        # Add a title for the entire figure
        fig.suptitle('Full SIOP Library Visualization', fontsize=16, y=1.02)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure saved to {save_path}")

        return fig

    def plot_comparison_spectra(self, sensor_name, save_path=None, figsize=(12, 10)):
        """
        Plot comparison spectra showing how various water conditions and depths would appear
        using the configured SIOPs for a specific sensor.

        Parameters:
        -----------
        siop_manager : SIOPManager
            The SIOPManager instance containing the SIOPs
        sensor_name : str
            Name of a registered sensor to use for the plots
        save_path : str, optional
            Path to save the figure. If None, the figure is displayed but not saved.
        figsize : tuple, optional
            Figure size (width, height) in inches

        Returns:
        --------
        fig : matplotlib.figure.Figure
            The created figure object
        """
        import matplotlib.pyplot as plt
        import numpy as np
        import sambuca_core as sbc

        # Check if sensor is registered
        if sensor_name not in self.sensor_configs:
            raise ValueError(f"Sensor '{sensor_name}' not registered in siop_manager")

        # Get standard SIOPs for the sensor
        std_siops = self.get_standard_siops(sensor_name)
        wavelengths = std_siops['wavelengths']
        sensor_bands = self.sensor_configs[sensor_name]

        # Create figure
        fig = plt.figure(figsize=figsize)

        # Define scenarios to compare
        scenarios = [
            {"title": "Depth Variation", "variable": "depth",
             "values": [0.5, 1, 2, 5, 10, 20], "unit": "m",
             "fixed": {"chl": 1.0, "cdom": 0.3, "nap": 1.0}},

            {"title": "Chlorophyll Variation", "variable": "chl",
             "values": [0.1, 0.5, 1.0, 2.0, 5.0], "unit": "mg/m³",
             "fixed": {"depth": 5.0, "cdom": 0.3, "nap": 1.0}},

            {"title": "CDOM Variation", "variable": "cdom",
             "values": [0.05, 0.1, 0.3, 0.5, 1.0], "unit": "m⁻¹",
             "fixed": {"depth": 5.0, "chl": 1.0, "nap": 1.0}},

            {"title": "NAP Variation", "variable": "nap",
             "values": [0.1, 0.5, 1.0, 2.0, 5.0], "unit": "mg/L",
             "fixed": {"depth": 5.0, "chl": 1.0, "cdom": 0.3}}
        ]

        # Plot each scenario
        for i, scenario in enumerate(scenarios):
            ax = plt.subplot(2, 2, i + 1)

            # Get variable parameters and values
            variable = scenario["variable"]
            values = scenario["values"]
            unit = scenario["unit"]
            fixed = scenario["fixed"]

            # Plot spectra for each value of the variable
            for value in values:
                # Set parameters for forward model
                params = fixed.copy()
                params[variable] = value

                # Run forward model
                results = sbc.forward_model(
                    substrate1=std_siops.get('substrate1', np.ones_like(wavelengths) * 0.3),
                    wavelengths=wavelengths,
                    a_water=std_siops.get('a_water'),
                    a_ph_star=std_siops.get('a_ph_star'),
                    num_bands=len(wavelengths),
                    **params
                )

                # Plot full spectrum
                label = f"{variable} = {value} {unit}"
                ax.plot(wavelengths, results.rrs, '-', label=label)

                # Highlight sensor bands
                ax.plot(sensor_bands, np.interp(sensor_bands, wavelengths, results.rrs),
                        'o', markersize=5)

            ax.set_title(scenario["title"])
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Rrs (sr⁻¹)")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize='small')

        plt.tight_layout()

        # Add a title for the entire figure
        fig.suptitle(f'Parameter Sensitivity Analysis for {sensor_name}', fontsize=16, y=1.02)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure saved to {save_path}")

        return fig

    # Example usage:
    # plot_full_siop_library('/path/to/siop_directory', 'siop_library.png')
    # plot_comparison_spectra(siop_manager, 'Sentinel-2', 'parameter_comparison.png')