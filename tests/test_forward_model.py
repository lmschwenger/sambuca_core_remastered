import numpy as np
from matplotlib import pyplot as plt
import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters


def test_debug_forward_model():
    """Debug test to understand forward model behavior."""
    # Set up basic parameters
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.05, 0.5, num_bands)
    a_ph_star = np.array([0.06, 0.05, 0.04, 0.03, 0.04, 0.02, 0.01, 0.01, 0.02, 0.03])
    substrate1 = np.array([0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55])

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
            num_bands=num_bands
        )
        plt.plot(wavelengths, result.rrs, 'o-', label=f'Depth={depth}m')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Depth on Rrs (fixed chl=1.2)')
    plt.legend()
    plt.grid(True)
    plt.savefig('debug_depth_effect.png')

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
            num_bands=num_bands
        )
        plt.plot(wavelengths, result.rrs, 'o-', label=f'Chl={chl}')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Chlorophyll on Rrs (fixed depth=3.5m)')
    plt.legend()
    plt.grid(True)
    plt.savefig('debug_chl_effect.png')


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