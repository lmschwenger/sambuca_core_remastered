# examples/siop_manager_example.py

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sambuca_core as sbc


def example_siop_manager_usage():
    """Example usage of SIOPManager for different sensors."""

    # Find the SIOP directory
    siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
    print(f"Using SIOP directory: {siop_dir}")

    # Initialize the SIOP manager
    siop_manager = sbc.SIOPManager(siop_dir)

    # Register different sensors
    siop_manager.register_sensor("Sentinel-2", [443, 490, 560, 665, 705, 740, 783, 842, 865])
    siop_manager.register_sensor("Landsat-8", [443, 482, 562, 655, 865])
    siop_manager.register_sensor("MODIS", [412, 443, 488, 531, 551, 667, 678, 748, 869])

    # List available spectral libraries
    print("\nAvailable libraries:")
    libraries = siop_manager.list_available_libraries()
    for library in libraries:
        print(f"  - {library}")

    # Get grouped libraries by type
    library_types = siop_manager.get_common_library_types()
    print("\nLibrary types:")
    for type_name, libs in library_types.items():
        if libs:  # Only print non-empty categories
            print(f"  {type_name}:")
            for lib in libs:
                print(f"    - {lib}")

    # Try to get standard SIOPs
    try:
        sentinel_siops = siop_manager.get_siops_for_sensor("Sentinel-2")
        print("\nInterpolated SIOPs for Sentinel-2:")
        for key in sentinel_siops.keys():
            if key not in ['wavelengths', 'num_bands']:
                print(f"  - {key}")

        std_siops = siop_manager.get_standard_siops("Sentinel-2")
        print("\nStandard SIOPs for Sentinel-2:")
        for key in std_siops.keys():
            if key not in ['wavelengths', 'num_bands']:
                print(f"  - {key}")
    except KeyError as e:
        print(f"Error getting standard SIOPs: {e}")

    # Plot interpolated spectra for different sensors if we have libraries
    if libraries:
        sensors = ["Sentinel-2", "Landsat-8", "MODIS"]

        plt.figure(figsize=(12, 8))

        # Get raw libraries
        raw_libs = siop_manager.raw_libraries

        # Determine which libraries to plot
        libraries_to_plot = {
            "Water Absorption": next((k for k in raw_libs if 'water_absorption' in k), None),
            "Phytoplankton Absorption": next((k for k in raw_libs if 'phytoplankton_absorption' in k), None),
            "Sand Substrate": next((k for k in raw_libs if 'sand_substrate' in k), None),
            "Seagrass Substrate": next((k for k in raw_libs if 'seagrass_substrate' in k), None)
        }

        # Plot libraries
        subplot_idx = 1
        for title, lib_key in libraries_to_plot.items():
            if lib_key:
                plt.subplot(2, 2, subplot_idx)
                plt.title(title)

                # Plot original
                plt.plot(raw_libs[lib_key][0], raw_libs[lib_key][1], 'k-', label='Original')

                # Plot sensor-specific
                for sensor in sensors:
                    siops = siop_manager.get_siops_for_sensor(sensor)
                    if lib_key in siops:
                        plt.plot(siops['wavelengths'], siops[lib_key], 'o-', label=sensor)

                plt.xlabel("Wavelength (nm)")
                if 'absorption' in lib_key:
                    plt.ylabel("Absorption")
                else:
                    plt.ylabel("Reflectance")

                plt.legend()
                plt.grid(True)
                subplot_idx += 1

        plt.tight_layout()
        plt.savefig("siops_comparison.png", dpi=300)
        plt.show()


# Run the example
if __name__ == "__main__":
    example_siop_manager_usage()