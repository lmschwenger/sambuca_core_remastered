Configuration
=============

This comprehensive guide covers all SAMBUCA configuration options, parameter optimization strategies, and advanced customization techniques for research and operational applications.

Overview of Configuration
-------------------------

SAMBUCA offers extensive configuration options across multiple levels:

**Model Parameters**
   Physical and optical parameters that control the forward model behavior

**Optimization Settings**
   Algorithm choices and convergence criteria for parameter estimation

**Processing Options**
   Performance tuning for different hardware and image sizes

**Quality Control**
   Validation thresholds and error handling strategies

Parameter Categories
--------------------

Forward Model Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

Core Water Properties
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Parameter
     - Symbol
     - Units
     - Description
   * - ``chl``
     - CHL
     - mg/m³
     - Chlorophyll-a concentration
   * - ``cdom``
     - CDOM
     - 1/m
     - CDOM absorption at reference wavelength
   * - ``nap``
     - NAP
     - mg/L
     - Non-algal particle concentration
   * - ``depth``
     - H
     - m
     - Water column depth

.. code-block:: python

   # Typical parameter ranges for different water types
   
   # Oligotrophic (clear oceanic waters)
   oligotrophic_ranges = {
       'chl': (0.1, 2.0),      # Low chlorophyll
       'cdom': (0.01, 0.3),    # Low CDOM
       'nap': (0.1, 1.0),      # Low particles
       'depth': (5, 50)        # Often deeper
   }
   
   # Mesotrophic (coastal waters)
   mesotrophic_ranges = {
       'chl': (1.0, 8.0),      # Moderate chlorophyll
       'cdom': (0.1, 1.0),     # Moderate CDOM
       'nap': (0.5, 3.0),      # Moderate particles
       'depth': (2, 25)        # Variable depth
   }
   
   # Eutrophic (productive waters)
   eutrophic_ranges = {
       'chl': (5.0, 30.0),     # High chlorophyll
       'cdom': (0.3, 2.0),     # Higher CDOM
       'nap': (1.0, 8.0),      # More particles
       'depth': (1, 15)        # Often shallower
   }

Substrate Properties
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Configure substrate parameters
   substrate_config = {
       'substrate_fraction': (0, 1),    # Mixing fraction for dual substrates
       'substrate1': sand_spectrum,     # Primary substrate
       'substrate2': seagrass_spectrum, # Secondary substrate (optional)
   }
   
   # Common substrate types and their characteristics
   substrate_types = {
       'quartz_sand': {
           'reflectance_level': 'high',      # 0.4-0.8
           'spectral_shape': 'increasing',   # Higher toward red/NIR
           'applications': ['beaches', 'shallow_lagoons']
       },
       'carbonate_sand': {
           'reflectance_level': 'very_high', # 0.6-0.9
           'spectral_shape': 'flat',         # Relatively flat spectrum
           'applications': ['coral_reefs', 'tropical_waters']
       },
       'seagrass': {
           'reflectance_level': 'low',       # 0.1-0.3
           'spectral_shape': 'vegetation',   # Green peak, red absorption
           'applications': ['coastal_meadows', 'estuaries']
       },
       'coral': {
           'reflectance_level': 'variable',  # 0.2-0.6
           'spectral_shape': 'complex',      # Species-dependent
           'applications': ['coral_reefs', 'tropical_shallow']
       },
       'mud': {
           'reflectance_level': 'very_low',  # 0.05-0.15
           'spectral_shape': 'slightly_increasing',
           'applications': ['estuaries', 'river_mouths']
       }
   }

