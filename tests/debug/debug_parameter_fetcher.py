#!/usr/bin/env python3
"""
Debug script to test the updated openEO parameter fetching step by step.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_step_1_connection():
    """Test basic openEO connection."""
    print("=== Step 1: Testing OpenEO Connection ===")

    try:
        from sambuca_core.data_fetchers import Sentinel3OLCIFetcher

        fetcher = Sentinel3OLCIFetcher()
        print("✅ Fetcher created successfully")

        # Test connection
        connection = fetcher._connect()
        print("✅ Connection established successfully")

        # List collections
        collections = connection.list_collection_ids()
        print(f"✅ Found {len(collections)} collections")

        # Find OLCI collections
        olci_collections = [c for c in collections if 'olci' in c.lower()]
        print(f"✅ Found {len(olci_collections)} OLCI collections:")
        for col in olci_collections:
            print(f"  - {col}")

        return True

    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        return False


def test_step_2_collection_loading():
    """Test loading the OLCI collection."""
    print("\n=== Step 2: Testing Collection Loading ===")

    try:
        from sambuca_core.data_fetchers import Sentinel3OLCIFetcher

        fetcher = Sentinel3OLCIFetcher()
        connection = fetcher._connect()

        # Find collection
        collection_id = fetcher._find_available_collection()
        print(f"✅ Using collection: {collection_id}")

        # Test basic loading
        spatial_extent = {"west": 12.0, "south": 56.0, "east": 12.5, "north": 56.5}
        temporal_extent = ["2024-06-01", "2024-06-30"]

        datacube = connection.load_collection(
            collection_id,
            spatial_extent=spatial_extent,
            temporal_extent=temporal_extent
        )
        print("✅ Collection loaded successfully")

        # Try to get metadata/bands
        try:
            # This might not work on all backends, but worth trying
            metadata = datacube.metadata
            if metadata and hasattr(metadata, 'bands'):
                print(f"✅ Available bands: {list(metadata.bands.keys())}")
        except:
            print("ℹ️ Could not retrieve band metadata (this is normal)")

        return datacube, collection_id

    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        return None, None


def test_step_3_band_filtering():
    """Test filtering specific bands."""
    print("\n=== Step 3: Testing Band Filtering ===")

    try:
        datacube, collection_id = test_step_2_collection_loading()
        if datacube is None:
            return False

        # Test different bands based on the log
        test_bands = ['CHL_NN', 'CHL_OC4ME', 'TSM_NN', 'ADG443_NN']

        for band in test_bands:
            try:
                filtered = datacube.filter_bands([band])
                print(f"✅ Successfully filtered band: {band}")
            except Exception as e:
                print(f"❌ Failed to filter band {band}: {e}")

        return True

    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        return False


def test_step_4_temporal_aggregation():
    """Test temporal aggregation before spatial."""
    print("\n=== Step 4: Testing Temporal Aggregation ===")

    try:
        datacube, collection_id = test_step_2_collection_loading()
        if datacube is None:
            return False

        # Test with CHL_NN band
        test_band = 'CHL_NN'

        print(f"Testing temporal aggregation with {test_band}...")

        # Filter band
        param_cube = datacube.filter_bands([test_band])
        print(f"✅ Filtered to {test_band}")

        # Temporal aggregation
        temporal_mean = param_cube.reduce_dimension(dimension="t", reducer="mean")
        print("✅ Temporal aggregation successful")

        return temporal_mean

    except Exception as e:
        print(f"❌ Step 4 failed: {e}")
        return None


def test_step_5_spatial_aggregation():
    """Test spatial aggregation after temporal."""
    print("\n=== Step 5: Testing Spatial Aggregation ===")

    try:
        temporal_cube = test_step_4_temporal_aggregation()
        if temporal_cube is None:
            return False

        # Test point
        lat, lon = 56.25, 12.25

        print(f"Testing spatial aggregation at point ({lat}, {lon})...")

        # Spatial aggregation
        spatial_mean = temporal_cube.aggregate_spatial(
            geometries={"type": "Point", "coordinates": [lon, lat]},
            reducer="mean"
        )
        print("✅ Spatial aggregation successful")

        return spatial_mean

    except Exception as e:
        print(f"❌ Step 5 failed: {e}")
        return None


def test_step_6_execution():
    """Test executing the computation."""
    print("\n=== Step 6: Testing Execution ===")

    try:
        result_cube = test_step_5_spatial_aggregation()
        if result_cube is None:
            return False

        print("Executing computation...")

        # Execute
        result = result_cube.execute()
        print("✅ Execution successful")

        print(f"Result type: {type(result)}")
        print(f"Result: {result}")

        # Try to extract value
        if isinstance(result, dict):
            print("Result keys:", list(result.keys()))
            if 'features' in result:
                print("Features found:", len(result['features']))
                if len(result['features']) > 0:
                    feature = result['features'][0]
                    print("Feature properties:", feature.get('properties', {}))

        return True

    except Exception as e:
        print(f"❌ Step 6 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_7_parameter_fetching():
    """Test the full parameter fetching."""
    print("\n=== Step 7: Testing Full Parameter Fetching ===")

    try:
        from sambuca_core.inversion import ParameterFetcher
        from sambuca_core.inversion import InversionParameters

        # Create test parameters
        test_params = InversionParameters(
            depth=(0, 25),
            wavelengths=[492.4, 559.8, 664.6, 704.1]
        )
        print("✅ Created test InversionParameters")

        # Test parameter fetcher
        param_fetcher = ParameterFetcher(fetcher_type='sentinel3')
        print("✅ Created ParameterFetcher")

        # Test location and date
        lat, lon = 56.25, 12.25  # Baltic Sea
        test_date = datetime(2024, 6, 15)

        print(f"Testing parameter fetch at ({lat}, {lon}) on {test_date.date()}")

        # Fetch parameters
        updated_params = param_fetcher.update_parameters_from_satellite(
            inversion_params=test_params,
            lat=lat,
            lon=lon,
            date=test_date,
            search_days=14,
            buffer_km=20.0
        )

        print("✅ Parameter fetching successful!")
        print(f"Chlorophyll: {updated_params.fixed_chl}")
        print(f"CDOM: {updated_params.fixed_cdom}")
        print(f"NAP: {updated_params.fixed_nap}")

        return True

    except Exception as e:
        print(f"❌ Step 7 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test steps."""
    print("🔍 OpenEO Parameter Fetching Debug Script")
    print("=" * 50)

    steps = [
        test_step_1_connection,
        test_step_2_collection_loading,
        test_step_3_band_filtering,
        test_step_4_temporal_aggregation,
        test_step_5_spatial_aggregation,
        test_step_6_execution,
        test_step_7_parameter_fetching,
    ]

    for i, step in enumerate(steps, 1):
        try:
            success = step()
            if not success:
                print(f"\n❌ Stopping at step {i}")
                break
        except Exception as e:
            print(f"\n❌ Step {i} crashed: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n" + "=" * 50)
    print("🔍 Debug complete!")


if __name__ == "__main__":
    main()