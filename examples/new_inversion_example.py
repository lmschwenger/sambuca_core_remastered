"""Enhanced SAMBUCA usage examples demonstrating the new capabilities."""

import numpy as np
import matplotlib.pyplot as plt
from sambuca_core.inversion import InversionParameters, process_image
from sambuca_core import SIOPManager


def example_shallow_water_with_substrate_unmixing():
    """Example of proper SAMBUCA shallow water inversion with substrate unmixing."""

    # Load your image data (example)
    # rrs_image = load_your_image()  # Shape: (height, width, bands)
    # mask = create_water_mask()     # Shape: (height, width)

    # Set up SIOP manager
    siop_dir = "../data/siops"
    siop_manager = SIOPManager(siop_dir)

    # Register sensor
    sentinel2_wavelengths = [492.4, 559.8, 664.6, 704.1]  # B2, B3, B4, B5
    siop_manager.register_sensor("Sentinel-2", wavelengths=sentinel2_wavelengths)

    # === PROPER SAMBUCA CONFIGURATION FOR SHALLOW WATER ===
    params = InversionParameters()

    # Update from SIOP manager
    params.update_from_siop_manager(siop_manager, "Sentinel-2")

    # Configure for shallow water (this is the key change)
    params.configure_for_shallow_water(enable_substrate_unmixing=True)

    # The above automatically sets:
    # - depth=(0.1, 20.0)
    # - substrate_fraction=(0.0, 1.0)  # CRITICAL - was missing in your examples
    # - chl=(0.1, 10.0)
    # - cdom=(0.01, 2.0)
    # - nap=(0.1, 5.0)

    # Optionally enable SIOP optimization if field data is limited
    # params.enable_siop_optimization(conservative=True)

    # Check optimization complexity
    complexity = params.get_optimization_complexity()
    print("Optimization Configuration:")
    print(f"  Total parameters to optimize: {complexity['total_parameters']}")
    print(f"  Spectral bands available: {complexity['spectral_bands']}")
    print(f"  System is overdetermined: {complexity['overdetermined']}")
    print(f"  Substrate unmixing enabled: {complexity['substrate_unmixing_enabled']}")
    print(f"  SIOP optimization enabled: {complexity['siop_optimization_enabled']}")
    print(f"  Parameter names: {complexity['parameter_names']}")

    # This should now show 5 parameters including substrate_fraction
    # instead of just 4 as in your original examples

    return params


def example_deep_water_with_siop_optimization():
    """Example of deep water configuration with SIOP optimization."""

    siop_dir = "../data/siops"
    siop_manager = SIOPManager(siop_dir)
    modis_wavelengths = [412, 443, 488, 531, 551, 667, 678, 748]
    siop_manager.register_sensor("MODIS", wavelengths=modis_wavelengths)

    params = InversionParameters()
    params.update_from_siop_manager(siop_manager, "MODIS")

    # Configure for deep water (no depth/substrate optimization)
    params.configure_for_deep_water()

    # Enable SIOP optimization (common for deep water when SIOPs are uncertain)
    params.enable_siop_optimization(conservative=False)

    complexity = params.get_optimization_complexity()
    print("Deep Water Configuration:")
    print(f"  Total parameters: {complexity['total_parameters']}")
    print(f"  Primary parameters: {complexity['primary_parameters']}")
    print(f"  SIOP parameters: {complexity['siop_parameters']}")
    print(f"  Parameters: {complexity['parameter_names']}")

    # This might show 6-8 parameters:
    # ['chl', 'cdom', 'nap', 'a_cdom_slope', 'bb_ph_slope', 'x_ph_lambda0x']

    return params