SIOP Configuration
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Advanced SIOP parameters
   siop_config = {
       # CDOM parameters
       'a_cdom_slope': 0.0168052,        # Spectral slope [1/nm]
       'lambda0cdom': 550.0,             # Reference wavelength [nm]
       'a_cdom_lambda0cdom': 1.0,        # Reference absorption [1/m]
       
       # NAP parameters
       'a_nap_slope': 0.00977262,        # Spectral slope [1/nm]
       'lambda0nap': 550.0,              # Reference wavelength [nm]
       'a_nap_lambda0nap': 0.00433,      # Reference absorption [m²/g]
       
       # Backscatter parameters
       'bb_ph_slope': 0.878138,          # Phytoplankton slope
       'bb_nap_slope': None,             # NAP slope (uses bb_ph_slope if None)
       'lambda0x': 546.0,                # Backscatter reference [nm]
       'x_ph_lambda0x': 0.00157747,      # Phytoplankton backscatter [m²/mg]
       'x_nap_lambda0x': 0.0225353,      # NAP backscatter [m²/g]
       'bb_lambda_ref': 550,             # Water backscatter reference [nm]
   }
   
   # Regional SIOP variations
   regional_variations = {
       'mediterranean': {
           'a_cdom_slope': 0.018,         # Steeper CDOM slope
           'bb_ph_slope': 0.85,           # Different phytoplankton community
       },
       'atlantic_coastal': {
           'a_cdom_slope': 0.015,         # Gentler CDOM slope
           'x_ph_lambda0x': 0.002,        # Higher phytoplankton backscatter
       },
       'pacific_tropical': {
           'bb_ph_slope': 0.90,           # Different size distribution
           'a_nap_slope': 0.012,          # Different particle composition
       }
   }

Viewing Geometry
^^^^^^^^^^^^^^^

.. code-block:: python

   # Viewing geometry configuration
   geometry_config = {
       'theta_air': 30.0,                # Solar zenith angle [degrees]
       'off_nadir': 0.0,                 # Off-nadir viewing [degrees]
       'water_refractive_index': 1.34,   # Refractive index of water
       'q_factor': np.pi,                # Q factor for R(0-) conversion
   }
   
   # Sensor-specific typical geometries
   sensor_geometries = {
       'sentinel2': {
           'typical_sza': (20, 60),       # Solar zenith angle range
           'typical_vza': (0, 10),        # View zenith angle range
           'swath_width': 290,            # km
       },
       'landsat8': {
           'typical_sza': (25, 65),
           'typical_vza': (0, 7.5),
           'swath_width': 185,
       },
       'modis': {
           'typical_sza': (0, 75),
           'typical_vza': (0, 65),
           'swath_width': 2330,
       }
   }

Optimization Configuration
-------------------------

Algorithm Selection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca_core.inversion import InversionParameters
   
   # Different optimization algorithms and their characteristics
   optimization_methods = {
       'L-BFGS-B': {
           'description': 'Limited-memory Broyden-Fletcher-Goldfarb-Shanno',
           'pros': ['Fast convergence', 'Handles bounds well', 'Memory efficient'],
           'cons': ['Local minimum susceptible', 'Requires gradients'],
           'best_for': ['Most general use', 'Large images', 'Standard problems'],
           'settings': {
               'method': 'L-BFGS-B',
               'max_iterations': 200,
               'tolerance': 1e-6
           }
       },
       'TNC': {
           'description': 'Truncated Newton Constrained',
           'pros': ['Good with constraints', 'Robust'],
           'cons': ['Slower than L-BFGS-B', 'More memory'],
           'best_for': ['Complex constraints', 'Difficult problems'],
           'settings': {
               'method': 'TNC',
               'max_iterations': 300,
               'tolerance': 1e-5
           }
       },
       'SLSQP': {
           'description': 'Sequential Least Squares Programming',
           'pros': ['Handles nonlinear constraints', 'Good for constrained problems'],
           'cons': ['Can be slow', 'Sensitive to scaling'],
           'best_for': ['Nonlinear constraints', 'Small problems'],
           'settings': {
               'method': 'SLSQP',
               'max_iterations': 150,
               'tolerance': 1e-5
           }
       },
       'trust-constr': {
           'description': 'Trust Region Constrained',
           'pros': ['Very robust', 'Handles difficult problems'],
           'cons': ['Slower', 'More complex'],
           'best_for': ['Research applications', 'Difficult optimization'],
           'settings': {
               'method': 'trust-constr',
               'max_iterations': 500,
               'tolerance': 1e-6
           }
       }
   }

Convergence Criteria
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure convergence criteria for different applications
   
   # Fast processing (operational)
   fast_config = {
       'max_iterations': 50,
       'tolerance': 1e-4,
       'gradient_tolerance': 1e-4,
       'function_tolerance': 1e-6,
   }
   
   # Standard processing (research)
   standard_config = {
       'max_iterations': 200,
       'tolerance': 1e-6,
       'gradient_tolerance': 1e-6,
       'function_tolerance': 1e-8,
   }
   
   # High precision (validation)
   precision_config = {
       'max_iterations': 1000,
       'tolerance': 1e-8,
       'gradient_tolerance': 1e-8,
       'function_tolerance': 1e-10,
   }
   
   def configure_optimization(application_type='standard'):
       """Configure optimization based on application requirements."""
       
       configs = {
           'fast': fast_config,
           'standard': standard_config,
           'precision': precision_config
       }
       
       config = configs.get(application_type, standard_config)
       
       params = InversionParameters()
       params.optimization_method = 'L-BFGS-B'
       params.max_iterations = config['max_iterations']
       params.tolerance = config['tolerance']
       
       return params

