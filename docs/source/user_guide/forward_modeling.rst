Forward Modeling
================

The forward model is the heart of SAMBUCA - it simulates the spectral reflectance that satellites observe over shallow waters. This guide covers the physics, implementation, and practical usage of the forward model.

Understanding the Physics
-------------------------

The SAMBUCA forward model implements the semi-analytical radiative transfer equations developed by Lee et al. (1999, 2001). It models how light travels through the water column and reflects off the bottom.

Conceptual Model
~~~~~~~~~~~~~~~~

.. code-block:: text

   Sun → Atmosphere → Water Surface → Water Column → Bottom → Water Column → Sensor

The model accounts for:

1. **Solar illumination** and viewing geometry
2. **Water surface** reflection and refraction  
3. **Water column** absorption and scattering
4. **Bottom reflection** and substrate properties
5. **Upwelling radiance** back to the sensor

Mathematical Foundation
~~~~~~~~~~~~~~~~~~~~~~~

The core equation for shallow water reflectance is:

.. math::

   R_{rs} = R_{rs}^{dp} \cdot [1 - e^{-(\frac{1}{\cos\theta_w} + \frac{Du}{\cos\theta_0}) \kappa H}] + \frac{R_{bottom}}{\pi} e^{-(\frac{1}{\cos\theta_w} + \frac{Du_b}{\cos\theta_0}) \kappa H}

Where:

- :math:`R_{rs}` = Remote sensing reflectance
- :math:`R_{rs}^{dp}` = Optically deep water reflectance
- :math:`\kappa` = Total attenuation coefficient
- :math:`H` = Water depth
- :math:`R_{bottom}` = Bottom reflectance

**Key Components:**

**Absorption** (:math:`a`)
   How strongly water constituents absorb light

**Backscatter** (:math:`b_b`) 
   How much light is scattered back toward the sensor

**Attenuation** (:math:`\kappa = a + b_b`)
   Total light loss through the water column

Water Constituents
~~~~~~~~~~~~~~~~~~

SAMBUCA models four main optically active constituents:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Constituent
     - Symbol
     - Units
     - Optical Effects
   * - **Pure Water**
     - H₂O
     - ---
     - Blue absorption, molecular scattering
   * - **Phytoplankton**
     - CHL
     - mg/m³
     - Blue/red absorption, moderate scattering
   * - **CDOM**
     - CDOM
     - 1/m
     - Exponential absorption (blue → red)
   * - **Non-algal Particles**
     - NAP
     - mg/L
     - Broad absorption, strong scattering

Each constituent has specific **Spectral Inherent Optical Properties (SIOPs)** that define how they interact with light at different wavelengths.

Basic Forward Model Usage
-------------------------

Simple Example
~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np
   import matplotlib.pyplot as plt

   # Define basic parameters
   wavelengths = [492.4, 559.8, 664.6, 704.1]  # Sentinel-2 bands
   a_water = [0.007, 0.015, 0.325, 0.619]      # Water absorption
   a_ph_star = [0.055, 0.023, 0.014, 0.010]    # Phytoplankton absorption
   substrate = [0.3, 0.3, 0.25, 0.2]           # Sand reflectance

   # Run forward model
   results = sbc.forward_model(
       chl=2.0,          # Chlorophyll concentration
       cdom=0.5,         # CDOM absorption
       nap=1.5,          # Non-algal particles
       depth=5.0,        # Water depth
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )

   print(f"Modeled reflectance: {results.rrs}")

Understanding Results
~~~~~~~~~~~~~~~~~~~~~

The forward model returns a comprehensive :class:`ForwardModelResults` object:

.. code-block:: python

   # Primary outputs
   print(f"Remote sensing reflectance: {results.rrs}")
   print(f"Optically deep reflectance: {results.rrsdp}")
   print(f"Combined substrate: {results.r_substratum}")

   # Optical coefficients  
   print(f"Total absorption: {results.a}")
   print(f"Total backscatter: {results.bb}")
   print(f"Diffuse attenuation: {results.kd}")

   # Component contributions
   print(f"Phytoplankton absorption: {results.a_ph}")
   print(f"CDOM absorption: {results.a_cdom}")
   print(f"NAP absorption: {results.a_nap}")

