#!/usr/bin/env python3
"""
SIOP Manager and Sensor Integration Example
==========================================

This example demonstrates how to:
1. Use the SIOPManager to load spectral libraries
2. Register different sensors (Sentinel-2, Landsat-8, etc.)
3. Interpolate SIOPs to sensor wavelengths
4. Compare forward model results across sensors
5. Visualize the differences

This builds on the basic example and shows real-world usage.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import sambuca_core as sbc


def main():
    print("=" * 70)
    print("SAMBUCA CORE - SIOP Manager and Sensor Integration Example")
    print("=" * 70)

    # 1. Set up SIOP directory (create synthetic data if needed)
    siop_dir = setup_siop_directory()

    # 2. Initialize SIOP Manager
    print("Initializing SIOP Manager...")
    siop_manager = sbc.SIOPManager(siop_dir)

    # List available libraries
    libraries = siop_manager.list_available_libraries()
    print(f"Found {len(libraries)} spectral libraries:")
    for lib in libraries:
        print(f"  - {lib}")

    # 3. Register multiple sensors
    print("\nRegistering sensors...")
    sensors = {
        "Sentinel-2": [492.4, 559.8, 664.6, 704.1, 740.5, 782.8, 832.8],
        "Landsat-8": [482, 562, 655, 865],
        "MODIS": [488, 531, 551, 667, 678, 748, 869],
        "Custom": [450, 500, 550, 600, 650, 700, 750, 800]
    }

    for sensor_name, wavelengths in sensors.items():
        siop_manager.register_sensor(sensor_name, wavelengths)
        print(f"  Registered {sensor_name} with {len(wavelengths)} bands")

    # 4. Demonstrate SIOP interpolation
    print("\nDemonstrating SIOP interpolation...")
    demonstrate_siop_interpolation(siop_manager)

    # 5. Compare forward model across sensors
    print("\nComparing forward model results across sensors...")
    compare_sensors(siop_manager, sensors)

    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("Check the generated plots to see sensor comparisons.")
    print("=" * 70)


def setup_siop_directory():
    """Create a basic SIOP directory with synthetic data if it doesn't exist."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "input", "examples", "basic", "example_siops")

    if not os.path.exists(base_dir):
        print("Creating synthetic SIOP data...")
        os.makedirs(base_dir, exist_ok=True)

        # Create wavelength range
        wavelengths = np.arange(400, 801, 1)

        # Create water absorption (based on literature)
        water_abs = create_water_absorption(wavelengths)
        save_siop(base_dir, "water_absorption.csv", wavelengths, water_abs)

        # Create phytoplankton absorption
        ph_abs = create_phytoplankton_absorption(wavelengths)
        save_siop(base_dir, "phytoplankton_absorption.csv", wavelengths, ph_abs)

        # Create substrate reflectance
        sand_refl = create_sand_substrate(wavelengths)
        save_siop(base_dir, "sand_substrate.csv", wavelengths, sand_refl)

        seagrass_refl = create_seagrass_substrate(wavelengths)
        save_siop(base_dir, "seagrass_substrate.csv", wavelengths, seagrass_refl)

        print(f"Synthetic SIOP data created in '{base_dir}' directory")

    return base_dir


def create_water_absorption(wavelengths):
    """Create synthetic water absorption spectrum."""
    # Simplified model based on literature
    abs_coeff = np.zeros_like(wavelengths, dtype=float)
    for i, wl in enumerate(wavelengths):
        if wl < 500:
            abs_coeff[i] = 0.01 + 0.05 * np.exp(-(wl - 400) / 30)
        elif wl < 600:
            abs_coeff[i] = 0.015 + (wl - 500) * 0.0006
        elif wl < 700:
            abs_coeff[i] = 0.075 + (wl - 600) * 0.003
        else:
            abs_coeff[i] = 0.375 + (wl - 700) * 0.005
    return abs_coeff


def create_phytoplankton_absorption(wavelengths):
    """Create synthetic phytoplankton absorption spectrum."""
    # Chlorophyll-a absorption peaks
    ph_abs = 0.02 * np.ones_like(wavelengths, dtype=float)
    ph_abs += 0.03 * np.exp(-0.005 * (wavelengths - 440) ** 2)  # Blue peak
    ph_abs += 0.01 * np.exp(-0.005 * (wavelengths - 675) ** 2)  # Red peak
    return ph_abs


def create_sand_substrate(wavelengths):
    """Create synthetic sand substrate reflectance."""
    # Bright substrate increasing with wavelength
    refl = 0.1 + 0.3 * (wavelengths - 400) / 400
    return np.clip(refl, 0, 1)


def create_seagrass_substrate(wavelengths):
    """Create synthetic seagrass substrate reflectance."""
    # Green vegetation with peak in green
    refl = 0.05 * np.ones_like(wavelengths, dtype=float)
    refl += 0.15 * np.exp(-0.001 * (wavelengths - 550) ** 2)  # Green peak
    refl += 0.25 * np.exp(-0.0001 * (wavelengths - 750) ** 2)  # NIR plateau
    return np.clip(refl, 0, 1)