Multi-Start Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Multi-start optimization for robustness
   multistart_config = {
       'n_starts': 10,                   # Number of random starts
       'start_method': 'latin_hypercube', # or 'random', 'grid'
       'convergence_threshold': 1e-6,    # Convergence similarity threshold
       'max_starts_without_improvement': 5, # Early stopping
   }
   
   def setup_multistart_optimization(param_bounds, n_starts=10):
       """Set up multi-start optimization configuration."""
       
       import numpy as np
       from scipy.stats import qmc
       
       # Generate starting points using Latin Hypercube Sampling
       sampler = qmc.LatinHypercube(d=len(param_bounds))
       unit_samples = sampler.random(n=n_starts)
       
       # Scale to parameter bounds
       starting_points = []
       param_names = list(param_bounds.keys())
       
       for i in range(n_starts):
           start_point = {}
           for j, param_name in enumerate(param_names):
               if isinstance(param_bounds[param_name], tuple):
                   low, high = param_bounds[param_name]
                   start_point[param_name] = low + unit_samples[i, j] * (high - low)
           starting_points.append(start_point)
       
       return starting_points

Performance Configuration
-------------------------

Parallel Processing
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import multiprocessing as mp
   
   # Automatic configuration based on system resources
   def configure_parallel_processing(image_size=None, available_memory_gb=None):
       """Configure parallel processing based on system resources."""
       
       # Get system information
       n_cores = mp.cpu_count()
       
       # Estimate memory usage
       if image_size and available_memory_gb:
           height, width, bands = image_size
           total_pixels = height * width
           
           # Rough memory estimate (bytes per pixel)
           memory_per_pixel = bands * 4 + 5 * 4  # Input + outputs
           total_memory_needed_gb = (total_pixels * memory_per_pixel) / (1024**3)
           
           # Memory-constrained core count
           memory_cores = max(1, int(available_memory_gb / total_memory_needed_gb * n_cores))
           
           recommended_cores = min(n_cores, memory_cores)
       else:
           # Default recommendations
           if n_cores <= 4:
               recommended_cores = n_cores
           elif n_cores <= 8:
               recommended_cores = n_cores - 1  # Leave one core free
           else:
               recommended_cores = int(n_cores * 0.8)  # Use 80% of cores
       
       # Chunk size recommendations
       if image_size:
           total_pixels = image_size[0] * image_size[1]
           
           if total_pixels < 10000:
               chunk_size = 100  # Small chunks for small images
           elif total_pixels < 100000:
               chunk_size = 500
           elif total_pixels < 1000000:
               chunk_size = 1000
           else:
               chunk_size = 2000  # Larger chunks for big images
       else:
           chunk_size = 1000  # Default
       
       config = {
           'n_processes': recommended_cores,
           'chunk_size': chunk_size,
           'max_pixels_per_chunk': chunk_size * chunk_size,
           'memory_management': 'auto'
       }
       
       print(f"Parallel processing configuration:")
       print(f"  Available cores: {n_cores}")
       print(f"  Recommended cores: {recommended_cores}")
       print(f"  Chunk size: {chunk_size}")
       
       return config

