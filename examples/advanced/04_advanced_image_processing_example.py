#!/usr/bin/env python3
"""
Advanced Image Processing Example
================================

This example demonstrates advanced features for processing satellite imagery:
1. Adaptive parameter bounds based on image statistics
2. Quality control and masking
3. Batch processing for memory efficiency
4. Uncertainty estimation
5. Advanced visualization and analysis
6. Export to different formats

This builds on the previous examples and shows production-ready workflows.
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from tqdm import tqdm

import sambuca_core as sbc
from sambuca_core.inversion import (
    InversionParameters, process_image, batch_process_image,
    create_adaptive_inversion_parameters, calculate_image_statistics
)


class AdvancedImageProcessor:
    """Advanced image processor with quality control and optimization."""

    def __init__(self, siop_directory: str):
        """Initialize the processor with SIOP data."""
        self.siop_manager = sbc.SIOPManager(siop_directory)
        self.setup_sensors()

    def setup_sensors(self):
        """Set up common sensor configurations."""
        self.sensor_configs = {
            "Sentinel-2": {
                "wavelengths": [492.4, 559.8, 664.6, 704.1, 740.5, 782.8, 832.8],
                "bands": ["B2", "B3", "B4", "B5", "B6", "B7", "B8"],
                "scaling_factor": 10000.0
            },
            "Landsat-8": {
                "wavelengths": [482, 562, 655, 865],
                "bands": ["B2", "B3", "B4", "B5"],
                "scaling_factor": 10000.0
            },
            "MODIS": {
                "wavelengths": [488, 531, 551, 667, 678, 748, 869],
                "bands": ["Band1", "Band2", "Band3", "Band4", "Band5", "Band6", "Band7"],
                "scaling_factor": 1.0
            }
        }

        # Register all sensors
        for sensor_name, config in self.sensor_configs.items():
            self.siop_manager.register_sensor(sensor_name, config["wavelengths"])

    def load_and_preprocess_image(self, image_path: str, sensor: str = "Sentinel-2",
                                  subset_bands: int = None) -> dict:
        """Load and preprocess satellite imagery with quality control."""

        print(f"Loading image: {image_path}")
        print(f"Sensor: {sensor}")

        sensor_config = self.sensor_configs[sensor]

        with rasterio.open(image_path) as src:
            # Read metadata
            metadata = src.meta
            print(f"Image dimensions: {src.height} x {src.width}")
            print(f"Number of bands: {src.count}")
            print(f"Data type: {metadata['dtype']}")

            # Determine how many bands to use
            max_bands = len(sensor_config["wavelengths"])
            if subset_bands:
                max_bands = min(subset_bands, max_bands)

            bands_to_use = min(src.count, max_bands)
            wavelengths_used = sensor_config["wavelengths"][:bands_to_use]

            print(f"Using {bands_to_use} bands: {wavelengths_used}")

            # Read image data
            image_data = src.read(list(range(1, bands_to_use + 1)))

            # Convert to reflectance
            scaling_factor = sensor_config["scaling_factor"]
            if metadata['dtype'] == 'float32':
                scaling_factor = 1.0

            print(f"Applying scaling factor: {scaling_factor}")

            # Convert to surface reflectance
            surface_reflectance = image_data.astype(np.float32) / scaling_factor

            # Quality control - remove invalid values
            invalid_mask = (image_data <= 0) | (image_data >= 65535)
            surface_reflectance[invalid_mask] = np.nan

            # Convert to remote sensing reflectance (Rrs)
            rrs = surface_reflectance / np.pi

            # Additional quality control
            rrs[rrs < 0] = np.nan
            rrs[rrs > 0.2] = np.nan  # Remove unrealistically high values

            # Transpose to (height, width, bands) format
            rrs_image = np.transpose(rrs, (1, 2, 0))

            return {
                'rrs_image': rrs_image,
                'metadata': metadata,
                'wavelengths': wavelengths_used,
                'sensor': sensor,
                'original_shape': image_data.shape,
                'valid_pixel_fraction': np.mean(~np.isnan(rrs_image[..., 0]))
            }

    def create_water_mask(self, rrs_image: np.ndarray, wavelengths: list) -> np.ndarray:
        """Create a water mask using spectral indices."""

        print("Creating water mask...")

        # Find band indices
        blue_idx = self._find_closest_band(wavelengths, 490)
        green_idx = self._find_closest_band(wavelengths, 560)
        red_idx = self._find_closest_band(wavelengths, 660)
        nir_idx = self._find_closest_band(wavelengths, 840)

        # Calculate NDWI (Normalized Difference Water Index)
        if green_idx is not None and nir_idx is not None:
            ndwi = ((rrs_image[..., green_idx] - rrs_image[..., nir_idx]) /
                    (rrs_image[..., green_idx] + rrs_image[..., nir_idx] + 1e-8))
            water_mask = ndwi > 0.1
        else:
            # Fallback: use NIR threshold
            if nir_idx is not None:
                water_mask = rrs_image[..., nir_idx] < 0.01
            else:
                # Use all pixels if no NIR available
                water_mask = ~np.isnan(rrs_image[..., 0])

        # Remove isolated pixels (morphological operations)
        from scipy import ndimage
        water_mask = ndimage.binary_opening(water_mask, structure=np.ones((3, 3)))
        water_mask = ndimage.binary_closing(water_mask, structure=np.ones((5, 5)))

        water_fraction = np.mean(water_mask)
        print(f"Water pixels: {water_fraction * 100:.1f}% of image")

        return water_mask

    def _find_closest_band(self, wavelengths: list, target_wl: float) -> int | None:
        """Find the band index closest to target wavelength."""
        if not wavelengths:
            return None
        differences = [abs(wl - target_wl) for wl in wavelengths]
        return differences.index(min(differences))

    def setup_adaptive_inversion(self, rrs_image: np.ndarray, wavelengths: list,
                                 sensor: str, water_type: str = "coastal") -> InversionParameters:
        """Set up adaptive inversion parameters based on image characteristics."""

        print("Setting up adaptive inversion parameters...")

        # Calculate image statistics
        valid_mask = ~np.isnan(rrs_image).any(axis=2)
        image_stats = calculate_image_statistics(rrs_image, valid_mask)

        print(f"Image statistics:")
        print(f"  Mean reflectance: {image_stats['mean_reflectance']:.4f}")
        print(f"  Blue-green ratio: {image_stats['blue_green_ratio']:.2f}")
        print(f"  Overall brightness: {image_stats['overall_brightness']:.4f}")

        # Create adaptive parameters
        params = create_adaptive_inversion_parameters(
            wavelengths=wavelengths,
            siop_manager=self.siop_manager,
            sensor_name=sensor,
            water_type=water_type,
            image_stats=image_stats
        )

        print("Inversion parameter bounds:")
        bounds = params.get_parameter_bounds()
        param_names = params.get_inversion_parameter_names()
        for name, (low, high) in zip(param_names, bounds):
            print(f"  {name}: {low:.3f} - {high:.3f}")

        return params

    def process_with_quality_control(self, rrs_image: np.ndarray, params: InversionParameters,
                                     water_mask: np.ndarray, **kwargs) -> dict:
        """Process image with comprehensive quality control."""

        print("Processing image with quality control...")

        # Process in batches for memory efficiency
        if rrs_image.shape[0] * rrs_image.shape[1] > 1000000:  # > 1M pixels
            print("Large image detected, using batch processing...")
            results = batch_process_image(
                rrs_image, params,
                mask=water_mask,
                batch_size=(512, 512),
                n_processes=4,
                **kwargs
            )
        else:
            results = process_image(
                rrs_image, params,
                mask=water_mask,
                **kwargs
            )

        # Quality control on results
        results = self._apply_quality_control(results)

        return results

    def _apply_quality_control(self, results: dict) -> dict:
        """Apply quality control filters to inversion results."""

        print("Applying quality control filters...")

        # Remove physically unrealistic results
        if 'depth' in results:
            # Remove negative depths
            invalid_depth = results['depth'] < 0
            results['depth'][invalid_depth] = np.nan

            # Remove unrealistically deep results (>100m for shallow water remote sensing)
            very_deep = results['depth'] > 100
            results['depth'][very_deep] = np.nan

        if 'chl' in results:
            # Remove negative chlorophyll
            invalid_chl = results['chl'] < 0
            results['chl'][invalid_chl] = np.nan

            # Remove extremely high chlorophyll (>200 mg/m³)
            very_high_chl = results['chl'] > 200
            results['chl'][very_high_chl] = np.nan

        # Remove pixels with very high errors
        if 'error' in results:
            high_error = results['error'] > 0.01  # Adjust threshold as needed
            for param in ['depth', 'chl', 'cdom', 'nap']:
                if param in results:
                    results[param][high_error] = np.nan

        # Calculate quality metrics
        if 'depth' in results:
            valid_pixels = np.sum(~np.isnan(results['depth']))
            total_pixels = np.size(results['depth'])
            print(f"Quality control: {valid_pixels}/{total_pixels} "
                  f"({valid_pixels / total_pixels * 100:.1f}%) pixels passed QC")

        return results

    def estimate_uncertainty(self, rrs_image: np.ndarray, params: InversionParameters,
                             results: dict, n_bootstrap: int = 50) -> dict:
        """Estimate uncertainty using bootstrap resampling."""

        print(f"Estimating uncertainty using {n_bootstrap} bootstrap samples...")

        # Simple uncertainty estimation by adding noise and re-inverting
        uncertainties = {}

        # Sample a subset of pixels for uncertainty analysis
        valid_mask = ~np.isnan(results['depth'])
        valid_coords = np.where(valid_mask)

        if len(valid_coords[0]) == 0:
            print("No valid pixels for uncertainty estimation")
            return {}

        # Sample up to 100 pixels for uncertainty analysis
        n_sample = min(100, len(valid_coords[0]))
        sample_indices = np.random.choice(len(valid_coords[0]), n_sample, replace=False)

        sample_y = valid_coords[0][sample_indices]
        sample_x = valid_coords[1][sample_indices]

        # For each parameter, collect bootstrap estimates
        param_names = params.get_inversion_parameter_names()
        bootstrap_results = {param: [] for param in param_names}

        for i in tqdm(range(n_bootstrap), desc="Bootstrap sampling"):
            for j, (y, x) in enumerate(zip(sample_y, sample_x)):
                # Add noise to observed spectrum
                observed_rrs = rrs_image[y, x, :]
                noise_level = 0.001  # 0.1% noise
                noise = np.random.normal(0, noise_level, len(observed_rrs))
                noisy_rrs = observed_rrs + noise

                try:
                    from sambuca_core.inversion import invert_spectrum
                    result = invert_spectrum(noisy_rrs, params)

                    for param in param_names:
                        bootstrap_results[param].append(result.parameters[param])

                except:
                    # Skip failed inversions
                    continue

        # Calculate uncertainty statistics
        for param in param_names:
            if bootstrap_results[param]:
                values = np.array(bootstrap_results[param])
                uncertainties[param] = {
                    'std': np.std(values),
                    'p5': np.percentile(values, 5),
                    'p95': np.percentile(values, 95),
                    'median': np.median(values)
                }

        print("Uncertainty estimates:")
        for param, stats in uncertainties.items():
            print(f"  {param}: std={stats['std']:.3f}, "
                  f"5-95%: {stats['p5']:.3f}-{stats['p95']:.3f}")

        return uncertainties

    def export_results(self, results: dict, output_dir: str, base_filename: str,
                       metadata: dict, export_formats: list = None):
        """Export results to various formats."""

        if export_formats is None:
            export_formats = ['geotiff', 'csv', 'netcdf']

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        print(f"Exporting results to {output_dir}...")

        # Export as GeoTIFF
        if 'geotiff' in export_formats:
            self._export_geotiff(results, output_dir, base_filename, metadata)

        # Export as CSV
        if 'csv' in export_formats:
            self._export_csv(results, output_dir, base_filename)

        # Export as NetCDF
        if 'netcdf' in export_formats:
            self._export_netcdf(results, output_dir, base_filename, metadata)

    def _export_geotiff(self, results: dict, output_dir: Path, base_filename: str, metadata: dict):
        """Export results as GeoTIFF files."""

        # Update metadata for single band output
        output_meta = metadata.copy()
        output_meta.update({
            'count': 1,
            'dtype': 'float32',
            'nodata': np.nan
        })

        for param_name, data in results.items():
            if param_name in ['depth', 'chl', 'cdom', 'nap', 'error']:
                output_path = output_dir / f"{base_filename}_{param_name}.tif"

                with rasterio.open(output_path, 'w', **output_meta) as dst:
                    dst.write(data.astype('float32'), 1)
                    dst.set_band_description(1, f"{param_name}")

                print(f"  Saved {param_name} to {output_path}")

    def _export_csv(self, results: dict, output_dir: Path, base_filename: str):
        """Export results as CSV file."""

        # Flatten all result arrays and create DataFrame
        data_dict = {}

        for param_name, data in results.items():
            if param_name in ['depth', 'chl', 'cdom', 'nap', 'error']:
                # Create coordinate arrays
                if 'y_coords' not in data_dict:
                    height, width = data.shape
                    y_coords, x_coords = np.meshgrid(range(height), range(width), indexing='ij')
                    data_dict['y'] = y_coords.flatten()
                    data_dict['x'] = x_coords.flatten()

                data_dict[param_name] = data.flatten()

        # Create DataFrame and remove NaN rows
        df = pd.DataFrame(data_dict)
        df = df.dropna()

        output_path = output_dir / f"{base_filename}_results.csv"
        df.to_csv(output_path, index=False)
        print(f"  Saved CSV to {output_path}")

    def _export_netcdf(self, results: dict, output_dir: Path, base_filename: str, metadata: dict):
        """Export results as NetCDF file."""

        try:
            import xarray as xr

            # Create coordinate arrays
            height, width = list(results.values())[0].shape
            y_coords = np.arange(height)
            x_coords = np.arange(width)

            # Create dataset
            data_vars = {}
            for param_name, data in results.items():
                if param_name in ['depth', 'chl', 'cdom', 'nap', 'error']:
                    data_vars[param_name] = (['y', 'x'], data)

            ds = xr.Dataset(
                data_vars,
                coords={'y': y_coords, 'x': x_coords}
            )

            # Add attributes
            ds.attrs['title'] = 'Sambuca Inversion Results'
            ds.attrs['source'] = 'Sambuca Core'

            output_path = output_dir / f"{base_filename}_results.nc"
            ds.to_netcdf(output_path)
            print(f"  Saved NetCDF to {output_path}")

        except ImportError:
            print("  xarray not available, skipping NetCDF export")

    def create_advanced_visualizations(self, results: dict, wavelengths: list,
                                       output_dir: str, uncertainties: dict = None):
        """Create advanced visualization plots."""

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        print("Creating advanced visualizations...")

        # Create multi-panel results plot
        self._create_results_overview(results, output_dir)

        # Create histogram plots
        self._create_parameter_histograms(results, output_dir)

        # Create scatter plots
        self._create_parameter_relationships(results, output_dir)

        # Create uncertainty plots if available
        if uncertainties:
            self._create_uncertainty_plots(uncertainties, output_dir)

        # Create quality assessment plots
        self._create_quality_assessment(results, output_dir)

    def _create_results_overview(self, results: dict, output_dir: Path):
        """Create overview plot of all results."""

        param_names = [p for p in ['depth', 'chl', 'cdom', 'nap'] if p in results]
        n_params = len(param_names)

        if n_params == 0:
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()

        for i, param in enumerate(param_names):
            if i >= 4:
                break

            ax = axes[i]
            data = results[param]

            # Create masked array for plotting
            masked_data = np.ma.masked_invalid(data)

            im = ax.imshow(masked_data, cmap='viridis')
            ax.set_title(f'{param.upper()}')
            plt.colorbar(im, ax=ax)

        # Hide unused subplots
        for i in range(n_params, 4):
            axes[i].set_visible(False)

        plt.tight_layout()
        plt.savefig(output_dir / 'results_overview.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_parameter_histograms(self, results: dict, output_dir: Path):
        """Create histogram plots for each parameter."""

        param_names = [p for p in ['depth', 'chl', 'cdom', 'nap'] if p in results]

        if not param_names:
            return

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()

        for i, param in enumerate(param_names):
            if i >= 4:
                break

            ax = axes[i]
            data = results[param]
            valid_data = data[~np.isnan(data)]

            if len(valid_data) > 0:
                ax.hist(valid_data, bins=50, alpha=0.7, edgecolor='black')
                ax.set_xlabel(f'{param.upper()}')
                ax.set_ylabel('Frequency')
                ax.set_title(f'{param.upper()} Distribution')
                ax.grid(True, alpha=0.3)

        # Hide unused subplots
        for i in range(len(param_names), 4):
            axes[i].set_visible(False)

        plt.tight_layout()
        plt.savefig(output_dir / 'parameter_histograms.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_parameter_relationships(self, results: dict, output_dir: Path):
        """Create scatter plots showing parameter relationships."""

        if 'depth' in results and 'chl' in results:
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))

            depth_data = results['depth'].flatten()
            chl_data = results['chl'].flatten()

            # Remove NaN values
            valid_mask = ~(np.isnan(depth_data) | np.isnan(chl_data))
            depth_valid = depth_data[valid_mask]
            chl_valid = chl_data[valid_mask]

            if len(depth_valid) > 0:
                ax.scatter(depth_valid, chl_valid, alpha=0.5, s=1)
                ax.set_xlabel('Depth (m)')
                ax.set_ylabel('Chlorophyll (mg/m³)')
                ax.set_title('Depth vs Chlorophyll Relationship')
                ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(output_dir / 'depth_chl_relationship.png', dpi=300, bbox_inches='tight')
            plt.close()

    def _create_uncertainty_plots(self, uncertainties: dict, output_dir: Path):
        """Create uncertainty visualization plots."""

        if not uncertainties:
            return

        # Create uncertainty summary plot
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

        params = list(uncertainties.keys())
        std_values = [uncertainties[p]['std'] for p in params]

        bars = ax.bar(params, std_values)
        ax.set_ylabel('Standard Deviation')
        ax.set_title('Parameter Uncertainty Estimates')
        ax.grid(True, alpha=0.3)

        # Add value labels on bars
        for bar, std_val in zip(bars, std_values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f'{std_val:.3f}', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(output_dir / 'uncertainty_estimates.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_quality_assessment(self, results: dict, output_dir: Path):
        """Create quality assessment plots."""

        if 'error' not in results:
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Error map
        error_data = results['error']
        masked_error = np.ma.masked_invalid(error_data)

        im1 = ax1.imshow(masked_error, cmap='Reds')
        ax1.set_title('Inversion Error (RMSE)')
        plt.colorbar(im1, ax=ax1)

        # Error histogram
        valid_errors = error_data[~np.isnan(error_data)]
        if len(valid_errors) > 0:
            ax2.hist(valid_errors, bins=50, alpha=0.7, edgecolor='black')
            ax2.set_xlabel('RMSE')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Error Distribution')
            ax2.grid(True, alpha=0.3)

            # Add statistics
            mean_error = np.mean(valid_errors)
            median_error = np.median(valid_errors)
            ax2.axvline(mean_error, color='red', linestyle='--', label=f'Mean: {mean_error:.4f}')
            ax2.axvline(median_error, color='blue', linestyle='--', label=f'Median: {median_error:.4f}')
            ax2.legend()

        plt.tight_layout()
        plt.savefig(output_dir / 'quality_assessment.png', dpi=300, bbox_inches='tight')
        plt.close()


def main():
    """Main function demonstrating advanced image processing workflow."""

    print("=" * 70)
    print("SAMBUCA CORE - Advanced Image Processing Example")
    print("=" * 70)

    # Configuration
    config = {
        'image_path': os.path.join(os.path.dirname(__file__), "..", "..", "data", "input", "examples",
                                  "advanced", "anholt_20170823_b02b09_clipped2.tif"),  # Update this path
        'siop_directory': os.path.join(os.path.dirname(__file__), "..", "..", "data", "siops"),  # Update this path
        'sensor': 'Sentinel-2',
        'water_type': 'coastal',  # 'oceanic', 'coastal', or 'inland'
        'output_directory': os.path.join(os.path.dirname(__file__), "..", "..", "data", "output", "examples",
                                         "advanced"),
        'n_processes': 4,
        'estimate_uncertainty': True,
        'export_formats': ['geotiff', 'csv']
    }

    # Initialize processor
    try:
        processor = AdvancedImageProcessor(config['siop_directory'])
    except Exception as e:
        print(f"Error initializing processor: {e}")
        print("Make sure the SIOP directory exists and contains valid data")
        return

    # Check if image file exists
    if not os.path.exists(config['image_path']):
        print(f"Image file not found: {config['image_path']}")
        print("Please update the image_path in the config dictionary")
        print("You can use the provided example or your own satellite imagery")
        return

    try:
        # Step 1: Load and preprocess image
        print("\nStep 1: Loading and preprocessing image...")
        image_data = processor.load_and_preprocess_image(
            config['image_path'],
            config['sensor']
        )

        print(f"Valid pixel fraction: {image_data['valid_pixel_fraction']:.2f}")

        # Step 2: Create water mask
        print("\nStep 2: Creating water mask...")
        water_mask = processor.create_water_mask(
            image_data['rrs_image'],
            image_data['wavelengths']
        )

        # Step 3: Set up adaptive inversion
        print("\nStep 3: Setting up adaptive inversion...")
        inversion_params = processor.setup_adaptive_inversion(
            image_data['rrs_image'],
            image_data['wavelengths'],
            config['sensor'],
            config['water_type']
        )

        # Step 4: Process image
        print("\nStep 4: Processing image...")
        results = processor.process_with_quality_control(
            image_data['rrs_image'],
            inversion_params,
            water_mask,
            n_processes=config['n_processes'],
            progress_bar=True
        )

        # Step 5: Estimate uncertainty (optional)
        uncertainties = {}
        if config['estimate_uncertainty']:
            print("\nStep 5: Estimating uncertainty...")
            uncertainties = processor.estimate_uncertainty(
                image_data['rrs_image'],
                inversion_params,
                results,
                n_bootstrap=25  # Reduced for example
            )

        # Step 6: Export results
        print("\nStep 6: Exporting results...")
        processor.export_results(
            results,
            config['output_directory'],
            'advanced_processing',
            image_data['metadata'],
            config['export_formats']
        )

        # Step 7: Create visualizations
        print("\nStep 7: Creating visualizations...")
        processor.create_advanced_visualizations(
            results,
            image_data['wavelengths'],
            config['output_directory'],
            uncertainties
        )

        # Step 8: Print summary statistics
        print("\nStep 8: Summary statistics...")
        print_processing_summary(results, uncertainties)

    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 70)
    print("Advanced image processing completed successfully!")
    print(f"Results saved to: {config['output_directory']}")
    print("=" * 70)


def print_processing_summary(results: dict, uncertainties: dict):
    """Print comprehensive processing summary."""

    print("Processing Summary:")
    print("-" * 30)

    for param_name in ['depth', 'chl', 'cdom', 'nap']:
        if param_name not in results:
            continue

        data = results[param_name]
        valid_data = data[~np.isnan(data)]

        if len(valid_data) == 0:
            print(f"{param_name.upper()}: No valid data")
            continue

        stats = {
            'count': len(valid_data),
            'min': np.min(valid_data),
            'max': np.max(valid_data),
            'mean': np.mean(valid_data),
            'median': np.median(valid_data),
            'std': np.std(valid_data)
        }

        print(f"{param_name.upper()}:")
        print(f"  Valid pixels: {stats['count']}")
        print(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
        print(f"  Mean ± Std: {stats['mean']:.3f} ± {stats['std']:.3f}")
        print(f"  Median: {stats['median']:.3f}")

        if param_name in uncertainties:
            unc = uncertainties[param_name]
            print(f"  Uncertainty (std): {unc['std']:.3f}")
            print(f"  90% CI: {unc['p5']:.3f} - {unc['p95']:.3f}")

        print()

    # Error statistics
    if 'error' in results:
        error_data = results['error']
        valid_errors = error_data[~np.isnan(error_data)]

        if len(valid_errors) > 0:
            print("INVERSION QUALITY:")
            print(f"  Mean RMSE: {np.mean(valid_errors):.6f}")
            print(f"  Median RMSE: {np.median(valid_errors):.6f}")
            print(f"  90th percentile RMSE: {np.percentile(valid_errors, 90):.6f}")

            # Quality categories
            excellent = np.sum(valid_errors < 0.001)
            good = np.sum((valid_errors >= 0.001) & (valid_errors < 0.005))
            fair = np.sum((valid_errors >= 0.005) & (valid_errors < 0.01))
            poor = np.sum(valid_errors >= 0.01)

            total = len(valid_errors)
            print(f"  Quality distribution:")
            print(f"    Excellent (<0.001): {excellent / total * 100:.1f}%")
            print(f"    Good (0.001-0.005): {good / total * 100:.1f}%")
            print(f"    Fair (0.005-0.01): {fair / total * 100:.1f}%")
            print(f"    Poor (>0.01): {poor / total * 100:.1f}%")


if __name__ == "__main__":
    main()
