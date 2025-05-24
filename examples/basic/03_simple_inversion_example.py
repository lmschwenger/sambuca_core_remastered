#!/usr/bin/env python3
"""
Simple Inversion Example
========================

This example demonstrates how to:
1. Generate synthetic observed data using the forward model
2. Set up inversion parameters
3. Invert the data to recover water properties
4. Compare original vs inverted parameters
5. Visualize the results

This shows the basic inversion workflow before moving to real data.
"""
import os

import numpy as np
import matplotlib.pyplot as plt
import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, invert_spectrum, multi_start_inversion


def main():
    print("=" * 60)
    print("SAMBUCA CORE - Simple Inversion Example")
    print("=" * 60)

    # 1. Set up synthetic scenario
    print("Setting up synthetic test scenario...")
    wavelengths, siops = create_synthetic_scenario()

    # 2. Define "true" water properties (what we want to recover)
    true_params = {
        'chl': 2.5,  # mg/m³
        'cdom': 0.15,  # 1/m
        'nap': 1.2,  # mg/L
        'depth': 4.0,  # m
    }

    print("True water parameters:")
    for param, value in true_params.items():
        print(f"  {param}: {value}")

    # 3. Generate synthetic "observed" data
    print("\nGenerating synthetic observed data...")
    observed_rrs = generate_synthetic_observations(wavelengths, siops, true_params)

    # Add some realistic noise
    noise_level = 0.0005  # 0.05% noise
    noise = np.random.normal(0, noise_level, len(observed_rrs))
    observed_rrs_noisy = observed_rrs + noise

    print(f"Added {noise_level * 100:.3f}% noise to simulate realistic observations")

    # 4. Set up inversion parameters
    print("\nSetting up inversion parameters...")
    inversion_params = InversionParameters(
        # Parameters to invert for (with reasonable bounds)
        chl=(0.1, 10.0),  # Chlorophyll bounds
        cdom=(0.01, 1.0),  # CDOM bounds
        nap=(0.1, 5.0),  # NAP bounds
        depth=(0.5, 15.0),  # Depth bounds

        # Fixed parameters from SIOPs
        wavelengths=wavelengths,
        a_water=siops['a_water'],
        a_ph_star=siops['a_ph_star'],
        substrate1=siops['substrate1']
    )

    print("Inversion bounds:")
    for param_name in inversion_params.get_inversion_parameter_names():
        bounds = getattr(inversion_params, param_name)
        print(f"  {param_name}: {bounds[0]} - {bounds[1]}")

    # 5. Perform inversion
    print("\nPerforming inversion...")

    # Try single inversion first
    print("  Single optimization...")
    result_single = invert_spectrum(observed_rrs_noisy, inversion_params)

    # Try multi-start inversion for comparison
    print("  Multi-start optimization...")
    result_multi = multi_start_inversion(observed_rrs_noisy, inversion_params, n_starts=5)

    # 6. Compare results
    print("\nInversion Results Comparison:")
    print("=" * 50)
    print(f"{'Parameter':<10} {'True':<10} {'Single':<10} {'Multi':<10} {'Error(S)':<10} {'Error(M)':<10}")
    print("=" * 50)

    for param in ['chl', 'cdom', 'nap', 'depth']:
        true_val = true_params[param]
        single_val = result_single.parameters[param]
        multi_val = result_multi.parameters[param]
        error_single = abs(single_val - true_val)
        error_multi = abs(multi_val - true_val)

        print(f"{param:<10} {true_val:<10.3f} {single_val:<10.3f} {multi_val:<10.3f} "
              f"{error_single:<10.3f} {error_multi:<10.3f}")

    print("=" * 50)
    print(f"{'RMSE':<10} {'':<10} {result_single.objective_value:<10.6f} "
          f"{result_multi.objective_value:<10.6f}")

    # 7. Create visualizations
    print("\nCreating visualizations...")
    create_inversion_plots(wavelengths, observed_rrs, observed_rrs_noisy,
                           result_single, result_multi, true_params)

    # 8. Analyze convergence
    analyze_convergence(result_single, result_multi)

    print("\n" + "=" * 60)
    print("Inversion example completed successfully!")
    print("Check the generated plots to see the inversion results.")
    print("=" * 60)


def create_synthetic_scenario():
    """Create a synthetic test scenario with SIOPs."""

    # Define wavelengths (Sentinel-2 bands)
    wavelengths = np.array([492.4, 559.8, 664.6, 704.1])

    # Create synthetic SIOPs
    siops = {
        'a_water': np.array([0.0105, 0.0162, 0.3946, 0.6250]),
        'a_ph_star': np.array([0.0280, 0.0200, 0.0120, 0.0100]),
        'substrate1': np.array([0.15, 0.25, 0.35, 0.40])
    }

    return wavelengths, siops


def generate_synthetic_observations(wavelengths, siops, true_params):
    """Generate synthetic observed spectra using the forward model."""

    results = sbc.forward_model(
        chl=true_params['chl'],
        cdom=true_params['cdom'],
        nap=true_params['nap'],
        depth=true_params['depth'],
        wavelengths=wavelengths,
        a_water=siops['a_water'],
        a_ph_star=siops['a_ph_star'],
        substrate1=siops['substrate1'],
        num_bands=len(wavelengths)
    )

    return results.rrs