Memory Management
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Memory management strategies
   memory_strategies = {
       'conservative': {
           'chunk_size': 500,
           'overlap': 20,
           'cache_size': 100,     # Number of cached results
           'gc_frequency': 50,     # Garbage collection frequency
       },
       'balanced': {
           'chunk_size': 1000,
           'overlap': 50,
           'cache_size': 500,
           'gc_frequency': 100,
       },
       'aggressive': {
           'chunk_size': 2000,
           'overlap': 100,
           'cache_size': 1000,
           'gc_frequency': 200,
       }
   }
   
   def estimate_memory_requirements(image_shape, n_processes=4):
       """Estimate memory requirements for image processing."""
       
       height, width, bands = image_shape
       total_pixels = height * width
       
       # Memory per pixel (rough estimates in bytes)
       input_memory = bands * 4        # Input reflectance (float32)
       working_memory = 200            # Temporary arrays during optimization
       output_memory = 5 * 4           # 5 output parameters (float32)
       
       total_per_pixel = input_memory + working_memory + output_memory
       
       # Total memory estimates
       single_thread_gb = (total_pixels * total_per_pixel) / (1024**3)
       parallel_overhead = 1.5  # 50% overhead for parallel processing
       total_estimated_gb = single_thread_gb * parallel_overhead
       
       # Add process overhead
       process_overhead_gb = n_processes * 0.1  # ~100MB per process
       final_estimate_gb = total_estimated_gb + process_overhead_gb
       
       return {
           'single_thread_gb': single_thread_gb,
           'parallel_estimated_gb': final_estimate_gb,
           'per_pixel_bytes': total_per_pixel,
           'recommendation': 'conservative' if final_estimate_gb > 8 else 'balanced'
       }

Sensor-Specific Configuration
-----------------------------

Sentinel-2 Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimized configuration for Sentinel-2 MSI
   sentinel2_config = {
       'wavelengths': [492.4, 559.8, 664.6, 704.1],
       'band_names': ['B2_Blue', 'B3_Green', 'B4_Red', 'B8A_NIR'],
       'spatial_resolution': [10, 10, 10, 20],  # meters
       'typical_scene_size': (10980, 10980),    # pixels
       
       # Optimized parameter bounds for coastal waters
       'parameter_bounds': {
           'depth': (0.5, 30),
           'chl': (0.1, 15.0),
           'cdom': (0.01, 2.5),
           'nap': (0.1, 8.0)
       },
       
       # Noise characteristics (typical NEDR values)
       'noise_levels': [0.0003, 0.0002, 0.0002, 0.0004],
       
       # Processing recommendations
       'processing': {
           'chunk_size': 1000,
           'n_processes': 'auto',
           'optimization_method': 'L-BFGS-B',
           'max_iterations': 100,
           'tolerance': 1e-5
       }
   }

Landsat Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimized configuration for Landsat 8/9 OLI
   landsat_config = {
       'wavelengths': [482, 561.5, 654.5, 864.5],
       'band_names': ['B2_Blue', 'B3_Green', 'B4_Red', 'B5_NIR'],
       'spatial_resolution': [30, 30, 30, 30],  # meters
       'typical_scene_size': (7731, 7591),      # pixels
       
       # Adjusted bounds for Landsat's spectral configuration
       'parameter_bounds': {
           'depth': (1.0, 25),     # Coarser resolution = deeper penetration
           'chl': (0.2, 12.0),
           'cdom': (0.02, 2.0),
           'nap': (0.2, 6.0)
       },
       
       # Landsat-specific noise levels
       'noise_levels': [0.0004, 0.0003, 0.0003, 0.0005],
       
       'processing': {
           'chunk_size': 500,      # Smaller chunks due to lower SNR
           'n_processes': 'auto',
           'optimization_method': 'TNC',  # More robust for noisier data
           'max_iterations': 150,
           'tolerance': 1e-4
       }
   }

MODIS Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configuration for MODIS ocean color bands
   modis_config = {
       'wavelengths': [469, 555, 645, 859],
       'band_names': ['Band_9', 'Band_12', 'Band_13', 'Band_15'],
       'spatial_resolution': [1000, 1000, 1000, 1000],  # meters
       
       # MODIS optimized for open ocean
       'parameter_bounds': {
           'depth': (5.0, 50),     # Typically deeper waters
           'chl': (0.05, 5.0),     # Lower chlorophyll range
           'cdom': (0.005, 0.5),   # Lower CDOM
           'nap': (0.05, 2.0)      # Lower particles
       },
       
       'processing': {
           'chunk_size': 2000,     # Larger chunks for coarse resolution
           'optimization_method': 'L-BFGS-B',
           'max_iterations': 80,   # Fewer iterations for operational processing
       }
   }

Application-Specific Configuration
----------------------------------