Advanced Parameters
-------------------

The forward model supports many optional parameters for customization:

Substrate Mixing
~~~~~~~~~~~~~~~~

Model mixed substrates (e.g., sand with seagrass patches):

.. code-block:: python

   # Define two substrate types
   sand = [0.3, 0.3, 0.25, 0.2]
   seagrass = [0.1, 0.15, 0.2, 0.25]

   # 70% sand, 30% seagrass
   results = sbc.forward_model(
       chl=1.5, cdom=0.3, nap=1.0, depth=8.0,
       substrate1=sand,
       substrate2=seagrass,
       substrate_fraction=0.7,  # Fraction of substrate1
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )

   print(f"Mixed substrate: {results.r_substratum}")

Custom SIOP Parameters
~~~~~~~~~~~~~~~~~~~~~~

Adjust spectral slopes and reference values:

.. code-block:: python

   results = sbc.forward_model(
       chl=2.0, cdom=0.8, nap=2.0, depth=6.0,
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths),
       
       # CDOM parameters
       a_cdom_slope=0.020,        # Steeper slope
       lambda0cdom=440.0,         # Different reference wavelength
       a_cdom_lambda0cdom=1.5,    # Higher reference absorption
       
       # NAP parameters  
       a_nap_slope=0.012,         # NAP absorption slope
       lambda0nap=550.0,          # NAP reference wavelength
       
       # Backscatter parameters
       bb_ph_slope=0.85,          # Phytoplankton backscatter slope
       bb_nap_slope=1.2,          # NAP backscatter slope
       x_ph_lambda0x=0.002,       # Phytoplankton backscatter magnitude
   )

Viewing Geometry
~~~~~~~~~~~~~~~~

Account for different sun and sensor angles:

.. code-block:: python

   # Model with realistic viewing geometry
   results = sbc.forward_model(
       chl=1.5, cdom=0.5, nap=1.0, depth=10.0,
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths),
       theta_air=45.0,           # 45° solar zenith angle
       off_nadir=15.0,           # 15° off-nadir viewing
       water_refractive_index=1.34  # Custom refractive index
   )

Water Column Analysis
---------------------

