Inversion
=========

Inversion is the process of estimating water properties from observed satellite reflectance. This is the inverse of forward modeling - instead of predicting what satellites observe, we estimate the water conditions that produced the observed signal.

Understanding Inversion
-----------------------

Conceptual Framework
~~~~~~~~~~~~~~~~~~~~

Inversion transforms satellite observations into meaningful water quality parameters:

.. code-block:: text

   Satellite Reflectance → Optimization Algorithm → Water Properties
   [0.012, 0.015, 0.008, 0.006] → SAMBUCA Inversion → CHL=2.5 mg/m³, Depth=8.2m, etc.

The inversion process finds the combination of water properties that, when input to the forward model, best reproduces the observed reflectance.

Optimization Problem
~~~~~~~~~~~~~~~~~~~~

Mathematically, inversion is an optimization problem:

.. math::

   \min_{\mathbf{p}} \sum_{i=1}^{N} \left( \frac{R_{obs}(\lambda_i) - R_{model}(\lambda_i, \mathbf{p})}{\sigma_i} \right)^2

Where:
- :math:`\mathbf{p}` = parameter vector (CHL, CDOM, NAP, depth, etc.)
- :math:`R_{obs}(\lambda_i)` = observed reflectance at wavelength :math:`\lambda_i`
- :math:`R_{model}(\lambda_i, \mathbf{p})` = forward model prediction
- :math:`\sigma_i` = uncertainty/weight for band :math:`i`
- :math:`N` = number of spectral bands

Challenges
~~~~~~~~~~

Inversion is challenging because:

1. **Non-linear**: Forward model is highly non-linear
2. **Non-unique**: Multiple parameter combinations can produce similar spectra
3. **Ill-conditioned**: Small changes in reflectance can imply large parameter changes
4. **Under-constrained**: Often more parameters than spectral bands

Basic Inversion Workflow
------------------------

Single Pixel Inversion
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca.core as sbc
   from sambuca_core.inversion import InversionParameters, invert_spectrum
   import numpy as np

   # Observed reflectance (e.g., from Sentinel-2 pixel)
   observed_rrs = np.array([0.012, 0.015, 0.008, 0.006])

   # Define basic spectral properties
   wavelengths = [492.4, 559.8, 664.6, 704.1]
   a_water = [0.007, 0.015, 0.325, 0.619]
   a_ph_star = [0.055, 0.023, 0.014, 0.010]
   substrate = [0.3, 0.3, 0.25, 0.2]

   # Set up inversion parameters
   params = InversionParameters(
       depth=(0, 20),       # Search depth range (0-20m)
       chl=(0.1, 10.0),     # Chlorophyll range (0.1-10 mg/m³)
       cdom=(0.01, 2.0),    # CDOM range (0.01-2.0 m⁻¹)
       nap=(0.1, 5.0),      # NAP range (0.1-5.0 mg/L)
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       substrate1=substrate,
       num_bands=len(wavelengths)
   )

   # Run inversion
   result = invert_spectrum(observed_rrs, params)

   # Display results
   print("Inversion Results:")
   print(f"Depth: {result.parameters['depth']:.2f} m")
   print(f"Chlorophyll: {result.parameters['chl']:.2f} mg/m³")
   print(f"CDOM: {result.parameters['cdom']:.3f} m⁻¹")
   print(f"NAP: {result.parameters['nap']:.2f} mg/L")
   print(f"RMSE: {result.objective_value:.6f}")
   print(f"Success: {result.success}")

Inversion Parameters
--------------------

The :class:`InversionParameters` class configures the inversion process:

Parameter Bounds
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Basic parameter ranges
   params = InversionParameters(
       depth=(1, 25),         # Depth bounds
       chl=(0.1, 20.0),       # Chlorophyll bounds
       cdom=(0.01, 3.0),      # CDOM bounds
       nap=(0.1, 10.0),       # NAP bounds
       substrate_fraction=(0, 1),  # Substrate mixing fraction
   )

   # Customize optimization settings
   params.optimization_method = 'L-BFGS-B'
   params.max_iterations = 1000
   params.tolerance = 1e-6