Research Applications
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # High-precision configuration for research
   research_config = {
       'optimization': {
           'method': 'trust-constr',
           'max_iterations': 1000,
           'tolerance': 1e-8,
           'multistart': True,
           'n_starts': 20
       },
       
       'uncertainty_analysis': {
           'monte_carlo_samples': 500,
           'bootstrap_samples': 1000,
           'confidence_intervals': [68, 95, 99]
       },
       
       'validation': {
           'cross_validation_folds': 5,
           'holdout_fraction': 0.2,
           'validation_metrics': ['rmse', 'mae', 'r2', 'bias']
       },
       
       'quality_control': {
           'rmse_threshold': 0.001,
           'parameter_bounds_strict': True,
           'physical_realism_checks': True
       }
   }

Operational Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Fast processing for operational monitoring
   operational_config = {
       'optimization': {
           'method': 'L-BFGS-B',
           'max_iterations': 50,
           'tolerance': 1e-4,
           'multistart': False
       },
       
       'processing': {
           'chunk_size': 2000,
           'n_processes': 'max',
           'memory_strategy': 'aggressive',
           'cache_results': True
       },
       
       'quality_control': {
           'rmse_threshold': 0.005,   # More relaxed for speed
           'skip_difficult_pixels': True,
           'timeout_per_pixel': 1.0   # seconds
       },
       
       'output': {
           'compression': 'lzw',
           'precision': 'float32',    # vs float64 for research
           'include_uncertainty': False
       }
   }

Validation Studies
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configuration for validation against field data
   validation_config = {
       'optimization': {
           'method': 'L-BFGS-B',
           'max_iterations': 200,
           'tolerance': 1e-6,
           'multistart': True,
           'n_starts': 10
       },
       
       'parameter_bounds': {
           # Tighter bounds based on field data range
           'depth': (0.5, 20),
           'chl': (0.1, 10.0),
           'cdom': (0.01, 1.5),
           'nap': (0.1, 5.0)
       },
       
       'matchup_criteria': {
           'spatial_window': 3,        # pixels
           'temporal_window': 3,       # hours
           'cloud_buffer': 5,          # pixels
           'land_buffer': 2            # pixels
       },
       
       'statistics': {
           'metrics': ['rmse', 'mae', 'mape', 'r2', 'slope', 'intercept'],
           'outlier_detection': 'iqr', # or 'zscore'
           'outlier_threshold': 2.5
       }
   }

Regional Customization
---------------------

Mediterranean Waters
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configuration optimized for Mediterranean Sea
   mediterranean_config = {
       'parameter_bounds': {
           'depth': (1, 40),           # Varying coastal bathymetry
           'chl': (0.1, 8.0),          # Typical Med range
           'cdom': (0.02, 0.8),        # Lower CDOM than Atlantic
           'nap': (0.1, 4.0)           # Moderate particles
       },
       
       'siop_adjustments': {
           'a_cdom_slope': 0.018,      # Steeper slope
           'bb_ph_slope': 0.85,        # Different phytoplankton community
           'x_ph_lambda0x': 0.0018     # Adjusted backscatter
       },
       
       'seasonal_adjustments': {
           'winter': {'chl_bounds': (0.1, 3.0)},
           'spring': {'chl_bounds': (0.5, 8.0)},
           'summer': {'chl_bounds': (0.1, 2.0)},
           'autumn': {'chl_bounds': (0.2, 5.0)}
       }
   }

Great Barrier Reef
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configuration for coral reef environments
   reef_config = {
       'parameter_bounds': {
           'depth': (0.5, 25),         # Shallow reef environments
           'chl': (0.1, 5.0),          # Generally lower chlorophyll
           'cdom': (0.01, 0.5),        # Low CDOM in clear tropical waters
           'nap': (0.05, 2.0),         # Low particles except during events
           'substrate_fraction': (0, 1) # Important for reef mapping
       },
       
       'substrate_types': {
           'sand': 'high_carbonate',
           'coral': 'mixed_species',
           'algae': 'macroalgae'
       },
       
       'processing': {
           'sun_glint_correction': True,
           'depth_dependent_bounds': True  # Adjust bounds by estimated depth
       }
   }

Chesapeake Bay
~~~~~~~~~~~~~

.. code-block:: python

   # Configuration for estuarine environments
   estuarine_config = {
       'parameter_bounds': {
           'depth': (0.5, 15),         # Shallow estuarine system
           'chl': (2.0, 40.0),         # High productivity
           'cdom': (0.5, 4.0),         # High CDOM from terrestrial input
           'nap': (1.0, 15.0)          # High sediment loads
       },
       
       'siop_adjustments': {
           'a_cdom_slope': 0.014,      # Different CDOM source
           'a_nap_slope': 0.008,       # Different particle composition
       },
       
       'quality_control': {
           'turbidity_threshold': 50,  # NTU
           'high_cdom_handling': 'specialized_algorithm'
       }
   }

