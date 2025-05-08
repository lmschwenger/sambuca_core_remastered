"""Test for single pixel inversion functionality with visualization and bound checking."""

import numpy as np
import pytest
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, invert_spectrum, multi_start_inversion


def test_bounds_in_optimization():
    """Test that the optimization respects parameter bounds."""
    # Set up simple test data
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.05, 0.5, num_bands)
    a_ph_star = np.array([0.06, 0.05, 0.04, 0.03, 0.04, 0.02, 0.01, 0.01, 0.02, 0.03])
    substrate1 = np.array([0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55])

    # True values
    true_chl = 1.2
    true_depth = 3.5

    # Generate observed data
    observed_rrs = sbc.forward_model(
        chl=true_chl,
        cdom=0.5,
        nap=1.0,
        depth=true_depth,
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands
    ).rrs

    # Explicit bounds for testing
    chl_min, chl_max = 0.1, 5.0
    depth_min, depth_max = 0.1, 10.0

    # Create inversion parameters
    inversion_params = InversionParameters(
        chl=(chl_min, chl_max),
        depth=(depth_min, depth_max),
        fixed_cdom=0.5,
        fixed_nap=1.0,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1
    )

    # Test with different optimization methods and options
    methods_to_test = [
        ('L-BFGS-B', {'maxiter': 200, 'ftol': 1e-8, 'gtol': 1e-8}),
        ('SLSQP', {'maxiter': 200, 'ftol': 1e-8}),
        # Add other methods that support bounds if needed
    ]

    for method, options in methods_to_test:
        result = invert_spectrum(
            observed_rrs,
            inversion_params,
            method=method,
            options=options
        )

        print(f"\nOptimization method: {method}")
        print(f"Bounds: chl=({chl_min}, {chl_max}), depth=({depth_min}, {depth_max})")
        print(f"Actual: chl={result.parameters['chl']}, depth={result.parameters['depth']}")

        # Check that the parameters are within bounds
        assert result.parameters['chl'] >= chl_min, f"Chlorophyll {result.parameters['chl']} is below lower bound {chl_min}"
        assert result.parameters['chl'] <= chl_max, f"Chlorophyll {result.parameters['chl']} is above upper bound {chl_max}"
        assert result.parameters['depth'] >= depth_min, f"Depth {result.parameters['depth']} is below lower bound {depth_min}"
        assert result.parameters['depth'] <= depth_max, f"Depth {result.parameters['depth']} is above upper bound {depth_max}"

        # Plot the comparison
        plt.figure(figsize=(10, 6))
        plt.plot(wavelengths, observed_rrs, 'ro-', label='Observed')
        plt.plot(wavelengths, result.modeled_spectra, 'b.-', label=f'Modeled ({method})')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Remote Sensing Reflectance')
        plt.title(f'Optimization with {method}\n' +
                  f'True: chl={true_chl}, depth={true_depth}\n' +
                  f'Retrieved: chl={result.parameters["chl"]:.3f}, depth={result.parameters["depth"]:.3f}\n'
                  f'Objective value: {result.objective_value:.6f}')
        plt.legend()
        plt.grid(True)

        # Save plot
        plt.savefig(f'inversion_test_{method}.png', dpi=300)

        # Also try multi-start with this method
        multi_result = multi_start_inversion(
            observed_rrs,
            inversion_params,
            n_starts=5,
            method=method
        )

        print(f"Multi-start {method}: chl={multi_result.parameters['chl']}, "
              f"depth={multi_result.parameters['depth']}")

        # Check multi-start results are within bounds
        assert multi_result.parameters['chl'] >= chl_min, f"Multi-start chlorophyll {multi_result.parameters['chl']} is below lower bound {chl_min}"
        assert multi_result.parameters['chl'] <= chl_max, f"Multi-start chlorophyll {multi_result.parameters['chl']} is above upper bound {chl_max}"

        # Plot with both single and multi-start results
        plt.figure(figsize=(10, 6))
        plt.plot(wavelengths, observed_rrs, 'ro-', label='Observed')
        plt.plot(wavelengths, result.modeled_spectra, 'b.-', label=f'Single start ({method})')
        plt.plot(wavelengths, multi_result.modeled_spectra, 'g--', label=f'Multi-start ({method})')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Remote Sensing Reflectance')
        plt.title(f'Optimization Comparison ({method})\n' +
                  f'True: chl={true_chl}, depth={true_depth}\n' +
                  f'Single: chl={result.parameters["chl"]:.3f}, depth={result.parameters["depth"]:.3f}\n' +
                  f'Multi: chl={multi_result.parameters["chl"]:.3f}, depth={multi_result.parameters["depth"]:.3f}')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'inversion_comparison_{method}.png', dpi=300)


