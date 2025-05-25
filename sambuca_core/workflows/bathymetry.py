from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
from .base import BaseWorkflow
from ..inversion import InversionParameters, process_image
from ..io import ImagePreprocessor
from ..results import ImageInversionResult


class BathymetryWorkflow(BaseWorkflow):
    """High-level workflow for satellite-derived bathymetry."""

    def _setup_defaults(self):
        """Set up default parameters optimized for bathymetry retrieval."""
        # Get standard bathymetry band configuration
        self.bands, self.wavelengths = self.sensor.get_standard_config('bathymetry')

        # Register sensor with SIOP manager
        self.siop_manager.register_sensor(self.sensor.name, self.wavelengths)

        # Set up inversion parameters optimized for bathymetry
        self.inversion_params = InversionParameters(
            # Primary parameter: depth
            depth=(0, 25),

            # Secondary parameters with reasonable bounds
            chl=(0.5, 3.0),  # Chlorophyll
            cdom=(0.001, 0.4),  # CDOM
            nap=(0.1, 8.0),  # NAP

            # Fixed substrate mixing (can be overridden)
            fixed_substrate_fraction=0.95,

            # Will be updated from SIOP manager
            wavelengths=self.wavelengths
        )

        # Update with SIOPs
        self.inversion_params.update_from_siop_manager(
            self.siop_manager,
            self.sensor.name
        )

    def process_image(self,
                      image_path: str,
                      mask_path: Optional[str] = None,
                      output_path: Optional[str] = None,
                      n_processes: int = 4,
                      progress_bar: bool = True,
                      **kwargs) -> 'ImageInversionResult':
        """
        Process entire image for bathymetry retrieval.

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
            result_text = f"Depth: {result.parameters['depth']:.2f} m\n"
            result_text += f"Chl: {result.parameters['chl']:.2f} mg/m³\n"
            result_text += f"RMSE: {result.objective_value:.4f}"

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

    def customize_parameters(self, **kwargs):
        """
        Customize inversion parameters.

        Args:
            **kwargs: Parameter bounds to update (e.g., depth=(0, 15), chl=(0.1, 5.0))
        """
        for param, bounds in kwargs.items():
            if hasattr(self.inversion_params, param):
                setattr(self.inversion_params, param, bounds)
                print(f"Updated {param} bounds to {bounds}")
            else:
                print(f"Warning: Unknown parameter '{param}'")

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