Examining Optical Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Analyze optical properties in detail
   results = sbc.forward_model(
       chl=3.0, cdom=1.0, nap=2.5, depth=8.0,
       substrate1=substrate, wavelengths=wavelengths,
       a_water=a_water, a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )

   # Create comprehensive optical analysis
   fig, axes = plt.subplots(2, 3, figsize=(15, 8))

   # Absorption budget
   axes[0,0].bar(range(len(wavelengths)), results.a_water, label='Water', alpha=0.7)
   axes[0,0].bar(range(len(wavelengths)), results.a_ph, bottom=results.a_water, 
                 label='Phytoplankton', alpha=0.7)
   axes[0,0].bar(range(len(wavelengths)), results.a_cdom, 
                 bottom=results.a_water + results.a_ph, label='CDOM', alpha=0.7)
   axes[0,0].bar(range(len(wavelengths)), results.a_nap,
                 bottom=results.a_water + results.a_ph + results.a_cdom, 
                 label='NAP', alpha=0.7)
   axes[0,0].set_xlabel('Band')
   axes[0,0].set_ylabel('Absorption (1/m)')
   axes[0,0].set_title('Absorption Budget')
   axes[0,0].legend()
   axes[0,0].set_xticks(range(len(wavelengths)))
   axes[0,0].set_xticklabels([f'{w:.0f}' for w in wavelengths])

   # Backscatter budget
   axes[0,1].bar(range(len(wavelengths)), results.bb_water, label='Water', alpha=0.7)
   axes[0,1].bar(range(len(wavelengths)), results.bb_ph, bottom=results.bb_water,
                 label='Phytoplankton', alpha=0.7)
   axes[0,1].bar(range(len(wavelengths)), results.bb_nap,
                 bottom=results.bb_water + results.bb_ph, label='NAP', alpha=0.7)
   axes[0,1].set_xlabel('Band')
   axes[0,1].set_ylabel('Backscatter (1/m)')
   axes[0,1].set_title('Backscatter Budget')
   axes[0,1].legend()
   axes[0,1].set_xticks(range(len(wavelengths)))
   axes[0,1].set_xticklabels([f'{w:.0f}' for w in wavelengths])

   # Single scattering albedo
   ssa = results.bb / (results.a + results.bb)
   axes[0,2].plot(wavelengths, ssa, 'ko-', linewidth=2, markersize=6)
   axes[0,2].set_xlabel('Wavelength (nm)')
   axes[0,2].set_ylabel('Single Scattering Albedo')
   axes[0,2].set_title('Single Scattering Albedo')
   axes[0,2].grid(True, alpha=0.3)

   # Attenuation coefficients
   axes[1,0].plot(wavelengths, results.kd, 'b-o', label='Kd (diffuse)', linewidth=2)
   axes[1,0].plot(wavelengths, results.kuc, 'r-s', label='Kuc (upwelling)', linewidth=2)
   axes[1,0].plot(wavelengths, results.kub, 'g-^', label='Kub (bottom)', linewidth=2)
   axes[1,0].set_xlabel('Wavelength (nm)')
   axes[1,0].set_ylabel('Attenuation (1/m)')
   axes[1,0].set_title('Attenuation Coefficients')
   axes[1,0].legend()
   axes[1,0].set_yscale('log')
   axes[1,0].grid(True, alpha=0.3)

   # Reflectance contributions
   deep_contribution = results.rrsdp * (1 - np.exp(-(1/np.cos(np.radians(30)) + 
                                                    1.03/np.cos(np.radians(0))) * 
                                                   (results.a + results.bb) * 8.0))
   bottom_contribution = results.rrs - deep_contribution
   
   axes[1,1].plot(wavelengths, results.rrs, 'k-o', label='Total', linewidth=2, markersize=6)
   axes[1,1].plot(wavelengths, deep_contribution, 'b--', label='Water column', linewidth=2)
   axes[1,1].plot(wavelengths, bottom_contribution, 'brown', label='Bottom', linewidth=2)
   axes[1,1].set_xlabel('Wavelength (nm)')
   axes[1,1].set_ylabel('Reflectance')
   axes[1,1].set_title('Reflectance Contributions')
   axes[1,1].legend()
   axes[1,1].grid(True, alpha=0.3)

   # Substrate vs depth effect
   axes[1,2].plot(wavelengths, results.r_substratum, 'brown', 
                  label='Substrate', linewidth=2)
   axes[1,2].plot(wavelengths, results.rrsdp, 'blue', 
                  label='Deep water', linewidth=2)
   axes[1,2].set_xlabel('Wavelength (nm)')
   axes[1,2].set_ylabel('Reflectance')
   axes[1,2].set_title('Substrate vs Deep Water')
   axes[1,2].legend()
   axes[1,2].grid(True, alpha=0.3)

   plt.tight_layout()
   plt.show()

Parameter Sensitivity Studies
-----------------------------

Understanding how parameters affect reflectance is crucial for inversion design:

Depth Sensitivity
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def depth_sensitivity_study():
       depths = np.linspace(1, 20, 20)
       base_params = {'chl': 2.0, 'cdom': 0.5, 'nap': 1.5}
       
       reflectances = []
       for depth in depths:
           results = sbc.forward_model(
               depth=depth, **base_params,
               substrate1=substrate, wavelengths=wavelengths,
               a_water=a_water, a_ph_star=a_ph_star,
               num_bands=len(wavelengths)
           )
           reflectances.append(results.rrs)
       
       reflectances = np.array(reflectances)
       
       # Plot depth sensitivity
       plt.figure(figsize=(12, 8))
       
       for i, wl in enumerate(wavelengths):
           plt.subplot(2, 2, i+1)
           plt.plot(depths, reflectances[:, i], 'o-', linewidth=2, markersize=4)
           plt.xlabel('Depth (m)')
           plt.ylabel('Remote Sensing Reflectance')
           plt.title(f'{wl:.1f} nm')
           plt.grid(True, alpha=0.3)
       
       plt.tight_layout()
       plt.show()
       
       return depths, reflectances

   depths, depth_reflectances = depth_sensitivity_study()

