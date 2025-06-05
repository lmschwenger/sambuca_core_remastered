Computational Algorithms
========================

This section details the computational algorithms and numerical methods implemented in SAMBUCA Core for forward modeling, parameter inversion, and uncertainty quantification.

Overview of SAMBUCA Algorithms
------------------------------

SAMBUCA implements several classes of algorithms:

**Forward Modeling Algorithms**
   Efficient computation of radiative transfer equations

**Optimization Algorithms**
   Parameter estimation through various optimization techniques

**Interpolation Algorithms**
   Spectral resampling and SIOP management

**Quality Control Algorithms**
   Result validation and uncertainty assessment

Forward Model Algorithms
------------------------

Semi-Analytical Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The core forward model implements the shallow water radiative transfer equation:

.. math::

   R_{rs}(\lambda) = R_{rs}^{\infty}(\lambda)[1 - e^{-(\frac{1}{\cos\theta_w} + \frac{Du}{\cos\theta_o})\kappa H}] + \frac{\rho_{bottom}(\lambda)}{\pi}e^{-(\frac{1}{\cos\theta_w} + \frac{Du_b}{\cos\theta_o})\kappa H}

**Algorithm Structure:**

.. code-block:: python

   def forward_model_algorithm(chl, cdom, nap, depth, substrate, wavelengths, siops):
       """
       Core forward model algorithm implementation.
       """
       # Step 1: Calculate absorption coefficients
       a_water = siops['a_water']
       a_ph = chl * siops['a_ph_star']
       a_cdom = cdom * cdom_spectrum(wavelengths, siops)
       a_nap = nap * nap_spectrum(wavelengths, siops)
       a_total = a_water + a_ph + a_cdom + a_nap
       
       # Step 2: Calculate scattering coefficients
       bb_water = water_backscatter(wavelengths)
       bb_ph = chl * phytoplankton_backscatter(wavelengths, siops)
       bb_nap = nap * nap_backscatter(wavelengths, siops)
       bb_total = bb_water + bb_ph + bb_nap
       
       # Step 3: Calculate optical properties
       kappa = a_total + bb_total
       u = bb_total / kappa
       
       # Step 4: Calculate path elongation
       Du = 1.03 * (1.0 + 2.4 * u)**0.5
       Du_b = 1.04 * (1.0 + 5.4 * u)**0.5
       
       # Step 5: Calculate geometric factors
       theta_w = refraction_angle(theta_air, n_water)
       cos_theta_w = np.cos(theta_w)
       cos_theta_o = np.cos(theta_o)
       
       # Step 6: Deep water reflectance
       rrs_deep = (0.084 + 0.17 * u) * u
       
       # Step 7: Shallow water equation
       exponential_factor = np.exp(-(1/cos_theta_w + Du/cos_theta_o) * kappa * depth)
       bottom_factor = np.exp(-(1/cos_theta_w + Du_b/cos_theta_o) * kappa * depth)
       
       rrs = rrs_deep * (1 - exponential_factor) + (substrate/np.pi) * bottom_factor
       
       return rrs, intermediate_results

SIOP Calculation Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Exponential CDOM Model:**

.. code-block:: python

   def cdom_absorption_spectrum(wavelengths, cdom_ref, lambda_ref, slope):
       """
       Calculate CDOM absorption spectrum using exponential model.
       
       a_cdom(λ) = a_cdom(λ₀) * exp(-S * (λ - λ₀))
       """
       return cdom_ref * np.exp(-slope * (wavelengths - lambda_ref))

**Power-Law Backscatter Model:**

.. code-block:: python

   def particle_backscatter_spectrum(wavelengths, bb_ref, lambda_ref, slope):
       """
       Calculate particle backscatter using power law model.
       
       bb_p(λ) = bb_p(λ₀) * (λ₀/λ)^γ
       """
       return bb_ref * (lambda_ref / wavelengths)**slope

**Interpolated SIOP Model:**

.. code-block:: python

   def interpolated_siop(target_wavelengths, source_wavelengths, source_values, method='linear'):
       """
       Interpolate SIOPs to target wavelengths.
       """
       from scipy.interpolate import interp1d
       
       # Handle extrapolation
       interpolator = interp1d(
           source_wavelengths, source_values,
           kind=method, bounds_error=False,
           fill_value='extrapolate'
       )
       
       return interpolator(target_wavelengths)

Optimization Algorithms
-----------------------

