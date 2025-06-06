"""
Simple LUT-based Bathymetry Processing Example

A streamlined example showing how to use Look-Up Tables for fast bathymetry mapping.
"""
import os
import time
from pathlib import Path

import numpy as np

from sambuca.core.workflows import BathymetryWorkflow
from sambuca.core.inversion import LookUpTable, process_image


def main():
    # Define paths
    siop_dir = Path("../data/siops")
    image_path = Path("../data/input/examples/anholt_20170823_b02b09.tif")
    output_dir = Path("../data/output/simple_lut_example")

    print("Building LUT for fast bathymetry processing...")

    # Create workflow
    workflow = BathymetryWorkflow(str(siop_dir), sensor='sentinel2')

    # Set up for depth-only inversion (fastest LUT option)
    workflow.customize_parameters(
        depth=(0, 25),
        fixed_chl=5.6,
        fixed_nap=0.001,
        fixed_cdom=0.09,
        fixed_substrate_fraction=1,
    )

    workflow.wavelengths = [492.4, 559.8, 664.6, 704.1]
    workflow.bands = [2, 3, 4, 5]

    # Build LUT (this may take a few minutes the first time)
    lut = LookUpTable(workflow.inversion_params)

    print("Building LUT with 30 depth levels...")
    start_time = time.time()
    lut.build_table(
        grid_size=200,  # 30 depth values from 0-25m
        progress_bar=True,
        use_kdtree=True  # Enable fast lookups
    )
    build_time = time.time() - start_time
    print(f"LUT built in {build_time:.1f} seconds")

    # Process image using LUT
    print(f"Processing image: {image_path.name}")

    # Load image
    image_data = workflow.image_loader.load(str(image_path), bands=workflow.bands)

    # Process with LUT (much faster than optimization)
    start_time = time.time()
    results = process_image(
        image_data.data,
        workflow.inversion_params,
        lut=lut,  # Use our LUT
        n_processes=4,
        progress_bar=True,
        refinement=False  # Pure LUT lookup for speed
    )
    process_time = time.time() - start_time

    print(f"Image processed in {process_time:.1f} seconds")

    # Show results
    depth_map = results['depth']
    valid_depths = depth_map[~np.isnan(depth_map)]

    if len(valid_depths) > 0:
        print(f"\nResults:")
        print(f"  Valid pixels: {len(valid_depths):,}")
        print(f"  Depth range: {valid_depths.min():.1f} - {valid_depths.max():.1f} m")
        print(f"  Mean depth: {valid_depths.mean():.1f} m")

    # Save results
    os.makedirs(output_dir, exist_ok=True)

    from sambuca.core.results import ImageInversionResult
    result_obj = ImageInversionResult(
        results=results,
        image_metadata=image_data.metadata,
        workflow_config=workflow.get_config(),
        image_path=str(image_path)
    )

    result_obj.save_all_parameters(str(output_dir), formats=['tiff'])
    result_obj.plot_summary(save_path=str(output_dir / "bathymetry_lut.png"))

    print(f"\nResults saved to: {output_dir}")
    print(f"Total processing time: {build_time + process_time:.1f} seconds")


if __name__ == "__main__":
    main()