Chlorophyll Sensitivity
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def chlorophyll_sensitivity_study():
       chls = np.logspace(-1, 1.5, 20)  # 0.1 to ~30 mg/m³
       base_params = {'depth': 5.0, 'cdom': 0.5, 'nap': 1.5}
       
       reflectances = []
       for chl in chls:
           results = sbc.forward_model(
               chl=chl, **base_params,
               substrate1=substrate, wavelengths=wavelengths,
               a_water=a_water, a_ph_star=a_ph_star,
               num_bands=len(wavelengths)
           )
           reflectances.append(results.rrs)
       
       reflectances = np.array(reflectances)
       
       # Plot chlorophyll sensitivity
       plt.figure(figsize=(10, 6))
       
       colors = ['blue', 'green', 'red', 'darkred']
       for i, (wl, color) in enumerate(zip(wavelengths, colors)):
           plt.loglog(chls, reflectances[:, i], 'o-', color=color,
                     label=f'{wl:.1f} nm', linewidth=2, markersize=4)
       
       plt.xlabel('Chlorophyll (mg/m³)')
       plt.ylabel('Remote Sensing Reflectance')
       plt.title('Chlorophyll Sensitivity')
       plt.legend()
       plt.grid(True, alpha=0.3)
       plt.show()
       
       return chls, reflectances

   chls, chl_reflectances = chlorophyll_sensitivity_study()

Multi-Parameter Analysis
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def parameter_interaction_study():
       # Create parameter grids
       depths = [2, 5, 10, 15]
       chls = [0.5, 1.0, 2.0, 5.0]
       
       # Storage for results
       results_grid = np.zeros((len(depths), len(chls), len(wavelengths)))
       
       for i, depth in enumerate(depths):
           for j, chl in enumerate(chls):
               results = sbc.forward_model(
                   chl=chl, depth=depth, cdom=0.5, nap=1.5,
                   substrate1=substrate, wavelengths=wavelengths,
                   a_water=a_water, a_ph_star=a_ph_star,
                   num_bands=len(wavelengths)
               )
               results_grid[i, j, :] = results.rrs
       
       # Plot interaction matrix for green band (index 1)
       plt.figure(figsize=(10, 8))
       
       # Green band reflectance as function of depth and chlorophyll
       green_reflectance = results_grid[:, :, 1]  # Green band
       
       im = plt.imshow(green_reflectance, cmap='viridis', aspect='auto',
                       extent=[min(chls), max(chls), min(depths), max(depths)])
       plt.colorbar(im, label='Green Reflectance')
       plt.xlabel('Chlorophyll (mg/m³)')
       plt.ylabel('Depth (m)')
       plt.title('Green Band Reflectance vs Depth and Chlorophyll')
       
       # Add contour lines
       X, Y = np.meshgrid(chls, depths)
       contours = plt.contour(X, Y, green_reflectance, colors='white', alpha=0.7)
       plt.clabel(contours, inline=True, fontsize=8)
       
       plt.show()
       
       return results_grid

   interaction_results = parameter_interaction_study()

Spectral Band Analysis
----------------------

Understanding how different wavelengths respond to water properties:

Band Sensitivity Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def band_sensitivity_analysis():
       # Define parameter ranges
       param_ranges = {
           'chl': np.linspace(0.1, 10, 50),
           'cdom': np.linspace(0.01, 2.0, 50),
           'nap': np.linspace(0.1, 5.0, 50),
           'depth': np.linspace(1, 20, 50)
       }
       
       base_params = {'chl': 2.0, 'cdom': 0.5, 'nap': 1.5, 'depth': 5.0}
       
       sensitivities = {}
       
       for param_name, param_values in param_ranges.items():
           band_sensitivities = []
           
           for param_val in param_values:
               params = base_params.copy()
               params[param_name] = param_val
               
               results = sbc.forward_model(
                   **params,
                   substrate1=substrate, wavelengths=wavelengths,
                   a_water=a_water, a_ph_star=a_ph_star,
                   num_bands=len(wavelengths)
               )
               band_sensitivities.append(results.rrs)
           
           sensitivities[param_name] = np.array(band_sensitivities)
       
       # Plot sensitivity matrix
       fig, axes = plt.subplots(2, 2, figsize=(15, 10))
       axes = axes.flatten()
       
       for i, (param_name, sensitivity) in enumerate(sensitivities.items()):
           param_values = param_ranges[param_name]
           
           for j, wl in enumerate(wavelengths):
               axes[i].plot(param_values, sensitivity[:, j], 
                           label=f'{wl:.0f} nm', linewidth=2)
           
           axes[i].set_xlabel(param_name.upper())
           axes[i].set_ylabel('Remote Sensing Reflectance')
           axes[i].set_title(f'Sensitivity to {param_name.upper()}')
           axes[i].legend()
           axes[i].grid(True, alpha=0.3)
           
           if param_name == 'chl':
               axes[i].set_xscale('log')
       
       plt.tight_layout()
       plt.show()
       
       return sensitivities

   sensitivities = band_sensitivity_analysis()