SAMBUCA supports multiple optimization approaches for parameter estimation:

Gradient-Based Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~

**L-BFGS-B Algorithm:**
The default algorithm for most applications:

.. code-block:: python

   from scipy.optimize import minimize
   
   def lbfgs_inversion(observed_rrs, initial_guess, bounds, forward_func):
       """
       L-BFGS-B optimization for parameter estimation.
       """
       def objective_function(params):
           predicted_rrs = forward_func(params)
           return np.sum((observed_rrs - predicted_rrs)**2)
       
       result = minimize(
           objective_function,
           initial_guess,
           method='L-BFGS-B',
           bounds=bounds,
           options={
               'maxiter': 200,
               'ftol': 1e-9,
               'gtol': 1e-5
           }
       )
       
       return result

**Advantages:**
- Fast convergence for well-conditioned problems
- Memory efficient
- Handles box constraints naturally

**Disadvantages:**
- Local optimization only
- Requires smooth objective function
- Sensitive to initial guess

Robust Optimization Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Trust Region Constrained:**

.. code-block:: python

   def trust_region_inversion(observed_rrs, initial_guess, bounds, forward_func):
       """
       Trust region optimization for robust parameter estimation.
       """
       def objective_function(params):
           predicted_rrs = forward_func(params)
           residuals = observed_rrs - predicted_rrs
           return np.sum(residuals**2)
       
       def jacobian(params):
           # Numerical gradient calculation
           return numerical_jacobian(objective_function, params)
       
       result = minimize(
           objective_function,
           initial_guess,
           method='trust-constr',
           jac=jacobian,
           bounds=bounds,
           options={'maxiter': 500}
       )
       
       return result

Multi-Start Optimization
~~~~~~~~~~~~~~~~~~~~~~~

**Latin Hypercube Sampling:**

.. code-block:: python

   def multistart_optimization(observed_rrs, bounds, forward_func, n_starts=10):
       """
       Multi-start optimization using Latin Hypercube Sampling.
       """
       from scipy.stats import qmc
       
       # Generate starting points
       sampler = qmc.LatinHypercube(d=len(bounds))
       unit_samples = sampler.random(n=n_starts)
       
       # Scale to parameter bounds
       scaled_samples = []
       for i, (low, high) in enumerate(bounds):
           scaled_samples.append(low + unit_samples[:, i] * (high - low))
       
       starting_points = np.column_stack(scaled_samples)
       
       # Run optimization from each starting point
       results = []
       for start_point in starting_points:
           result = lbfgs_inversion(observed_rrs, start_point, bounds, forward_func)
           results.append(result)
       
       # Select best result
       best_result = min(results, key=lambda r: r.fun if r.success else np.inf)
       
       return best_result, results

Global Optimization
~~~~~~~~~~~~~~~~~~

**Differential Evolution:**

.. code-block:: python

   from scipy.optimize import differential_evolution
   
   def global_optimization(observed_rrs, bounds, forward_func):
       """
       Global optimization using Differential Evolution.
       """
       def objective_function(params):
           try:
               predicted_rrs = forward_func(params)
               return np.sum((observed_rrs - predicted_rrs)**2)
           except:
               return 1e6  # Large penalty for invalid parameters
       
       result = differential_evolution(
           objective_function,
           bounds,
           maxiter=100,
           popsize=15,
           seed=42,
           atol=1e-6,
           updating='deferred',
           workers=1
       )
       
       return result

Lookup Table Methods
~~~~~~~~~~~~~~~~~~~

For rapid processing of large datasets:

.. code-block:: python

   def create_lookup_table(parameter_ranges, n_samples_per_dim=50):
       """
       Create lookup table for fast inversion.
       """
       # Generate parameter grid
       param_grids = []
       for param_name, (min_val, max_val) in parameter_ranges.items():
           param_grids.append(np.linspace(min_val, max_val, n_samples_per_dim))
       
       # Create meshgrid
       meshgrids = np.meshgrid(*param_grids, indexing='ij')
       
       # Flatten for forward model calculation
       param_combinations = []
       for i, param_name in enumerate(parameter_ranges.keys()):
           param_combinations.append(meshgrids[i].flatten())
       
       # Calculate forward model for all combinations
       lut_spectra = []
       lut_parameters = []
       
       for i in range(len(param_combinations[0])):
           params = {name: param_combinations[j][i] 
                    for j, name in enumerate(parameter_ranges.keys())}
           
           try:
               spectrum = forward_model(**params)
               lut_spectra.append(spectrum)
               lut_parameters.append(params)
           except:
               continue  # Skip invalid parameter combinations
       
       return np.array(lut_spectra), lut_parameters
   
   def lut_inversion(observed_rrs, lut_spectra, lut_parameters):
       """
       Fast inversion using lookup table.
       """
       # Calculate distances to all LUT entries
       distances = np.sum((lut_spectra - observed_rrs)**2, axis=1)
       
       # Find best match
       best_idx = np.argmin(distances)
       
       return lut_parameters[best_idx], distances[best_idx]