def save_siop(base_dir, filename, wavelengths, values):
    """Save SIOP data to CSV file."""
    import pandas as pd
    df = pd.DataFrame({
        'Wavelength': wavelengths,
        'Value': values
    })
    df.to_csv(os.path.join(base_dir, filename), index=False)


def demonstrate_siop_interpolation(siop_manager):
    """Demonstrate how SIOPs are interpolated to different sensor wavelengths."""

    # Get original wavelengths (from raw libraries)
    raw_wavelengths = None
    raw_water_abs = None

    for lib_name, (wl, values) in siop_manager.raw_libraries.items():
        if 'water_absorption' in lib_name:
            raw_wavelengths = wl
            raw_water_abs = values
            break

    if raw_wavelengths is None:
        print("No water absorption data found for interpolation demo")
        return

    # Get interpolated data for different sensors
    sensors_to_compare = ["Sentinel-2", "Landsat-8", "MODIS"]

    plt.figure(figsize=(12, 8))

    # Plot original data
    plt.plot(raw_wavelengths, raw_water_abs, 'k-', linewidth=1, alpha=0.7, label='Original (1nm)')

    colors = ['red', 'blue', 'green']
    markers = ['o', 's', '^']

    for i, sensor_name in enumerate(sensors_to_compare):
        # Get interpolated SIOPs
        siops = siop_manager.get_siops_for_sensor(sensor_name)

        # Plot interpolated points
        plt.plot(siops['wavelengths'], siops['water_absorption'],
                 markers[i], color=colors[i], markersize=8,
                 label=f'{sensor_name} interpolated', linestyle='--', linewidth=2)

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Water Absorption (1/m)')
    plt.title('SIOP Interpolation Example: Water Absorption')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(400, 900)

    plt.tight_layout()
    # Ensure output directory exists (relative to script location)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output", "examples", "basic")
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'siop_interpolation_example.png'), dpi=300, bbox_inches='tight')
    plt.show()


def compare_sensors(siop_manager, sensors):
    """Compare forward model results across different sensors."""

    # Define water conditions
    water_conditions = [
        {"name": "Clear Ocean", "chl": 0.5, "cdom": 0.01, "nap": 0.1, "depth": 10.0},
        {"name": "Coastal Water", "chl": 2.0, "cdom": 0.1, "nap": 1.0, "depth": 5.0},
        {"name": "Turbid Water", "chl": 5.0, "cdom": 0.3, "nap": 3.0, "depth": 2.0}
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    colors = ['red', 'blue', 'green', 'orange']

    for i, condition in enumerate(water_conditions):
        ax = axes[i]

        for j, (sensor_name, wavelengths) in enumerate(sensors.items()):
            # Get standard SIOPs for this sensor
            try:
                std_siops = siop_manager.get_standard_siops(sensor_name)
            except KeyError:
                print(f"Could not get standard SIOPs for {sensor_name}, skipping...")
                continue

            # Run forward model
            results = sbc.forward_model(
                chl=condition["chl"],
                cdom=condition["cdom"],
                nap=condition["nap"],
                depth=condition["depth"],
                wavelengths=std_siops['wavelengths'],
                a_water=std_siops['a_water'],
                a_ph_star=std_siops['a_ph_star'],
                substrate1=std_siops['substrate1'],
                num_bands=len(std_siops['wavelengths'])
            )

            # Plot results
            ax.plot(std_siops['wavelengths'], results.rrs,
                    'o-', color=colors[j], label=sensor_name,
                    linewidth=2, markersize=6)

        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Rrs (sr⁻¹)')
        ax.set_title(f'{condition["name"]}\n'
                     f'Chl: {condition["chl"]} mg/m³, '
                     f'Depth: {condition["depth"]} m')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output", "examples", "basic")
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "sensor_comparison.png"), dpi=300)
    plt.show()

    # Print summary statistics
    print("\nForward model comparison summary:")
    for condition in water_conditions:
        print(f"\n{condition['name']}:")
        print(f"  Parameters: Chl={condition['chl']}, CDOM={condition['cdom']}, "
              f"NAP={condition['nap']}, Depth={condition['depth']}")

        for sensor_name in sensors.keys():
            try:
                std_siops = siop_manager.get_standard_siops(sensor_name)
                results = sbc.forward_model(
                    chl=condition["chl"],
                    cdom=condition["cdom"],
                    nap=condition["nap"],
                    depth=condition["depth"],
                    wavelengths=std_siops['wavelengths'],
                    a_water=std_siops['a_water'],
                    a_ph_star=std_siops['a_ph_star'],
                    substrate1=std_siops['substrate1'],
                    num_bands=len(std_siops['wavelengths'])
                )

                mean_rrs = np.mean(results.rrs)
                max_rrs = np.max(results.rrs)
                print(f"    {sensor_name}: Mean Rrs = {mean_rrs:.6f}, Max Rrs = {max_rrs:.6f}")

            except KeyError:
                continue


if __name__ == "__main__":
    main()