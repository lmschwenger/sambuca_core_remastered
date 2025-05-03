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