Working with Different Sensors
-------------------------------

Adapt the forward model for different satellite sensors:

Multi-Sensor Comparison
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def multi_sensor_comparison():
       # Define sensor configurations
       sensors = {
           'Sentinel-2': {
               'wavelengths': [492.4, 559.8, 664.6, 704.1],
               'a_water': [0.007, 0.015, 0.325, 0.619],
               'a_ph_star': [0.055, 0.023, 0.014, 0.010],
               'substrate': [0.30, 0.30, 0.25, 0.20]
           },
           'Landsat-8': {
               'wavelengths': [482.0, 561.5, 654.5, 864.5],
               'a_water': [0.006, 0.015, 0.298, 2.404],
               'a_ph_star': [0.058, 0.023, 0.015, 0.002],
               'substrate': [0.30, 0.30, 0.25, 0.10]
           },
           'MODIS': {
               'wavelengths': [469.0, 555.0, 645.0, 859.0],
               'a_water': [0.005, 0.014, 0.289, 2.386],
               'a_ph_star': [0.062, 0.024, 0.016, 0.002],
               'substrate': [0.30, 0.30, 0.25, 0.10]
           }
       }
       
       # Common water properties
       water_props = {'chl': 2.0, 'cdom': 0.5, 'nap': 1.5, 'depth': 8.0}
       
       # Compare sensors
       sensor_results = {}
       
       plt.figure(figsize=(12, 8))
       
       colors = ['blue', 'red', 'green']
       for i, (sensor_name, sensor_config) in enumerate(sensors.items()):
           results = sbc.forward_model(
               **water_props,
               substrate1=sensor_config['substrate'],
               wavelengths=sensor_config['wavelengths'],
               a_water=sensor_config['a_water'],
               a_ph_star=sensor_config['a_ph_star'],
               num_bands=len(sensor_config['wavelengths'])
           )
           
           sensor_results[sensor_name] = results
           
           plt.subplot(2, 2, i+1)
           plt.plot(sensor_config['wavelengths'], results.rrs, 
                   'o-', color=colors[i], linewidth=2, markersize=8)
           plt.xlabel('Wavelength (nm)')
           plt.ylabel('Remote Sensing Reflectance')
           plt.title(f'{sensor_name}')
           plt.grid(True, alpha=0.3)
       
       # Combined comparison
       plt.subplot(2, 2, 4)
       for i, (sensor_name, sensor_config) in enumerate(sensors.items()):
           results = sensor_results[sensor_name]
           plt.plot(sensor_config['wavelengths'], results.rrs, 
                   'o-', color=colors[i], label=sensor_name, 
                   linewidth=2, markersize=6)
       
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Remote Sensing Reflectance')
       plt.title('Sensor Comparison')
       plt.legend()
       plt.grid(True, alpha=0.3)
       
       plt.tight_layout()
       plt.show()
       
       return sensor_results

   sensor_comparison = multi_sensor_comparison()