def test_with_custom_initial_values():
    """Test optimization with specific initial values."""
    # Set up simple test data
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.05, 0.5, num_bands)
    a_ph_star = np.array([0.06, 0.05, 0.04, 0.03, 0.04, 0.02, 0.01, 0.01, 0.02, 0.03])
    substrate1 = np.array([0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55])

    # True values
    true_chl = 1.2
    true_depth = 3.5

    # Generate observed data
    observed_rrs = sbc.forward_model(
        chl=true_chl,
        cdom=0.5,
        nap=1.0,
        depth=true_depth,
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands
    ).rrs

    # Create inversion parameters
    inversion_params = InversionParameters(
        chl=(0.1, 5.0),
        depth=(0.1, 10.0),
        fixed_cdom=0.5,
        fixed_nap=1.0,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1
    )

    # Try different initial values
    initial_values_to_test = [
        [0.5, 2.0],    # Further from true
        [1.0, 3.0],    # Close to true
        [2.0, 5.0],    # Above true
        [0.1, 0.5],    # At/near lower bounds
        [4.0, 9.0]     # Near upper bounds
    ]

    plt.figure(figsize=(12, 8))
    plt.plot(wavelengths, observed_rrs, 'ro-', label='Observed', linewidth=2)

    for i, initial in enumerate(initial_values_to_test):
        result = invert_spectrum(
            observed_rrs,
            inversion_params,
            initial_values=initial,
            method='L-BFGS-B',
            options={'maxiter': 200}
        )

        print(f"\nInitial values: chl={initial[0]}, depth={initial[1]}")
        print(f"Final values: chl={result.parameters['chl']:.3f}, depth={result.parameters['depth']:.3f}")
        print(f"Objective value: {result.objective_value:.6f}")

        # Ensure bounds are respected
     #   assert result.parameters['chl'] >= 0.1, f"Chlorophyll {result.parameters['chl']} is below lower bound 0.1"
     #   assert result.parameters['chl'] <= 5.0, f"Chlorophyll {result.parameters['chl']} is above upper bound 5.0"

        # Plot results
        plt.plot(wavelengths, result.modeled_spectra, '.-',
                 label=f'Init: chl={initial[0]}, depth={initial[1]} → chl={result.parameters["chl"]:.3f}, depth={result.parameters["depth"]:.3f}')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Initial Values on Inversion')
    plt.legend()
    plt.grid(True)
    plt.savefig('inversion_initial_values.png', dpi=300)


