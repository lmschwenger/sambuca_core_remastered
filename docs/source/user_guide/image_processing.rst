Image Processing
================

This guide covers processing entire satellite images with SAMBUCA to create maps of water properties. You'll learn to handle real satellite data, optimize processing workflows, and generate publication-quality results.

Overview of Image Processing
----------------------------

Image processing with SAMBUCA transforms satellite scenes into meaningful parameter maps:

.. code-block:: text

   Satellite Image → SAMBUCA Processing → Parameter Maps
   [Height × Width × Bands] → Pixel-by-pixel Inversion → [Depth, CHL, CDOM, NAP maps]

**Input**: Multi-band satellite imagery (Sentinel-2, Landsat, etc.)  
**Output**: Georeferenced parameter maps with uncertainty estimates  
**Scale**: From small coastal areas to entire scenes  

Key Concepts
~~~~~~~~~~~~

**Pixel-wise Processing**
   Each pixel is processed independently using the inversion algorithm

**Parallel Processing**
   Utilize multiple CPU cores for faster processing

**Memory Management**
   Handle large images efficiently without running out of memory

**Quality Control**
   Identify and flag problematic pixels during processing

**Georeferencing**
   Maintain spatial reference information throughout processing

Basic Image Processing Workflow
-------------------------------

Simple Example with Synthetic Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca.core as sbc
   from sambuca_core.inversion import InversionParameters, process_image
   import numpy as np
   import matplotlib.pyplot as plt

   # Create synthetic image data
   def create_synthetic_image():
       """Create a realistic synthetic satellite image."""
       
       height, width, n_bands = 200, 200, 4
       image = np.zeros((height, width, n_bands))
       
       # Create realistic spatial patterns
       x, y = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
       
       # Depth gradient (shore to offshore)
       depth_truth = 1 + 20 * x  # 1-21m depth gradient
       
       # Chlorophyll pattern (coastal productivity)
       chl_truth = 0.5 + 2.0 * np.exp(-5 * x) + 0.5 * np.sin(10 * y)
       chl_truth = np.clip(chl_truth, 0.1, 8.0)
       
       # CDOM pattern (river inputs)
       cdom_truth = 0.1 + 1.0 * np.exp(-8 * x) * np.exp(-3 * (y - 0.3)**2)
       cdom_truth = np.clip(cdom_truth, 0.05, 2.0)
       
       # NAP pattern (sediment resuspension)
       nap_truth = 0.5 + 1.5 * np.exp(-3 * x) + 0.3 * np.random.random((height, width))
       nap_truth = np.clip(nap_truth, 0.1, 4.0)
       
       # Define basic SIOPs (Sentinel-2)
       wavelengths = [492.4, 559.8, 664.6, 704.1]
       a_water = [0.007, 0.015, 0.325, 0.619]
       a_ph_star = [0.055, 0.023, 0.014, 0.010]
       substrate = [0.3, 0.3, 0.25, 0.2]
       
       # Generate realistic reflectance for each pixel
       print("Generating synthetic reflectance...")
       for i in range(height):
           if i % 50 == 0:
               print(f"  Processing row {i}/{height}")
           
           for j in range(width):
               # Get parameters for this pixel
               pixel_depth = depth_truth[i, j]
               pixel_chl = chl_truth[i, j]
               pixel_cdom = cdom_truth[i, j]
               pixel_nap = nap_truth[i, j]
               
               # Run forward model
               try:
                   results = sbc.forward_model(
                       chl=pixel_chl, cdom=pixel_cdom, nap=pixel_nap, depth=pixel_depth,
                       substrate1=substrate, wavelengths=wavelengths,
                       a_water=a_water, a_ph_star=a_ph_star,
                       num_bands=len(wavelengths)
                   )
                   image[i, j, :] = results.rrs
               except:
                   # Handle edge cases with default values
                   image[i, j, :] = [0.01, 0.012, 0.006, 0.004]
       
       # Add realistic noise
       noise_level = 0.0003
       image += np.random.normal(0, noise_level, image.shape)
       
       # Ensure positive values
       image = np.maximum(image, 0.0001)
       
       truth_maps = {
           'depth': depth_truth,
           'chl': chl_truth,
           'cdom': cdom_truth,
           'nap': nap_truth
       }
       
       return image, truth_maps, wavelengths, a_water, a_ph_star, substrate

   # Create synthetic data
   image, truth_maps, wavelengths, a_water, a_ph_star, substrate = create_synthetic_image()
   
   print(f"Created synthetic image: {image.shape}")
   print(f"Reflectance range: {image.min():.6f} - {image.max():.6f}")