Custom Sensor Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_custom_sensor():
       # Define custom hyperspectral configuration
       custom_wavelengths = np.arange(400, 801, 10)  # 400-800nm, 10nm steps
       
       # Interpolate water absorption to custom wavelengths
       # (In practice, use spectral libraries)
       from scipy.interpolate import interp1d
       
       # Standard water absorption data (example)
       std_wl = [400, 450, 500, 550, 600, 650, 700, 750, 800]
       std_a_water = [0.004, 0.005, 0.008, 0.014, 0.050, 0.280, 0.620, 1.200, 2.100]
       
       # Interpolate to custom wavelengths
       interp_func = interp1d(std_wl, std_a_water, kind='cubic', 
                             bounds_error=False, fill_value='extrapolate')
       custom_a_water = interp_func(custom_wavelengths)
       
       # Similarly for phytoplankton (simplified example)
       std_a_ph = [0.080, 0.060, 0.040, 0.025, 0.018, 0.015, 0.012, 0.008, 0.005]
       interp_func_ph = interp1d(std_wl, std_a_ph, kind='cubic',
                                bounds_error=False, fill_value='extrapolate')
       custom_a_ph_star = interp_func_ph(custom_wavelengths)
       
       # Substrate reflectance (sand-like)
       custom_substrate = 0.2 + 0.3 * (custom_wavelengths - 400) / (800 - 400)
       
       # Run forward model with custom sensor
       results = sbc.forward_model(
           chl=2.0, cdom=0.5, nap=1.5, depth=6.0,
           substrate1=custom_substrate,
           wavelengths=custom_wavelengths,
           a_water=custom_a_water,
           a_ph_star=custom_a_ph_star,
           num_bands=len(custom_wavelengths)
       )
       
       # Plot high-resolution spectrum
       plt.figure(figsize=(12, 8))
       
       plt.subplot(2, 2, 1)
       plt.plot(custom_wavelengths, results.rrs, 'b-', linewidth=1.5)
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Remote Sensing Reflectance')
       plt.title('High-Resolution Spectrum')
       plt.grid(True, alpha=0.3)
       
       plt.subplot(2, 2, 2)
       plt.plot(custom_wavelengths, custom_a_water, 'b-', label='Water')
       plt.plot(custom_wavelengths, results.a_ph, 'g-', label='Phytoplankton')
       plt.plot(custom_wavelengths, results.a_cdom, 'y-', label='CDOM')
       plt.plot(custom_wavelengths, results.a_nap, 'r-', label='NAP')
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Absorption (1/m)')
       plt.title('Absorption Components')
       plt.legend()
       plt.yscale('log')
       plt.grid(True, alpha=0.3)
       
       plt.subplot(2, 2, 3)
       plt.plot(custom_wavelengths, custom_substrate, 'brown', linewidth=2)
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Substrate Reflectance')
       plt.title('Substrate Spectrum')
       plt.grid(True, alpha=0.3)
       
       plt.subplot(2, 2, 4)
       plt.plot(custom_wavelengths, results.kd, 'purple', linewidth=2)
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Diffuse Attenuation (1/m)')
       plt.title('Attenuation Coefficient')
       plt.yscale('log')
       plt.grid(True, alpha=0.3)
       
       plt.tight_layout()
       plt.show()
       
       return custom_wavelengths, results

   custom_wl, custom_results = create_custom_sensor()

Performance Optimization
-------------------------

Tips for efficient forward model usage:

Vectorization
~~~~~~~~~~~~~

.. code-block:: python

   # Process multiple spectra efficiently
   def batch_forward_modeling():
       # Parameter combinations
       n_samples = 1000
       chls = np.random.uniform(0.1, 10.0, n_samples)
       cdoms = np.random.uniform(0.01, 2.0, n_samples)
       naps = np.random.uniform(0.1, 5.0, n_samples)
       depths = np.random.uniform(1.0, 20.0, n_samples)
       
       # Process in batches for memory efficiency
       batch_size = 100
       all_results = []
       
       for i in range(0, n_samples, batch_size):
           batch_end = min(i + batch_size, n_samples)
           batch_results = []
           
           for j in range(i, batch_end):
               results = sbc.forward_model(
                   chl=chls[j], cdom=cdoms[j], nap=naps[j], depth=depths[j],
                   substrate1=substrate, wavelengths=wavelengths,
                   a_water=a_water, a_ph_star=a_ph_star,
                   num_bands=len(wavelengths)
               )
               batch_results.append(results.rrs)
           
           all_results.extend(batch_results)
       
       return np.array(all_results)

   # Time the operation
   import time
   start_time = time.time()
   batch_results = batch_forward_modeling()
   end_time = time.time()
   print(f"Processed {len(batch_results)} spectra in {end_time - start_time:.2f} seconds")

