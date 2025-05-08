import numpy as np
from matplotlib import pyplot as plt
import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters


def test_debug_forward_model():
    """Test forward model with more realistic inherent optical properties."""
    # Set up basic parameters
    num_bands = 20  # More bands for better spectral resolution
    wavelengths = np.linspace(400, 800, num_bands)

    # Realistic water absorption that increases dramatically in the red/NIR
    # Based on Pope and Fry (1997) pattern
    a_water = np.zeros_like(wavelengths)
    for i, wl in enumerate(wavelengths):
        if wl < 550:  # Low absorption in blue/green
            a_water[i] = 0.01 + 0.001 * (wl - 400)
        elif wl < 650:  # Moderate increase in green/yellow
            a_water[i] = 0.02 + 0.003 * (wl - 550)
        else:  # Strong increase in red/NIR
            a_water[i] = 0.05 + 0.08 * np.exp(0.01 * (wl - 650))

    # Realistic phytoplankton absorption with peaks at 440 and 675 nm
    a_ph_star = 0.01 + 0.05 * np.exp(-0.005 * (wavelengths - 440) ** 2) + \
                0.02 * np.exp(-0.01 * (wavelengths - 675) ** 2)

    # Typical sand substrate (increasing with wavelength)
    substrate1 = 0.1 + 0.3 * (wavelengths - 400) / 400
    substrate1 = np.clip(substrate1, 0, 1)

    # Test with a grid of parameters
    depths = [0.5, 1.0, 2.0, 3.5, 5.0, 10.0]
    chls = [0.1, 0.5, 1.2, 2.0, 5.0]

    plt.figure(figsize=(15, 10))

    # Plot effect of depth
    for depth in depths:
        result = sbc.forward_model(
            chl=1.2,
            cdom=0.5,
            nap=1.0,
            depth=depth,
            substrate1=substrate1,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=len(wavelengths)
        )
        plt.plot(wavelengths, result.rrs, 'o-', label=f'Depth={depth}m')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Depth on Rrs with Realistic IOPs (fixed chl=1.2)')
    plt.legend()
    plt.grid(True)
    plt.savefig('realistic_depth_effect.png')

    # In a second plot, show effect of chl
    plt.figure(figsize=(15, 10))

    for chl in chls:
        result = sbc.forward_model(
            chl=chl,
            cdom=0.5,
            nap=1.0,
            depth=3.5,
            substrate1=substrate1,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=len(wavelengths)
        )
        plt.plot(wavelengths, result.rrs, 'o-', label=f'Chl={chl}')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Chlorophyll on Rrs with Realistic IOPs (fixed depth=3.5m)')
    plt.legend()
    plt.grid(True)
    plt.savefig('realistic_chl_effect.png')

    # Now try inversion with these realistic spectra
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
        num_bands=len(wavelengths)
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

    # Perform inversion
    result = sbc.inversion.invert_spectrum(
        observed_rrs,
        inversion_params,
        method='L-BFGS-B',
        options={'maxiter': 200}
    )

    # Plot inversion results
    plt.figure(figsize=(12, 8))
    plt.plot(wavelengths, observed_rrs, 'ro-', label='Observed')
    plt.plot(wavelengths, result.modeled_spectra, 'b.-', label='Modeled')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title(f'Inversion with Realistic IOPs\n' +
              f'True: chl={true_chl}, depth={true_depth}\n' +
              f'Retrieved: chl={result.parameters["chl"]:.3f}, depth={result.parameters["depth"]:.3f}')
    plt.legend()
    plt.grid(True)
    plt.savefig('realistic_inversion.png')

    print(f"True parameters: chl={true_chl}, depth={true_depth}")
    print(f"Retrieved parameters: chl={result.parameters['chl']}, depth={result.parameters['depth']}")
    print(f"Objective value: {result.objective_value}")


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


def test_revised_forward_model():
    """Test forward model with revised parameters to match published SAMBUCA spectra."""
    # Set up parameters
    num_bands = 41  # Higher resolution for better visualization
    wavelengths = np.linspace(400, 800, num_bands)

    # Revise water absorption to ensure strong NIR absorption
    a_water = np.zeros_like(wavelengths)
    for i, wl in enumerate(wavelengths):
        if wl < 550:  # Blue-green region - low absorption
            a_water[i] = 0.02 + 0.0001 * (wl - 400)
        elif wl < 650:  # Yellow-red region - moderate increase
            a_water[i] = 0.025 + 0.001 * (wl - 550)
        else:  # NIR region - steep increase
            a_water[i] = 0.125 + 0.015 * (wl - 650) ** 1.5

    # Phytoplankton absorption with more pronounced peaks
    a_ph_star = 0.01 * np.ones_like(wavelengths)
    a_ph_star += 0.03 * np.exp(-0.008 * (wavelengths - 440) ** 2)  # Blue peak
    a_ph_star += 0.015 * np.exp(-0.012 * (wavelengths - 675) ** 2)  # Red peak

    # More realistic sand substrate that levels off in the NIR
    substrate1 = np.zeros_like(wavelengths)
    for i, wl in enumerate(wavelengths):
        if wl < 600:  # Increasing into the green-yellow
            substrate1[i] = 0.1 + 0.2 * (wl - 400) / 200
        else:  # Plateauing in the red-NIR
            substrate1[i] = 0.3 + 0.05 * np.exp(-(wl - 600) / 100)

    # Test with a grid of depths
    depths = [0.5, 1.0, 2.0, 3.5, 5.0, 10.0]

    # Adjust model parameters for better physical realism
    bb_ph_slope = 1.0  # Slightly higher than default
    bb_nap_slope = 1.0  # Match phytoplankton for simplicity

    plt.figure(figsize=(12, 8))

    for depth in depths:
        result = sbc.forward_model(
            chl=1.0,
            cdom=0.5,
            nap=1.0,
            depth=depth,
            substrate1=substrate1,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=num_bands,
            bb_ph_slope=bb_ph_slope,
            bb_nap_slope=bb_nap_slope,
            # You might need to adjust these parameters too:
            # theta_air=30.0,  # Solar zenith angle
            # q_factor=np.pi  # Q-factor for R(0-) conversion
        )
        plt.plot(wavelengths, result.rrs, '-', linewidth=2, label=f'Depth = {depth}m')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Revised: Effect of Depth on Reflectance (Fixed Chl=1.0 mg/m³)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    plt.savefig('revised_depth_effect.png', dpi=300)

    # Also try a single depth with varying chlorophyll to check sensitivity
    plt.figure(figsize=(12, 8))

    chls = [0.1, 0.5, 1.0, 2.0, 5.0]
    for chl in chls:
        result = sbc.forward_model(
            chl=chl,
            cdom=0.5,
            nap=1.0,
            depth=2.0,  # Fixed medium depth
            substrate1=substrate1,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=num_bands,
            bb_ph_slope=bb_ph_slope,
            bb_nap_slope=bb_nap_slope
        )
        plt.plot(wavelengths, result.rrs, '-', linewidth=2, label=f'Chl = {chl} mg/m³')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Revised: Effect of Chlorophyll on Reflectance (Fixed Depth=2.0m)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    plt.savefig('revised_chlorophyll_effect.png', dpi=300)