Visualize Input Data
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Visualize the synthetic image and truth maps
   fig, axes = plt.subplots(2, 3, figsize=(18, 12))

   # RGB composite (approximate)
   rgb_image = np.stack([
       image[:, :, 2],  # Red band
       image[:, :, 1],  # Green band  
       image[:, :, 0]   # Blue band
   ], axis=-1)
   
   # Normalize for display
   rgb_display = rgb_image / np.percentile(rgb_image, 99) * 255
   rgb_display = np.clip(rgb_display, 0, 255).astype(np.uint8)
   
   axes[0,0].imshow(rgb_display)
   axes[0,0].set_title('RGB Composite (Synthetic)')
   axes[0,0].axis('off')

   # Truth maps
   im1 = axes[0,1].imshow(truth_maps['depth'], cmap='viridis_r', aspect='equal')
   axes[0,1].set_title('True Depth (m)')
   plt.colorbar(im1, ax=axes[0,1])
   axes[0,1].axis('off')

   im2 = axes[0,2].imshow(truth_maps['chl'], cmap='YlGn', aspect='equal')
   axes[0,2].set_title('True Chlorophyll (mg/m³)')
   plt.colorbar(im2, ax=axes[0,2])
   axes[0,2].axis('off')

   im3 = axes[1,0].imshow(truth_maps['cdom'], cmap='YlOrBr', aspect='equal')
   axes[1,0].set_title('True CDOM (1/m)')
   plt.colorbar(im3, ax=axes[1,0])
   axes[1,0].axis('off')

   im4 = axes[1,1].imshow(truth_maps['nap'], cmap='Oranges', aspect='equal')
   axes[1,1].set_title('True NAP (mg/L)')
   plt.colorbar(im4, ax=axes[1,1])
   axes[1,1].axis('off')

   # Individual band
   im5 = axes[1,2].imshow(image[:, :, 1], cmap='viridis', aspect='equal')
   axes[1,2].set_title('Green Band Reflectance')
   plt.colorbar(im5, ax=axes[1,2])
   axes[1,2].axis('off')

   plt.tight_layout()
   plt.show()

Set Up Inversion Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure inversion parameters for image processing
   params = InversionParameters(
       depth=(0.5, 25),      # Depth range
       chl=(0.1, 15.0),      # Chlorophyll range
       cdom=(0.01, 3.0),     # CDOM range
       nap=(0.1, 8.0),       # NAP range
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       substrate1=substrate,
       num_bands=len(wavelengths)
   )

   # Optimize for batch processing
   params.optimization_method = 'L-BFGS-B'
   params.max_iterations = 100  # Reduce for speed
   params.tolerance = 1e-4      # Relax tolerance slightly

   print("Inversion parameters configured")

Process the Image
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process the entire image
   print("Starting image processing...")
   print("This may take several minutes depending on image size and CPU cores")

   results = process_image(
       image,
       params,
       n_processes=4,        # Use 4 CPU cores
       progress_bar=True,    # Show progress bar
       chunk_size=20,        # Process in chunks for memory efficiency
       max_pixels=None       # Process all pixels
   )

   print("Image processing complete!")
   print(f"Results contain: {list(results.keys())}")

Analyze and Visualize Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Extract result maps
   depth_map = results['depth']
   chl_map = results['chl']
   cdom_map = results['cdom']
   nap_map = results['nap']
   error_map = results['error']

   # Calculate accuracy statistics
   def calculate_accuracy(estimated, truth, param_name):
       """Calculate accuracy statistics for a parameter."""
       valid_mask = ~np.isnan(estimated) & ~np.isnan(truth)
       
       if np.sum(valid_mask) == 0:
           return None
           
       est_valid = estimated[valid_mask]
       truth_valid = truth[valid_mask]
       
       rmse = np.sqrt(np.mean((est_valid - truth_valid)**2))
       mae = np.mean(np.abs(est_valid - truth_valid))
       bias = np.mean(est_valid - truth_valid)
       r_squared = 1 - np.sum((est_valid - truth_valid)**2) / np.sum((truth_valid - np.mean(truth_valid))**2)
       
       return {
           'rmse': rmse,
           'mae': mae,
           'bias': bias,
           'r_squared': r_squared,
           'valid_pixels': np.sum(valid_mask)
       }

   # Calculate accuracy for each parameter
   accuracy_stats = {}
   for param in ['depth', 'chl', 'cdom', 'nap']:
       stats = calculate_accuracy(results[param], truth_maps[param], param)
       accuracy_stats[param] = stats
       
       if stats:
           print(f"\\n{param.upper()} Accuracy:")
           print(f"  RMSE: {stats['rmse']:.3f}")
           print(f"  MAE: {stats['mae']:.3f}")
           print(f"  Bias: {stats['bias']:.3f}")
           print(f"  R²: {stats['r_squared']:.3f}")
           print(f"  Valid pixels: {stats['valid_pixels']}")

