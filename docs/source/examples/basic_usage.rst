Basic Usage Examples
====================

This section provides simple, practical examples to get you started with SAMBUCA Core. These examples demonstrate the fundamental operations and workflows.

Getting Started
---------------

First, make sure SAMBUCA Core is installed and working:

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np
   import matplotlib.pyplot as plt
   
   print(f"SAMBUCA Core v{sbc.__version__} is ready!")

Example 1: Basic Forward Model
------------------------------

This example shows how to run the forward model to simulate satellite reflectance.

Simple Forward Model
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np
   
   # Define water conditions
   chl = 2.0        # Chlorophyll concentration [mg/m³]
   cdom = 0.5       # CDOM absorption [1/m]
   nap = 1.5        # Non-algal particles [mg/L]
   depth = 8.0      # Water depth [m]
   
   # Define spectral properties (Sentinel-2 bands)
   wavelengths = [492.4, 559.8, 664.6, 704.1]  # nm
   a_water = [0.007, 0.015, 0.325, 0.619]      # Pure water absorption
   a_ph_star = [0.055, 0.023, 0.014, 0.010]    # Phytoplankton specific absorption
   substrate = [0.3, 0.3, 0.25, 0.2]           # Sand substrate reflectance
   
   # Run forward model
   results = sbc.forward_model(
       chl=chl, cdom=cdom, nap=nap, depth=depth,
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   print("Forward Model Results:")
   print(f"Modeled reflectance: {results.rrs}")
   print(f"Total absorption: {results.a}")
   print(f"Total backscatter: {results.bb}")

Expected Output:

.. code-block:: text

   Forward Model Results:
   Modeled reflectance: [0.0089 0.0134 0.0051 0.0039]
   Total absorption: [0.1175 0.0610 0.3530 0.6490]
   Total backscatter: [0.0203 0.0176 0.0141 0.0135]

Visualizing Results
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create a simple plot
   plt.figure(figsize=(10, 6))
   
   plt.subplot(1, 2, 1)
   plt.plot(wavelengths, results.rrs, 'bo-', linewidth=2, markersize=8)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Modeled Reflectance Spectrum')
   plt.grid(True, alpha=0.3)
   
   plt.subplot(1, 2, 2)
   plt.plot(wavelengths, results.a, 'r-', label='Absorption', linewidth=2)
   plt.plot(wavelengths, results.bb, 'b-', label='Backscatter', linewidth=2)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Coefficient (1/m)')
   plt.title('Optical Properties')
   plt.legend()
   plt.yscale('log')
   plt.grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Example 2: Parameter Sensitivity
--------------------------------

Explore how different parameters affect the reflectance spectrum.

Depth Sensitivity
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Test different depths
   depths = [2, 5, 10, 15, 20]  # meters
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
   plt.title('Effect of Water Depth')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.show()

Chlorophyll Sensitivity
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Test different chlorophyll concentrations
   chls = [0.5, 1.0, 2.0, 5.0, 10.0]  # mg/m³
   
   plt.figure(figsize=(10, 6))
   
   for chl in chls:
       results = sbc.forward_model(
           chl=chl, cdom=0.5, nap=1.5, depth=8.0,
           substrate1=substrate, wavelengths=wavelengths,
           a_water=a_water, a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       plt.plot(wavelengths, results.rrs, 'o-', 
                label=f'{chl} mg/m³', linewidth=2, markersize=6)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Effect of Chlorophyll Concentration')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.show()

Example 3: Basic Inversion
--------------------------

Estimate water properties from observed reflectance.

Single Pixel Inversion
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca_core.inversion import InversionParameters, invert_spectrum
   
   # Simulate observed reflectance (from previous forward model)
   observed_rrs = np.array([0.0089, 0.0134, 0.0051, 0.0039])
   
   # Set up inversion parameters
   params = InversionParameters(
       depth=(1, 20),       # Search depth range
       chl=(0.1, 10.0),     # Chlorophyll range
       cdom=(0.01, 2.0),    # CDOM range
       nap=(0.1, 5.0),      # NAP range
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       substrate1=substrate,
       num_bands=len(wavelengths)
   )
   
   # Run inversion
   result = invert_spectrum(observed_rrs, params)
   
   if result.success:
       print("Inversion Results:")
       print(f"Depth: {result.parameters['depth']:.2f} m")
       print(f"Chlorophyll: {result.parameters['chl']:.2f} mg/m³")
       print(f"CDOM: {result.parameters['cdom']:.3f} 1/m")
       print(f"NAP: {result.parameters['nap']:.2f} mg/L")
       print(f"RMSE: {result.objective_value:.6f}")
   else:
       print(f"Inversion failed: {result.message}")

Expected Output:

.. code-block:: text

   Inversion Results:
   Depth: 8.02 m
   Chlorophyll: 1.98 mg/m³
   CDOM: 0.502 1/m
   NAP: 1.49 mg/L
   RMSE: 0.000234

Validating Inversion Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
   plt.figure(figsize=(10, 6))
   
   plt.subplot(1, 2, 1)
   plt.plot(wavelengths, observed_rrs, 'ro-', label='Observed', 
            linewidth=2, markersize=8)
   plt.plot(wavelengths, inverted_results.rrs, 'b--', label='Inverted', 
            linewidth=2)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Spectral Fit')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   # Show parameter comparison
   plt.subplot(1, 2, 2)
   params = ['depth', 'chl', 'cdom', 'nap']
   true_vals = [8.0, 2.0, 0.5, 1.5]  # From original forward model
   estimated_vals = [result.parameters[p] for p in params]
   
   x = np.arange(len(params))
   width = 0.35
   
   plt.bar(x - width/2, true_vals, width, label='True', alpha=0.7)
   plt.bar(x + width/2, estimated_vals, width, label='Estimated', alpha=0.7)
   plt.xlabel('Parameters')
   plt.ylabel('Values')
   plt.title('Parameter Recovery')
   plt.xticks(x, params)
   plt.legend()
   
   plt.tight_layout()
   plt.show()

Example 4: Working with Different Substrates
--------------------------------------------

Compare different bottom types and substrate mixing.

Substrate Comparison
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define different substrate types
   substrates = {
       'Sand': [0.3, 0.3, 0.25, 0.2],
       'Seagrass': [0.1, 0.15, 0.2, 0.25],
       'Coral': [0.4, 0.45, 0.4, 0.35],
       'Mud': [0.08, 0.09, 0.1, 0.11]
   }
   
   plt.figure(figsize=(12, 8))
   
   # Plot substrate spectra
   plt.subplot(2, 2, 1)
   for name, spectrum in substrates.items():
       plt.plot(wavelengths, spectrum, 'o-', label=name, linewidth=2, markersize=6)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Substrate Reflectance')
   plt.title('Substrate Spectra')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   # Model water-leaving reflectance for each substrate
   plt.subplot(2, 2, 2)
   for name, substrate_spec in substrates.items():
       results = sbc.forward_model(
           chl=2.0, cdom=0.5, nap=1.5, depth=5.0,
           substrate1=substrate_spec,
           wavelengths=wavelengths,
           a_water=a_water,
           a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       plt.plot(wavelengths, results.rrs, 'o-', label=name, linewidth=2, markersize=6)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Water-Leaving Reflectance')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Substrate Mixing
~~~~~~~~~~~~~~~

.. code-block:: python

   # Model mixed substrates (sand + seagrass)
   sand = [0.3, 0.3, 0.25, 0.2]
   seagrass = [0.1, 0.15, 0.2, 0.25]
   
   fractions = [0.0, 0.25, 0.5, 0.75, 1.0]  # Fraction of seagrass
   
   plt.figure(figsize=(10, 6))
   
   for fraction in fractions:
       results = sbc.forward_model(
           chl=1.5, cdom=0.3, nap=1.0, depth=6.0,
           substrate1=sand,
           substrate2=seagrass,
           substrate_fraction=1-fraction,  # Fraction of substrate1 (sand)
           wavelengths=wavelengths,
           a_water=a_water,
           a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       plt.plot(wavelengths, results.rrs, 'o-', 
                label=f'{fraction*100:.0f}% Seagrass', linewidth=2, markersize=6)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Effect of Substrate Mixing')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.show()

Example 5: Multiple Sensor Simulation
-------------------------------------

Compare how different satellite sensors would observe the same water.

Sensor Definitions
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define sensor configurations
   sensors = {
       'Sentinel-2': {
           'wavelengths': [492.4, 559.8, 664.6, 704.1],
           'names': ['B2_Blue', 'B3_Green', 'B4_Red', 'B8A_NIR']
       },
       'Landsat-8': {
           'wavelengths': [482.0, 561.5, 654.5, 864.5],
           'names': ['B2_Blue', 'B3_Green', 'B4_Red', 'B5_NIR']
       },
       'MODIS': {
           'wavelengths': [469.0, 555.0, 645.0, 859.0],
           'names': ['Band9', 'Band12', 'Band13', 'Band15']
       }
   }
   
   # Water properties to model
   water_props = {'chl': 2.5, 'cdom': 0.8, 'nap': 2.0, 'depth': 6.0}

Multi-Sensor Comparison
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   plt.figure(figsize=(15, 10))
   
   colors = ['blue', 'red', 'green']
   
   for i, (sensor_name, sensor_config) in enumerate(sensors.items()):
       # Get water absorption for this sensor's wavelengths
       # (In practice, you'd interpolate from a full spectrum)
       sensor_wavelengths = sensor_config['wavelengths']
       
       # Simple interpolation for this example
       sensor_a_water = np.interp(sensor_wavelengths, wavelengths, a_water)
       sensor_a_ph_star = np.interp(sensor_wavelengths, wavelengths, a_ph_star)
       sensor_substrate = np.interp(sensor_wavelengths, wavelengths, substrate)
       
       # Run forward model
       results = sbc.forward_model(
           **water_props,
           substrate1=sensor_substrate,
           wavelengths=sensor_wavelengths,
           a_water=sensor_a_water,
           a_ph_star=sensor_a_ph_star,
           num_bands=len(sensor_wavelengths)
       )
       
       # Plot results
       plt.subplot(2, 2, i+1)
       plt.plot(sensor_wavelengths, results.rrs, 'o-', color=colors[i], 
                linewidth=2, markersize=8)
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Remote Sensing Reflectance')
       plt.title(f'{sensor_name}')
       plt.grid(True, alpha=0.3)
   
   # Combined comparison
   plt.subplot(2, 2, 4)
   for i, (sensor_name, sensor_config) in enumerate(sensors.items()):
       sensor_wavelengths = sensor_config['wavelengths']
       sensor_a_water = np.interp(sensor_wavelengths, wavelengths, a_water)
       sensor_a_ph_star = np.interp(sensor_wavelengths, wavelengths, a_ph_star)
       sensor_substrate = np.interp(sensor_wavelengths, wavelengths, substrate)
       
       results = sbc.forward_model(
           **water_props,
           substrate1=sensor_substrate,
           wavelengths=sensor_wavelengths,
           a_water=sensor_a_water,
           a_ph_star=sensor_a_ph_star,
           num_bands=len(sensor_wavelengths)
       )
       
       plt.plot(sensor_wavelengths, results.rrs, 'o-', color=colors[i], 
                label=sensor_name, linewidth=2, markersize=6)
   
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Sensor Comparison')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Example 6: Batch Processing Multiple Spectra
--------------------------------------------

Process multiple spectra efficiently.

Generate Test Data
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create multiple test cases
   n_spectra = 100
   
   # Random parameter combinations
   np.random.seed(42)  # For reproducible results
   
   test_params = {
       'chl': np.random.uniform(0.5, 8.0, n_spectra),
       'cdom': np.random.uniform(0.1, 1.5, n_spectra),
       'nap': np.random.uniform(0.5, 4.0, n_spectra),
       'depth': np.random.uniform(2.0, 15.0, n_spectra)
   }
   
   print(f"Generated {n_spectra} test cases")
   print(f"CHL range: {test_params['chl'].min():.2f} - {test_params['chl'].max():.2f} mg/m³")
   print(f"Depth range: {test_params['depth'].min():.1f} - {test_params['depth'].max():.1f} m")

Batch Forward Modeling
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate spectra for all parameter combinations
   all_spectra = []
   
   for i in range(n_spectra):
       # Extract parameters for this spectrum
       params = {key: values[i] for key, values in test_params.items()}
       
       # Run forward model
       results = sbc.forward_model(
           **params,
           substrate1=substrate,
           wavelengths=wavelengths,
           a_water=a_water,
           a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       
       all_spectra.append(results.rrs)
   
   all_spectra = np.array(all_spectra)
   print(f"Generated {len(all_spectra)} spectra")

Analyze Spectral Variability
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   plt.figure(figsize=(12, 8))
   
   # Plot all spectra
   plt.subplot(2, 2, 1)
   for i in range(min(20, n_spectra)):  # Plot first 20 spectra
       plt.plot(wavelengths, all_spectra[i], alpha=0.5, linewidth=1)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Sample Spectra')
   plt.grid(True, alpha=0.3)
   
   # Plot mean ± std
   plt.subplot(2, 2, 2)
   mean_spectrum = np.mean(all_spectra, axis=0)
   std_spectrum = np.std(all_spectra, axis=0)
   
   plt.plot(wavelengths, mean_spectrum, 'k-', linewidth=2, label='Mean')
   plt.fill_between(wavelengths, 
                    mean_spectrum - std_spectrum,
                    mean_spectrum + std_spectrum,
                    alpha=0.3, label='±1 Std')
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title('Spectral Statistics')
   plt.legend()
   plt.grid(True, alpha=0.3)
   
   # Scatter plot: depth vs blue reflectance
   plt.subplot(2, 2, 3)
   blue_reflectance = all_spectra[:, 0]  # First band (blue)
   plt.scatter(test_params['depth'], blue_reflectance, alpha=0.6)
   plt.xlabel('Depth (m)')
   plt.ylabel('Blue Reflectance')
   plt.title('Depth vs Blue Reflectance')
   plt.grid(True, alpha=0.3)
   
   # Scatter plot: chlorophyll vs green/blue ratio
   plt.subplot(2, 2, 4)
   green_blue_ratio = all_spectra[:, 1] / all_spectra[:, 0]  # Green/Blue ratio
   plt.scatter(test_params['chl'], green_blue_ratio, alpha=0.6)
   plt.xlabel('Chlorophyll (mg/m³)')
   plt.ylabel('Green/Blue Ratio')
   plt.title('Chlorophyll vs Green/Blue Ratio')
   plt.grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.show()

Example 7: Error Analysis and Validation
----------------------------------------

Analyze how noise affects inversion accuracy.

Add Realistic Noise
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def add_sensor_noise(clean_spectrum, noise_level=0.0005):
       """Add realistic sensor noise to spectrum."""
       # Additive Gaussian noise
       noise = np.random.normal(0, noise_level, len(clean_spectrum))
       noisy_spectrum = clean_spectrum + noise
       
       # Ensure positive values
       noisy_spectrum = np.maximum(noisy_spectrum, 0.0001)
       
       return noisy_spectrum

Noise Impact Study
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # True parameters
   true_params = {'chl': 3.0, 'cdom': 0.6, 'nap': 2.0, 'depth': 7.0}
   
   # Generate clean spectrum
   clean_results = sbc.forward_model(
       **true_params,
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   clean_spectrum = clean_results.rrs
   
   # Test different noise levels
   noise_levels = [0.0001, 0.0005, 0.001, 0.002]
   n_trials = 20
   
   results_summary = []
   
   for noise_level in noise_levels:
       print(f"Testing noise level: {noise_level}")
       
       trial_results = []
       
       for trial in range(n_trials):
           # Add noise
           noisy_spectrum = add_sensor_noise(clean_spectrum, noise_level)
           
           # Set up inversion
           params = InversionParameters(
               depth=(1, 15), chl=(0.5, 8.0), cdom=(0.1, 2.0), nap=(0.5, 5.0),
               wavelengths=wavelengths, a_water=a_water, a_ph_star=a_ph_star,
               substrate1=substrate, num_bands=len(wavelengths)
           )
           
           # Run inversion
           result = invert_spectrum(noisy_spectrum, params)
           
           if result.success:
               # Calculate errors
               errors = {}
               for param, true_val in true_params.items():
                   est_val = result.parameters[param]
                   errors[param] = abs(est_val - true_val) / true_val * 100  # Percent error
               
               trial_results.append(errors)
       
       # Calculate statistics
       if trial_results:
           avg_errors = {}
           for param in true_params.keys():
               param_errors = [r[param] for r in trial_results]
               avg_errors[param] = {
                   'mean': np.mean(param_errors),
                   'std': np.std(param_errors),
                   'median': np.median(param_errors)
               }
           
           results_summary.append({
               'noise_level': noise_level,
               'errors': avg_errors,
               'success_rate': len(trial_results) / n_trials
           })

Plot Error Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Plot error vs noise level
   fig, axes = plt.subplots(2, 2, figsize=(12, 10))
   axes = axes.flatten()
   
   params = ['depth', 'chl', 'cdom', 'nap']
   
   for i, param in enumerate(params):
       noise_vals = [r['noise_level'] for r in results_summary]
       mean_errors = [r['errors'][param]['mean'] for r in results_summary]
       std_errors = [r['errors'][param]['std'] for r in results_summary]
       
       axes[i].errorbar(noise_vals, mean_errors, yerr=std_errors, 
                       'o-', linewidth=2, markersize=6, capsize=5)
       axes[i].set_xlabel('Noise Level')
       axes[i].set_ylabel('Mean Error (%)')
       axes[i].set_title(f'{param.upper()} Error vs Noise')
       axes[i].grid(True, alpha=0.3)
       axes[i].set_xscale('log')
   
   plt.tight_layout()
   plt.show()

Print Summary Statistics
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   print("\\nError Analysis Summary:")
   print("=" * 60)
   
   for result in results_summary:
       print(f"\\nNoise Level: {result['noise_level']:.4f}")
       print(f"Success Rate: {result['success_rate']:.1%}")
       
       for param, error_stats in result['errors'].items():
           print(f"  {param:>6}: {error_stats['mean']:5.1f}% ± {error_stats['std']:4.1f}%")

Summary and Next Steps
---------------------

These basic examples demonstrate:

✅ **Forward modeling** with different parameter combinations  
✅ **Parameter sensitivity analysis** to understand model behavior  
✅ **Single pixel inversion** for parameter estimation  
✅ **Substrate effects** and mixing scenarios  
✅ **Multi-sensor comparisons** for different satellite platforms  
✅ **Batch processing** for multiple spectra  
✅ **Error analysis** and noise impact assessment  

Next Steps
~~~~~~~~~

Now that you've mastered the basics, you can:

🚀 **Try real satellite data** with :doc:`advanced_examples`  
📚 **Follow detailed tutorials** in :doc:`tutorials`  
🔧 **Customize parameters** using :doc:`../user_guide/configuration`  
📊 **Process full images** with :doc:`../user_guide/image_processing`

Common Patterns
~~~~~~~~~~~~~~

You'll notice these patterns throughout SAMBUCA:

1. **Parameter dictionaries** for water properties
2. **Results objects** with comprehensive outputs
3. **Vectorized operations** for efficiency
4. **Validation and error checking** at each step
5. **Flexible configuration** for different scenarios

Tips for Success
~~~~~~~~~~~~~~~

💡 **Start simple** - Master basic examples before complex applications  
💡 **Validate results** - Always check if outputs make physical sense  
💡 **Use visualization** - Plots help understand model behavior  
💡 **Test with synthetic data** - Know the answer before real applications  
💡 **Document your work** - Keep track of parameter choices and results  

Ready to tackle more complex applications? Continue with :doc:`advanced_examples` for real-world satellite data processing!