Interpolation Algorithms
-----------------------

Spectral Interpolation
~~~~~~~~~~~~~~~~~~~~~

SAMBUCA uses sophisticated interpolation for SIOP management:

.. code-block:: python

   def spectral_interpolation(source_wavelengths, source_values, target_wavelengths, 
                             method='cubic', extrapolation='linear'):
       """
       Advanced spectral interpolation with extrapolation handling.
       """
       from scipy.interpolate import interp1d, UnivariateSpline
       
       if method == 'cubic':
           # Cubic spline interpolation
           interpolator = interp1d(
               source_wavelengths, source_values,
               kind='cubic', bounds_error=False
           )
           
           # Handle extrapolation
           result = interpolator(target_wavelengths)
           
           # Linear extrapolation for out-of-bounds values
           if extrapolation == 'linear':
               mask = np.isnan(result)
               if np.any(mask):
                   linear_interp = interp1d(
                       source_wavelengths, source_values,
                       kind='linear', fill_value='extrapolate'
                   )
                   result[mask] = linear_interp(target_wavelengths[mask])
       
       elif method == 'spline':
           # Smoothing spline
           spline = UnivariateSpline(source_wavelengths, source_values, s=0)
           result = spline(target_wavelengths)
       
       return result

Sensor Response Function Convolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For accurate sensor simulation:

.. code-block:: python

   def convolve_with_srf(wavelengths, spectrum, srf_wavelengths, srf_response):
       """
       Convolve spectrum with sensor response function.
       """
       from scipy.integrate import trapz
       
       # Interpolate spectrum to SRF wavelengths
       interp_spectrum = np.interp(srf_wavelengths, wavelengths, spectrum)
       
       # Convolve with SRF
       convolved_spectrum = interp_spectrum * srf_response
       
       # Integrate over SRF
       band_value = trapz(convolved_spectrum, srf_wavelengths) / trapz(srf_response, srf_wavelengths)
       
       return band_value

Numerical Differentiation
~~~~~~~~~~~~~~~~~~~~~~~~~

For gradient calculations:

.. code-block:: python

   def numerical_gradient(func, x, h=1e-5):
       """
       Calculate numerical gradient using central differences.
       """
       gradient = np.zeros_like(x)
       
       for i in range(len(x)):
           x_plus = x.copy()
           x_minus = x.copy()
           
           x_plus[i] += h
           x_minus[i] -= h
           
           gradient[i] = (func(x_plus) - func(x_minus)) / (2 * h)
       
       return gradient

Quality Control Algorithms
--------------------------

Parameter Validation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def validate_parameters(parameters, bounds, physical_constraints=True):
       """
       Validate parameter values against bounds and physical constraints.
       """
       validation_results = {'valid': True, 'warnings': [], 'errors': []}
       
       # Check bounds
       for param_name, value in parameters.items():
           if param_name in bounds:
               low, high = bounds[param_name]
               if value < low or value > high:
                   validation_results['valid'] = False
                   validation_results['errors'].append(
                       f"{param_name} = {value} outside bounds [{low}, {high}]"
                   )
       
       # Physical constraints
       if physical_constraints:
           if parameters.get('depth', 0) <= 0:
               validation_results['valid'] = False
               validation_results['errors'].append("Depth must be positive")
           
           if parameters.get('chl', 0) <= 0:
               validation_results['valid'] = False
               validation_results['errors'].append("Chlorophyll must be positive")
       
       return validation_results

