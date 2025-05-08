# examples/swampy_inversion_example.py

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import rasterio

# Add parent directory to path if needed when running directly from scripts folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sambuca_core as sbc


def run_swampy_example():
    """Example script for processing data using SWAMpy format."""

    # Define paths
    # Update these paths to match your data location
    base_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'swampy_data')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', 'swampy_results')

    # Check if paths exist
    if not os.path.exists(base_path):
        print(f"Error: SWAMpy data directory not found at {base_path}")
        print(
            "Please create this directory with the appropriate structure (image, siop, nedr, substrates, sensor_filters)")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    print(f"Processing SWAMpy data from: {base_path}")
    print(f"Results will be saved to: {output_path}")

    # Initialize SIOPManager
    siop_manager = sbc.SIOPManager()

    try:
        # Option 1: Use the all-in-one method
        results = siop_manager.process_swampy_dataset(
            base_path=base_path,
            output_dir=output_path,
            # Optional: Process only a subset of the image for testing
            subset=(0, 30, 0, 30),  # (xstart, xend, ystart, yend)
            use_rrs=False,  # Assume below-surface reflectance
            shallow=False,  # Don't use the "go shallow" option
            relaxed_constraints=True  # Use relaxed abundance constraints (RASC)
        )

        # Option 2: Step-by-step processing (uncomment to use)
        """
        # Load SWAMpy data
        print("Loading SWAMpy data...")
        swampy_data = siop_manager.load_swampy_data(base_path, use_rrs=False)

        # Prepare data
        print("Preparing data...")
        prepared_data = siop_manager.prepare_swampy_data(swampy_data)

        # Run inversion
        print("Running SAMBUCA inversion...")
        results = siop_manager.run_swampy_inversion(
            prepared_data, 
            subset=(0, 30, 0, 30),
            shallow=False,
            relaxed_constraints=True
        )

        # Save results
        print("Saving results...")
        siop_manager.save_swampy_results(results, output_dir=output_path)
        """

        # Display some statistics from the results if processing was successful
        if results and 'depth' in results:
            # Extract coordinates
            xstart, xend, ystart, yend = results['coordinates']

            # Create mask for valid pixels
            valid_mask = results['success'][xstart:xend, ystart:yend]

            # Get depth statistics
            depth_data = results['depth'][xstart:xend, ystart:yend][valid_mask]
            if len(depth_data) > 0:
                print("\nDepth Statistics:")
                print(f"  Min depth: {np.min(depth_data):.2f} m")
                print(f"  Max depth: {np.max(depth_data):.2f} m")
                print(f"  Mean depth: {np.mean(depth_data):.2f} m")
                print(f"  Median depth: {np.median(depth_data):.2f} m")

            # Get substrate composition statistics
            sub1_data = results['sub1_norm'][xstart:xend, ystart:yend][valid_mask]
            sub2_data = results['sub2_norm'][xstart:xend, ystart:yend][valid_mask]
            sub3_data = results['sub3_norm'][xstart:xend, ystart:yend][valid_mask]

            if len(sub1_data) > 0:
                print("\nSubstrate Composition:")
                print(f"  Mean Substrate 1: {np.mean(sub1_data):.2f} (proportion)")
                print(f"  Mean Substrate 2: {np.mean(sub2_data):.2f} (proportion)")
                print(f"  Mean Substrate 3: {np.mean(sub3_data):.2f} (proportion)")

            # Report on processing success
            total_pixels = (xend - xstart) * (yend - ystart)
            successful_pixels = np.sum(valid_mask)
            print(f"\nProcessing Summary:")
            print(f"  Total pixels: {total_pixels}")
            print(f"  Successfully processed: {successful_pixels} ({successful_pixels / total_pixels * 100:.1f}%)")
            print(
                f"  Failed: {total_pixels - successful_pixels} ({(total_pixels - successful_pixels) / total_pixels * 100:.1f}%)")

            # Show where results were saved
            print(f"\nResults have been saved to: {output_path}")
            print("Output files include:")
            for file in os.listdir(output_path):
                if file.endswith('.tif'):
                    print(f"  - {file}")

            # Display example visualization
            depth_file = os.path.join(output_path, "depth.png")
            if os.path.exists(depth_file):
                print(f"\nDepth visualization saved to: {depth_file}")

                # If running in a notebook or interactive environment that supports display
                try:
                    from IPython.display import Image, display
                    display(Image(depth_file))
                except ImportError:
                    print("Run in interactive environment to see visualizations")

    except Exception as e:
        print(f"Error processing SWAMpy data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_swampy_example()