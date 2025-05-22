"""
Quick test script to validate the enhanced model on a single pixel.
Run this to check if the depth sensitivity improvements work.
"""

import numpy as np
import matplotlib.pyplot as plt
from sambuca_core.forward_model import forward_model as original_forward_model


from sambuca_core.enhanced_forward_model import enhanced_forward_model, enhanced_initial_values, enhanced_objective_function  # Import the new one

def test_depth_sensitivity():
    """Test if the enhanced model shows better depth sensitivity."""

    # Test parameters
    wavelengths = np.array([442.7, 492.4, 559.8, 664.6, 704.1])
    a_water = np.array([0.0044, 0.0071, 0.0596, 0.2885, 0.4398])
    a_ph_star = np.array([0.055, 0.041, 0.023, 0.015, 0.011])
    substrate1 = np.array([0.05, 0.08, 0.12, 0.15, 0.18])

    # Test different depths
    depths = np.array([1.0, 3.0, 5.0, 8.0, 12.0, 20.0])

    # Fixed water quality
    chl, cdom, nap = 2.0, 0.5, 1.0

    print("Testing depth sensitivity...")
    print("Depth (m) | RRS@550nm | Bottom Contrib | Comment")
    print("-" * 55)

    rrs_values = []
    bottom_contribs = []

    for depth in depths:
        # Test with enhanced model
        result = enhanced_forward_model(
            chl=chl, cdom=cdom, nap=nap, depth=depth,
            substrate1=substrate1, wavelengths=wavelengths,
            a_water=a_water, a_ph_star=a_ph_star,
            num_bands=len(wavelengths),
            enhance_depth_sensitivity=True
        )

        rrs_550 = result.rrs[2]  # Green band
        bottom_contrib = np.mean(
            result.optical_depth_contribution) if result.optical_depth_contribution is not None else 0

        rrs_values.append(rrs_550)
        bottom_contribs.append(bottom_contrib)

        # Determine if depth is detectable
        if bottom_contrib > 0.05:
            comment = "Detectable"
        elif bottom_contrib > 0.02:
            comment = "Marginal"
        else:
            comment = "Too deep"

        print(f"{depth:6.1f}    | {rrs_550:8.5f}  | {bottom_contrib:10.3f} | {comment}")

    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # RRS vs Depth
    ax1.plot(depths, rrs_values, 'o-', linewidth=2, markersize=8)
    ax1.set_xlabel('Depth (m)')
    ax1.set_ylabel('RRS at 550nm')
    ax1.set_title('Spectral Response vs Depth')
    ax1.grid(True, alpha=0.3)

    # Bottom contribution vs Depth
    ax2.plot(depths, bottom_contribs, 'o-', color='orange', linewidth=2, markersize=8)
    ax2.axhline(y=0.05, color='red', linestyle='--', label='Minimum for reliable depth')
    ax2.axhline(y=0.02, color='yellow', linestyle='--', label='Marginal detection')
    ax2.set_xlabel('Depth (m)')
    ax2.set_ylabel('Bottom Contribution Fraction')
    ax2.set_title('Bottom Signal vs Depth')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # Analysis
    print(f"\nAnalysis:")
    print(f"RRS range: {np.min(rrs_values):.5f} to {np.max(rrs_values):.5f}")
    print(f"RRS variation: {(np.max(rrs_values) - np.min(rrs_values)) / np.mean(rrs_values) * 100:.1f}%")
    print(f"Detectable depths (>5% bottom contrib): {np.sum(np.array(bottom_contribs) > 0.05)} of {len(depths)}")

    # Check if model is working
    if (np.max(rrs_values) - np.min(rrs_values)) / np.mean(rrs_values) < 0.05:
        print("❌ WARNING: Low depth sensitivity - model may not detect depth changes well")
        return False
    else:
        print("✅ Good depth sensitivity - model should detect depth changes")
        return True