Spectral Fit Assessment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def assess_spectral_fit(observed, predicted, wavelengths):
       """
       Assess quality of spectral fit.
       """
       # Basic statistics
       rmse = np.sqrt(np.mean((observed - predicted)**2))
       mae = np.mean(np.abs(observed - predicted))
       r_squared = 1 - np.sum((observed - predicted)**2) / np.sum((observed - np.mean(observed))**2)
       
       # Spectral shape analysis
       obs_slope = np.polyfit(wavelengths, observed, 1)[0]
       pred_slope = np.polyfit(wavelengths, predicted, 1)[0]
       slope_error = abs(obs_slope - pred_slope)
       
       # Band-specific errors
       relative_errors = np.abs(observed - predicted) / observed
       
       fit_quality = {
           'rmse': rmse,
           'mae': mae,
           'r_squared': r_squared,
           'slope_error': slope_error,
           'relative_errors': relative_errors,
           'max_relative_error': np.max(relative_errors)
       }
       
       return fit_quality

Uncertainty Quantification
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def monte_carlo_uncertainty(parameters, parameter_errors, forward_func, n_samples=1000):
       """
       Estimate parameter uncertainties using Monte Carlo simulation.
       """
       results = []
       
       for _ in range(n_samples):
           # Perturb parameters
           perturbed_params = {}
           for param_name, nominal_value in parameters.items():
               if param_name in parameter_errors:
                   error = parameter_errors[param_name]
                   perturbed_value = np.random.normal(nominal_value, error)
                   perturbed_params[param_name] = max(0, perturbed_value)  # Ensure positive
               else:
                   perturbed_params[param_name] = nominal_value
           
           # Run forward model
           try:
               result = forward_func(perturbed_params)
               results.append(result)
           except:
               continue  # Skip failed runs
       
       # Calculate statistics
       results = np.array(results)
       uncertainty = {
           'mean': np.mean(results, axis=0),
           'std': np.std(results, axis=0),
           'percentiles': {
               '5': np.percentile(results, 5, axis=0),
               '25': np.percentile(results, 25, axis=0),
               '75': np.percentile(results, 75, axis=0),
               '95': np.percentile(results, 95, axis=0)
           }
       }
       
       return uncertainty

Parallel Processing Algorithms
------------------------------

Image Processing Parallelization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def parallel_image_processing(image, inversion_func, n_processes=4, chunk_size=1000):
       """
       Process image in parallel using multiprocessing.
       """
       import multiprocessing as mp
       from functools import partial
       
       height, width, bands = image.shape
       total_pixels = height * width
       
       # Flatten image for processing
       flat_image = image.reshape(total_pixels, bands)
       
       # Create chunks
       chunks = [flat_image[i:i+chunk_size] for i in range(0, total_pixels, chunk_size)]
       
       # Process chunks in parallel
       with mp.Pool(n_processes) as pool:
           chunk_results = pool.map(
               partial(process_chunk, inversion_func=inversion_func),
               chunks
           )
       
       # Combine results
       all_results = np.concatenate(chunk_results)
       
       # Reshape back to image format
       result_image = all_results.reshape(height, width, -1)
       
       return result_image
   
   def process_chunk(chunk, inversion_func):
       """
       Process a chunk of pixels.
       """
       results = []
       for pixel_spectrum in chunk:
           try:
               result = inversion_func(pixel_spectrum)
               results.append(result)
           except:
               # Handle failed pixels
               results.append([np.nan] * n_output_params)
       
       return np.array(results)