Fixed vs Variable Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Fix some parameters, optimize others
   params = InversionParameters(
       depth=(5, 15),         # Optimize depth in known range
       chl=(0.5, 8.0),        # Optimize chlorophyll
       cdom=0.5,              # Fix CDOM (scalar = fixed)
       nap=1.5,               # Fix NAP
       wavelengths=wavelengths
   )

   # Add spectral properties
   params.a_water = a_water
   params.a_ph_star = a_ph_star
   params.substrate1 = substrate

Substrate Handling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Single substrate (fixed)
   params = InversionParameters(
       depth=(0, 20), chl=(0.1, 10.0),
       substrate1=sand_spectrum,  # Fixed sand substrate
       wavelengths=wavelengths
   )

   # Mixed substrates (optimize mixing fraction)
   params = InversionParameters(
       depth=(0, 20), chl=(0.1, 10.0),
       substrate_fraction=(0, 1),    # Optimize mixing
       substrate1=sand_spectrum,     # Substrate 1: sand
       substrate2=seagrass_spectrum, # Substrate 2: seagrass
       wavelengths=wavelengths
   )

Advanced Inversion Techniques
-----------------------------

Multi-Start Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def robust_inversion(observed_rrs, params, n_starts=10):
       """Run inversion with multiple starting points for robustness."""
       
       best_result = None
       best_rmse = np.inf
       all_results = []
       
       for i in range(n_starts):
           # Random starting point within bounds
           start_params = {}
           for param_name, bounds in params.parameter_bounds.items():
               if isinstance(bounds, tuple):
                   low, high = bounds
                   start_params[param_name] = np.random.uniform(low, high)
           
           # Set starting point
           params.initial_guess = start_params
           
           # Run inversion
           result = invert_spectrum(observed_rrs, params)
           all_results.append(result)
           
           # Track best result
           if result.success and result.objective_value < best_rmse:
               best_rmse = result.objective_value
               best_result = result
       
       return best_result, all_results

   # Use robust inversion
   best_result, all_results = robust_inversion(observed_rrs, params, n_starts=20)
   
   print(f"Best RMSE: {best_result.objective_value:.6f}")
   print(f"Successful runs: {sum(1 for r in all_results if r.success)}/{len(all_results)}")

Constrained Inversion
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def constrained_inversion_example():
       """Example with additional constraints."""
       
       # Add realistic constraints
       params = InversionParameters(
           depth=(2, 15),       # Exclude very shallow water
           chl=(0.3, 8.0),      # Realistic chlorophyll range
           cdom=(0.05, 1.5),    # Typical CDOM range
           nap=(0.2, 3.0),      # Reasonable particle range
           wavelengths=wavelengths
       )
       
       # Add spectral properties
       params.a_water = a_water
       params.a_ph_star = a_ph_star
       params.substrate1 = substrate
       
       # Custom constraints (example: depth-chlorophyll relationship)
       def additional_constraints(p):
           """Additional physics-based constraints."""
           penalty = 0
           
           # Shallow water tends to have higher chlorophyll (coastal productivity)
           if p['depth'] < 3 and p['chl'] < 1.0:
               penalty += 10 * (1.0 - p['chl'])**2
           
           # Very clear water (low CDOM) usually has low particles
           if p['cdom'] < 0.2 and p['nap'] > 2.0:
               penalty += 5 * (p['nap'] - 2.0)**2
           
           return penalty
       
       params.additional_constraints = additional_constraints
       
       return params

   constrained_params = constrained_inversion_example()

Uncertainty Quantification
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def uncertainty_analysis(observed_rrs, params, n_monte_carlo=100):
       """Estimate parameter uncertainties using Monte Carlo."""
       
       # Estimate noise level from data (simple approach)
       noise_level = 0.0005  # Typical for Sentinel-2
       
       results = []
       
       for i in range(n_monte_carlo):
           # Add noise to observations
           noisy_rrs = observed_rrs + np.random.normal(0, noise_level, len(observed_rrs))
           
           # Run inversion
           result = invert_spectrum(noisy_rrs, params)
           
           if result.success:
               results.append(result.parameters)
       
       # Calculate statistics
       if results:
           param_names = list(results[0].keys())
           uncertainties = {}
           
           for param in param_names:
               values = [r[param] for r in results]
               uncertainties[param] = {
                   'mean': np.mean(values),
                   'std': np.std(values),
                   'median': np.median(values),
                   'q25': np.percentile(values, 25),
                   'q75': np.percentile(values, 75)
               }
       
       return uncertainties

   # Run uncertainty analysis
   uncertainties = uncertainty_analysis(observed_rrs, params, n_monte_carlo=50)
   
   for param, stats in uncertainties.items():
       print(f"{param}: {stats['mean']:.3f} ± {stats['std']:.3f}")

