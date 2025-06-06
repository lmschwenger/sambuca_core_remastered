Inversion Module
================

.. automodule:: sambuca.core.inversion
   :members:
   :undoc-members:
   :show-inheritance:

The inversion module provides algorithms and utilities for estimating water properties from observed reflectance spectra.

Core Classes and Functions
--------------------------

InversionParameters Class
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: sambuca.core.inversion.InversionParameters
   :members:
   :undoc-members:
   :show-inheritance:

The :class:`InversionParameters` class configures the inversion process, including parameter bounds, optimization settings, and spectral properties.

**Key Attributes:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Attribute
     - Description
   * - ``parameter_bounds``
     - Dictionary of parameter bounds (min, max) tuples
   * - ``optimization_method``
     - Optimization algorithm ('L-BFGS-B', 'TNC', etc.)
   * - ``max_iterations``
     - Maximum number of optimization iterations
   * - ``tolerance``
     - Convergence tolerance for optimization

Inversion Functions
~~~~~~~~~~~~~~~~~~

.. autofunction:: sambuca.core.inversion.invert_spectrum

.. autofunction:: sambuca.core.inversion.process_image

Primary inversion functions for single spectra and full images.

Result Classes
~~~~~~~~~~~~~~

.. autoclass:: sambuca.core.inversion.InversionResult
   :members:
   :undoc-members:
   :show-inheritance:

Contains the results of a single spectrum inversion.

Usage Examples
--------------

Basic Single Pixel Inversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca.core.inversion import InversionParameters, invert_spectrum
   import numpy as np

   # Observed reflectance spectrum
   observed_rrs = np.array([0.012, 0.015, 0.008, 0.006])

   # Set up inversion parameters
   params = InversionParameters(
       depth=(0, 20),
       chl=(0.1, 10.0),
       cdom=(0.01, 2.0),
       nap=(0.1, 5.0),
       wavelengths=[492.4, 559.8, 664.6, 704.1]
   )

   # Add spectral properties
   params.a_water = [0.007, 0.015, 0.325, 0.619]
   params.a_ph_star = [0.055, 0.023, 0.014, 0.010]
   params.substrate1 = [0.3, 0.3, 0.25, 0.2]
   params.num_bands = 4

   # Run inversion
   result = invert_spectrum(observed_rrs, params)

   print(f"Estimated depth: {result.parameters['depth']:.2f} m")
   print(f"Estimated chlorophyll: {result.parameters['chl']:.2f} mg/m³")
   print(f"RMSE: {result.objective_value:.6f}")

Image Processing
~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca.core.inversion import process_image
   import numpy as np

   # Image array (height, width, bands)
   image = np.random.random((100, 100, 4)) * 0.05

   # Process entire image
   results = process_image(
       image,
       params,
       n_processes=4,
       progress_bar=True,
       chunk_size=20
   )

   # Access results
   depth_map = results['depth']
   chl_map = results['chl']
   error_map = results['error']

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Advanced parameter configuration
   params = InversionParameters()

   # Set parameter bounds
   params.depth = (0.5, 25)
   params.chl = (0.1, 15.0)
   params.cdom = (0.01, 3.0)
   params.nap = (0.1, 8.0)
   params.substrate_fraction = (0, 1)  # For dual substrates

   # Optimization settings
   params.optimization_method = 'L-BFGS-B'
   params.max_iterations = 200
   params.tolerance = 1e-6

   # Multi-start optimization
   params.use_multistart = True
   params.n_starts = 10

   # Uncertainty analysis
   params.uncertainty_analysis = True
   params.monte_carlo_samples = 100

Integration with SIOP Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca.core as sbc

   # Set up SIOP manager
   siop_manager = sbc.SIOPManager("data/")
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])

   # Create parameters
   params = InversionParameters(
       depth=(0, 20),
       chl=(0.1, 10.0),
       cdom=(0.01, 2.0),
       wavelengths=[492.4, 559.8, 664.6, 704.1]
   )

   # Update with SIOPs from manager
   params.update_from_siop_manager(siop_manager, "Sentinel-2")

   # Now params contains all necessary spectral properties