Advanced Configuration Techniques
---------------------------------

Dynamic Parameter Bounds
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def dynamic_parameter_bounds(pixel_spectrum, initial_bounds):
       """Adjust parameter bounds based on spectral characteristics."""
       
       # Analyze spectral shape
       blue_green_ratio = pixel_spectrum[0] / pixel_spectrum[1]
       green_red_ratio = pixel_spectrum[1] / pixel_spectrum[2]
       
       # Estimate water type
       if blue_green_ratio > 0.9 and green_red_ratio > 2.0:
           # Clear water
           chl_bounds = (0.1, 3.0)
           cdom_bounds = (0.01, 0.5)
       elif blue_green_ratio < 0.6:
           # Turbid water
           chl_bounds = (1.0, 20.0)
           cdom_bounds = (0.2, 3.0)
       else:
           # Moderate water
           chl_bounds = initial_bounds['chl']
           cdom_bounds = initial_bounds['cdom']
       
       # Estimate depth from NIR penetration (if available)
       if len(pixel_spectrum) >= 4:
           nir_value = pixel_spectrum[3]
           if nir_value > 0.01:
               depth_bounds = (0.5, 8.0)  # Shallow
           elif nir_value > 0.003:
               depth_bounds = (2.0, 15.0)  # Medium
           else:
               depth_bounds = (5.0, 30.0)  # Deep
       else:
           depth_bounds = initial_bounds['depth']
       
       return {
           'depth': depth_bounds,
           'chl': chl_bounds,
           'cdom': cdom_bounds,
           'nap': initial_bounds['nap']  # Keep NAP bounds standard
       }

Adaptive SIOP Selection
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def adaptive_siop_selection(location, season, water_type):
       """Select appropriate SIOPs based on location and conditions."""
       
       # Regional SIOP libraries
       siop_libraries = {
           'mediterranean': 'med_siops.csv',
           'atlantic_coastal': 'atlantic_siops.csv',
           'pacific_tropical': 'pacific_siops.csv',
           'great_lakes': 'great_lakes_siops.csv'
       }
       
       # Seasonal adjustments
       seasonal_factors = {
           'spring': {'chl_factor': 1.5, 'cdom_factor': 1.2},
           'summer': {'chl_factor': 0.8, 'cdom_factor': 0.9},
           'autumn': {'chl_factor': 1.2, 'cdom_factor': 1.1},
           'winter': {'chl_factor': 0.6, 'cdom_factor': 1.0}
       }
       
       # Water type modifications
       water_type_mods = {
           'oligotrophic': {'a_ph_scale': 0.8, 'bb_ph_scale': 0.7},
           'mesotrophic': {'a_ph_scale': 1.0, 'bb_ph_scale': 1.0},
           'eutrophic': {'a_ph_scale': 1.3, 'bb_ph_scale': 1.5}
       }
       
       # Select base library
       base_library = siop_libraries.get(location, 'standard_siops.csv')
       
       # Apply seasonal and water type adjustments
       # (Implementation would load and modify SIOP values)
       
       return {
           'library_path': base_library,
           'seasonal_factor': seasonal_factors.get(season, seasonal_factors['summer']),
           'water_type_mod': water_type_mods.get(water_type, water_type_mods['mesotrophic'])
       }

Configuration Validation
------------------------