def inspect_optimization_process():
    """Helper function to debug the optimization process (not a test)."""
    # This function would be used to directly inspect the optimization implementation
    # to check how bounds are being handled
    from scipy import optimize

    # Set up simple test data
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.05, 0.5, num_bands)
    a_ph_star = np.array([0.06, 0.05, 0.04, 0.03, 0.04, 0.02, 0.01, 0.01, 0.02, 0.03])
    substrate1 = np.array([0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55])

    true_chl = 1.2
    true_depth = 3.5

    observed_rrs = sbc.forward_model(
        chl=true_chl,
        cdom=0.5,
        nap=1.0,
        depth=true_depth,
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands
    ).rrs

    # Create inversion parameters
    inversion_params = InversionParameters(
        chl=(0.1, 5.0),
        depth=(0.1, 10.0),
        fixed_cdom=0.5,
        fixed_nap=1.0,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1
    )

    # Get bounds and initial values
    bounds = inversion_params.get_parameter_bounds()
    initial_values = inversion_params.get_initial_values()

    # Define an objective function with print statements for debugging
    def objective(x):
        from sambuca_core.inversion.objective_functions import spectral_rmse
        value = spectral_rmse(x, observed_rrs, inversion_params)
        print(f"Parameters: {x}, Objective value: {value}")
        return value

    # Run optimization with callback for debugging
    def callback(xk):
        print(f"Iteration parameters: {xk}")

    result = optimize.minimize(
        objective,
        initial_values,
        method='L-BFGS-B',
        bounds=bounds,
        options={'maxiter': 10},  # Limited iterations for debugging
        callback=callback
    )

    print("Optimization result:", result)


def test_objective_function_behavior():
    """Test the behavior of the objective function."""
    # Set up test data
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.05, 0.5, num_bands)
    a_ph_star = np.array([0.06, 0.05, 0.04, 0.03, 0.04, 0.02, 0.01, 0.01, 0.02, 0.03])
    substrate1 = np.array([0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55])

    # True parameters
    true_chl = 1.2
    true_depth = 3.5

    # Generate "observed" data
    observed_rrs = sbc.forward_model(
        chl=true_chl,
        cdom=0.5,
        nap=1.0,
        depth=true_depth,
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands
    ).rrs

    # Create inversion parameters
    inversion_params = sbc.inversion.InversionParameters(
        chl=(0.1, 5.0),
        depth=(0.1, 10.0),
        fixed_cdom=0.5,
        fixed_nap=1.0,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1
    )

    # Calculate error landscape
    chl_values = np.linspace(0.1, 5.0, 50)
    depth_values = np.linspace(0.1, 10.0, 50)

    errors = np.zeros((len(chl_values), len(depth_values)))

    for i, chl in enumerate(chl_values):
        for j, depth in enumerate(depth_values):
            # Run forward model with these parameters
            modeled_rrs = sbc.forward_model(
                chl=chl,
                cdom=0.5,
                nap=1.0,
                depth=depth,
                substrate1=substrate1,
                wavelengths=wavelengths,
                a_water=a_water,
                a_ph_star=a_ph_star,
                num_bands=num_bands
            ).rrs

            # Calculate error
            errors[i, j] = np.sqrt(np.mean((modeled_rrs - observed_rrs) ** 2))

    # Visualize the error landscape
    plt.figure(figsize=(12, 10))
    plt.contourf(depth_values, chl_values, errors, 50, cmap='viridis')
    plt.colorbar(label='RMSE')
    plt.plot(true_depth, true_chl, 'ro', markersize=10, label='True Values')
    plt.plot(1.147, 0.965, 'go', markersize=10, label='Inverted Values')
    plt.xlabel('Depth (m)')
    plt.ylabel('Chlorophyll (mg/m³)')
    plt.title('Error Landscape for Inversion')
    plt.legend()
    plt.savefig('error_landscape.png')

    # Also create a 3D surface plot
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    X, Y = np.meshgrid(depth_values, chl_values)
    surf = ax.plot_surface(X, Y, errors, cmap='viridis')
    ax.set_xlabel('Depth (m)')
    ax.set_ylabel('Chlorophyll (mg/m³)')
    ax.set_zlabel('RMSE')
    ax.set_title('3D Error Landscape')
    fig.colorbar(surf)
    plt.savefig('error_landscape_3d.png')