Optimization Algorithms
-----------------------

Supported Methods
~~~~~~~~~~~~~~~~

The inversion module supports multiple optimization algorithms from SciPy:

**L-BFGS-B** (Default)
   - **Pros**: Fast, memory efficient, handles bounds well
   - **Cons**: Local optimization only
   - **Best for**: Most applications, large images

**TNC (Truncated Newton Constrained)**
   - **Pros**: Robust, good with constraints
   - **Cons**: Slower than L-BFGS-B
   - **Best for**: Difficult optimization problems

**SLSQP**
   - **Pros**: Handles nonlinear constraints
   - **Cons**: Can be sensitive to scaling
   - **Best for**: Problems with complex constraints

**trust-constr**
   - **Pros**: Very robust, handles difficult problems
   - **Cons**: Slower, more complex
   - **Best for**: Research applications

Algorithm Selection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Choose algorithm based on application
   
   # Fast processing (operational)
   params.optimization_method = 'L-BFGS-B'
   params.max_iterations = 50
   params.tolerance = 1e-4
   
   # Research (high precision)
   params.optimization_method = 'trust-constr'
   params.max_iterations = 500
   params.tolerance = 1e-8
   
   # Robust processing (difficult data)
   params.optimization_method = 'TNC'
   params.max_iterations = 300
   params.tolerance = 1e-5

Multi-Start Optimization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable multi-start for robustness
   params.use_multistart = True
   params.n_starts = 10
   params.start_method = 'latin_hypercube'  # or 'random'
   
   # Early stopping criteria
   params.max_starts_without_improvement = 5
   params.convergence_threshold = 1e-6

Global Optimization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use global optimization for very difficult problems
   from scipy.optimize import differential_evolution
   
   def global_inversion_example(observed_rrs, bounds):
       """Example using global optimization."""
       
       def objective(x):
           # Unpack parameters
           chl, cdom, nap, depth = x
           
           # Run forward model
           results = sbc.forward_model(
               chl=chl, cdom=cdom, nap=nap, depth=depth,
               # ... other parameters
           )
           
           # Calculate RMSE
           rmse = np.sqrt(np.mean((observed_rrs - results.rrs)**2))
           return rmse
       
       # Define bounds
       bounds = [(0.1, 10), (0.01, 2.0), (0.1, 5.0), (1, 20)]
       
       # Run global optimization
       result = differential_evolution(objective, bounds)
       return result

Error Handling and Quality Control
----------------------------------

Convergence Diagnostics
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Check inversion quality
   result = invert_spectrum(observed_rrs, params)
   
   if result.success:
       print(f"Converged in {result.nit} iterations")
       print(f"Final RMSE: {result.objective_value:.6f}")
       
       # Check parameter bounds
       for param, value in result.parameters.items():
           bounds = getattr(params, param)
           if isinstance(bounds, tuple):
               low, high = bounds
               if abs(value - low) < 0.01 or abs(value - high) < 0.01:
                   print(f"WARNING: {param} at boundary")
   else:
       print(f"Optimization failed: {result.message}")

Quality Metrics
~~~~~~~~~~~~~~

.. code-block:: python

   def assess_inversion_quality(result, observed_rrs):
       """Assess quality of inversion result."""
       
       if not result.success:
           return {'quality': 'failed', 'reason': result.message}
       
       # Regenerate spectrum
       predicted_results = sbc.forward_model(**result.parameters)
       predicted_rrs = predicted_results.rrs
       
       # Calculate metrics
       rmse = np.sqrt(np.mean((observed_rrs - predicted_rrs)**2))
       mae = np.mean(np.abs(observed_rrs - predicted_rrs))
       mape = np.mean(np.abs((observed_rrs - predicted_rrs) / observed_rrs)) * 100
       
       # Quality assessment
       if rmse < 0.0005:
           quality = 'excellent'
       elif rmse < 0.001:
           quality = 'good'
       elif rmse < 0.002:
           quality = 'fair'
       else:
           quality = 'poor'
       
       return {
           'quality': quality,
           'rmse': rmse,
           'mae': mae,
           'mape': mape,
           'iterations': result.nit
       }

