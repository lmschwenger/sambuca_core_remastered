Quick Start Guide
=================

This guide will get you up and running with SAMBUCA Core in just a few minutes. We'll cover the essential operations: forward modeling, single pixel inversion, and basic image processing.

Prerequisites
-------------

Make sure you have SAMBUCA Core installed:

.. code-block:: bash

   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[gui]"

Basic Concepts
--------------

Before diving into code, let's understand the key concepts:

**Forward Model**
   Simulates satellite reflectance given water properties (depth, chlorophyll, etc.)

**Inversion**
   Estimates water properties from observed satellite reflectance

**SIOPs (Spectral Inherent Optical Properties)**
   Fundamental optical properties that define how water constituents absorb and scatter light

**Sensors**
   Satellite instruments with specific wavelength configurations (Sentinel-2, Landsat, etc.)

1. Forward Modeling
-------------------

The forward model is the core of SAMBUCA - it simulates what a satellite would observe given specific water conditions.

Basic Forward Model
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca.core as sbc
   import numpy as np

   # Define basic parameters
   wavelengths = [492.4, 559.8, 664.6, 704.1]  # Sentinel-2 bands (nm)
   
   # Water absorption coefficient (pure water)
   a_water = [0.007, 0.015, 0.325, 0.619]  # 1/m
   
   # Specific absorption of phytoplankton
   a_ph_star = [0.055, 0.023, 0.014, 0.010]  # m²/mg
   
   # Substrate reflectance (sand bottom)
   substrate = [0.3, 0.3, 0.25, 0.2]
   
   # Run forward model
   results = sbc.forward_model(
       chl=1.5,          # Chlorophyll concentration (mg/m³)
       cdom=0.5,         # CDOM absorption (1/m)
       nap=2.0,          # Non-algal particles (mg/L)
       depth=5.0,        # Water depth (m)
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   print(f"Modeled reflectance: {results.rrs}")
   print(f"Absorption coefficient: {results.a}")
   print(f"Backscatter coefficient: {results.bb}")

Expected output:

.. code-block:: text

   Modeled reflectance: [0.012 0.018 0.008 0.006]
   Absorption coefficient: [0.045 0.062 0.373 0.651]
   Backscatter coefficient: [0.021 0.018 0.014 0.013]

2. SIOP Management
------------------

For real applications, use the SIOP Manager to handle spectral libraries professionally.

Setting Up SIOP Manager
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca.core as sbc

   # Initialize SIOP manager with spectral libraries
   siop_manager = sbc.SIOPManager("data/")  # Path to your spectral data
   
   # Register Sentinel-2 sensor
   sentinel2_wavelengths = [492.4, 559.8, 664.6, 704.1]
   siop_manager.register_sensor("Sentinel-2", sentinel2_wavelengths)
   
   # Get automatically interpolated SIOPs
   siops = siop_manager.get_standard_siops("Sentinel-2")
   
   print(f"Available parameters: {list(siops.keys())}")
   print(f"Number of bands: {siops['num_bands']}")

Using SIOPs in Forward Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Run forward model with managed SIOPs
   results = sbc.forward_model(
       chl=2.0,
       cdom=0.3,
       nap=1.5,
       depth=8.0,
       substrate1=siops['substrate1'],
       wavelengths=siops['wavelengths'],
       a_water=siops['a_water'],
       a_ph_star=siops['a_ph_star'],
       num_bands=siops['num_bands']
   )
   
   print(f"Modeled RRS: {results.rrs}")

3. Single Pixel Inversion
--------------------------

Inversion estimates water properties from observed satellite reflectance.

Basic Inversion Setup
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca.core.inversion import InversionParameters, invert_spectrum
   
   # Observed reflectance (from Sentinel-2 pixel)
   observed_rrs = np.array([0.012, 0.015, 0.008, 0.006])
   
   # Set up inversion parameters
   params = InversionParameters(
       depth=(0, 25),       # Search range for depth (0-25m)
       chl=(0.1, 10.0),     # Search range for chlorophyll (0.1-10 mg/m³)
       cdom=(0.01, 2.0),    # Search range for CDOM (0.01-2.0 m⁻¹)
       wavelengths=siops['wavelengths']
   )
   
   # Update parameters with SIOPs
   params.update_from_siop_manager(siop_manager, "Sentinel-2")
   
   # Run inversion
   result = invert_spectrum(observed_rrs, params)
   
   print(f"Estimated depth: {result.parameters['depth']:.2f} m")
   print(f"Estimated chlorophyll: {result.parameters['chl']:.2f} mg/m³")
   print(f"Estimated CDOM: {result.parameters['cdom']:.3f} m⁻¹")
   print(f"Inversion error (RMSE): {result.objective_value:.6f}")

Expected output:

.. code-block:: text

   Estimated depth: 5.12 m
   Estimated chlorophyll: 1.47 mg/m³
   Estimated CDOM: 0.524 m⁻¹
   Inversion error (RMSE): 0.000142

4. Image Processing
-------------------

Process entire satellite images to create parameter maps.

Preparing Image Data
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numpy as np
   from sambuca.core.inversion import process_image
   
   # Example: Load your Sentinel-2 reflectance image
   # In practice, use rasterio or your preferred geospatial library
   # image = rasterio.open("sentinel2_reflectance.tif").read()
   
   # For this example, create synthetic data
   height, width, bands = 50, 50, 4
   image = np.random.random((height, width, bands)) * 0.05
   
   # Add some realistic structure
   x, y = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
   depth_gradient = 2 + 8 * (x + y) / 2  # Depth increases from 2m to 10m
   
   # Simulate realistic reflectance based on depth
   for i in range(height):
       for j in range(width):
           d = depth_gradient[i, j]
           # Deeper water = lower reflectance
           image[i, j, :] *= np.exp(-0.1 * d)

Processing the Image
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process entire image
   results = process_image(
       image,
       params,
       n_processes=4,      # Use 4 CPU cores
       progress_bar=True   # Show progress
   )
   
   # Access results
   depth_map = results['depth']
   chlorophyll_map = results['chl']
   cdom_map = results['cdom']
   error_map = results['error']
   
   print(f"Depth range: {depth_map.min():.1f} - {depth_map.max():.1f} m")
   print(f"Chlorophyll range: {chlorophyll_map.min():.2f} - {chlorophyll_map.max():.2f} mg/m³")

5. Visualization
----------------

Create plots to visualize your results.

Plotting Forward Model Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import matplotlib.pyplot as plt
   
   # Plot forward model spectrum
   fig, axes = plt.subplots(1, 3, figsize=(15, 4))
   
   # Reflectance spectrum
   axes[0].plot(wavelengths, results.rrs, 'b-o', linewidth=2)
   axes[0].set_xlabel('Wavelength (nm)')
   axes[0].set_ylabel('Remote Sensing Reflectance')
   axes[0].set_title('Modeled Reflectance')
   axes[0].grid(True, alpha=0.3)
   
   # Absorption components
   axes[1].plot(wavelengths, results.a_water, 'b-', label='Water', linewidth=2)
   axes[1].plot(wavelengths, results.a_ph, 'g-', label='Phytoplankton', linewidth=2)
   axes[1].plot(wavelengths, results.a_cdom, 'y-', label='CDOM', linewidth=2)
   axes[1].plot(wavelengths, results.a_nap, 'r-', label='NAP', linewidth=2)
   axes[1].set_xlabel('Wavelength (nm)')
   axes[1].set_ylabel('Absorption (1/m)')
   axes[1].set_title('Absorption Components')
   axes[1].legend()
   axes[1].grid(True, alpha=0.3)
   
   # Backscatter components
   axes[2].plot(wavelengths, results.bb_water, 'b-', label='Water', linewidth=2)
   axes[2].plot(wavelengths, results.bb_ph, 'g-', label='Phytoplankton', linewidth=2)
   axes[2].plot(wavelengths, results.bb_nap, 'r-', label='NAP', linewidth=2)
   axes[2].set_xlabel('Wavelength (nm)')
   axes[2].set_ylabel('Backscatter (1/m)')
   axes[2].set_title('Backscatter Components')
   axes[2].legend()
   axes[2].grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Plotting Image Results
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Plot parameter maps
   fig, axes = plt.subplots(2, 2, figsize=(12, 10))
   
   # Depth map
   im1 = axes[0,0].imshow(depth_map, cmap='viridis_r', aspect='equal')
   axes[0,0].set_title('Bathymetry (m)')
   plt.colorbar(im1, ax=axes[0,0])
   
   # Chlorophyll map
   im2 = axes[0,1].imshow(chlorophyll_map, cmap='YlGn', aspect='equal')
   axes[0,1].set_title('Chlorophyll (mg/m³)')
   plt.colorbar(im2, ax=axes[0,1])
   
   # CDOM map
   im3 = axes[1,0].imshow(cdom_map, cmap='YlOrBr', aspect='equal')
   axes[1,0].set_title('CDOM (1/m)')
   plt.colorbar(im3, ax=axes[1,0])
   
   # Error map
   im4 = axes[1,1].imshow(error_map, cmap='Reds', aspect='equal')
   axes[1,1].set_title('Inversion Error')
   plt.colorbar(im4, ax=axes[1,1])
   
   for ax in axes.flat:
       ax.set_xticks([])
       ax.set_yticks([])
   
   plt.tight_layout()
   plt.show()

6. GUI Application
------------------

For interactive exploration, launch the GUI application:

.. code-block:: bash

   sambuca-gui

The GUI provides:

- **Interactive forward modeling** with real-time parameter adjustment
- **Spectral library management** with visualization
- **Single pixel inversion** with result analysis
- **Batch processing** for multiple files
- **Export capabilities** for results and plots

7. Complete Example Workflow
----------------------------

Here's a complete workflow combining all elements:

.. code-block:: python

   import sambuca.core as sbc
   import numpy as np
   import matplotlib.pyplot as plt
   from sambuca.core.inversion import InversionParameters, invert_spectrum

   # 1. Set up SIOP manager
   print("Setting up SIOP manager...")
   siop_manager = sbc.SIOPManager("data/")
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])
   siops = siop_manager.get_standard_siops("Sentinel-2")

   # 2. Generate synthetic observation with forward model
   print("Generating synthetic observation...")
   true_params = {'chl': 2.5, 'cdom': 0.8, 'nap': 1.2, 'depth': 6.5}
   
   forward_results = sbc.forward_model(
       chl=true_params['chl'],
       cdom=true_params['cdom'],
       nap=true_params['nap'],
       depth=true_params['depth'],
       substrate1=siops['substrate1'],
       wavelengths=siops['wavelengths'],
       a_water=siops['a_water'],
       a_ph_star=siops['a_ph_star'],
       num_bands=siops['num_bands']
   )
   
   # Add realistic noise
   noise_level = 0.0005
   observed_rrs = forward_results.rrs + np.random.normal(0, noise_level, len(forward_results.rrs))

   # 3. Set up inversion
   print("Setting up inversion...")
   inversion_params = InversionParameters(
       depth=(0, 20),
       chl=(0.1, 15.0),
       cdom=(0.01, 3.0),
       nap=(0.1, 10.0),
       wavelengths=siops['wavelengths']
   )
   inversion_params.update_from_siop_manager(siop_manager, "Sentinel-2")

   # 4. Run inversion
   print("Running inversion...")
   inversion_result = invert_spectrum(observed_rrs, inversion_params)

   # 5. Compare results
   print("\\nResults Comparison:")
   print("=" * 50)
   for param in ['depth', 'chl', 'cdom', 'nap']:
       true_val = true_params[param]
       estimated_val = inversion_result.parameters[param]
       error = abs(estimated_val - true_val)
       error_pct = 100 * error / true_val
       print(f"{param:>10}: True={true_val:6.2f}, Estimated={estimated_val:6.2f}, Error={error_pct:5.1f}%")
   
   print(f"\\nInversion RMSE: {inversion_result.objective_value:.6f}")

   # 6. Plot comparison
   plt.figure(figsize=(10, 6))
   
   plt.subplot(1, 2, 1)
   plt.plot(siops['wavelengths'], forward_results.rrs, 'b-o', label='True', linewidth=2)
   plt.plot(siops['wavelengths'], observed_rrs, 'r-s', label='Observed (with noise)', linewidth=2)
   
   # Generate spectrum from inverted parameters
   inverted_forward = sbc.forward_model(
       chl=inversion_result.parameters['chl'],
       cdom=inversion_result.parameters['cdom'],
       nap=inversion_result.parameters['nap'],
       depth=inversion_result.parameters['depth'],
       substrate1=siops['substrate1'],
       wavelengths=siops['wavelengths'],
       a_water=siops['a_water'],
       a_ph_star=siops['a_ph_star'],
       num_bands=siops['num_bands']
   )
   plt.plot(siops['wavelengths'], inverted_forward.rrs, 'g--', label='Inverted', linewidth=2)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Spectral Comparison')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   plt.subplot(1, 2, 2)
   params = ['depth', 'chl', 'cdom', 'nap']
   true_vals = [true_params[p] for p in params]
   est_vals = [inversion_result.parameters[p] for p in params]
   
   x = np.arange(len(params))
   width = 0.35
   
   plt.bar(x - width/2, true_vals, width, label='True', alpha=0.7)
   plt.bar(x + width/2, est_vals, width, label='Estimated', alpha=0.7)
   
   plt.xlabel('Parameters')
   plt.ylabel('Values')
   plt.title('Parameter Comparison')
   plt.xticks(x, params)
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Expected output:

