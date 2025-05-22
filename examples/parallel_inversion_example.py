#!/usr/bin/env python
"""Example demonstrating parallel inversion with Sambuca.

This script demonstrates how to use the parallel processing capabilities
for inverting a hyperspectral image with Sambuca.
"""

import os
import time
import numpy as np
import matplotlib.pyplot as plt
import rasterio

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, process_image
from sambuca_core.utility.plotting import plot_inversion_results

# Try to import parallel processing modules
try:
    from sambuca_core.inversion.parallel_processor import parallel_inversion

    PARALLEL_AVAILABLE = True
    print("Parallel processing is available")
except ImportError:
    PARALLEL_AVAILABLE = False
    print("Parallel processing is not available")


def main():
    """Run the parallel inversion example."""
    # Define paths - adjust these as needed
    input_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'images', 'Browser_images_clipped.tif')
    mask_input = os.path.join(os.path.dirname(input_file), 'Browser_images__ndwi_clipped.tif')
    siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
    sensor_filter_input = os.path.join(os.path.dirname(input_file), '..', '..', 'sensor_filters', 'sensor_filters.csv')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'output')

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define Sentinel-2 band wavelengths
    sentinel2_wavelengths = {
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
    bands_used = ["B1", "B2", "B3", "B4", "B5"]
    wavelengths_used = [sentinel2_wavelengths[w] for w in bands_used]

    # Load the image
    with rasterio.open(input_file) as src:
        # Read all bands
        image_int16 = src.read()[:, :, :]
        metadata = src.meta

        # Use appropriate scaling factor
        scaling_factor = 10000.0 if metadata['dtype'] == 'uint16' else 1.0

        # Convert to surface reflectance (0-1)
        surface_reflectance = image_int16.astype(np.float32) / scaling_factor

        # Handle no-data values
        no_data_mask = (image_int16 <= 0)
        surface_reflectance[no_data_mask] = np.nan

        # Convert to remote sensing reflectance
        rrs = surface_reflectance / np.pi

        # Transpose to (height, width, bands) for easier pixel access
        rrs_image = np.transpose(rrs, (1, 2, 0))

    if mask_input is not None and mask_input != '':
        with rasterio.open(mask_input) as src:
            mask_image = src.read()
            data_mask = (mask_image[2, ...] > 0.75)
    else:
        data_mask = np.ones_like(rrs_image[..., 0], dtype=bool)

    # Initialize SIOP manager
    siop_manager = sbc.SIOPManager(siop_dir)
    siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)

    # Create inversion parameters
    params = InversionParameters(
        # Parameters to invert for (with bounds)
      #  depth=(0.1, 10.0),
      #  chl=(1, 5.2),
      #  cdom=(0.0001, .0221),
      #  nap=(0, 5),
      #  substrate_fraction=(0, 1)
    )

    # Update parameters from SIOP manager
    params.update_from_siop_manager(siop_manager, "Sentinel-2")
    params.configure_for_shallow_water()
 #   params.enable_siop_optimization(conservative=False)
    # Print inversion settings
    print("\n" + "=" * 50)
    print("INVERSION SETTINGS:")
    print("=" * 50)
    print(f"Wavelengths: {wavelengths_used} nm")
    print(f"Parameters to invert: {params.get_inversion_parameter_names()}")
    print(f"Depth range: {params.depth}")
    print(f"Chlorophyll range: {params.chl}")
    print(f"CDOM range: {params.cdom}")
    print(f"NAP range: {params.nap}")
    print("=" * 50)

    # Time the execution
    start_time = time.time()

    # For demonstration, let's use a small subset of the image
    subset_size = 100
    h, w = rrs_image.shape[:2]
    start_h, start_w = h // 2 - subset_size // 2, w // 2 - subset_size // 2
    rrs_subset = rrs_image[start_h:start_h + subset_size, start_w:start_w + subset_size, :]
    mask_subset = data_mask[start_h:start_h + subset_size, start_w:start_w + subset_size]

    use_subset = True
    if use_subset:
        rrs_to_use = rrs_subset
        mask_to_use = mask_subset
    else:
        rrs_to_use = rrs_image
        mask_to_use = data_mask

    # Run parallel processing on the subset
    print(f"\nProcessing image subset of shape {rrs_to_use.shape}...")

    # Compare parallel vs. non-parallel processing
    results = {}

    # Process with different configurations
    configs = [
        # name, use_multi_start, n_processes, parallel_batch_processing
    ]

    if PARALLEL_AVAILABLE:
        configs.extend([
            ("Parallel", True, 4, True),
        ])

    sensor_filter = sbc.load_sensor_filter_from_csv(filename=sensor_filter_input)
    wl, responses = sensor_filter
    sensor_filter = tuple((wl, responses[1:]))
    for name, use_multi_start, n_processes, parallel_batch_processing in configs:
        print(f"\nRunning {name} inversion...")
        config_start_time = time.time()

        results[name] = process_image(
            rrs_to_use,
            params,
            mask=mask_to_use,
            n_processes=n_processes,
            progress_bar=True,
            sensor_filter=sensor_filter,
            use_multi_start=use_multi_start,
            n_starts=5 if use_multi_start else 1,
            parallel_batch_processing=parallel_batch_processing,
            chunk_size=50,
        )

        config_elapsed_time = time.time() - config_start_time
        print(f"{name} processing completed in {config_elapsed_time:.2f} seconds")

    # Compare results
    print("\n" + "=" * 50)
    print("RESULTS COMPARISON:")
    print("=" * 50)

    for name, result in results.items():
        valid_mask = ~np.isnan(result['depth'])
        n_valid = np.sum(valid_mask)

        if n_valid > 0:
            print(f"\n{name} Statistics:")
            print(f"  Valid pixels: {n_valid} ({n_valid / mask_subset.sum() * 100:.1f}%)")
            print(f"  Mean depth: {np.nanmean(result['depth']):.2f} m")
            print(f"  Mean error: {np.nanmean(result['error']):.6f}")
        else:
            print(f"NO VALID RESULTS ...")
    # Plot results
    plt.figure(figsize=(15, 10))

    for i, (name, result) in enumerate(results.items()):
        plt.subplot(2, len(results), i + 1)
        plt.imshow(result['depth'], cmap='viridis')
        plt.title(f"{name}: Depth")
        plt.colorbar(label='Depth (m)')

        plt.subplot(2, len(results), i + 1 + len(results))
        plt.imshow(result['error'], cmap='Reds')
        plt.title(f"{name}: Error")
        plt.colorbar(label='Error (RMSE)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "parallel_inversion_comparison.png"), dpi=300)

    # Get elapsed time
    elapsed_time = time.time() - start_time
    print(f"\nTotal processing time: {elapsed_time:.2f} seconds")
    print("\nResults saved to output directory")


if __name__ == "__main__":
    main()