Parameter Consistency Checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def validate_configuration(config):
       """Validate configuration for consistency and reasonableness."""
       
       validation_results = {
           'errors': [],
           'warnings': [],
           'recommendations': []
       }
       
       # Check parameter bounds
       if 'parameter_bounds' in config:
           bounds = config['parameter_bounds']
           
           # Depth bounds
           if 'depth' in bounds:
               depth_min, depth_max = bounds['depth']
               if depth_min <= 0:
                   validation_results['errors'].append("Depth minimum must be > 0")
               if depth_max > 100:
                   validation_results['warnings'].append("Very deep water (>100m) may be unrealistic for SAMBUCA")
           
           # Chlorophyll bounds
           if 'chl' in bounds:
               chl_min, chl_max = bounds['chl']
               if chl_min <= 0:
                   validation_results['errors'].append("Chlorophyll minimum must be > 0")
               if chl_max > 100:
                   validation_results['warnings'].append("Very high chlorophyll (>100 mg/m³) may be unrealistic")
       
       # Check optimization settings
       if 'optimization' in config:
           opt = config['optimization']
           
           if opt.get('max_iterations', 0) < 10:
               validation_results['warnings'].append("Very few iterations may lead to poor convergence")
           
           if opt.get('tolerance', 1) > 1e-3:
               validation_results['warnings'].append("Loose tolerance may reduce accuracy")
       
       # Check processing settings
       if 'processing' in config:
           proc = config['processing']
           
           if proc.get('chunk_size', 0) > 5000:
               validation_results['warnings'].append("Large chunk size may cause memory issues")
           
           n_proc = proc.get('n_processes', 1)
           max_cores = mp.cpu_count()
           if n_proc > max_cores:
               validation_results['errors'].append(f"Cannot use {n_proc} processes with {max_cores} cores")
       
       return validation_results

Performance Benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def benchmark_configuration(config, test_image_size=(100, 100, 4)):
       """Benchmark configuration performance on test data."""
       
       import time
       import numpy as np
       
       # Create synthetic test data
       test_image = np.random.random(test_image_size) * 0.05
       
       # Run with different configurations
       results = {}
       
       for config_name, settings in config.items():
           print(f"Benchmarking {config_name}...")
           
           start_time = time.time()
           
           try:
               # Create parameters from settings
               params = InversionParameters(**settings.get('parameter_bounds', {}))
               
               # Apply optimization settings
               if 'optimization' in settings:
                   for key, value in settings['optimization'].items():
                       setattr(params, key, value)
               
               # Process small test image
               from sambuca_core.inversion import process_image
               
               test_results = process_image(
                   test_image,
                   params,
                   n_processes=settings.get('processing', {}).get('n_processes', 2),
                   progress_bar=False
               )
               
               end_time = time.time()
               processing_time = end_time - start_time
               
               # Calculate metrics
               success_rate = np.sum(~np.isnan(test_results['depth'])) / test_results['depth'].size
               
               results[config_name] = {
                   'processing_time': processing_time,
                   'success_rate': success_rate,
                   'pixels_per_second': test_results['depth'].size / processing_time,
                   'status': 'success'
               }
               
           except Exception as e:
               results[config_name] = {
                   'status': 'failed',
                   'error': str(e)
               }
       
       return results

Configuration Templates
-----------------------

Template Generator
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def generate_configuration_template(application, region=None, sensor=None):
       """Generate configuration template for specific application."""
       
       templates = {
           'research': {
               'description': 'High-precision configuration for research applications',
               'optimization': {
                   'method': 'trust-constr',
                   'max_iterations': 500,
                   'tolerance': 1e-8,
                   'multistart': True,
                   'n_starts': 15
               },
               'processing': {
                   'chunk_size': 500,
                   'n_processes': 'conservative'
               },
               'quality_control': {
                   'rmse_threshold': 0.001,
                   'strict_bounds': True
               }
           },
           
           'operational': {
               'description': 'Fast processing for operational monitoring',
               'optimization': {
                   'method': 'L-BFGS-B',
                   'max_iterations': 100,
                   'tolerance': 1e-5,
                   'multistart': False
               },
               'processing': {
                   'chunk_size': 2000,
                   'n_processes': 'aggressive'
               },
               'quality_control': {
                   'rmse_threshold': 0.003,
                   'strict_bounds': False
               }
           },
           
           'validation': {
               'description': 'Optimized for validation against field data',
               'optimization': {
                   'method': 'L-BFGS-B',
                   'max_iterations': 200,
                   'tolerance': 1e-6,
                   'multistart': True,
                   'n_starts': 5
               },
               'processing': {
                   'chunk_size': 1000,
                   'n_processes': 'balanced'
               },
               'matchup': {
                   'spatial_window': 3,
                   'temporal_window': 3
               }
           }
       }
       
       # Get base template
       template = templates.get(application, templates['research']).copy()
       
       # Add regional customizations
       if region:
           regional_params = get_regional_parameters(region)
           template['parameter_bounds'] = regional_params
       
       # Add sensor-specific settings
       if sensor:
           sensor_settings = get_sensor_configuration(sensor)
           template.update(sensor_settings)
       
       return template