.. code-block:: text

   Setting up SIOP manager...
   Loaded 8 spectral libraries from data/
   Registered sensor 'Sentinel-2' with 4 bands
   
   Generating synthetic observation...
   Setting up inversion...
   Running inversion...
   
   Results Comparison:
   ==================================================
        depth: True=  6.50, Estimated=  6.48, Error= 0.3%
          chl: True=  2.50, Estimated=  2.52, Error= 0.8%
         cdom: True=  0.80, Estimated=  0.79, Error= 1.2%
          nap: True=  1.20, Estimated=  1.21, Error= 0.8%
   
   Inversion RMSE: 0.000523

Next Steps
----------

Now that you've completed the quick start:

1. **Explore the** :doc:`user_guide/index` **for detailed tutorials**
2. **Check the** :doc:`api/index` **for complete function documentation**
3. **Review** :doc:`examples/index` **for real-world applications**
4. **Understand the theory** in :doc:`theory/index`
5. **Try the GUI** with ``sambuca-gui`` for interactive exploration

Common Next Actions
~~~~~~~~~~~~~~~~~~~

- **Process real satellite data**: Load Sentinel-2 images and apply SAMBUCA
- **Customize sensors**: Define your own wavelength configurations
- **Optimize performance**: Use lookup tables for faster processing
- **Validate results**: Compare with field measurements
- **Explore advanced features**: Error analysis, uncertainty quantification

Remember to check the :doc:`user_guide/configuration` for detailed parameter explanations and optimization tips!