def create_inversion_plots(wavelengths, observed_clean, observed_noisy,
                           result_single, result_multi, true_params):
    """Create comprehensive visualization of inversion results."""

    fig = plt.figure(figsize=(15, 10))

    # Plot 1: Spectral comparison
    ax1 = plt.subplot(2, 3, 1)
    plt.plot(wavelengths, observed_clean, 'g-o', label='True spectrum', linewidth=2, markersize=8)
    plt.plot(wavelengths, observed_noisy, 'ko', label='Observed (noisy)', markersize=6)
    plt.plot(wavelengths, result_single.modeled_spectra, 'r--s',
             label='Single inversion', linewidth=2, markersize=6)
    plt.plot(wavelengths, result_multi.modeled_spectra, 'b--^',
             label='Multi-start inversion', linewidth=2, markersize=6)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Rrs (sr⁻¹)')
    plt.title('Spectral Fit Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Plot 2: Parameter recovery comparison
    ax2 = plt.subplot(2, 3, 2)
    params = ['chl', 'cdom', 'nap', 'depth']
    x_pos = np.arange(len(params))

    true_vals = [true_params[p] for p in params]
    single_vals = [result_single.parameters[p] for p in params]
    multi_vals = [result_multi.parameters[p] for p in params]

    width = 0.25
    plt.bar(x_pos - width, true_vals, width, label='True', alpha=0.8, color='green')
    plt.bar(x_pos, single_vals, width, label='Single', alpha=0.8, color='red')
    plt.bar(x_pos + width, multi_vals, width, label='Multi-start', alpha=0.8, color='blue')

    plt.xlabel('Parameter')
    plt.ylabel('Value')
    plt.title('Parameter Recovery')
    plt.xticks(x_pos, params)
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')

    # Plot 3: Absolute errors
    ax3 = plt.subplot(2, 3, 3)
    single_errors = [abs(result_single.parameters[p] - true_params[p]) for p in params]
    multi_errors = [abs(result_multi.parameters[p] - true_params[p]) for p in params]

    plt.bar(x_pos - width / 2, single_errors, width, label='Single', alpha=0.8, color='red')
    plt.bar(x_pos + width / 2, multi_errors, width, label='Multi-start', alpha=0.8, color='blue')

    plt.xlabel('Parameter')
    plt.ylabel('Absolute Error')
    plt.title('Inversion Errors')
    plt.xticks(x_pos, params)
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.yscale('log')

    # Plot 4: Residuals
    ax4 = plt.subplot(2, 3, 4)
    residuals_single = observed_noisy - result_single.modeled_spectra
    residuals_multi = observed_noisy - result_multi.modeled_spectra

    plt.plot(wavelengths, residuals_single, 'r-o', label='Single', linewidth=2)
    plt.plot(wavelengths, residuals_multi, 'b-s', label='Multi-start', linewidth=2)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Residual (observed - modeled)')
    plt.title('Spectral Residuals')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Plot 5: Error metrics comparison
    ax5 = plt.subplot(2, 3, 5)
    metrics = ['RMSE', 'Max Abs\nResidual', 'Mean Abs\nResidual']

    single_metrics = [
        result_single.objective_value,
        np.max(np.abs(residuals_single)),
        np.mean(np.abs(residuals_single))
    ]

    multi_metrics = [
        result_multi.objective_value,
        np.max(np.abs(residuals_multi)),
        np.mean(np.abs(residuals_multi))
    ]

    x_pos = np.arange(len(metrics))
    plt.bar(x_pos - width / 2, single_metrics, width, label='Single', alpha=0.8, color='red')
    plt.bar(x_pos + width / 2, multi_metrics, width, label='Multi-start', alpha=0.8, color='blue')

    plt.xlabel('Metric')
    plt.ylabel('Value')
    plt.title('Error Metrics')
    plt.xticks(x_pos, metrics)
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.yscale('log')

    # Plot 6: Convergence status
    ax6 = plt.subplot(2, 3, 6)
    convergence_data = [
        ['Single', 'Converged' if result_single.convergence_status else 'Failed'],
        ['Multi-start', 'Converged' if result_multi.convergence_status else 'Failed']
    ]

    colors = ['green' if status == 'Converged' else 'red' for _, status in convergence_data]
    methods = [method for method, _ in convergence_data]

    plt.bar(methods, [1, 1], color=colors, alpha=0.7)
    plt.ylabel('Convergence Status')
    plt.title('Optimization Convergence')
    plt.ylim(0, 1.2)

    # Add text labels
    for i, (method, status) in enumerate(convergence_data):
        plt.text(i, 0.5, status, ha='center', va='center', fontweight='bold')

    plt.tight_layout()
    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output", "examples", "basic")
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "simple_inversion_result.png"), dpi=300)
    plt.show()


def analyze_convergence(result_single, result_multi):
    """Analyze and report convergence details."""

    print("\nConvergence Analysis:")
    print("-" * 30)

    print("Single optimization:")
    print(f"  Converged: {result_single.convergence_status}")
    print(f"  Final RMSE: {result_single.objective_value:.6f}")
    if 'iterations' in result_single.additional_info:
        print(f"  Iterations: {result_single.additional_info['iterations']}")

    print("\nMulti-start optimization:")
    print(f"  Converged: {result_multi.convergence_status}")
    print(f"  Final RMSE: {result_multi.objective_value:.6f}")
    if 'iterations' in result_multi.additional_info:
        print(f"  Iterations: {result_multi.additional_info['iterations']}")

    # Determine which method performed better
    if result_multi.objective_value < result_single.objective_value:
        improvement = ((result_single.objective_value - result_multi.objective_value) /
                       result_single.objective_value) * 100
        print(f"\nMulti-start improved RMSE by {improvement:.2f}%")
    else:
        print(f"\nSingle optimization performed as well as multi-start")


if __name__ == "__main__":
    main()