Image Processing
----------------

Processing entire satellite images to create parameter maps:

Basic Image Processing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca_core.inversion import process_image
   import numpy as np

   # Load or create image data
   # Image shape: (height, width, bands)
   height, width, n_bands = 100, 100, 4
   
   # Example: synthetic image with depth gradient
   image = np.zeros((height, width, n_bands))
   
   # Create realistic depth gradient
   x, y = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
   depth_truth = 2 + 15 * (x + y) / 2  # 2-17m depth gradient
   
   # Generate synthetic reflectance for each pixel
   for i in range(height):
       for j in range(width):
           # Generate realistic spectrum for this depth
           pixel_results = sbc.forward_model(
               chl=1.0 + np.random.uniform(-0.3, 0.3),
               cdom=0.3 + np.random.uniform(-0.1, 0.1),
               nap=1.0 + np.random.uniform(-0.3, 0.3),
               depth=depth_truth[i, j],
               substrate1=substrate,
               wavelengths=wavelengths,
               a_water=a_water,
               a_ph_star=a_ph_star,
               num_bands=len(wavelengths)
           )
           image[i, j, :] = pixel_results.rrs
   
   # Add noise
   noise_level = 0.0003
   image += np.random.normal(0, noise_level, image.shape)
   
   print(f"Created synthetic image: {image.shape}")
   print(f"Depth range: {depth_truth.min():.1f} - {depth_truth.max():.1f} m")

Process Image with Inversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Set up inversion parameters for image processing
   image_params = InversionParameters(
       depth=(1, 20),
       chl=(0.3, 5.0),
       cdom=(0.1, 1.0),
       nap=(0.3, 3.0),
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       substrate1=substrate,
       num_bands=len(wavelengths)
   )

   # Process image (this may take several minutes)
   print("Processing image... (this may take a while)")
   results = process_image(
       image,
       image_params,
       n_processes=4,        # Use 4 CPU cores
       progress_bar=True,    # Show progress
       chunk_size=10         # Process in chunks for memory efficiency
   )

   print("Image processing complete!")
   print(f"Output maps: {list(results.keys())}")

Visualize Results
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import matplotlib.pyplot as plt

   # Extract result maps
   depth_map = results['depth']
   chl_map = results['chl']
   cdom_map = results['cdom']
   nap_map = results['nap']
   error_map = results['error']

   # Create comprehensive visualization
   fig, axes = plt.subplots(2, 3, figsize=(18, 12))

   # Truth vs estimated depth
   im1 = axes[0,0].imshow(depth_truth, cmap='viridis_r', aspect='equal')
   axes[0,0].set_title('True Depth (m)')
   plt.colorbar(im1, ax=axes[0,0])

   im2 = axes[0,1].imshow(depth_map, cmap='viridis_r', aspect='equal')
   axes[0,1].set_title('Estimated Depth (m)')
   plt.colorbar(im2, ax=axes[0,1])

   # Depth difference
   depth_diff = depth_map - depth_truth
   im3 = axes[0,2].imshow(depth_diff, cmap='RdBu_r', aspect='equal')
   axes[0,2].set_title('Depth Error (m)')
   plt.colorbar(im3, ax=axes[0,2])

   # Water quality parameters
   im4 = axes[1,0].imshow(chl_map, cmap='YlGn', aspect='equal')
   axes[1,0].set_title('Chlorophyll (mg/m³)')
   plt.colorbar(im4, ax=axes[1,0])

   im5 = axes[1,1].imshow(cdom_map, cmap='YlOrBr', aspect='equal')
   axes[1,1].set_title('CDOM (1/m)')
   plt.colorbar(im5, ax=axes[1,1])

   # Inversion quality
   im6 = axes[1,2].imshow(error_map, cmap='Reds', aspect='equal')
   axes[1,2].set_title('Inversion RMSE')
   plt.colorbar(im6, ax=axes[1,2])

   # Remove ticks
   for ax in axes.flat:
       ax.set_xticks([])
       ax.set_yticks([])

   plt.tight_layout()
   plt.show()

   # Print accuracy statistics
   valid_pixels = ~np.isnan(depth_map)
   depth_rmse = np.sqrt(np.mean((depth_map[valid_pixels] - depth_truth[valid_pixels])**2))
   depth_mae = np.mean(np.abs(depth_map[valid_pixels] - depth_truth[valid_pixels]))
   
   print(f"\\nAccuracy Statistics:")
   print(f"Depth RMSE: {depth_rmse:.2f} m")
   print(f"Depth MAE: {depth_mae:.2f} m")
   print(f"Valid pixels: {np.sum(valid_pixels)}/{valid_pixels.size} ({100*np.sum(valid_pixels)/valid_pixels.size:.1f}%)")