Comprehensive Result Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create comprehensive result visualization
   fig, axes = plt.subplots(3, 4, figsize=(20, 15))

   params_info = [
       ('depth', 'Depth (m)', 'viridis_r'),
       ('chl', 'Chlorophyll (mg/m³)', 'YlGn'),
       ('cdom', 'CDOM (1/m)', 'YlOrBr'),
       ('nap', 'NAP (mg/L)', 'Oranges')
   ]

   for i, (param, title, cmap) in enumerate(params_info):
       # Truth
       im1 = axes[0, i].imshow(truth_maps[param], cmap=cmap, aspect='equal')
       axes[0, i].set_title(f'True {title}')
       plt.colorbar(im1, ax=axes[0, i])
       axes[0, i].axis('off')
       
       # Estimated
       im2 = axes[1, i].imshow(results[param], cmap=cmap, aspect='equal')
       axes[1, i].set_title(f'Estimated {title}')
       plt.colorbar(im2, ax=axes[1, i])
       axes[1, i].axis('off')
       
       # Difference
       diff = results[param] - truth_maps[param]
       im3 = axes[2, i].imshow(diff, cmap='RdBu_r', aspect='equal')
       axes[2, i].set_title(f'{title} Error')
       plt.colorbar(im3, ax=axes[2, i])
       axes[2, i].axis('off')

   plt.tight_layout()
   plt.show()

   # Scatter plots for validation
   fig, axes = plt.subplots(2, 2, figsize=(12, 10))
   axes = axes.flatten()

   for i, (param, title, cmap) in enumerate(params_info):
       truth_flat = truth_maps[param].flatten()
       est_flat = results[param].flatten()
       
       # Remove invalid pixels
       valid_mask = ~np.isnan(truth_flat) & ~np.isnan(est_flat)
       
       if np.sum(valid_mask) > 0:
           truth_valid = truth_flat[valid_mask]
           est_valid = est_flat[valid_mask]
           
           # Scatter plot
           axes[i].scatter(truth_valid, est_valid, alpha=0.5, s=1)
           
           # 1:1 line
           min_val = min(np.min(truth_valid), np.min(est_valid))
           max_val = max(np.max(truth_valid), np.max(est_valid))
           axes[i].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
           
           # Statistics
           stats = accuracy_stats[param]
           if stats:
               axes[i].text(0.05, 0.95, f'R² = {stats["r_squared"]:.3f}\\nRMSE = {stats["rmse"]:.3f}',
                           transform=axes[i].transAxes, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
           
           axes[i].set_xlabel(f'True {title}')
           axes[i].set_ylabel(f'Estimated {title}')
           axes[i].set_title(f'{title} Validation')
           axes[i].grid(True, alpha=0.3)

   plt.tight_layout()
   plt.show()

Working with Real Satellite Data
---------------------------------

Loading Sentinel-2 Data
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def load_sentinel2_data(file_path):
       """Load and preprocess Sentinel-2 data."""
       
       try:
           import rasterio
           import rasterio.plot
       except ImportError:
           print("rasterio not installed. Install with: pip install rasterio")
           return None
       
       # Load Sentinel-2 image
       with rasterio.open(file_path) as src:
           # Read bands (assuming B2, B3, B4, B8A order)
           bands = src.read([2, 3, 4, 8])  # Blue, Green, Red, NIR
           
           # Get metadata
           transform = src.transform
           crs = src.crs
           
           # Convert to reflectance (if needed)
           # Note: Adjust scaling based on your data format
           reflectance = bands.astype(np.float32) / 10000.0  # For L2A products
           
           # Rearrange to (height, width, bands)
           image = np.transpose(reflectance, (1, 2, 0))
           
           print(f"Loaded Sentinel-2 data: {image.shape}")
           print(f"Reflectance range: {image.min():.6f} - {image.max():.6f}")
           
           return {
               'image': image,
               'transform': transform,
               'crs': crs,
               'wavelengths': [492.4, 559.8, 664.6, 704.1]  # Sentinel-2 MSI
           }
   
   # Example usage (uncomment when you have real data)
   # sentinel2_data = load_sentinel2_data("path/to/sentinel2_scene.tif")

Loading Landsat Data
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def load_landsat_data(file_path):
       """Load and preprocess Landsat 8/9 data."""
       
       try:
           import rasterio
       except ImportError:
           print("rasterio not installed")
           return None
       
       with rasterio.open(file_path) as src:
           # Read coastal, blue, green, red bands
           bands = src.read([1, 2, 3, 4])  # Coastal, Blue, Green, Red
           
           # Convert to reflectance
           reflectance = bands.astype(np.float32) * 2.75e-5 - 0.2  # L8/L9 scaling
           reflectance = np.clip(reflectance, 0, 1)
           
           # Rearrange dimensions
           image = np.transpose(reflectance, (1, 2, 0))
           
           return {
               'image': image,
               'transform': src.transform,
               'crs': src.crs,
               'wavelengths': [443, 482, 561, 655]  # Landsat 8/9 OLI
           }

Preprocessing Steps
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def preprocess_satellite_image(image_data):
       """Comprehensive preprocessing of satellite imagery."""
       
       image = image_data['image'].copy()
       height, width, bands = image.shape
       
       print(f"Preprocessing image: {height}x{width}x{bands}")
       
       # 1. Quality control checks
       print("1. Quality control...")
       
       # Check for invalid values
       invalid_mask = (image <= 0) | (image > 1) | np.isnan(image)
       invalid_pixels = np.sum(invalid_mask)
       print(f"   Invalid pixels: {invalid_pixels} ({100*invalid_pixels/image.size:.2f}%)")
       
       # 2. Remove obviously invalid pixels
       print("2. Removing invalid pixels...")
       
       # Land/cloud mask (simple approach - very high NIR)
       if bands >= 4:  # Has NIR band
           nir_band = image[:, :, -1]
           land_mask = nir_band > 0.3  # Likely land/clouds
           print(f"   Land/cloud pixels: {np.sum(land_mask)} ({100*np.sum(land_mask)/land_mask.size:.2f}%)")
       else:
           land_mask = np.zeros((height, width), dtype=bool)
       
       # Very dark water (sensor issues)
       dark_mask = np.all(image < 0.001, axis=2)
       print(f"   Very dark pixels: {np.sum(dark_mask)} ({100*np.sum(dark_mask)/dark_mask.size:.2f}%)")
       
       # Combined mask
       processing_mask = ~(land_mask | dark_mask | np.any(invalid_mask, axis=2))
       
       print(f"   Pixels for processing: {np.sum(processing_mask)} ({100*np.sum(processing_mask)/processing_mask.size:.2f}%)")
       
       # 3. Spectral smoothing (optional)
       print("3. Optional spectral smoothing...")
       
       # Apply mild Gaussian smoothing to reduce noise
       from scipy.ndimage import gaussian_filter
       
       smoothed_image = image.copy()
       for band in range(bands):
           smoothed_image[:, :, band] = gaussian_filter(image[:, :, band], sigma=0.5)
       
       # 4. Sun glint correction (simplified)
       print("4. Basic sun glint correction...")
       
       if bands >= 4:  # Has NIR band
           nir_band = smoothed_image[:, :, -1]
           
           # Estimate glint from NIR (assumes NIR should be ~0 over water)
           glint_threshold = 0.01
           glint_pixels = (nir_band > glint_threshold) & processing_mask
           
           if np.sum(glint_pixels) > 0:
               # Simple linear glint correction
               for band in range(bands-1):  # Exclude NIR
                   # Assume linear relationship between NIR and glint
                   glint_correction = nir_band * 0.5  # Simplified coefficient
                   smoothed_image[:, :, band] = np.maximum(
                       smoothed_image[:, :, band] - glint_correction, 0
                   )
               
               print(f"   Glint-corrected pixels: {np.sum(glint_pixels)}")
       
       preprocessed_data = {
           'image': smoothed_image,
           'processing_mask': processing_mask,
           'land_mask': land_mask,
           'transform': image_data.get('transform'),
           'crs': image_data.get('crs'),
           'wavelengths': image_data.get('wavelengths')
       }
       
       return preprocessed_data

   # Example preprocessing
   if image is not None:
       dummy_data = {
           'image': image,
           'wavelengths': wavelengths
       }
       preprocessed = preprocess_satellite_image(dummy_data)
       print("Preprocessing complete")

Advanced Processing Techniques
------------------------------

Chunked Processing for Large Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def process_large_image(image, params, chunk_size=1000, overlap=50):
       """Process very large images in overlapping chunks."""
       
       height, width, bands = image.shape
       
       print(f"Processing large image: {height}x{width}")
       print(f"Chunk size: {chunk_size}x{chunk_size}, Overlap: {overlap}")
       
       # Initialize output arrays
       result_maps = {
           'depth': np.full((height, width), np.nan),
           'chl': np.full((height, width), np.nan),
           'cdom': np.full((height, width), np.nan),
           'nap': np.full((height, width), np.nan),
           'error': np.full((height, width), np.nan)
       }
       
       # Calculate chunk positions
       y_starts = range(0, height, chunk_size - overlap)
       x_starts = range(0, width, chunk_size - overlap)
       
       total_chunks = len(y_starts) * len(x_starts)
       chunk_count = 0
       
       for y_start in y_starts:
           for x_start in x_starts:
               chunk_count += 1
               print(f"Processing chunk {chunk_count}/{total_chunks}")
               
               # Calculate chunk bounds
               y_end = min(y_start + chunk_size, height)
               x_end = min(x_start + chunk_size, width)
               
               # Extract chunk
               chunk = image[y_start:y_end, x_start:x_end, :]
               
               # Process chunk
               try:
                   chunk_results = process_image(
                       chunk, params,
                       n_processes=2,  # Reduce for memory
                       progress_bar=False
                   )
                   
                   # Handle overlap regions (simple averaging)
                   for param_name, param_map in chunk_results.items():
                       if param_name in result_maps:
                           # Get current chunk region
                           current_result = result_maps[param_name][y_start:y_end, x_start:x_end]
                           
                           # Average overlapping regions
                           valid_current = ~np.isnan(current_result)
                           valid_new = ~np.isnan(param_map)
                           
                           # Where both exist, average
                           both_valid = valid_current & valid_new
                           result_maps[param_name][y_start:y_end, x_start:x_end][both_valid] = (
                               current_result[both_valid] + param_map[both_valid]
                           ) / 2
                           
                           # Where only new exists, use new
                           only_new = ~valid_current & valid_new
                           result_maps[param_name][y_start:y_end, x_start:x_end][only_new] = param_map[only_new]
               
               except Exception as e:
                   print(f"Error processing chunk {chunk_count}: {e}")
                   continue
       
       return result_maps

Adaptive Parameter Bounds
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def adaptive_parameter_bounds(image, initial_params):
       """Adapt parameter bounds based on image characteristics."""
       
       # Analyze image statistics
       mean_reflectance = np.nanmean(image, axis=(0, 1))
       std_reflectance = np.nanstd(image, axis=(0, 1))
       
       print(f"Image reflectance statistics:")
       for i, (mean_val, std_val) in enumerate(zip(mean_reflectance, std_reflectance)):
           print(f"  Band {i+1}: {mean_val:.6f} ± {std_val:.6f}")
       
       # Estimate approximate water conditions
       blue_green_ratio = mean_reflectance[0] / mean_reflectance[1] if len(mean_reflectance) > 1 else 1.0
       
       # Adapt bounds based on water type
       if blue_green_ratio > 0.9:
           # Clear water - likely oligotrophic
           chl_bounds = (0.1, 3.0)
           cdom_bounds = (0.01, 0.5)
           print("Detected clear water conditions")
       elif blue_green_ratio > 0.7:
           # Moderate water
           chl_bounds = (0.5, 8.0)
           cdom_bounds = (0.1, 1.5)
           print("Detected moderate water conditions")
       else:
           # Turbid water
           chl_bounds = (1.0, 20.0)
           cdom_bounds = (0.2, 3.0)
           print("Detected turbid water conditions")
       
       # Depth bounds based on penetration depth
       # Rough estimate from NIR attenuation
       if len(mean_reflectance) >= 4:
           nir_reflectance = mean_reflectance[3]
           if nir_reflectance > 0.01:
               depth_bounds = (0.5, 8.0)  # Shallow water
           elif nir_reflectance > 0.003:
               depth_bounds = (2.0, 15.0)  # Medium depth
           else:
               depth_bounds = (5.0, 25.0)  # Deeper water
       else:
           depth_bounds = (1.0, 20.0)  # Default
       
       # Create new parameters with adaptive bounds
       adaptive_params = InversionParameters(
           depth=depth_bounds,
           chl=chl_bounds,
           cdom=cdom_bounds,
           nap=(0.1, 8.0),  # Keep NAP bounds standard
           wavelengths=initial_params.wavelengths,
           a_water=initial_params.a_water,
           a_ph_star=initial_params.a_ph_star,
           substrate1=initial_params.substrate1,
           num_bands=initial_params.num_bands
       )
       
       print(f"Adaptive bounds:")
       print(f"  Depth: {depth_bounds}")
       print(f"  Chlorophyll: {chl_bounds}")
       print(f"  CDOM: {cdom_bounds}")
       
       return adaptive_params

Parallel Processing Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def optimize_parallel_processing(image, params):
       """Determine optimal parallel processing configuration."""
       
       import multiprocessing as mp
       import time
       
       height, width, bands = image.shape
       total_pixels = height * width
       
       print(f"Optimizing parallel processing for {total_pixels} pixels")
       
       # Test different configurations on a subset
       test_size = min(1000, total_pixels)
       test_indices = np.random.choice(total_pixels, test_size, replace=False)
       
       # Create test data
       flat_image = image.reshape(-1, bands)
       test_spectra = flat_image[test_indices]
       
       # Test different core counts
       available_cores = mp.cpu_count()
       test_cores = [1, 2, 4, min(8, available_cores), available_cores]
       
       print(f"Testing with {len(test_spectra)} pixels on different core counts...")
       
       best_config = {'cores': 1, 'time_per_pixel': float('inf')}
       
       for n_cores in test_cores:
           if n_cores > available_cores:
               continue
           
           print(f"  Testing {n_cores} cores...")
           
           start_time = time.time()
           
           # Process test subset
           try:
               test_results = process_image(
                   test_spectra.reshape(len(test_spectra), 1, bands),
                   params,
                   n_processes=n_cores,
                   progress_bar=False
               )
               
               end_time = time.time()
               processing_time = end_time - start_time
               time_per_pixel = processing_time / len(test_spectra)
               
               print(f"    Time: {processing_time:.2f}s ({time_per_pixel*1000:.2f}ms/pixel)")
               
               if time_per_pixel < best_config['time_per_pixel']:
                   best_config = {'cores': n_cores, 'time_per_pixel': time_per_pixel}
           
           except Exception as e:
               print(f"    Failed: {e}")
       
       # Estimate total processing time
       estimated_total_time = best_config['time_per_pixel'] * total_pixels
       
       print(f"\\nOptimal configuration:")
       print(f"  Cores: {best_config['cores']}")
       print(f"  Estimated total time: {estimated_total_time/60:.1f} minutes")
       
       return best_config['cores']

Quality Control and Validation
------------------------------

Automated Quality Assessment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def quality_control_assessment(results, image, threshold_rmse=0.002):
       """Comprehensive quality control of processing results."""
       
       print("Quality Control Assessment")
       print("=" * 50)
       
       height, width = results['depth'].shape
       total_pixels = height * width
       
       # 1. Check processing success rate
       valid_depth = ~np.isnan(results['depth'])
       success_rate = np.sum(valid_depth) / total_pixels
       
       print(f"1. Processing Success Rate: {success_rate:.1%}")
       
       # 2. Error distribution analysis
       error_map = results['error']
       valid_errors = error_map[~np.isnan(error_map)]
       
       if len(valid_errors) > 0:
           print(f"2. Error Statistics:")
           print(f"   Mean RMSE: {np.mean(valid_errors):.6f}")
           print(f"   Median RMSE: {np.median(valid_errors):.6f}")
           print(f"   Max RMSE: {np.max(valid_errors):.6f}")
           
           # High error pixels
           high_error_pixels = np.sum(error_map > threshold_rmse)
           print(f"   High error pixels (>{threshold_rmse}): {high_error_pixels} ({100*high_error_pixels/total_pixels:.1f}%)")
       
       # 3. Parameter range analysis
       print(f"3. Parameter Ranges:")
       for param in ['depth', 'chl', 'cdom', 'nap']:
           if param in results:
               param_map = results[param]
               valid_values = param_map[~np.isnan(param_map)]
               
               if len(valid_values) > 0:
                   print(f"   {param.upper()}: {np.min(valid_values):.3f} - {np.max(valid_values):.3f}")
                   
                   # Check for boundary values (potential optimization issues)
                   if param == 'depth':
                       boundary_check = [0.5, 25]  # Typical bounds
                   elif param == 'chl':
                       boundary_check = [0.1, 15]
                   elif param == 'cdom':
                       boundary_check = [0.01, 3.0]
                   else:  # nap
                       boundary_check = [0.1, 8.0]
                   
                   at_lower = np.sum(np.abs(valid_values - boundary_check[0]) < 0.01)
                   at_upper = np.sum(np.abs(valid_values - boundary_check[1]) < 0.01)
                   
                   if at_lower > 0 or at_upper > 0:
                       print(f"     WARNING: {at_lower + at_upper} pixels at parameter bounds")
       
       # 4. Spatial consistency check
       print(f"4. Spatial Consistency:")
       
       for param in ['depth', 'chl']:
           if param in results:
               param_map = results[param]
               
               # Calculate spatial gradients
               from scipy.ndimage import sobel
               
               # Handle NaN values
               filled_map = np.copy(param_map)
               filled_map[np.isnan(filled_map)] = np.nanmean(filled_map)
               
               gradient_x = sobel(filled_map, axis=1)
               gradient_y = sobel(filled_map, axis=0)
               gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
               
               mean_gradient = np.nanmean(gradient_magnitude)
               high_gradient_pixels = np.sum(gradient_magnitude > 3 * mean_gradient)
               
               print(f"   {param.upper()} spatial gradient: {mean_gradient:.3f}")
               print(f"   High gradient pixels: {high_gradient_pixels} ({100*high_gradient_pixels/total_pixels:.1f}%)")
       
       # 5. Spectral fit quality
       print(f"5. Spectral Fit Quality:")
       
       if len(valid_errors) > 0:
           excellent_fit = np.sum(valid_errors < 0.0005)
           good_fit = np.sum((valid_errors >= 0.0005) & (valid_errors < 0.001))
           fair_fit = np.sum((valid_errors >= 0.001) & (valid_errors < threshold_rmse))
           poor_fit = np.sum(valid_errors >= threshold_rmse)
           
           total_processed = len(valid_errors)
           
           print(f"   Excellent fit (<0.0005): {excellent_fit} ({100*excellent_fit/total_processed:.1f}%)")
           print(f"   Good fit (0.0005-0.001): {good_fit} ({100*good_fit/total_processed:.1f}%)")
           print(f"   Fair fit (0.001-{threshold_rmse}): {fair_fit} ({100*fair_fit/total_processed:.1f}%)")
           print(f"   Poor fit (>{threshold_rmse}): {poor_fit} ({100*poor_fit/total_processed:.1f}%)")
       
       # 6. Overall quality score
       quality_score = (
           success_rate * 0.3 +
           (1 - min(np.mean(valid_errors) / threshold_rmse, 1.0)) * 0.4 +
           (1 - (high_error_pixels / total_pixels)) * 0.3
       )
       
       print(f"\\n6. Overall Quality Score: {quality_score:.3f} / 1.000")
       
       if quality_score > 0.8:
           print("   Status: EXCELLENT")
       elif quality_score > 0.6:
           print("   Status: GOOD")
       elif quality_score > 0.4:
           print("   Status: FAIR")
       else:
           print("   Status: POOR - Consider parameter adjustment")
       
       return quality_score

Export and Visualization
------------------------

Exporting Results
~~~~~~~~~~~~~~~~

.. code-block:: python

   def export_results(results, output_path, image_metadata=None):
       """Export processing results to various formats."""
       
       try:
           import rasterio
           from rasterio.transform import from_bounds
       except ImportError:
           print("rasterio not available - saving as NumPy arrays")
           
           # Save as NumPy arrays
           for param_name, param_map in results.items():
               np.save(f"{output_path}_{param_name}.npy", param_map)
           
           print(f"Results exported as NumPy arrays to {output_path}_*.npy")
           return
       
       # Export as GeoTIFF (if spatial metadata available)
       if image_metadata and 'transform' in image_metadata and 'crs' in image_metadata:
           print("Exporting as GeoTIFF...")
           
           height, width = results['depth'].shape
           
           for param_name, param_map in results.items():
               output_file = f"{output_path}_{param_name}.tif"
               
               with rasterio.open(
                   output_file, 'w',
                   driver='GTiff',
                   height=height, width=width,
                   count=1, dtype=param_map.dtype,
                   crs=image_metadata['crs'],
                   transform=image_metadata['transform'],
                   compress='lzw'
               ) as dst:
                   dst.write(param_map, 1)
               
               print(f"  Exported {param_name} to {output_file}")
       
       else:
           print("No spatial metadata - exporting as simple TIFFs...")
           
           for param_name, param_map in results.items():
               output_file = f"{output_path}_{param_name}.tif"
               
               with rasterio.open(
                   output_file, 'w',
                   driver='GTiff',
                   height=param_map.shape[0], width=param_map.shape[1],
                   count=1, dtype=param_map.dtype
               ) as dst:
                   dst.write(param_map, 1)

Publication-Quality Figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_publication_figure(results, truth_maps=None, output_file=None):
       """Create publication-quality figure of results."""
       
       import matplotlib.pyplot as plt
       from matplotlib.patches import Rectangle
       import matplotlib.patches as mpatches
       
       # Set up the figure with professional styling
       plt.style.use('default')  # Clean style
       fig = plt.figure(figsize=(16, 12))
       
       # Define parameters and their display properties
       params_info = [
           ('depth', 'Bathymetry (m)', 'viridis_r', (0, 20)),
           ('chl', 'Chlorophyll-a (mg m⁻³)', 'YlGn', (0, 8)),
           ('cdom', 'CDOM (m⁻¹)', 'YlOrBr', (0, 2)),
           ('error', 'RMSE', 'Reds', (0, 0.002))
       ]
       
       # Create subplots
       if truth_maps is not None:
           # Show truth vs estimated
           for i, (param, title, cmap, vrange) in enumerate(params_info[:-1]):  # Exclude error
               # Truth
               ax1 = plt.subplot(3, 3, i*3 + 1)
               im1 = ax1.imshow(truth_maps[param], cmap=cmap, vmin=vrange[0], vmax=vrange[1], aspect='equal')
               ax1.set_title(f'True {title}', fontsize=12, fontweight='bold')
               ax1.axis('off')
               
               # Add colorbar
               cbar1 = plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
               cbar1.ax.tick_params(labelsize=10)
               
               # Estimated
               ax2 = plt.subplot(3, 3, i*3 + 2)
               im2 = ax2.imshow(results[param], cmap=cmap, vmin=vrange[0], vmax=vrange[1], aspect='equal')
               ax2.set_title(f'Estimated {title}', fontsize=12, fontweight='bold')
               ax2.axis('off')
               
               # Add colorbar
               cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
               cbar2.ax.tick_params(labelsize=10)
               
               # Difference
               ax3 = plt.subplot(3, 3, i*3 + 3)
               diff = results[param] - truth_maps[param]
               diff_max = np.nanmax(np.abs(diff))
               im3 = ax3.imshow(diff, cmap='RdBu_r', vmin=-diff_max, vmax=diff_max, aspect='equal')
               ax3.set_title(f'{title} Difference', fontsize=12, fontweight='bold')
               ax3.axis('off')
               
               # Add colorbar
               cbar3 = plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
               cbar3.ax.tick_params(labelsize=10)
       
       else:
           # Show results only
           for i, (param, title, cmap, vrange) in enumerate(params_info):
               ax = plt.subplot(2, 2, i + 1)
               
               if param in results:
                   im = ax.imshow(results[param], cmap=cmap, vmin=vrange[0], vmax=vrange[1], aspect='equal')
                   ax.set_title(title, fontsize=14, fontweight='bold')
                   ax.axis('off')
                   
                   # Add colorbar
                   cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                   cbar.ax.tick_params(labelsize=12)
       
       # Add metadata text
       fig.text(0.02, 0.98, 'SAMBUCA Processing Results', fontsize=16, fontweight='bold', va='top')
       fig.text(0.02, 0.94, f'Image size: {results["depth"].shape[0]} × {results["depth"].shape[1]} pixels', 
                fontsize=10, va='top')
       
       # Add scale bar (if spatial info available)
       # This would require actual spatial metadata
       
       plt.tight_layout()
       
       if output_file:
           plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
           print(f"Figure saved to {output_file}")
       
       plt.show()

   # Create publication figure
   create_publication_figure(results, truth_maps, "sambuca_results.png")

Performance Monitoring
----------------------

Processing Performance Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def analyze_processing_performance(image_shape, processing_time, n_processes):
       """Analyze and report processing performance."""
       
       height, width, bands = image_shape
       total_pixels = height * width
       
       print("Processing Performance Analysis")
       print("=" * 50)
       print(f"Image dimensions: {height} × {width} × {bands}")
       print(f"Total pixels: {total_pixels:,}")
       print(f"Processing time: {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)")
       print(f"CPU cores used: {n_processes}")
       
       # Performance metrics
       pixels_per_second = total_pixels / processing_time
       time_per_pixel_ms = (processing_time / total_pixels) * 1000
       
       print(f"\\nPerformance Metrics:")
       print(f"  Pixels per second: {pixels_per_second:.0f}")
       print(f"  Time per pixel: {time_per_pixel_ms:.2f} ms")
       
       # Efficiency analysis
       theoretical_linear_speedup = n_processes
       single_core_time = processing_time * n_processes  # Rough estimate
       actual_speedup = single_core_time / processing_time if processing_time > 0 else 0
       efficiency = actual_speedup / theoretical_linear_speedup if theoretical_linear_speedup > 0 else 0
       
       print(f"\\nParallelization Efficiency:")
       print(f"  Theoretical speedup: {theoretical_linear_speedup:.1f}x")
       print(f"  Actual speedup: {actual_speedup:.1f}x")
       print(f"  Efficiency: {efficiency:.1%}")
       
       # Memory estimates
       memory_per_pixel_bytes = 4 * bands + 4 * 5  # Input + ~5 outputs
       total_memory_mb = (total_pixels * memory_per_pixel_bytes) / (1024 * 1024)
       
       print(f"\\nMemory Usage:")
       print(f"  Estimated peak memory: {total_memory_mb:.1f} MB")
       
       # Scaling predictions
       print(f"\\nScaling Predictions:")
       
       # Predict times for different image sizes
       test_sizes = [
           (500, 500, "Small scene"),
           (1000, 1000, "Medium scene"),
           (5000, 5000, "Large scene"),
           (10000, 10000, "Full Sentinel-2 scene")
       ]
       
       for test_h, test_w, description in test_sizes:
           test_pixels = test_h * test_w
           predicted_time = test_pixels * time_per_pixel_ms / 1000
           
           print(f"  {description} ({test_h}×{test_w}): {predicted_time/60:.1f} minutes")

Memory Usage Monitoring
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def monitor_memory_usage():
       """Monitor memory usage during processing."""
       
       try:
           import psutil
           import os
       except ImportError:
           print("psutil not available - install with: pip install psutil")
           return None
       
       process = psutil.Process(os.getpid())
       
       def get_memory_info():
           memory_info = process.memory_info()
           return {
               'rss_mb': memory_info.rss / (1024 * 1024),  # Resident Set Size
               'vms_mb': memory_info.vms / (1024 * 1024),  # Virtual Memory Size
               'percent': process.memory_percent()
           }
       
       print("Memory Usage Monitor")
       print("=" * 30)
       
       initial_memory = get_memory_info()
       print(f"Initial memory: {initial_memory['rss_mb']:.1f} MB ({initial_memory['percent']:.1f}%)")
       
       return get_memory_info

Best Practices
--------------

1. **Preprocessing**
   - Always perform quality control on input data
   - Remove clouds, land, and obviously invalid pixels
   - Consider atmospheric correction if not already applied

2. **Parameter Settings**
   - Use realistic parameter bounds for your study area
   - Consider adaptive bounds based on water type
   - Validate bounds with field data when possible

3. **Processing Optimization**
   - Test with small subsets first
   - Use appropriate chunk sizes for large images
   - Monitor memory usage and adjust accordingly

4. **Quality Control**
   - Always check processing success rates
   - Analyze error distributions
   - Validate against independent data

5. **Visualization**
   - Use appropriate color scales for each parameter
   - Include uncertainty/error information
   - Create publication-quality figures

Next Steps
----------

Now that you understand image processing:

🎛️ **For parameter optimization**: :doc:`configuration`  
🔬 **For theoretical background**: :doc:`../theory/algorithms`  
📊 **For real-world examples**: :doc:`../examples/advanced_examples`  
📈 **For validation techniques**: :doc:`../examples/tutorials`

**Practice Projects:**

1. **Process a real satellite scene** from your study area
2. **Compare different sensors** (Sentinel-2 vs Landsat) over the same area
3. **Analyze seasonal changes** by processing time series
4. **Validate results** against field measurements
5. **Optimize processing** for your specific use case

Advanced processing techniques, including time series analysis and multi-sensor fusion, can be found in :doc:`../examples/advanced_examples`.