Best Practices and Recommendations
----------------------------------

General Guidelines
~~~~~~~~~~~~~~~~~

1. **Start Conservative**
   - Begin with well-tested parameter bounds
   - Use standard optimization settings initially
   - Validate on known data before applying to new areas

2. **Iterative Refinement**
   - Analyze results and adjust bounds accordingly
   - Monitor convergence rates and success rates
   - Use validation data to guide improvements

3. **Regional Adaptation**
   - Customize SIOPs for your study area when possible
   - Adjust parameter bounds based on local conditions
   - Consider seasonal variations

4. **Performance vs Accuracy Trade-offs**
   - Use appropriate precision for your application
   - Balance processing speed with result quality
   - Consider computational resources available

Configuration Checklist
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Pre-Processing Checklist:
   □ Atmospheric correction applied
   □ Cloud and land masking completed
   □ Sun glint correction (if needed)
   □ Sensor calibration verified
   
   Parameter Configuration:
   □ Bounds appropriate for study area
   □ SIOP libraries suitable for region
   □ Substrate types representative
   □ Seasonal adjustments considered
   
   Optimization Settings:
   □ Algorithm appropriate for problem
   □ Convergence criteria reasonable
   □ Multi-start enabled for difficult problems
   □ Timeout settings configured
   
   Processing Configuration:
   □ Parallel processing optimized
   □ Memory requirements checked
   □ Chunk size appropriate
   □ Quality control thresholds set
   
   Validation Setup:
   □ Test data available
   □ Accuracy metrics defined
   □ Uncertainty analysis planned
   □ Output format specified

Troubleshooting Configuration Issues
-----------------------------------

Common Problems and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Low convergence rates
**Solutions**:
- Widen parameter bounds
- Increase max iterations
- Try different optimization algorithm
- Use multi-start optimization

**Problem**: Unrealistic parameter values
**Solutions**:
- Tighten parameter bounds
- Check SIOP quality
- Validate input data preprocessing
- Add physical constraints

**Problem**: Slow processing
**Solutions**:
- Reduce max iterations
- Increase tolerance
- Use faster optimization method
- Increase chunk size (if memory allows)

**Problem**: High memory usage
**Solutions**:
- Reduce chunk size
- Decrease number of processes
- Use conservative memory strategy
- Process in smaller regions

Expert Configuration Examples
----------------------------

High-Performance Computing Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configuration for HPC cluster processing
   hpc_config = {
       'optimization': {
           'method': 'L-BFGS-B',
           'max_iterations': 150,
           'tolerance': 1e-5
       },
       'processing': {
           'n_processes': 64,        # Large cluster node
           'chunk_size': 5000,       # Large memory available
           'memory_strategy': 'aggressive',
           'distributed': True       # Multi-node processing
       },
       'io': {
           'compression': 'blosc',   # Fast compression
           'chunk_cache': '1GB',     # Large cache
           'parallel_io': True
       }
   }

Real-Time Processing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configuration for real-time processing
   realtime_config = {
       'optimization': {
           'method': 'L-BFGS-B',
           'max_iterations': 30,     # Very fast
           'tolerance': 1e-3,        # Relaxed
           'timeout_per_pixel': 0.5  # 500ms max per pixel
       },
       'processing': {
           'streaming': True,
           'buffer_size': 1000,
           'latency_target': 10,     # seconds
       },
       'quality_control': {
           'fast_reject': True,      # Quick quality checks
           'minimal_validation': True
       }
   }

This comprehensive configuration guide provides the foundation for optimizing SAMBUCA for your specific application, study area, and computational resources. Proper configuration is crucial for achieving accurate, reliable results while maintaining efficient processing performance.

Next Steps
----------

Now that you understand configuration:

🔬 **For theoretical background**: :doc:`../theory/algorithms`  
📊 **For real-world examples**: :doc:`../examples/advanced_examples`  
📈 **For validation techniques**: :doc:`../examples/tutorials`  
🛠️ **For development**: Contributing to SAMBUCA Core

**Configuration Exercises:**

1. **Create configurations** for your specific study area and sensor
2. **Benchmark different settings** on your typical data
3. **Validate configurations** against field measurements
4. **Optimize for your hardware** and processing requirements
5. **Develop regional templates** for repeated use

Advanced configuration techniques and optimization strategies can be found in the examples and theory sections.