Caching Results
~~~~~~~~~~~~~~~

.. code-block:: python

   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def cached_forward_model(chl, cdom, nap, depth):
       """Cached version for repeated parameter combinations."""
       results = sbc.forward_model(
           chl=chl, cdom=cdom, nap=nap, depth=depth,
           substrate1=tuple(substrate),  # Convert to hashable type
           wavelengths=tuple(wavelengths),
           a_water=tuple(a_water),
           a_ph_star=tuple(a_ph_star),
           num_bands=len(wavelengths)
       )
       return results.rrs
   
   # Use cached version
   rrs1 = cached_forward_model(2.0, 0.5, 1.5, 5.0)  # Computed
   rrs2 = cached_forward_model(2.0, 0.5, 1.5, 5.0)  # Cached

Validation and Quality Control
------------------------------

Ensuring forward model results are physically reasonable:

Range Checking
~~~~~~~~~~~~~~

.. code-block:: python

   def validate_forward_model_results(results, wavelengths):
       """Validate forward model outputs for physical realism."""
       
       issues = []
       
       # Check reflectance range
       if np.any(results.rrs < 0):
           issues.append("Negative reflectance values")
       if np.any(results.rrs > 0.5):
           issues.append("Unrealistically high reflectance (>0.5)")
       
       # Check spectral shape
       blue_idx = np.argmin(np.abs(np.array(wavelengths) - 490))
       nir_idx = np.argmin(np.abs(np.array(wavelengths) - 700))
       
       if results.rrs[nir_idx] > results.rrs[blue_idx]:
           issues.append("NIR > Blue reflectance (unusual for water)")
       
       # Check optical coefficients
       if np.any(results.a <= 0):
           issues.append("Non-positive absorption coefficients")
       if np.any(results.bb <= 0):
           issues.append("Non-positive backscatter coefficients")
       
       # Check attenuation
       if np.any(results.kd <= 0):
           issues.append("Non-positive diffuse attenuation")
       
       if issues:
           print("Validation issues found:")
           for issue in issues:
               print(f"  - {issue}")
       else:
           print("Results pass validation checks")
       
       return len(issues) == 0

   # Example usage
   test_results = sbc.forward_model(
       chl=2.0, cdom=0.5, nap=1.5, depth=5.0,
       substrate1=substrate, wavelengths=wavelengths,
       a_water=a_water, a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   is_valid = validate_forward_model_results(test_results, wavelengths)

Common Issues and Solutions
---------------------------

**Issue**: Unrealistically high reflectance values

**Solution**: Check input parameter ranges and substrate reflectance

.. code-block:: python

   # Ensure substrate reflectance is reasonable (typically 0.1-0.8)
   substrate = np.clip(substrate, 0.05, 0.8)

**Issue**: Negative absorption coefficients

**Solution**: Verify SIOP inputs are positive

.. code-block:: python

   # Check SIOP inputs
   assert all(a > 0 for a in a_water), "Water absorption must be positive"
   assert all(a > 0 for a in a_ph_star), "Phytoplankton absorption must be positive"

**Issue**: Model fails with very shallow/deep water

**Solution**: Use appropriate depth ranges

.. code-block:: python

   # Clip depth to reasonable range
   depth = np.clip(depth, 0.5, 50.0)  # 0.5m to 50m

Next Steps
----------

Now that you understand forward modeling:

🎯 **For parameter estimation**: :doc:`inversion`  
📊 **For spectral library management**: :doc:`siop_management`  
🗺️ **For image processing**: :doc:`image_processing`  
🎛️ **For advanced configuration**: :doc:`configuration`

**Practice Exercises:**

1. **Create a depth sensitivity study** for your local area
2. **Compare different substrate types** (sand, seagrass, coral)
3. **Analyze seasonal variations** by changing chlorophyll levels
4. **Design a custom sensor** for your specific application

Advanced forward modeling techniques and applications can be found in :doc:`../examples/advanced_examples`.