Batch Processing Utilities
--------------------------

Parallel Image Processing
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure parallel processing
   def optimize_parallel_config(image_shape):
       """Optimize parallel configuration for image."""
       
       height, width, bands = image_shape
       total_pixels = height * width
       
       import multiprocessing as mp
       n_cores = mp.cpu_count()
       
       # Memory-based recommendations
       if total_pixels < 10000:
           return {'n_processes': min(2, n_cores), 'chunk_size': 100}
       elif total_pixels < 100000:
           return {'n_processes': min(4, n_cores), 'chunk_size': 500}
       else:
           return {'n_processes': min(8, n_cores), 'chunk_size': 1000}

Custom Processing Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def process_with_quality_control(image, params, **kwargs):
       """Process image with enhanced quality control."""
       
       # Pre-processing quality checks
       valid_pixels = preprocess_image(image)
       
       # Process only valid pixels
       results = process_image(image, params, **kwargs)
       
       # Post-processing quality control
       results = apply_quality_filters(results, valid_pixels)
       
       return results

Performance Optimization
-----------------------

Memory Management
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimize memory usage for large images
   def process_large_image_efficiently(image, params):
       """Process large images with memory optimization."""
       
       # Calculate optimal chunk size
       available_memory_gb = 8  # Adjust based on system
       chunk_size = calculate_optimal_chunk_size(image.shape, available_memory_gb)
       
       # Process in chunks with overlap
       results = process_image(
           image, params,
           chunk_size=chunk_size,
           overlap=50,
           memory_efficient=True
       )
       
       return results

Caching and Lookup Tables
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create lookup table for fast processing
   def create_inversion_lut(params, n_samples=10000):
       """Create lookup table for rapid inversion."""
       
       # Generate parameter combinations
       param_samples = generate_parameter_samples(params, n_samples)
       
       # Generate corresponding spectra
       lut_spectra = []
       for sample in param_samples:
           results = sbc.forward_model(**sample)
           lut_spectra.append(results.rrs)
       
       return np.array(lut_spectra), param_samples
   
   def lut_inversion(observed_rrs, lut_spectra, lut_params):
       """Fast inversion using lookup table."""
       
       # Find best match
       distances = np.sum((lut_spectra - observed_rrs)**2, axis=1)
       best_idx = np.argmin(distances)
       
       return lut_params[best_idx], distances[best_idx]

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~

**Issue**: Slow convergence or no convergence

**Solutions**:
- Check parameter bounds (too tight or too loose)
- Try different optimization algorithm
- Use multi-start optimization
- Increase max_iterations

**Issue**: Unrealistic parameter values

**Solutions**:
- Tighten parameter bounds
- Check input data quality
- Validate spectral properties (SIOPs)
- Add physical constraints

**Issue**: High error values

**Solutions**:
- Check data preprocessing (atmospheric correction, etc.)
- Validate SIOP libraries
- Consider different water type
- Check for sun glint or other artifacts

Debugging Tools
~~~~~~~~~~~~~~

.. code-block:: python

   # Enable detailed diagnostics
   params.verbose = True
   params.save_intermediate_results = True
   
   # Run with debugging
   result = invert_spectrum(observed_rrs, params)
   
   # Analyze results
   if hasattr(result, 'optimization_trace'):
       plot_optimization_trace(result.optimization_trace)

See Also
--------

- :doc:`forward_model` for the underlying physics model
- :doc:`siop_manager` for spectral property management
- :doc:`../user_guide/inversion` for detailed usage guide
- :doc:`../theory/algorithms` for mathematical background
