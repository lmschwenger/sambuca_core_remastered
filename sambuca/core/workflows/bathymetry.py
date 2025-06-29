from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np

from .base import BaseWorkflow
from ..inversion import InversionParameters, process_image
from ..io import ImagePreprocessor
from ..results import ImageInversionResult


class BathymetryWorkflow(BaseWorkflow):
    """High-level workflow for satellite-derived bathymetry."""

    def _setup_defaults(self):
        """Set up default parameters optimized for bathymetry retrieval."""
        if self.sensor_name.lower() in ['sentinel2', 's2']:
            # Standard bathymetry bands: B02, B03, B04, B05
            self.bands = ['B02', 'B03', 'B04', 'B05']
            self.wavelengths = [492.4, 559.8, 664.6, 704.1]
        else:
            # Fallback for other sensors
            self.bands = ['B2', 'B3', 'B4', 'B5']
            self.wavelengths = [492.4, 559.8, 664.6, 704.1]

        # Register sensor with SIOP manager
        self.siop_manager.register_sensor(self.sensor_name, self.wavelengths)

        # Set up inversion parameters optimized for bathymetry
        # Start with depth-only inversion as default
        self.inversion_params = InversionParameters(
            # Primary parameter: depth
            depth=(0, 25),

            # Fix other parameters by default (can be overridden)
            fixed_chl=1.0,
            fixed_cdom=0.1,
            fixed_nap=1.0,
            fixed_substrate_fraction=0.95,

            # Will be updated from SIOP manager
            wavelengths=self.wavelengths
        )

        # Update with SIOPs
        self.inversion_params.update_from_siop_manager(
            self.siop_manager,
            self.sensor_name
        )

    def customize_parameters(self, **kwargs):
        """
        Customize inversion parameters.

        Args:
            **kwargs: Parameter bounds to update (e.g., depth=(0, 15), chl=(0.1, 5.0))
                     or fixed values (e.g., fixed_chl=0.5, fixed_nap=0.001)
        """
        for param, value in kwargs.items():
            if param.startswith('fixed_'):
                # Handle fixed parameters
                base_param = param[6:]  # Remove 'fixed_' prefix

                # Remove any existing bounds for this parameter
                if hasattr(self.inversion_params, base_param):
                    setattr(self.inversion_params, base_param, None)

                # Set the fixed value
                setattr(self.inversion_params, param, value)
                print(f"Fixed {base_param} to {value}")

            elif hasattr(self.inversion_params, param):
                # Handle parameter bounds
                # First remove any fixed value for this parameter
                fixed_param = f"fixed_{param}"
                if hasattr(self.inversion_params, fixed_param):
                    setattr(self.inversion_params, fixed_param, None)

                # Set the bounds
                setattr(self.inversion_params, param, value)
                print(f"Updated {param} bounds to {value}")
            else:
                print(f"Warning: Unknown parameter '{param}'")

    def process_image(self,
                      image_path: str,
                      mask_path: Optional[str] = None,
                      output_path: Optional[str] = None,
                      n_processes: int = 4,
                      progress_bar: bool = True,
                      **kwargs) -> 'ImageInversionResult':
        """
        Process the entire image for bathymetry retrieval.

        Args:
            image_path: Path to satellite image
            mask_path: Optional path to water mask
            output_path: Optional path to save depth map
            n_processes: Number of parallel processes
            progress_bar: Show progress bar
            **kwargs: Additional arguments for process_image

        Returns:
            ImageInversionResult object with results and metadata
        """

        # Load and preprocess image
        print(f"Loading image: {image_path}")
        image_data = self.image_loader.load(image_path, bands=self.bands)

        # Apply water mask
        if mask_path:
            print(f"Applying water mask: {mask_path}")
            water_mask = ImagePreprocessor.apply_water_mask(image_data, mask_path)
        else:
            water_mask = None

        # Print inversion settings for debugging
        print("\n" + "=" * 50)
        print("INVERSION SETTINGS:")
        print("=" * 50)
        print(f"Wavelengths: {self.wavelengths} nm")
        print(f"Parameters to invert: {self.inversion_params.get_inversion_parameter_names()}")

        # Print bounds for parameters being inverted
        bounds = self.inversion_params.get_parameter_bounds()
        param_names = self.inversion_params.get_inversion_parameter_names()
        for i, param_name in enumerate(param_names):
            print(f"{param_name} range: {bounds[i]}")

        # Print fixed parameter values
        fixed_params = []
        for attr in ['fixed_chl', 'fixed_cdom', 'fixed_nap', 'fixed_substrate_fraction']:
            if hasattr(self.inversion_params, attr):
                value = getattr(self.inversion_params, attr)
                if value is not None:
                    fixed_params.append(f"{attr}: {value}")

        if fixed_params:
            print("Fixed parameters:")
            for param in fixed_params:
                print(f"  {param}")

        print(f"Number of processes: {n_processes}")
        print("=" * 50)

        # Run inversion
        print(f"Processing {np.sum(water_mask) if water_mask is not None else 'all'} pixels...")
        results = process_image(
            image_data.data,
            self.inversion_params,
            mask=water_mask,
            n_processes=n_processes,
            progress_bar=progress_bar,
            **kwargs
        )

        # Create result object
        result = ImageInversionResult(
            results=results,
            image_metadata=image_data.metadata,
            workflow_config=self.get_config(),
            image_path=image_path
        )

        # Save depth map if requested
        if output_path:
            result.save_depth_map(output_path)

        return result

    def process_pixel(self,
                      image_path: str,
                      pixel_coords: Tuple[int, int],
                      show_plot: bool = True) -> Dict[str, Any]:
        """
        Process single pixel for analysis and validation.

        Args:
            image_path: Path to satellite image
            pixel_coords: (row, col) coordinates of pixel
            show_plot: Show spectral fit plot

        Returns:
            Dictionary with inversion results and fit quality
        """
        from ..inversion import invert_spectrum
        import matplotlib.pyplot as plt

        # Load image
        image_data = self.image_loader.load(image_path, bands=None)

        # Extract pixel spectrum
        y, x = pixel_coords
        pixel_spectrum = ImagePreprocessor.extract_pixel_spectrum(image_data, y, x)

        # Check for valid pixel
        if np.any(np.isnan(pixel_spectrum)) or np.all(pixel_spectrum <= 0):
            raise ValueError(f"Invalid pixel at coordinates {pixel_coords}")

        # Run inversion
        result = invert_spectrum(pixel_spectrum, self.inversion_params)

        # Create visualization if requested
        if show_plot:
            plt.figure(figsize=(10, 6))
            plt.plot(self.wavelengths, pixel_spectrum, 'o-',
                     color='blue', label='Observed', linewidth=2, markersize=6)
            plt.plot(self.wavelengths, result.modeled_spectra, 's--',
                     color='red', label='Modeled', linewidth=2, markersize=6)

            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Remote Sensing Reflectance')
            plt.title(f'Spectral Fit at Pixel ({y}, {x})')
            plt.legend()
            plt.grid(True, alpha=0.3)

            # Add results as text
            result_text = f"Inversion Results:\n"
            for param, value in result.parameters.items():
                if param == 'depth':
                    result_text += f"Depth: {value:.2f} m\n"
                elif param == 'chl':
                    result_text += f"Chl: {value:.2f} mg/m³\n"
                elif param == 'cdom':
                    result_text += f"CDOM: {value:.4f} m⁻¹\n"
                elif param == 'nap':
                    result_text += f"NAP: {value:.2f} mg/L\n"

            result_text += f"RMSE: {result.objective_value:.6f}"

            plt.text(0.02, 0.98, result_text, transform=plt.gca().transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                     verticalalignment='top')

            plt.tight_layout()
            plt.show()

        return {
            'parameters': result.parameters,
            'error': result.objective_value,
            'convergence': result.convergence_status,
            'observed_spectrum': pixel_spectrum,
            'modeled_spectrum': result.modeled_spectra,
            'wavelengths': self.wavelengths,
            'pixel_coords': pixel_coords
        }

    def quick_preview(self, image_path: str, pixel_coords: Optional[Tuple[int, int]] = None):
        """
        Create quick RGB preview with optional pixel location.

        Args:
            image_path: Path to satellite image
            pixel_coords: Optional pixel coordinates to highlight
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        # Load image
        image_data = self.image_loader.load(image_path, bands=None)

        # Create RGB preview
        rgb = ImagePreprocessor.create_rgb_preview(image_data)

        # Plot
        plt.figure(figsize=(12, 8))
        plt.imshow(rgb)
        plt.title(f"RGB Preview: {Path(image_path).name}")

        # Highlight pixel if provided
        if pixel_coords:
            y, x = pixel_coords
            plt.plot(x, y, 'ro', markersize=10, markeredgecolor='white', markeredgewidth=2)
            rect = Rectangle((x - 10, y - 10), 20, 20, linewidth=2,
                             edgecolor='red', facecolor='none')
            plt.gca().add_patch(rect)
            plt.text(x + 15, y - 15, f'({y}, {x})', color='red', fontweight='bold',
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        plt.axis('off')
        plt.tight_layout()
        plt.show()