def example_comparison_original_vs_enhanced():
    """Compare your original approach vs enhanced SAMBUCA approach."""

    print("=== COMPARISON: Original vs Enhanced SAMBUCA ===\n")

    # Simulate your original approach
    print("1. YOUR ORIGINAL APPROACH:")
    original_params = InversionParameters(
        depth=(0.1, 10.0),
        chl=(0.5, 3),
        cdom=(0.0005, 0.01),
        nap=(0.01, 0.5)
        # NOTE: Missing substrate_fraction - this is the problem!
    )

    original_complexity = original_params.get_optimization_complexity()
    print(f"   Parameters: {original_complexity['parameter_names']}")
    print(f"   Count: {original_complexity['total_parameters']}")
    print(f"   Substrate unmixing: {original_complexity['substrate_unmixing_enabled']}")

    print("\n2. ENHANCED SAMBUCA APPROACH:")
    enhanced_params = InversionParameters()
    enhanced_params.configure_for_shallow_water(enable_substrate_unmixing=True)

    enhanced_complexity = enhanced_params.get_optimization_complexity()
    print(f"   Parameters: {enhanced_complexity['parameter_names']}")
    print(f"   Count: {enhanced_complexity['total_parameters']}")
    print(f"   Substrate unmixing: {enhanced_complexity['substrate_unmixing_enabled']}")

    print("\n3. WITH SIOP OPTIMIZATION (when field data limited):")
    siop_params = InversionParameters()
    siop_params.configure_for_shallow_water(enable_substrate_unmixing=True)
    siop_params.enable_siop_optimization(conservative=True)

    siop_complexity = siop_params.get_optimization_complexity()
    print(f"   Parameters: {siop_complexity['parameter_names']}")
    print(f"   Count: {siop_complexity['total_parameters']}")
    print(f"   SIOP optimization: {siop_complexity['siop_optimization_enabled']}")

    print(f"\n=== KEY DIFFERENCES ===")
    print(f"Original: {original_complexity['total_parameters']} parameters, no substrate unmixing")
    print(f"Enhanced: {enhanced_complexity['total_parameters']} parameters, with substrate unmixing")
    print(f"Full SAMBUCA: {siop_complexity['total_parameters']} parameters, substrate + SIOP optimization")

    print(f"\nCRITICAL: Your examples were missing 'substrate_fraction' parameter!")
    print(f"This is fundamental to SAMBUCA's substrate unmixing capability.")


def example_forward_model_with_substrate_unmixing():
    """Example showing enhanced forward model with substrate unmixing."""

    from sambuca_core.forward_model import forward_model

    # Set up test parameters
    wavelengths = np.array([450, 500, 550, 600, 650, 700])
    num_bands = len(wavelengths)

    # Create example SIOPs
    a_water = np.array([0.0044, 0.0071, 0.0596, 0.2885, 0.4398, 0.6250])
    a_ph_star = np.array([0.055, 0.041, 0.023, 0.015, 0.011, 0.010])

    # Create two different substrates for unmixing
    substrate1 = np.array([0.05, 0.08, 0.12, 0.15, 0.18, 0.20])  # Sand
    substrate2 = np.array([0.02, 0.03, 0.15, 0.25, 0.30, 0.25])  # Seagrass

    # Test different substrate mixing ratios
    substrate_fractions = [0.0, 0.25, 0.5, 0.75, 1.0]

    print("=== SUBSTRATE UNMIXING EXAMPLE ===")

    for frac in substrate_fractions:
        # Run forward model with different substrate fractions
        results = forward_model(
            chl=2.0,
            cdom=0.5,
            nap=1.0,
            depth=5.0,
            substrate1=substrate1,
            substrate2=substrate2,
            substrate_fraction=frac,  # This is what was missing!
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=num_bands,
        )

        print(f"\nSubstrate fraction = {frac:.2f}:")
        print(f"  Substrate fractions: {results.substrate_fractions}")
        print(f"  Is optically shallow: {results.is_optically_shallow}")
        print(f"  Mean bottom contribution: {np.mean(results.optical_depth_contribution):.3f}")
        print(f"  RRS at 550nm: {results.rrs[2]:.6f}")


def example_nedr_weighted_inversion():
    """Example showing NEDR-weighted inversion as in your examples."""

    # This shows how your NEDR examples should be enhanced
    import pandas as pd

    # Load NEDR values (as in your example)
    nedr_csv = "../data/nedr/s2testc.csv"
    # nedr_df = pd.read_csv(nedr_csv)  # Uncomment if file exists

    # Set up parameters with substrate unmixing
    params = InversionParameters()
    params.configure_for_shallow_water(enable_substrate_unmixing=True)

    # Add NEDR values (your existing code works here)
    # nedr_values = extract_nedr_for_wavelengths(nedr_df, wavelengths)
    # params.set_nedr(nedr_values)

    print("=== NEDR-WEIGHTED INVERSION WITH SUBSTRATE UNMIXING ===")
    print("Your NEDR examples should be updated to include:")
    print("1. substrate_fraction=(0.0, 1.0) in the InversionParameters")
    print("2. This enables proper substrate unmixing during inversion")
    print("3. The NEDR weighting still works the same way")

    # The rest of your NEDR code remains the same, but now with proper
    # substrate unmixing capability


if __name__ == "__main__":
    print("Enhanced SAMBUCA Implementation Examples")
    print("=" * 50)

    # Run examples
    example_comparison_original_vs_enhanced()
    print("\n" + "=" * 50)

    example_forward_model_with_substrate_unmixing()
    print("\n" + "=" * 50)

    # Demonstrate proper configurations
    print("SHALLOW WATER CONFIGURATION:")
    shallow_params = example_shallow_water_with_substrate_unmixing()

    print("\nDEEP WATER CONFIGURATION:")
    deep_params = example_deep_water_with_siop_optimization()

    print("\n" + "=" * 50)
    example_nedr_weighted_inversion()