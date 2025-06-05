Getting Started
===============

This guide will introduce you to SAMBUCA Core concepts and walk you through your first successful forward model and inversion. By the end, you'll understand the basic workflow and be ready to tackle more advanced applications.

What is SAMBUCA?
----------------

SAMBUCA (Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment) is a physics-based model that:

🌊 **Simulates** how light travels through water columns  
📡 **Predicts** what satellites observe over shallow waters  
🔍 **Estimates** water properties from satellite measurements  
🗺️ **Maps** bathymetry and water quality at scale  

Key Concepts
------------

Before we dive into code, let's understand the fundamental concepts:

Forward Model vs. Inversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: ../_static/forward_vs_inversion.png
   :alt: Forward model vs inversion diagram
   :align: center
   :width: 600px

**Forward Model** (Physics → Observations)
   Given water properties (depth, chlorophyll, etc.), predict satellite reflectance

**Inversion** (Observations → Physics)  
   Given satellite reflectance, estimate water properties

Water Constituents
~~~~~~~~~~~~~~~~~~

SAMBUCA models four main components:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Component
     - Symbol
     - Description
   * - **Chlorophyll**
     - CHL
     - Phytoplankton concentration [mg/m³]
   * - **CDOM**
     - CDOM
     - Colored dissolved organic matter [1/m]
   * - **NAP**
     - NAP
     - Non-algal particles [mg/L]
   * - **Depth**
     - H
     - Water column depth [m]

Each component has specific optical properties that affect how light is absorbed and scattered.

Spectral Bands
~~~~~~~~~~~~~~

SAMBUCA works with multispectral data. Common sensors:

- **Sentinel-2**: 4 bands [492, 560, 665, 704 nm]
- **Landsat-8**: 4 bands [482, 562, 655, 865 nm]  
- **Custom**: Any wavelength configuration

Installation Check
------------------

First, verify your installation is working:

.. code-block:: python

   import sambuca_core as sbc
   print(f"SAMBUCA Core v{sbc.__version__} ready!")

If this works, you're ready to proceed. If not, see :doc:`../installation`.

Your First Forward Model
-------------------------

Let's start with the core of SAMBUCA - the forward model.

Step 1: Import and Setup
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np
   import matplotlib.pyplot as plt

Step 2: Define Basic Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Sentinel-2 wavelengths (blue, green, red, NIR)
   wavelengths = [492.4, 559.8, 664.6, 704.1]  # nm
   
   # Pure water absorption coefficient  
   a_water = [0.007, 0.015, 0.325, 0.619]  # 1/m
   
   # Specific absorption of phytoplankton
   a_ph_star = [0.055, 0.023, 0.014, 0.010]  # m²/mg
   
   # Sand substrate reflectance
   substrate = [0.3, 0.3, 0.25, 0.2]  # unitless
   
   print("Parameters defined successfully!")

