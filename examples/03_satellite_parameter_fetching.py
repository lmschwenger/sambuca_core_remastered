# examples/03_satellite_parameter_fetching.py
"""
Example: Depth-only inversion using satellite-derived water parameters

This example shows how to:
1. Fetch chlorophyll, CDOM, and NAP from Sentinel-3 OLCI data using openEO
2. Use these as fixed parameters for depth-only bathymetry inversion
3. Process an image with satellite-constrained parameters
"""

import os
from datetime import datetime
from pathlib import Path

from sambuca_core.workflows import BathymetryWorkflow, BaseWorkflow
from sambuca_core.inversion import ParameterFetcher


def main():
    # Define paths and location
    siop_dir = Path("../data/siops")
    image_path = Path("../data/input/anholt_20170823_b02b09.tif")
    output_dir = Path("../data/output/satellite_constrained")

    # Image location and date (adjust for your data)
    image_lat = 56.5  # Latitude of image center
    image_lon = 12.3  # Longitude of image center
    image_date = datetime(2017, 8, 23)  # Date of image acquisition

    print("=== Satellite-Constrained Bathymetry Processing ===")
    print(f"Location: {image_lat:.3f}°N, {image_lon:.3f}°E")
    print(f"Date: {image_date.date()}")

    # Step 1: Set up basic workflow
    workflow = BathymetryWorkflow(str(siop_dir), sensor='sentinel2')
    workflow.wavelengths = [492.4, 559.8, 664.6, 704.1]
    workflow.bands = [2, 3, 4, 5]

    # Step 2: Initialize satellite parameter fetcher (now using openEO)
    try:
        print("\n--- Fetching satellite parameters using openEO ---")

        param_fetcher = ParameterFetcher(fetcher_type='sentinel3')

        # Fetch and apply satellite parameters
        updated_params = param_fetcher.update_parameters_from_satellite(
            inversion_params=workflow.inversion_params,
            lat=image_lat,
            lon=image_lon,
            date=image_date,
            parameters_to_fetch=['chl', 'cdom', 'nap'],
            search_days=7,  # Search ±7 days from image date
            max_cloud_cover=30.0,  # Allow up to 30% cloud cover
            buffer_km=10.0  # Search within 10km of location
        )

        # Update workflow with satellite-constrained parameters
        workflow.inversion_params = updated_params

        # Ensure we're only inverting for depth
        workflow.customize_parameters(depth=(0, 25))

        print("\n--- Updated inversion configuration ---")
        print(f"Parameters to invert: {workflow.inversion_params.get_inversion_parameter_names()}")
        print(f"Fixed chlorophyll: {workflow.inversion_params.fixed_chl:.3f} mg/m³")
        print(f"Fixed CDOM: {workflow.inversion_params.fixed_cdom:.3f} m⁻¹")
        print(f"Fixed NAP: {workflow.inversion_params.fixed_nap:.3f} g/m³")

    except Exception as e:
        print(f"⚠️  Satellite parameter fetching failed: {e}")
        print("Falling back to default parameter values...")

        # Use default values if satellite fetch fails
        workflow.customize_parameters(
            depth=(0, 25),
            fixed_chl=1.0,  # Default chlorophyll
            fixed_cdom=0.1,  # Default CDOM
            fixed_nap=0.5  # Default NAP
        )

    # Step 3: Process image with constrained parameters
    print(f"\n--- Processing image: {image_path.name} ---")

    result = workflow.process_image(
        image_path=str(image_path),
        mask_path=None,
        n_processes=4,
        progress_bar=True
    )

    # Step 4: Analyze and save results
    result.print_summary()

    os.makedirs(output_dir, exist_ok=True)
    result.plot_summary(save_path=str(output_dir / "satellite_constrained_bathymetry.png"))
    result.save_all_parameters(str(output_dir), formats=['tiff'])

    print(f"\n✅ Results saved to: {output_dir}")

    # Step 5: Compare with default parameters (optional)
    print("\n--- Comparison with default parameters ---")

    # Process with default parameters for comparison
    workflow_default = BathymetryWorkflow(str(siop_dir), sensor='sentinel2')
    workflow_default.wavelengths = [492.4, 559.8, 664.6, 704.1]
    workflow_default.bands = [2, 3, 4, 5]
    workflow_default.customize_parameters(
        depth=(0, 25),
        fixed_chl=1.0,
        fixed_cdom=0.1,
        fixed_nap=0.5
    )

    result_default = workflow_default.process_image(
        image_path=str(image_path),
        mask_path=None,
        n_processes=2,  # Use fewer processes for comparison
        progress_bar=False
    )

    # Compare depth statistics
    import numpy as np

    satellite_depths = result.get_parameter_map('depth')
    default_depths = result_default.get_parameter_map('depth')

    sat_valid = satellite_depths[~np.isnan(satellite_depths)]
    def_valid = default_depths[~np.isnan(default_depths)]

    if len(sat_valid) > 0 and len(def_valid) > 0:
        print(f"Satellite-constrained depth: {np.mean(sat_valid):.2f} ± {np.std(sat_valid):.2f} m")
        print(f"Default parameters depth:   {np.mean(def_valid):.2f} ± {np.std(def_valid):.2f} m")
        print(f"Mean difference: {np.mean(sat_valid) - np.mean(def_valid):.2f} m")


def check_satellite_availability():
    """Check if satellite data is available for a given location and date."""

    param_fetcher = ParameterFetcher(fetcher_type='sentinel3')

    test_locations = [
        (56.5, 12.3, "Baltic Sea"),
        (25.2, -80.3, "Florida Keys"),
        (36.8, 23.4, "Aegean Sea"),
    ]

    test_date = datetime(2023, 6, 15)

    print("=== Checking Sentinel-3 OLCI Data Availability (via openEO) ===")
    for lat, lon, name in test_locations:
        try:
            available = param_fetcher.is_available(lat, lon, test_date)
            status = "✅ Available" if available else "❌ Not available"
            print(f"{name} ({lat:.1f}°N, {lon:.1f}°E): {status}")
        except Exception as e:
            print(f"{name} ({lat:.1f}°N, {lon:.1f}°E): ⚠️ Error checking: {e}")


def test_openeo_connection():
    """Test openEO connection and authentication."""
    print("=== Testing OpenEO Connection ===")

    try:
        from sambuca_core.data_fetchers import Sentinel3OLCIFetcher

        # Test connection
        fetcher = Sentinel3OLCIFetcher()

        # Try to connect (this will prompt for authentication if needed)
        connection = fetcher._connect()

        if connection:
            print("✅ Successfully connected to openEO backend")

            # List available collections
            collections = fetcher.get_available_collections()
            print(f"✅ Found {len(collections)} water-related collections")

            # Test data availability for a known location
            test_date = datetime(2024, 6, 15)
            available = fetcher.is_available(55.0, 12.0, test_date)
            print(f"✅ Data availability test: {'Available' if available else 'Not available'}")

        else:
            print("❌ Failed to establish connection")

    except ImportError:
        print("❌ OpenEO not installed. Run: pip install openeo")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure you have valid credentials or use device authentication")


if __name__ == "__main__":
    # You can run different parts of the example
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--check-availability":
            check_satellite_availability()
        elif sys.argv[1] == "--test-connection":
            test_openeo_connection()
        else:
            print("Usage: python 03_satellite_parameter_fetching.py [--check-availability|--test-connection]")
    else:
        main()