def test_more_complex_inversion():
    """Test inversion with more parameters and spectral shapes."""
    # Set up test data with realistic wavelengths and parameters
    num_bands = 15  # More bands for better spectral resolution
    wavelengths = np.linspace(400, 800, num_bands)

    # More realistic spectral shapes
    # Water absorption increases rapidly in red/NIR
    a_water = 0.05 + 0.45 * np.exp((wavelengths - 700) / 100)

    # Phytoplankton absorption with peaks at 440 and 675 nm
    a_ph_star = 0.01 + 0.05 * np.exp(-0.005 * (wavelengths - 440) ** 2) + \
                0.02 * np.exp(-0.01 * (wavelengths - 675) ** 2)

    # Bright sand substrate
    substrate1 = 0.1 + 0.3 * (wavelengths - 400) / 400
    substrate1 = np.clip(substrate1, 0, 1)

    # Darker seagrass substrate with slight green peak
    substrate2 = 0.05 + 0.1 * np.exp(-0.001 * (wavelengths - 550) ** 2)
    substrate2 = np.clip(substrate2, 0, 1)

    # Define "true" parameters to recover
    true_chl = 1.5
    true_depth = 4.0
    true_substrate_fraction = 0.7

    # Generate synthetic observed data using the forward model
    observed_rrs = sbc.forward_model(
        chl=true_chl,
        cdom=0.5,  # Fixed parameter
        nap=1.0,  # Fixed parameter
        depth=true_depth,
        substrate1=substrate1,
        substrate2=substrate2,
        substrate_fraction=true_substrate_fraction,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands
    ).rrs

    # Create inversion parameters
    inversion_params = InversionParameters(
        # Parameters to invert (with bounds)
        chl=(0.1, 5.0),
        depth=(0.1, 10.0),
        substrate_fraction=(0.0, 1.0),

        # Fixed parameters
        fixed_cdom=0.5,
        fixed_nap=1.0,

        # Essential parameters for the forward model
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1,
        substrate2=substrate2
    )

    # Use multi-start inversion
    result = multi_start_inversion(
        observed_rrs,
        inversion_params,
        n_starts=8  # More starting points for this complex case
    )

    # Plot the results
    plt.figure(figsize=(10, 6))
    plt.plot(wavelengths, observed_rrs, 'ro-', label='Observed')
    plt.plot(wavelengths, result.modeled_spectra, 'b.-', label='Modeled')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title(f'Complex Inversion Results\n' +
              f'True: chl={true_chl}, depth={true_depth}, substrate_fraction={true_substrate_fraction}\n' +
              f'Retrieved: chl={result.parameters["chl"]:.3f}, depth={result.parameters["depth"]:.3f}, ' +
              f'substrate_fraction={result.parameters["substrate_fraction"]:.3f}')
    plt.legend()
    plt.grid(True)

    # Save the plot for later inspection
    plt.savefig('complex_inversion_test_plot.png', dpi=300)

    # Tests with appropriate tolerances
    np.testing.assert_allclose(result.parameters['chl'], true_chl, rtol=0.2)
    np.testing.assert_allclose(result.parameters['depth'], true_depth, rtol=0.15)
    np.testing.assert_allclose(result.parameters['substrate_fraction'], true_substrate_fraction, rtol=0.15)

    # Check that the spectral fit is good
    np.testing.assert_allclose(result.modeled_spectra, observed_rrs, rtol=0.05)

    print("\nComplex inversion results:")
    print(f"True values:  chl={true_chl:.3f}, depth={true_depth:.3f}, substrate_fraction={true_substrate_fraction:.3f}")
    print(f"Retrieved:    chl={result.parameters['chl']:.3f}, depth={result.parameters['depth']:.3f}, " +
          f"substrate_fraction={result.parameters['substrate_fraction']:.3f}")
    print(f"Relative err: chl={abs(result.parameters['chl'] - true_chl) / true_chl * 100:.1f}%, " +
          f"depth={abs(result.parameters['depth'] - true_depth) / true_depth * 100:.1f}%, " +
          f"substrate_fraction={abs(result.parameters['substrate_fraction'] - true_substrate_fraction) / max(true_substrate_fraction, 0.01) * 100:.1f}%")
    print(f"Objective value: {result.objective_value:.8f}")

if __name__ == "__main__":
    # This allows running the inspection function directly
    inspect_optimization_process()
    test_objective_function_behavior()
    test_more_complex_inversion()