Step 3: Run Your First Forward Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define water conditions
   water_properties = {
       'chl': 2.0,      # 2 mg/m³ chlorophyll
       'cdom': 0.5,     # 0.5 1/m CDOM absorption
       'nap': 1.5,      # 1.5 mg/L particles
       'depth': 5.0     # 5 m depth
   }
   
   # Run forward model
   results = sbc.forward_model(
       chl=water_properties['chl'],
       cdom=water_properties['cdom'],
       nap=water_properties['nap'],
       depth=water_properties['depth'],
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   print(f"Success! Modeled reflectance: {results.rrs}")
   print(f"Absorption coefficients: {results.a}")

Expected output:

.. code-block:: text

   Success! Modeled reflectance: [0.0089 0.0134 0.0051 0.0039]
   Absorption coefficients: [0.1175 0.0610 0.3530 0.6490]

Step 4: Visualize the Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create a comprehensive plot
   fig, axes = plt.subplots(2, 2, figsize=(12, 8))
   
   # Plot 1: Reflectance spectrum
   axes[0,0].plot(wavelengths, results.rrs, 'b-o', linewidth=2, markersize=8)
   axes[0,0].set_xlabel('Wavelength (nm)')
   axes[0,0].set_ylabel('Remote Sensing Reflectance')
   axes[0,0].set_title('Modeled Reflectance Spectrum')
   axes[0,0].grid(True, alpha=0.3)
   
   # Plot 2: Absorption components
   axes[0,1].plot(wavelengths, results.a_water, 'b-', label='Water', linewidth=2)
   axes[0,1].plot(wavelengths, results.a_ph, 'g-', label='Phytoplankton', linewidth=2)
   axes[0,1].plot(wavelengths, results.a_cdom, 'y-', label='CDOM', linewidth=2)
   axes[0,1].plot(wavelengths, results.a_nap, 'r-', label='NAP', linewidth=2)
   axes[0,1].set_xlabel('Wavelength (nm)')
   axes[0,1].set_ylabel('Absorption (1/m)')
   axes[0,1].set_title('Absorption Components')
   axes[0,1].legend()
   axes[0,1].set_yscale('log')
   axes[0,1].grid(True, alpha=0.3)
   
   # Plot 3: Backscatter components
   axes[1,0].plot(wavelengths, results.bb_water, 'b-', label='Water', linewidth=2)
   axes[1,0].plot(wavelengths, results.bb_ph, 'g-', label='Phytoplankton', linewidth=2)
   axes[1,0].plot(wavelengths, results.bb_nap, 'r-', label='NAP', linewidth=2)
   axes[1,0].set_xlabel('Wavelength (nm)')
   axes[1,0].set_ylabel('Backscatter (1/m)')
   axes[1,0].set_title('Backscatter Components')
   axes[1,0].legend()
   axes[1,0].grid(True, alpha=0.3)
   
   # Plot 4: Attenuation coefficients
   axes[1,1].plot(wavelengths, results.kd, 'purple', label='Diffuse (Kd)', linewidth=2)
   axes[1,1].plot(wavelengths, results.kuc, 'orange', label='Upwelling (Kuc)', linewidth=2)
   axes[1,1].set_xlabel('Wavelength (nm)')
   axes[1,1].set_ylabel('Attenuation (1/m)')
   axes[1,1].set_title('Attenuation Coefficients')
   axes[1,1].legend()
   axes[1,1].set_yscale('log')
   axes[1,1].grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Understanding the Results
~~~~~~~~~~~~~~~~~~~~~~~~~

The forward model returns a comprehensive :class:`ForwardModelResults` object containing:

**Primary Outputs:**
- ``rrs``: What the satellite observes
- ``r_substratum``: Bottom reflectance contribution

**Optical Components:**
- ``a``: Total absorption (water + phytoplankton + CDOM + NAP)
- ``bb``: Total backscatter (water + phytoplankton + NAP)

**Attenuation Coefficients:**
- ``kd``: Diffuse attenuation (how fast light decreases with depth)
- ``kuc``, ``kub``: Upwelling attenuation coefficients

Exploring Parameter Effects
---------------------------

Let's see how changing water properties affects the spectrum:

Depth Effect
~~~~~~~~~~~~

.. code-block:: python

   # Test different depths
   depths = [1, 3, 5, 10, 20]  # meters
   colors = ['red', 'orange', 'green', 'blue', 'purple']
   
   plt.figure(figsize=(10, 6))
   
   for depth, color in zip(depths, colors):
       results = sbc.forward_model(
           chl=2.0, cdom=0.5, nap=1.5, depth=depth,
           substrate1=substrate, wavelengths=wavelengths,
           a_water=a_water, a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       plt.plot(wavelengths, results.rrs, 'o-', color=color, 
                label=f'{depth}m', linewidth=2, markersize=6)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Effect of Water Depth on Reflectance')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.show()

**Observation**: Deeper water = lower reflectance (less bottom contribution)

Chlorophyll Effect
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Test different chlorophyll concentrations
   chls = [0.5, 1.0, 2.0, 5.0, 10.0]  # mg/m³
   
   plt.figure(figsize=(10, 6))
   
   for chl in chls:
       results = sbc.forward_model(
           chl=chl, cdom=0.5, nap=1.5, depth=5.0,
           substrate1=substrate, wavelengths=wavelengths,
           a_water=a_water, a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       plt.plot(wavelengths, results.rrs, 'o-', 
                label=f'{chl} mg/m³', linewidth=2, markersize=6)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Effect of Chlorophyll on Reflectance')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.show()

**Observation**: Higher chlorophyll = lower blue/green, slightly higher red edge

Working with SIOP Manager
--------------------------

For real applications, use the SIOP Manager to handle spectral libraries professionally:

Setup SIOP Manager
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Note: This requires spectral library files
   # For now, we'll show the structure
   
   try:
       # Initialize with spectral libraries (if available)
       siop_manager = sbc.SIOPManager("data/")
       
       # Register Sentinel-2
       siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])
       
       # Get automatically interpolated SIOPs
       siops = siop_manager.get_standard_siops("Sentinel-2")
       
       print("SIOP Manager setup successful!")
       print(f"Available SIOPs: {list(siops.keys())}")
       
       # Use managed SIOPs in forward model
       results = sbc.forward_model(
           chl=2.0, cdom=0.5, nap=1.5, depth=5.0,
           substrate1=siops['substrate1'],
           wavelengths=siops['wavelengths'],
           a_water=siops['a_water'],
           a_ph_star=siops['a_ph_star'],
           num_bands=siops['num_bands']
       )
       
   except FileNotFoundError:
       print("Spectral library files not found - using manual SIOPs")
       print("See user_guide/siop_management for setup instructions")

Your First Inversion
---------------------

Now let's estimate water properties from observed reflectance:

Generate Synthetic Observation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # First, generate a "true" spectrum with known properties
   true_properties = {
       'chl': 3.0,    # True chlorophyll
       'cdom': 0.8,   # True CDOM
       'nap': 2.0,    # True NAP
       'depth': 7.5   # True depth
   }
   
   # Generate synthetic observation
   true_results = sbc.forward_model(
       chl=true_properties['chl'],
       cdom=true_properties['cdom'],
       nap=true_properties['nap'],
       depth=true_properties['depth'],
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   # Add realistic noise
   noise_level = 0.0005  # 0.05% relative noise
   observed_rrs = true_results.rrs + np.random.normal(0, noise_level, len(wavelengths))
   
   print(f"True properties: {true_properties}")
   print(f"Observed RRS: {observed_rrs}")

Run Inversion
~~~~~~~~~~~~~

.. code-block:: python

   from sambuca_core.inversion import InversionParameters, invert_spectrum
   
   # Set up inversion parameters
   params = InversionParameters(
       depth=(0, 15),       # Search range for depth
       chl=(0.1, 10.0),     # Search range for chlorophyll
       cdom=(0.01, 2.0),    # Search range for CDOM
       nap=(0.1, 5.0),      # Search range for NAP
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       substrate1=substrate,
       num_bands=len(wavelengths)
   )
   
   # Run inversion
   result = invert_spectrum(observed_rrs, params)
   
   print("\\nInversion Results:")
   print("=" * 50)
   for param in ['depth', 'chl', 'cdom', 'nap']:
       true_val = true_properties[param]
       estimated_val = result.parameters[param]
       error = abs(estimated_val - true_val)
       error_pct = 100 * error / true_val
       print(f"{param:>6}: True={true_val:6.2f}, Est={estimated_val:6.2f}, Error={error_pct:5.1f}%")
   
   print(f"\\nRMSE: {result.objective_value:.6f}")

Expected output:

.. code-block:: text

   Inversion Results:
   ==================================================
    depth: True=  7.50, Est=  7.48, Error= 0.3%
      chl: True=  3.00, Est=  3.02, Error= 0.7%
     cdom: True=  0.80, Est=  0.79, Error= 1.2%
      nap: True=  2.00, Est=  2.01, Error= 0.5%
   
   RMSE: 0.000523

Validate Inversion Results
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate spectrum from inverted parameters
   inverted_results = sbc.forward_model(
       chl=result.parameters['chl'],
       cdom=result.parameters['cdom'],
       nap=result.parameters['nap'],
       depth=result.parameters['depth'],
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   # Plot comparison
   plt.figure(figsize=(12, 5))
   
   # Spectral comparison
   plt.subplot(1, 2, 1)
   plt.plot(wavelengths, true_results.rrs, 'b-o', label='True', linewidth=2, markersize=8)
   plt.plot(wavelengths, observed_rrs, 'r-s', label='Observed (noisy)', linewidth=2, markersize=8)
   plt.plot(wavelengths, inverted_results.rrs, 'g--', label='Inverted', linewidth=2)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Spectral Fit Comparison')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   # Parameter comparison
   plt.subplot(1, 2, 2)
   params = ['depth', 'chl', 'cdom', 'nap']
   true_vals = [true_properties[p] for p in params]
   est_vals = [result.parameters[p] for p in params]
   
   x = np.arange(len(params))
   width = 0.35
   
   plt.bar(x - width/2, true_vals, width, label='True', alpha=0.7, color='blue')
   plt.bar(x + width/2, est_vals, width, label='Estimated', alpha=0.7, color='green')
   
   plt.xlabel('Parameters')
   plt.ylabel('Values')
   plt.title('Parameter Recovery')
   plt.xticks(x, params)
   plt.legend()
   plt.grid(True, alpha=0.3, axis='y')
   
   plt.tight_layout()
   plt.show()

Understanding Inversion Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The inversion returns an :class:`InversionResult` object containing:

- **parameters**: Dictionary of estimated values
- **objective_value**: Goodness of fit (lower = better)
- **success**: Whether optimization converged
- **message**: Detailed optimization information

Common Workflows
----------------

Here are the most common SAMBUCA workflows:

Single Pixel Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Analyze one satellite pixel
   def analyze_pixel(observed_rrs, sensor_wavelengths):
       # Setup inversion
       params = InversionParameters(
           depth=(0, 20), chl=(0.1, 15.0), cdom=(0.01, 2.0),
           wavelengths=sensor_wavelengths
       )
       # Add SIOPs (manual or from SIOP manager)
       # Run inversion
       return invert_spectrum(observed_rrs, params)

Sensitivity Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Study how parameters affect reflectance
   def sensitivity_study():
       base_params = {'chl': 2.0, 'cdom': 0.5, 'nap': 1.5, 'depth': 5.0}
       
       for param in base_params:
           # Vary one parameter, keep others fixed
           values = np.linspace(0.5 * base_params[param], 2.0 * base_params[param], 10)
           # Run forward model for each value
           # Plot results
           pass

Validation Study
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Compare with field measurements
   def validation_study(field_data, satellite_data):
       results = []
       for i, (field, satellite) in enumerate(zip(field_data, satellite_data)):
           # Run inversion on satellite
           inverted = invert_spectrum(satellite, params)
           # Compare with field measurements
           results.append({
               'field_chl': field['chl'],
               'satellite_chl': inverted.parameters['chl'],
               'error': abs(field['chl'] - inverted.parameters['chl'])
           })
       return results

Troubleshooting
---------------

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: ``AssertionError: substrate1 length must match num_bands``

**Solution**: Ensure all spectral arrays have the same length

.. code-block:: python

   # Check array lengths
   print(f"Wavelengths: {len(wavelengths)}")
   print(f"A_water: {len(a_water)}")
   print(f"A_ph_star: {len(a_ph_star)}")
   print(f"Substrate: {len(substrate)}")
   print(f"Num_bands: {len(wavelengths)}")

**Issue**: Inversion returns unrealistic values

**Solution**: Check parameter bounds and add constraints

.. code-block:: python

   # Tighten parameter bounds
   params = InversionParameters(
       depth=(2, 15),      # Exclude very shallow water
       chl=(0.5, 8.0),     # Realistic chlorophyll range
       cdom=(0.05, 1.5),   # Typical CDOM range
   )

**Issue**: Forward model returns very high/low reflectance

**Solution**: Check input parameter ranges

.. code-block:: python

   # Validate input ranges
   assert 0.1 <= chl <= 50.0, "Chlorophyll out of range"
   assert 0.01 <= cdom <= 5.0, "CDOM out of range"
   assert 0.1 <= nap <= 20.0, "NAP out of range"
   assert 0.5 <= depth <= 50.0, "Depth out of range"

Performance Tips
~~~~~~~~~~~~~~~~

- **Use SIOP Manager** for better organization
- **Vectorize calculations** when processing multiple spectra
- **Cache results** for repeated parameter combinations
- **Use appropriate bounds** to speed up inversion

Next Steps
----------

Congratulations! You've successfully:

✅ Run your first forward model  
✅ Understood the key outputs  
✅ Explored parameter effects  
✅ Performed your first inversion  
✅ Validated the results  

**Where to go next:**

🎯 **For detailed forward modeling**: :doc:`forward_modeling`  
🔍 **For advanced inversion**: :doc:`inversion`  
📊 **For spectral library management**: :doc:`siop_management`  
🗺️ **For image processing**: :doc:`image_processing`  
🎛️ **For parameter optimization**: :doc:`configuration`

**Ready for real data?**

1. **Prepare your satellite data** (Sentinel-2, Landsat, etc.)
2. **Set up spectral libraries** using the SIOP Manager
3. **Process images** using the workflows in :doc:`image_processing`
4. **Validate results** against field measurements

Remember: SAMBUCA is a powerful tool, but like any model, it requires understanding of the underlying physics and careful validation against real-world data.

Exercises
---------

Try these exercises to reinforce your learning:

**Exercise 1: Parameter Exploration**
   Create a grid of chlorophyll vs depth combinations and visualize how reflectance changes

**Exercise 2: Sensor Comparison**
   Compare how Sentinel-2 vs Landsat-8 wavelengths affect the same water conditions

**Exercise 3: Substrate Effects**
   Model the same water column over sand vs seagrass substrates

**Exercise 4: Noise Analysis**
   Add different levels of noise to synthetic observations and see how it affects inversion accuracy

**Exercise 5: Real Data**
   Download a Sentinel-2 scene over coastal waters and try to process a few pixels

Solutions and more advanced examples can be found in :doc:`../examples/index`.