Memory-Efficient Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def memory_efficient_processing(large_image, processing_func, max_memory_gb=4):
       """
       Process large images with memory constraints.
       """
       import psutil
       
       # Calculate optimal chunk size based on available memory
       available_memory = psutil.virtual_memory().available
       target_memory = min(max_memory_gb * 1024**3, available_memory * 0.8)
       
       height, width, bands = large_image.shape
       bytes_per_pixel = bands * 8  # Assuming float64
       
       max_pixels_per_chunk = int(target_memory / bytes_per_pixel)
       chunk_height = min(height, int(np.sqrt(max_pixels_per_chunk * height / width)))
       
       # Process in overlapping chunks
       results = []
       overlap = 10  # Pixel overlap for edge effects
       
       for start_row in range(0, height, chunk_height - overlap):
           end_row = min(start_row + chunk_height, height)
           chunk = large_image[start_row:end_row, :, :]
           
           chunk_result = processing_func(chunk)
           
           # Handle overlap
           if start_row > 0:
               chunk_result = chunk_result[overlap//2:, :, :]
           if end_row < height:
               chunk_result = chunk_result[:-overlap//2, :, :]
           
           results.append(chunk_result)
       
       return np.concatenate(results, axis=0)

Performance Optimization
------------------------

Vectorization Strategies
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def vectorized_forward_model(chl_array, cdom_array, nap_array, depth_array, siops):
       """
       Vectorized forward model for multiple parameter sets.
       """
       # Broadcast parameters to common shape
       n_spectra = len(chl_array)
       n_bands = len(siops['wavelengths'])
       
       # Calculate absorption for all spectra simultaneously
       a_ph = np.outer(chl_array, siops['a_ph_star'])
       a_cdom = np.outer(cdom_array, siops['a_cdom_spectrum'])
       a_nap = np.outer(nap_array, siops['a_nap_spectrum'])
       
       # Broadcast water absorption
       a_water = np.tile(siops['a_water'], (n_spectra, 1))
       
       # Total absorption
       a_total = a_water + a_ph + a_cdom + a_nap
       
       # Continue with vectorized calculations...
       return results

Caching Mechanisms
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from functools import lru_cache
   
   @lru_cache(maxsize=10000)
   def cached_siop_calculation(wavelength_tuple, cdom, slope):
       """
       Cached SIOP calculation for frequently used wavelength sets.
       """
       wavelengths = np.array(wavelength_tuple)
       return cdom_absorption_spectrum(wavelengths, cdom, 440, slope)

Algorithm Validation
-------------------

Synthetic Data Testing
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def validate_algorithm_accuracy():
       """
       Validate algorithms using synthetic data with known answers.
       """
       # Generate test cases
       test_cases = [
           {'chl': 1.0, 'cdom': 0.3, 'nap': 1.0, 'depth': 5.0},
           {'chl': 5.0, 'cdom': 1.0, 'nap': 3.0, 'depth': 10.0},
           {'chl': 0.1, 'cdom': 0.05, 'nap': 0.5, 'depth': 2.0}
       ]
       
       results = []
       for true_params in test_cases:
           # Generate synthetic observation
           true_spectrum = forward_model(true_params)
           
           # Add noise
           noisy_spectrum = true_spectrum + np.random.normal(0, 0.0005, len(true_spectrum))
           
           # Run inversion
           estimated_params = invert_spectrum(noisy_spectrum)
           
           # Calculate errors
           errors = {}
           for param, true_val in true_params.items():
               est_val = estimated_params[param]
               errors[param] = abs(est_val - true_val) / true_val
           
           results.append(errors)
       
       return results

Computational Complexity Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def analyze_computational_complexity():
       """
       Analyze algorithm performance vs problem size.
       """
       import time
       
       sizes = [10, 50, 100, 500, 1000]
       times = []
       
       for size in sizes:
           # Create test problem of given size
           test_image = np.random.random((size, size, 4)) * 0.05
           
           start_time = time.time()
           process_image(test_image, inversion_params)
           end_time = time.time()
           
           times.append(end_time - start_time)
       
       # Analyze scaling
       import matplotlib.pyplot as plt
       plt.loglog(sizes, times, 'o-')
       plt.xlabel('Image Size (pixels)')
       plt.ylabel('Processing Time (s)')
       plt.title('Algorithm Scaling Analysis')
       plt.show()

Future Algorithm Developments
----------------------------

Machine Learning Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def neural_network_forward_model(parameters):
       """
       Example of ML-accelerated forward model.
       """
       import tensorflow as tf
       
       # Load pre-trained model
       model = tf.keras.models.load_model('sambuca_nn_model.h5')
       
       # Prepare input
       input_vector = np.array([parameters['chl'], parameters['cdom'], 
                               parameters['nap'], parameters['depth']])
       
       # Predict spectrum
       predicted_spectrum = model.predict(input_vector.reshape(1, -1))
       
       return predicted_spectrum[0]

Adaptive Algorithms
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def adaptive_optimization(observed_rrs, initial_bounds):
       """
       Adaptive optimization that adjusts strategy based on convergence.
       """
       # Start with fast algorithm
       result = lbfgs_optimization(observed_rrs, initial_bounds)
       
       # If convergence is poor, try more robust method
       if result.fun > 0.01 or not result.success:
           result = trust_region_optimization(observed_rrs, initial_bounds)
       
       # If still poor, try global optimization
       if result.fun > 0.005:
           result = global_optimization(observed_rrs, initial_bounds)
       
       return result

This comprehensive algorithmic foundation enables SAMBUCA to provide accurate, efficient, and robust parameter retrievals across diverse applications and datasets.