def test_single_pixel_inversion():
    """Test inversion on a single synthetic pixel."""

    print("\n" + "=" * 60)
    print("TESTING SINGLE PIXEL INVERSION")
    print("=" * 60)

    # Create synthetic "observed" data
    wavelengths = np.array([442.7, 492.4, 559.8, 664.6, 704.1])
    a_water = np.array([0.0044, 0.0071, 0.0596, 0.2885, 0.4398])
    a_ph_star = np.array([0.055, 0.041, 0.023, 0.015, 0.011])
    substrate1 = np.array([0.05, 0.08, 0.12, 0.15, 0.18])

    # True parameters
    true_params = {
        'chl': 1.5, 'cdom': 0.3, 'nap': 0.8, 'depth': 4.0,
        'substrate_fraction': 1.0
    }

    # Generate "observed" spectrum
    observed_result = enhanced_forward_model(
        chl=true_params['chl'],
        cdom=true_params['cdom'],
        nap=true_params['nap'],
        depth=true_params['depth'],
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=len(wavelengths),
        enhance_depth_sensitivity=True
    )

    observed_rrs = observed_result.rrs
    print(f"True depth: {true_params['depth']} m")
    print(f"True bottom contribution: {np.mean(observed_result.optical_depth_contribution):.3f}")

    # Test initial value estimation
    param_names = ['chl', 'cdom', 'nap', 'depth', 'substrate_fraction']
    initial_values = enhanced_initial_values(observed_rrs, wavelengths, param_names)

    print(f"\nInitial value estimation:")
    for name, init_val, true_val in zip(param_names, initial_values,
                                        [true_params[name] for name in param_names]):
        print(f"  {name:>18}: {init_val:6.3f} (true: {true_val:6.3f})")

    # Simple test of objective function
    from scipy.optimize import minimize

    # Mock InversionParameters for testing
    class MockInversionParams:
        def __init__(self):
            self.wavelengths = wavelengths
            self.a_water = a_water
            self.a_ph_star = a_ph_star
            self.substrate1 = substrate1
            self.nedr = None

        def get_forward_model_params(self, params):
            return {
                'chl': params[0], 'cdom': params[1], 'nap': params[2],
                'depth': params[3], 'substrate_fraction': params[4],
                'substrate1': self.substrate1, 'wavelengths': self.wavelengths,
                'a_water': self.a_water, 'a_ph_star': self.a_ph_star,
                'num_bands': len(self.wavelengths)
            }

    mock_params = MockInversionParams()

    # Test objective function at true values
    true_values = [true_params[name] for name in param_names]
    error_at_true = enhanced_objective_function(
        true_values, observed_rrs, mock_params
    )
    print(f"\nObjective function at true values: {error_at_true:.6f}")

    # Test objective function at initial values
    error_at_initial = enhanced_objective_function(
        initial_values, observed_rrs, mock_params
    )
    print(f"Objective function at initial values: {error_at_initial:.6f}")

    if error_at_true < 1e-10:
        print("✅ Perfect match at true values")
    else:
        print("❌ Error at true values - check forward model")

    return observed_rrs, true_params, initial_values


if __name__ == "__main__":
    # Run tests
    print("ENHANCED SAMBUCA MODEL VALIDATION")
    print("=" * 50)

    # Test 1: Depth sensitivity
    depth_ok = test_depth_sensitivity()

    # Test 2: Single pixel inversion
    obs_rrs, true_params, init_vals = test_single_pixel_inversion()

    print(f"\n{'=' * 50}")
    if depth_ok:
        print("✅ Enhanced model shows good depth sensitivity")
        print("✅ Ready to integrate into your codebase")
        print("\nNext steps:")
        print("1. Replace your forward_model function")
        print("2. Update your initial value estimation")
        print("3. Test on a small image subset")
    else:
        print("❌ Model still has depth sensitivity issues")
        print("❌ Check the path elongation factor implementation")