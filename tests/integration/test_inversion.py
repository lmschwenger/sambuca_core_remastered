import unittest
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import rasterio
from pathlib import Path

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, invert_spectrum, multi_start_inversion
from sambuca_core.utility.plotting import plot_siops


class TestSpectrumInversion(unittest.TestCase):
    """Test the inversion of a specific pixel from an image."""

    def setUp(self):
        """Set up the test data and parameters."""
        # Path to the test image - modify this to point to your image
        self.image_path = os.path.join("../..", "data", "input", "anholt_20170823_b02b09.tif")

        # Path to SIOP directory - modify as needed
        self.siop_dir = os.path.join("../..", "data", "siops")

        # Test pixel coordinates [y, x] - modify these to select your pixel of interest
        self.test_pixel = [600, 600]

        # Define Sentinel-2 band wavelengths
        self.s2_wavelengths = {
            "B1": 442.7,  # Coastal aerosol
            "B2": 492.4,  # Blue
            "B3": 559.8,  # Green
            "B4": 664.6,  # Red
            "B5": 704.1,  # Vegetation red edge
            "B6": 740.5,  # Vegetation red edge
            "B7": 782.8,  # Vegetation red edge
            "B8": 832.8,  # NIR
            "B8A": 864.7,  # Narrow NIR
            "B9": 945.1,  # Water vapour
            "B10": 1373.5,  # SWIR - Cirrus
            "B11": 1613.7,  # SWIR
            "B12": 2202.4  # SWIR
        }

        # Define which bands to use
        self.bands_used = ["B2", "B3", "B4", "B5", "B6", "B7", "B8"]
        self.wavelengths_used = [self.s2_wavelengths[b] for b in self.bands_used]

        # Load the SIOPs
        self.siop_manager = sbc.SIOPManager(self.siop_dir)
        self.siop_manager.register_sensor("Sentinel-2", wavelengths=self.wavelengths_used)

        # Inversion parameters
        self.inversion_params = InversionParameters(
            # Parameters to invert for (with bounds)
         #   chl=(0.1, 3.0),  # Chlorophyll concentration
            depth=(0, 10),  # Water depth
            chl=(0.5, 3.30),
            # Optional: include CDOM and NAP if needed
            cdom=(0.001, 0.42),      # CDOM concentration
            nap=(0.1, 9.0),        # NAP concentration
            fixed_substrate_fraction=.95,
            # Fixed parameters - will be updated from the SIOP manager
            wavelengths=self.wavelengths_used
        )

        # Update parameters from SIOP manager
        self.inversion_params.update_from_siop_manager(self.siop_manager, "Sentinel-2")

    def load_image_and_extract_pixel(self):
        """Load the image and extract the test pixel's spectrum."""
        with rasterio.open(self.image_path) as src:
            # Read all bands
            image_data = src.read()[:len(self.bands_used), :, :].astype(np.float32)
            self.metadata = src.meta

            # Determine scaling factor based on data type
            scaling_factor = 10000.0 if self.metadata['dtype'] == 'uint16' else 1.0

            # Convert to surface reflectance (0-1)
            surface_reflectance = image_data.astype(np.float32) / scaling_factor

            # Convert to remote sensing reflectance (Rrs)
            rrs = surface_reflectance / np.pi

            # Extract the pixel spectrum
            y, x = self.test_pixel
            pixel_rrs = rrs[:, y, x]

            # Check if pixel is valid (not NaN or 0)
            if np.any(np.isnan(pixel_rrs)) or np.all(pixel_rrs <= 0):
                raise ValueError(f"Invalid pixel at coordinates {self.test_pixel}")

            return image_data, rrs, pixel_rrs

    def visualize_pixel_location(self, image_data):
        """Create a plot showing the location of the test pixel."""
        # Use the first band for visualization
        band_for_vis = 0

        # Create a RGB composite if image has at least 3 bands
        if image_data.shape[0] >= 3:
            # Use standard RGB bands (assuming order B, G, R)
            rgb = np.zeros((image_data.shape[1], image_data.shape[2], 3))

            # For visualization purposes, use simple stretching
            for i, band_idx in enumerate([0, 1, 2]):  # B, G, R order
                if band_idx < image_data.shape[0]:
                    band = image_data[band_idx].astype(float)
                    p2 = np.percentile(band, 98)
                    rgb[:, :, i] = np.clip(band / p2, 0, 1)

            plt.figure(figsize=(10, 8))
            plt.imshow(rgb)
            plt.title("RGB Composite with Test Pixel Location")
        else:
            # Single band visualization
            plt.figure(figsize=(10, 8))
            band = image_data[band_for_vis].astype(float)
            p2 = np.percentile(band, 98)
            plt.imshow(band / p2, cmap='gray')
            plt.title(f"Band {band_for_vis + 1} with Test Pixel Location")

        # Highlight the test pixel
        y, x = self.test_pixel
        plt.plot(x, y, 'ro', markersize=10)

        # Add a rectangle around the pixel for better visibility
        rect = Rectangle((x - 10, y - 10), 20, 20, linewidth=2, edgecolor='r', facecolor='none')
        plt.gca().add_patch(rect)

        plt.colorbar(label='Scaled Reflectance')
        plt.xlabel('Column (X)')
        plt.ylabel('Row (Y)')
        plt.tight_layout()

        # Save the figure
        output_dir = Path('../../tests/output')
        output_dir.mkdir(exist_ok=True)
        plt.savefig(output_dir / 'test_pixel_location.png', dpi=300)

        return plt.gcf()

    def run_inversion_and_visualize(self, pixel_rrs):
        """Run the inversion on the pixel spectrum and visualize the results."""
        # Run inversion with multiple starting points for better results
        result = invert_spectrum(
            pixel_rrs,
            self.inversion_params,
        )

        # Plot the results
        plt.figure(figsize=(10, 6))

        # Plot observed vs modeled spectra
        plt.plot(self.wavelengths_used, pixel_rrs, 'o-', color='blue', label='Observed Rrs')
        plt.plot(self.wavelengths_used, result.modeled_spectra, 's-', color='red', label='Modeled Rrs')

        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Remote Sensing Reflectance (sr⁻¹)')
        plt.title('Observed vs Modeled Remote Sensing Reflectance')
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Print the inversion results
        print("\nInversion Results:")
        for param, value in result.parameters.items():
            print(f"  {param}: {value:.4f}")
        print(f"  RMSE: {result.objective_value:.6f}")

        # Create a text box with the results
        textstr = '\n'.join([
            f"Inversion Results:",
            f"Depth: {result.parameters.get('depth', 'N/A'):.2f} m",
            f"Chl: {result.parameters.get('chl', 'N/A'):.2f} mg/m³"
        ])

        if 'cdom' in result.parameters:
            textstr += f"\nCDOM: {result.parameters['cdom']:.4f} m⁻¹"
        if 'nap' in result.parameters:
            textstr += f"\nNAP: {result.parameters['nap']:.2f} mg/L"

        textstr += f"\nRMSE: {result.objective_value:.6f}"

        # Add text box
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        plt.gca().text(0.05, 0.95, textstr, transform=plt.gca().transAxes,
                       fontsize=10, verticalalignment='top', bbox=props)

        plt.tight_layout()

        # Save the figure
        output_dir = Path('../../tests/output')
        output_dir.mkdir(exist_ok=True)
        plt.show()
        plt.savefig(output_dir / 'inversion_results.png', dpi=300)

        return result, plt.gcf()

    def visualize_siops(self):
        """Visualize the SIOPs used in the inversion."""
        # Create output directory if it doesn't exist
        output_dir = Path('../../tests/output')
        output_dir.mkdir(exist_ok=True)

        # Plot absorption SIOPs
        categories = sbc.utility.plotting.find_siops(self.siop_dir)

        if categories.get('absorption'):
            sbc.utility.plotting.plot_siops(
                [os.path.join('absorption', f) for f in categories['absorption']],
                self.siop_dir,
                output_file=str(output_dir / 'absorption_siops.png'),
                title="Absorption Coefficients",
                y_label="Absorption (1/m)"
            )

        if categories.get('backscatter'):
            sbc.utility.plotting.plot_siops(
                [os.path.join('backscatter', f) for f in categories['backscatter']],
                self.siop_dir,
                output_file=str(output_dir / 'backscatter_siops.png'),
                title="Backscatter Coefficients",
                y_label="Backscatter (1/m)"
            )

        if categories.get('substrates'):
            sbc.utility.plotting.plot_siops(
                [os.path.join('substrates', f) for f in categories['substrates']],
                self.siop_dir,
                output_file=str(output_dir / 'substrate_siops.png'),
                title="Substrate Reflectance",
                y_label="Reflectance"
            )

    def test_inversion(self):
        """Test spectrum inversion on a specific pixel."""
        # Load the image and extract the pixel spectrum
        try:
            image_data, rrs_image, pixel_rrs = self.load_image_and_extract_pixel()
        except FileNotFoundError:
            self.skipTest(f"Image file not found: {self.image_path}")
            return

        # Visualize the pixel location
        self.visualize_pixel_location(image_data)

        # Visualize SIOPs
    #    self.visualize_siops()

        # Run inversion and visualize results
        result, _ = self.run_inversion_and_visualize(pixel_rrs)

        # Add assertions to validate the inversion results
        self.assertIsNotNone(result)
        self.assertIn('depth', result.parameters)
        self.assertIn('chl', result.parameters)

        # Check if depth and chlorophyll values are within expected ranges
        self.assertGreater(result.parameters['depth'], 0)
        self.assertLess(result.parameters['depth'], 50)  # Adjust based on your expected max depth

        self.assertGreater(result.parameters['chl'], 0)
        self.assertLess(result.parameters['chl'], 20)  # Adjust based on your expected max chl

        # Verify that RMSE is reasonably low (adjust threshold as needed)
        self.assertLess(result.objective_value, 0.1)

    def test_error_space_visualization(self):
        """Visualize the error space for different parameter combinations."""
        try:
            # Load the image and extract the pixel spectrum
            _, _, pixel_rrs = self.load_image_and_extract_pixel()
        except FileNotFoundError:
            self.skipTest(f"Image file not found: {self.image_path}")
            return
        
        # Create output directory
        output_dir = Path('../../tests/output')
        output_dir.mkdir(exist_ok=True)
        
        # Define parameter pairs to visualize
        param_pairs = [
            ('depth', 'chl'),
            ('cdom', 'nap'),
            ('depth', 'cdom'),
            ('chl', 'nap')
        ]
        
        # Define grid sizes for each parameter
        grid_size = 20
        param_ranges = {
            'depth': np.linspace(0.1, 10, grid_size),
            'chl': np.linspace(0.5, 3.3, grid_size),
            'cdom': np.linspace(0.001, 0.42, grid_size),
            'nap': np.linspace(0.1, 9.0, grid_size)
        }
        
        # For each parameter pair, create a heatmap
        for param1, param2 in param_pairs:
            print(f"Generating error heatmap for {param1} vs {param2}...")
            
            # Create error grid
            error_grid = np.zeros((grid_size, grid_size))
            
            # Get the best values from a regular inversion to use for fixed parameters
            base_result = invert_spectrum(pixel_rrs, self.inversion_params)
            best_params = base_result.parameters
            
            # Loop through parameter combinations
            for i, val1 in enumerate(param_ranges[param1]):
                for j, val2 in enumerate(param_ranges[param2]):
                    # Create parameters for forward model
                    forward_params = {
                        'wavelengths': self.wavelengths_used,
                        'a_water': self.inversion_params.a_water,
                        'a_ph_star': self.inversion_params.a_ph_star,
                        'a_cdom_slope': self.inversion_params.a_cdom_slope,
                        'a_nap_slope': self.inversion_params.a_nap_slope,
                        'bb_ph_slope': self.inversion_params.bb_ph_slope,
                        'lambda0cdom': self.inversion_params.lambda0cdom,
                        'lambda0nap': self.inversion_params.lambda0nap,
                        'lambda0x': self.inversion_params.lambda0x,
                        'x_ph_lambda0x': self.inversion_params.x_ph_lambda0x,
                        'x_nap_lambda0x': self.inversion_params.x_nap_lambda0x,
                        'a_cdom_lambda0cdom': self.inversion_params.a_cdom_lambda0cdom,
                        'a_nap_lambda0nap': self.inversion_params.a_nap_lambda0nap,
                        'substrate1': self.inversion_params.substrate1,
                        'substrate2': self.inversion_params.substrate2,
                        'substrate_fraction': self.inversion_params.fixed_substrate_fraction
                    }
                    
                    # Add the best parameters from inversion
                    for param_name in ['chl', 'cdom', 'nap', 'depth']:
                        if param_name in best_params:
                            forward_params[param_name] = best_params[param_name]
                    
                    # Override the two parameters we're testing
                    forward_params[param1] = val1
                    forward_params[param2] = val2
                    
                    # Run forward model to get modeled spectrum
                    results = sbc.forward_model(**forward_params, num_bands=len(pixel_rrs))
                    
                    # Calculate error
                    error = np.sqrt(np.mean((results.rrs - pixel_rrs) ** 2))
                    error_grid[i, j] = error
            
            # Create heatmap
            plt.figure(figsize=(10, 8))
            
            # Use log scale for better visualization of error differences
            vmin = np.min(error_grid[error_grid > 0])
            plt.imshow(error_grid, origin='lower', aspect='auto', 
                      extent=[param_ranges[param2][0], param_ranges[param2][-1], 
                              param_ranges[param1][0], param_ranges[param1][-1]],
                      cmap='viridis_r', norm=plt.cm.colors.LogNorm(vmin=vmin))
            
            plt.colorbar(label='RMSE')
            plt.xlabel(f'{param2}')
            plt.ylabel(f'{param1}')
            plt.title(f'Error Space: {param1} vs {param2}')
            
            # Mark the best solution
            plt.plot(best_params[param2], best_params[param1], 'ro', markersize=10)
            plt.annotate('Best fit', (best_params[param2], best_params[param1]), 
                        xytext=(10, 10), textcoords='offset points', color='white')
            
            # Save the figure
            plt.tight_layout()
            plt.savefig(output_dir / f'error_heatmap_{param1}_vs_{param2}.png', dpi=300)
            plt.close()
        
        # Create a 3D visualization for depth, chl, and error
        from mpl_toolkits.mplot3d import Axes3D
        
        # Select two parameters for 3D plot
        param1, param2 = 'depth', 'chl'
        
        # Create meshgrid for 3D surface
        X, Y = np.meshgrid(param_ranges[param2], param_ranges[param1])
        
        # Get the corresponding error grid
        idx = param_pairs.index((param1, param2))
        Z = error_grid  # This should be the error grid for depth vs chl
        
        # Create 3D plot
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot surface
        surf = ax.plot_surface(X, Y, Z, cmap='viridis_r', alpha=0.8)
        
        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='RMSE')
        
        # Set labels
        ax.set_xlabel(param2)
        ax.set_ylabel(param1)
        ax.set_zlabel('Error (RMSE)')
        ax.set_title(f'3D Error Surface: {param1} vs {param2}')
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(output_dir / f'error_surface_3d_{param1}_vs_{param2}.png', dpi=300)
        plt.close()
        
        print("Error space visualization completed. Check the output directory for heatmaps.")


if __name__ == '__main__':
    unittest.main()