Quality Control and Validation
------------------------------

Assessing Inversion Quality
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def assess_inversion_quality(result, observed_rrs, wavelengths):
       """Comprehensive quality assessment for inversion results."""
       
       # Regenerate spectrum from inverted parameters
       predicted_results = sbc.forward_model(
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
       
       predicted_rrs = predicted_results.rrs
       
       # Calculate quality metrics
       rmse = np.sqrt(np.mean((observed_rrs - predicted_rrs)**2))
       mae = np.mean(np.abs(observed_rrs - predicted_rrs))
       r_squared = 1 - np.sum((observed_rrs - predicted_rrs)**2) / np.sum((observed_rrs - np.mean(observed_rrs))**2)
       
       # Relative errors per band
       rel_errors = 100 * np.abs(observed_rrs - predicted_rrs) / observed_rrs
       
       # Physical realism checks
       physics_checks = {
           'reasonable_depth': 0.5 <= result.parameters['depth'] <= 50,
           'reasonable_chl': 0.01 <= result.parameters['chl'] <= 100,
           'reasonable_cdom': 0.001 <= result.parameters['cdom'] <= 10,
           'reasonable_nap': 0.01 <= result.parameters['nap'] <= 50,
           'convergence': result.success,
           'low_rmse': rmse < 0.002
       }
       
       quality_score = sum(physics_checks.values()) / len(physics_checks)
       
       quality_report = {
           'rmse': rmse,
           'mae': mae,
           'r_squared': r_squared,
           'relative_errors': rel_errors,
           'physics_checks': physics_checks,
           'quality_score': quality_score,
           'observed_rrs': observed_rrs,
           'predicted_rrs': predicted_rrs
       }
       
       return quality_report

   # Example usage
   quality = assess_inversion_quality(result, observed_rrs, wavelengths)
   
   print(f"Quality Assessment:")
   print(f"RMSE: {quality['rmse']:.6f}")
   print(f"MAE: {quality['mae']:.6f}")
   print(f"R²: {quality['r_squared']:.4f}")
   print(f"Quality Score: {quality['quality_score']:.2f}")
   
   # Plot spectral fit
   plt.figure(figsize=(10, 6))
   plt.plot(wavelengths, quality['observed_rrs'], 'ro-', label='Observed', markersize=8, linewidth=2)
   plt.plot(wavelengths, quality['predicted_rrs'], 'b--', label='Predicted', linewidth=2)
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Remote Sensing Reflectance')
   plt.title(f'Spectral Fit (RMSE: {quality["rmse"]:.6f})')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.show()

Parameter Correlation Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def parameter_correlation_study(observed_rrs, params, n_runs=100):
       """Study parameter correlations and identifiability."""
       
       # Run multiple inversions with noise
       results = []
       noise_level = 0.0005
       
       for i in range(n_runs):
           noisy_rrs = observed_rrs + np.random.normal(0, noise_level, len(observed_rrs))
           result = invert_spectrum(noisy_rrs, params)
           
           if result.success:
               results.append(result.parameters)
       
       if len(results) < 10:
           print("Too few successful inversions for correlation analysis")
           return None
       
       # Convert to DataFrame for analysis
       import pandas as pd
       df = pd.DataFrame(results)
       
       # Calculate correlation matrix
       correlation_matrix = df.corr()
       
       # Plot correlation matrix
       plt.figure(figsize=(10, 8))
       im = plt.imshow(correlation_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')
       
       # Add text annotations
       for i in range(len(correlation_matrix.columns)):
           for j in range(len(correlation_matrix.columns)):
               text = plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black", fontweight='bold')
       
       plt.colorbar(im)
       plt.xticks(range(len(correlation_matrix.columns)), correlation_matrix.columns)
       plt.yticks(range(len(correlation_matrix.columns)), correlation_matrix.columns)
       plt.title('Parameter Correlation Matrix')
       plt.tight_layout()
       plt.show()
       
       # Identify problematic correlations
       high_corr_pairs = []
       for i in range(len(correlation_matrix.columns)):
           for j in range(i+1, len(correlation_matrix.columns)):
               corr_val = abs(correlation_matrix.iloc[i, j])
               if corr_val > 0.8:  # High correlation threshold
                   pair = (correlation_matrix.columns[i], correlation_matrix.columns[j])
                   high_corr_pairs.append((pair, corr_val))
       
       if high_corr_pairs:
           print("High parameter correlations found:")
           for pair, corr in high_corr_pairs:
               print(f"  {pair[0]} vs {pair[1]}: {corr:.3f}")
       
       return df, correlation_matrix

   # Run correlation study
   param_df, corr_matrix = parameter_correlation_study(observed_rrs, params, n_runs=50)

Optimization Methods
--------------------

SAMBUCA supports multiple optimization algorithms:

scipy-based Methods
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Different optimization algorithms
   methods = ['L-BFGS-B', 'TNC', 'SLSQP', 'trust-constr']
   
   method_results = {}
   
   for method in methods:
       params.optimization_method = method
       result = invert_spectrum(observed_rrs, params)
       method_results[method] = result
       
       print(f"{method}: RMSE={result.objective_value:.6f}, Success={result.success}")

   # Compare results
   best_method = min(method_results.keys(), 
                    key=lambda k: method_results[k].objective_value if method_results[k].success else np.inf)
   print(f"Best method: {best_method}")

Global Optimization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def global_optimization_example():
       """Example using global optimization for robustness."""
       
       from scipy.optimize import differential_evolution
       
       def objective_function(x):
           """Objective function for global optimization."""
           
           # Unpack parameters (example for 4 parameters)
           chl, cdom, nap, depth = x
           
           try:
               # Run forward model
               results = sbc.forward_model(
                   chl=chl, cdom=cdom, nap=nap, depth=depth,
                   substrate1=substrate, wavelengths=wavelengths,
                   a_water=a_water, a_ph_star=a_ph_star,
                   num_bands=len(wavelengths)
               )
               
               # Calculate RMSE
               rmse = np.sqrt(np.mean((observed_rrs - results.rrs)**2))
               return rmse
               
           except:
               return 1e6  # Large penalty for invalid parameters
       
       # Define bounds
       bounds = [
           (0.1, 10.0),   # chlorophyll
           (0.01, 2.0),   # cdom
           (0.1, 5.0),    # nap
           (1.0, 20.0)    # depth
       ]
       
       # Run global optimization
       result = differential_evolution(
           objective_function,
           bounds,
           maxiter=100,
           popsize=15,
           seed=42
       )
       
       if result.success:
           chl_opt, cdom_opt, nap_opt, depth_opt = result.x
           print(f"Global optimization results:")
           print(f"  Chlorophyll: {chl_opt:.3f} mg/m³")
           print(f"  CDOM: {cdom_opt:.3f} m⁻¹")
           print(f"  NAP: {nap_opt:.3f} mg/L")
           print(f"  Depth: {depth_opt:.3f} m")
           print(f"  RMSE: {result.fun:.6f}")
       
       return result

   # Run global optimization
   global_result = global_optimization_example()

Lookup Table Methods
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_lookup_table(params, n_samples=10000):
       """Create lookup table for fast inversion."""
       
       # Generate parameter combinations
       np.random.seed(42)  # For reproducibility
       
       param_samples = {}
       for param_name, bounds in params.parameter_bounds.items():
           if isinstance(bounds, tuple):
               low, high = bounds
               if param_name == 'chl':
                   # Log-uniform sampling for chlorophyll
                   samples = np.random.lognormal(np.log(np.sqrt(low * high)), 0.5, n_samples)
                   samples = np.clip(samples, low, high)
               else:
                   # Uniform sampling for other parameters
                   samples = np.random.uniform(low, high, n_samples)
               param_samples[param_name] = samples
       
       # Generate lookup table
       lut_params = []
       lut_spectra = []
       
       for i in range(n_samples):
           param_combo = {name: samples[i] for name, samples in param_samples.items()}
           
           try:
               results = sbc.forward_model(
                   **param_combo,
                   substrate1=substrate,
                   wavelengths=wavelengths,
                   a_water=a_water,
                   a_ph_star=a_ph_star,
                   num_bands=len(wavelengths)
               )
               
               lut_params.append(param_combo)
               lut_spectra.append(results.rrs)
               
           except:
               continue  # Skip invalid parameter combinations
       
       return np.array(lut_spectra), lut_params

   def lut_inversion(observed_rrs, lut_spectra, lut_params):
       """Fast inversion using lookup table."""
       
       # Calculate distances to all LUT entries
       distances = np.sqrt(np.sum((lut_spectra - observed_rrs)**2, axis=1))
       
       # Find best match
       best_idx = np.argmin(distances)
       best_match = lut_params[best_idx]
       best_rmse = distances[best_idx]
       
       return best_match, best_rmse

   # Create and use lookup table
   print("Creating lookup table...")
   lut_spectra, lut_params = create_lookup_table(params, n_samples=5000)
   print(f"LUT created with {len(lut_params)} entries")

   # Use LUT for inversion
   lut_result, lut_rmse = lut_inversion(observed_rrs, lut_spectra, lut_params)
   
   print(f"LUT Inversion Results:")
   for param, value in lut_result.items():
       print(f"  {param}: {value:.3f}")
   print(f"  RMSE: {lut_rmse:.6f}")

Troubleshooting Common Issues
-----------------------------

Convergence Problems
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def troubleshoot_convergence(observed_rrs, params):
       """Diagnose and fix convergence issues."""
       
       # Check 1: Parameter bounds
       print("1. Checking parameter bounds...")
       for param_name, bounds in params.parameter_bounds.items():
           if isinstance(bounds, tuple):
               low, high = bounds
               if high <= low:
                   print(f"  ERROR: {param_name} bounds are invalid: {bounds}")
               elif (high - low) < 0.01:
                   print(f"  WARNING: {param_name} bounds are very tight: {bounds}")
       
       # Check 2: Initial guess
       print("2. Checking initial guess...")
       if hasattr(params, 'initial_guess') and params.initial_guess:
           for param_name, value in params.initial_guess.items():
               bounds = params.parameter_bounds.get(param_name)
               if isinstance(bounds, tuple):
                   low, high = bounds
                   if not (low <= value <= high):
                       print(f"  ERROR: {param_name} initial guess {value} outside bounds {bounds}")
       
       # Check 3: Forward model with initial guess
       print("3. Testing forward model...")
       try:
           test_params = {
               'chl': 2.0, 'cdom': 0.5, 'nap': 1.5, 'depth': 5.0
           }
           
           results = sbc.forward_model(
               **test_params,
               substrate1=substrate,
               wavelengths=wavelengths,
               a_water=a_water,
               a_ph_star=a_ph_star,
               num_bands=len(wavelengths)
           )
           print(f"  Forward model test successful: RRS range [{results.rrs.min():.6f}, {results.rrs.max():.6f}]")
           
       except Exception as e:
           print(f"  ERROR: Forward model failed: {e}")
       
       # Check 4: Observed data quality
       print("4. Checking observed data...")
       if np.any(observed_rrs <= 0):
           print(f"  WARNING: Negative/zero reflectance values found")
       if np.any(observed_rrs > 0.5):
           print(f"  WARNING: Very high reflectance values (>{0.5}) found")
       if np.any(np.isnan(observed_rrs)):
           print(f"  ERROR: NaN values in observed data")
       
       # Suggest fixes
       print("\\nSuggested fixes:")
       print("- Widen parameter bounds if too restrictive")
       print("- Use multiple starting points (multi-start optimization)")
       print("- Check data quality and preprocessing")
       print("- Try different optimization method")
       print("- Use global optimization (differential_evolution)")

   # Run troubleshooting
   troubleshoot_convergence(observed_rrs, params)

Parameter Identifiability
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def check_parameter_identifiability(params, wavelengths):
       """Check which parameters are identifiable with given spectral bands."""
       
       # Test parameter sensitivity
       base_params = {'chl': 2.0, 'cdom': 0.5, 'nap': 1.5, 'depth': 5.0}
       base_results = sbc.forward_model(
           **base_params,
           substrate1=substrate, wavelengths=wavelengths,
           a_water=a_water, a_ph_star=a_ph_star,
           num_bands=len(wavelengths)
       )
       
       sensitivities = {}
       
       for param_name in base_params.keys():
           # Calculate numerical derivative
           delta = base_params[param_name] * 0.01  # 1% change
           
           perturbed_params = base_params.copy()
           perturbed_params[param_name] += delta
           
           perturbed_results = sbc.forward_model(
               **perturbed_params,
               substrate1=substrate, wavelengths=wavelengths,
               a_water=a_water, a_ph_star=a_ph_star,
               num_bands=len(wavelengths)
           )
           
           # Sensitivity = change in reflectance / change in parameter
           sensitivity = (perturbed_results.rrs - base_results.rrs) / delta
           sensitivities[param_name] = sensitivity
       
       # Plot sensitivity matrix
       plt.figure(figsize=(10, 8))
       
       sensitivity_matrix = np.array([sensitivities[param] for param in base_params.keys()]).T
       
       im = plt.imshow(np.abs(sensitivity_matrix), cmap='viridis', aspect='auto')
       plt.colorbar(im, label='|Sensitivity|')
       
       plt.xticks(range(len(base_params)), list(base_params.keys()))
       plt.yticks(range(len(wavelengths)), [f'{w:.0f}' for w in wavelengths])
       plt.xlabel('Parameters')
       plt.ylabel('Wavelength (nm)')
       plt.title('Parameter Sensitivity Matrix')
       
       # Add text annotations
       for i in range(len(wavelengths)):
           for j in range(len(base_params)):
               text = plt.text(j, i, f'{sensitivity_matrix[i, j]:.3f}',
                             ha="center", va="center", 
                             color="white" if np.abs(sensitivity_matrix[i, j]) > 0.5*np.max(np.abs(sensitivity_matrix)) else "black")
       
       plt.tight_layout()
       plt.show()
       
       # Analyze identifiability
       print("Parameter Identifiability Analysis:")
       for param, sens in sensitivities.items():
           max_sens = np.max(np.abs(sens))
           total_sens = np.sum(np.abs(sens))
           print(f"{param:>6}: Max sensitivity = {max_sens:.6f}, Total = {total_sens:.6f}")
           
           if max_sens < 1e-6:
               print(f"        WARNING: Very low sensitivity - may be difficult to estimate")

   # Run identifiability check
   check_parameter_identifiability(params, wavelengths)

Best Practices
--------------

1. **Start with realistic bounds** based on your study area
2. **Use multiple starting points** for robust optimization
3. **Validate with synthetic data** before applying to real observations
4. **Check parameter correlations** to identify problematic combinations
5. **Quality control results** using physical realism checks
6. **Consider uncertainty** when interpreting results

Next Steps
----------

Now that you understand inversion:

📊 **For spectral library management**: :doc:`siop_management`  
🗺️ **For large-scale processing**: :doc:`image_processing`  
🎛️ **For parameter optimization**: :doc:`configuration`  
🔬 **For theoretical background**: :doc:`../theory/algorithms`

**Practice Exercises:**

1. **Run sensitivity studies** to understand which parameters affect your bands most
2. **Test different optimization methods** and compare results
3. **Create validation datasets** with known parameters
4. **Analyze parameter correlations** for your sensor configuration
5. **Implement quality control** metrics for your application

Advanced inversion techniques and real-world applications can be found in :doc:`../examples/advanced_examples`.
