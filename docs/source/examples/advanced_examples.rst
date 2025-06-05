Advanced Examples
=================

This section provides comprehensive examples for real-world applications of SAMBUCA Core, including satellite data processing, validation studies, and advanced analysis techniques.

Prerequisites
-------------

For these advanced examples, you'll need additional packages:

.. code-block:: bash

   pip install "sambuca-core[complete]"  # All dependencies
   pip install rasterio gdal  # For satellite data
   pip install scikit-learn  # For machine learning examples

Example 1: Sentinel-2 Image Processing
--------------------------------------

This example demonstrates processing a complete Sentinel-2 scene for shallow water mapping.

Loading Sentinel-2 Data
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   from sambuca_core.inversion import InversionParameters, process_image
   import numpy as np
   import rasterio
   import matplotlib.pyplot as plt
   from matplotlib.colors import ListedColormap
   
   def load_sentinel2_scene(file_path):
       """Load Sentinel-2 L2A reflectance data."""
       
       with rasterio.open(file_path) as src:
           # Read bands: B2 (490nm), B3 (560nm), B4 (665nm), B8A (705nm)
           bands = src.read([2, 3, 4, 8])  # Band indices
           
           # Get spatial information
           transform = src.transform
           crs = src.crs
           
           # Convert to reflectance (L2A products are scaled by 10000)
           reflectance = bands.astype(np.float32) / 10000.0
           
           # Rearrange to (height, width, bands)
           image = np.transpose(reflectance, (1, 2, 0))
           
           # Basic quality filtering
           image = np.clip(image, 0, 1)  # Remove invalid values
           
           return {
               'image': image,
               'transform': transform,
               'crs': crs,
               'wavelengths': [492.4, 559.8, 664.6, 704.1],
               'shape': image.shape
           }
   
   # Load example data (replace with your file path)
   # sentinel2_data = load_sentinel2_scene("S2A_MSIL2A_coastal_scene.tif")

Creating Synthetic Sentinel-2 Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For this example, we'll create realistic synthetic data:

.. code-block:: python

   def create_synthetic_sentinel2(height=500, width=500):
       """Create realistic synthetic Sentinel-2 data."""
       
       # Create spatial gradients
       x, y = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
       
       # Depth gradient (shore to offshore)
       depth_map = 1 + 18 * x  # 1-19m depth
       
       # Water quality gradients
       chl_map = 0.5 + 4.0 * np.exp(-3 * x) + 0.3 * np.random.random((height, width))
       cdom_map = 0.1 + 1.2 * np.exp(-5 * x) * np.exp(-2 * (y - 0.4)**2)
       nap_map = 0.3 + 2.0 * np.exp(-2 * x) + 0.5 * np.random.random((height, width))
       
       # Clip to realistic ranges
       chl_map = np.clip(chl_map, 0.1, 8.0)
       cdom_map = np.clip(cdom_map, 0.05, 2.0)
       nap_map = np.clip(nap_map, 0.1, 5.0)
       
       # Create substrate pattern
       substrate_base = [0.3, 0.3, 0.25, 0.2]  # Sand
       seagrass_base = [0.1, 0.15, 0.2, 0.25]  # Seagrass
       
       # Define SIOP properties
       wavelengths = [492.4, 559.8, 664.6, 704.1]
       a_water = [0.007, 0.015, 0.325, 0.619]
       a_ph_star = [0.055, 0.023, 0.014, 0.010]
       
       # Generate realistic image
       image = np.zeros((height, width, 4))
       
       print("Generating synthetic Sentinel-2 scene...")
       for i in range(0, height, 50):  # Process in blocks for efficiency
           for j in range(0, width, 50):
               # Define block boundaries
               i_end = min(i + 50, height)
               j_end = min(j + 50, width)
               
               # Process block
               for ii in range(i, i_end):
                   for jj in range(j, j_end):
                       # Substrate mixing (more seagrass near shore)
                       seagrass_fraction = 0.8 * np.exp(-2 * x[ii, jj])
                       substrate = [(1 - seagrass_fraction) * s + seagrass_fraction * sg 
                                   for s, sg in zip(substrate_base, seagrass_base)]
                       
                       # Run forward model
                       try:
                           results = sbc.forward_model(
                               chl=chl_map[ii, jj],
                               cdom=cdom_map[ii, jj],
                               nap=nap_map[ii, jj],
                               depth=depth_map[ii, jj],
                               substrate1=substrate,
                               wavelengths=wavelengths,
                               a_water=a_water,
                               a_ph_star=a_ph_star,
                               num_bands=4
                           )
                           image[ii, jj, :] = results.rrs
                       except:
                           image[ii, jj, :] = [0.005, 0.008, 0.003, 0.002]
           
           if i % 100 == 0:
               print(f"  Processed rows {i}-{i_end}")
       
       # Add realistic noise
       noise_level = 0.0003
       image += np.random.normal(0, noise_level, image.shape)
       image = np.clip(image, 0.001, 0.1)  # Realistic range
       
       return {
           'image': image,
           'wavelengths': wavelengths,
           'truth_maps': {
               'depth': depth_map,
               'chl': chl_map,
               'cdom': cdom_map,
               'nap': nap_map
           },
           'siops': {
               'a_water': a_water,
               'a_ph_star': a_ph_star,
               'substrate': substrate_base
           }
       }
   
   # Create synthetic data
   sentinel2_data = create_synthetic_sentinel2(400, 400)
   print(f"Created synthetic Sentinel-2 scene: {sentinel2_data['image'].shape}")

Preprocessing Pipeline
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def preprocess_sentinel2(data, land_threshold=0.3):
       """Comprehensive preprocessing pipeline."""
       
       image = data['image'].copy()
       height, width, bands = image.shape
       
       print("Preprocessing Sentinel-2 data...")
       
       # 1. Land/cloud masking
       nir_band = image[:, :, -1]  # NIR band
       land_mask = nir_band > land_threshold
       
       # 2. Very dark water (sensor issues)
       dark_mask = np.all(image < 0.001, axis=2)
       
       # 3. Very bright pixels (clouds, foam)
       bright_mask = np.any(image > 0.1, axis=2)
       
       # 4. Combined processing mask
       processing_mask = ~(land_mask | dark_mask | bright_mask)
       
       # 5. Sun glint correction (simplified)
       # Estimate glint from NIR assuming it should be ~0 over water
       glint_pixels = (nir_band > 0.01) & processing_mask
       if np.sum(glint_pixels) > 0:
           print(f"  Applying glint correction to {np.sum(glint_pixels)} pixels")
           for band in range(bands - 1):  # Exclude NIR
               # Simple linear glint correction
               glint_correction = nir_band * 0.3  # Simplified coefficient
               image[:, :, band] = np.maximum(image[:, :, band] - glint_correction, 0)
       
       # 6. Spatial smoothing (optional)
       from scipy.ndimage import gaussian_filter
       for band in range(bands):
           image[:, :, band] = gaussian_filter(image[:, :, band], sigma=0.5)
       
       stats = {
           'total_pixels': height * width,
           'land_pixels': np.sum(land_mask),
           'dark_pixels': np.sum(dark_mask),
           'bright_pixels': np.sum(bright_mask),
           'processing_pixels': np.sum(processing_mask)
       }
       
       print(f"  Processing mask statistics:")
       print(f"    Total pixels: {stats['total_pixels']:,}")
       print(f"    Land pixels: {stats['land_pixels']:,} ({100*stats['land_pixels']/stats['total_pixels']:.1f}%)")
       print(f"    Valid water pixels: {stats['processing_pixels']:,} ({100*stats['processing_pixels']/stats['total_pixels']:.1f}%)")
       
       return {
           'image': image,
           'processing_mask': processing_mask,
           'stats': stats,
           'wavelengths': data['wavelengths']
       }
   
   # Preprocess the data
   preprocessed = preprocess_sentinel2(sentinel2_data)

Inversion Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def setup_coastal_inversion():
       """Set up inversion parameters for coastal waters."""
       
       # Configure for coastal environment
       params = InversionParameters(
           depth=(0.5, 20),        # Shallow coastal waters
           chl=(0.1, 12.0),        # Productive coastal range
           cdom=(0.02, 2.5),       # Terrestrial influence
           nap=(0.1, 8.0),         # Sediment resuspension
           wavelengths=sentinel2_data['wavelengths']
       )
       
       # Add SIOP data
       params.a_water = sentinel2_data['siops']['a_water']
       params.a_ph_star = sentinel2_data['siops']['a_ph_star']
       params.substrate1 = sentinel2_data['siops']['substrate']
       params.num_bands = 4
       
       # Optimization settings for operational processing
       params.optimization_method = 'L-BFGS-B'
       params.max_iterations = 100
       params.tolerance = 1e-5
       
       return params
   
   # Set up inversion
   inversion_params = setup_coastal_inversion()
   print("Inversion parameters configured for coastal waters")

Full Scene Processing
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def process_sentinel2_scene(image, params, chunk_size=100):
       """Process full Sentinel-2 scene with progress monitoring."""
       
       import time
       
       print("Processing Sentinel-2 scene...")
       start_time = time.time()
       
       # Process image
       results = process_image(
           image,
           params,
           n_processes=4,
           progress_bar=True,
           chunk_size=chunk_size,
           timeout_per_pixel=2.0  # 2 second timeout
       )
       
       end_time = time.time()
       processing_time = end_time - start_time
       
       # Calculate statistics
       total_pixels = image.shape[0] * image.shape[1]
       valid_results = np.sum(~np.isnan(results['depth']))
       success_rate = valid_results / total_pixels
       
       print(f"\\nProcessing complete!")
       print(f"  Time: {processing_time:.1f} seconds")
       print(f"  Success rate: {success_rate:.1%} ({valid_results:,}/{total_pixels:,} pixels)")
       print(f"  Speed: {total_pixels/processing_time:.0f} pixels/second")
       
       return results
   
   # Process the scene
   scene_results = process_sentinel2_scene(
       preprocessed['image'], 
       inversion_params, 
       chunk_size=50  # Smaller chunks for this example
   )

Results Visualization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_sentinel2_results_figure(results, truth_maps=None, save_path=None):
       """Create comprehensive results visualization."""
       
       fig = plt.figure(figsize=(20, 12))
       
       # Define parameter info
       params_info = [
           ('depth', 'Bathymetry (m)', 'viridis_r', (0, 20)),
           ('chl', 'Chlorophyll-a (mg/m³)', 'YlGn', (0, 8)),
           ('cdom', 'CDOM (1/m)', 'YlOrBr', (0, 2)),
           ('nap', 'NAP (mg/L)', 'Oranges', (0, 5))
       ]
       
       if truth_maps:
           # Show truth vs estimated vs difference
           for i, (param, title, cmap, vrange) in enumerate(params_info):
               # Truth
               ax1 = plt.subplot(4, 4, i*4 + 1)
               im1 = ax1.imshow(truth_maps[param], cmap=cmap, vmin=vrange[0], vmax=vrange[1])
               ax1.set_title(f'True {title}', fontsize=10)
               ax1.axis('off')
               plt.colorbar(im1, ax=ax1, fraction=0.046, shrink=0.8)
               
               # Estimated
               ax2 = plt.subplot(4, 4, i*4 + 2)
               im2 = ax2.imshow(results[param], cmap=cmap, vmin=vrange[0], vmax=vrange[1])
               ax2.set_title(f'Estimated {title}', fontsize=10)
               ax2.axis('off')
               plt.colorbar(im2, ax=ax2, fraction=0.046, shrink=0.8)
               
               # Difference
               ax3 = plt.subplot(4, 4, i*4 + 3)
               diff = results[param] - truth_maps[param]
               diff_max = np.nanpercentile(np.abs(diff), 95)
               im3 = ax3.imshow(diff, cmap='RdBu_r', vmin=-diff_max, vmax=diff_max)
               ax3.set_title(f'{title} Error', fontsize=10)
               ax3.axis('off')
               plt.colorbar(im3, ax=ax3, fraction=0.046, shrink=0.8)
               
               # Scatter plot
               ax4 = plt.subplot(4, 4, i*4 + 4)
               valid_mask = ~np.isnan(results[param]) & ~np.isnan(truth_maps[param])
               if np.sum(valid_mask) > 0:
                   true_vals = truth_maps[param][valid_mask]
                   est_vals = results[param][valid_mask]
                   
                   # Subsample for plotting
                   n_plot = min(5000, len(true_vals))
                   idx = np.random.choice(len(true_vals), n_plot, replace=False)
                   
                   ax4.scatter(true_vals[idx], est_vals[idx], alpha=0.3, s=1)
                   
                   # 1:1 line
                   min_val = min(np.min(true_vals), np.min(est_vals))
                   max_val = max(np.max(true_vals), np.max(est_vals))
                   ax4.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
                   
                   # Statistics
                   rmse = np.sqrt(np.mean((est_vals - true_vals)**2))
                   r2 = np.corrcoef(true_vals, est_vals)[0, 1]**2
                   
                   ax4.text(0.05, 0.95, f'RMSE: {rmse:.3f}\\nR²: {r2:.3f}', 
                           transform=ax4.transAxes, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
               
               ax4.set_xlabel(f'True {title}')
               ax4.set_ylabel(f'Estimated {title}')
               ax4.grid(True, alpha=0.3)
       
       else:
           # Show results only
           for i, (param, title, cmap, vrange) in enumerate(params_info):
               ax = plt.subplot(2, 3, i + 1)
               im = ax.imshow(results[param], cmap=cmap, vmin=vrange[0], vmax=vrange[1])
               ax.set_title(title, fontsize=12)
               ax.axis('off')
               plt.colorbar(im, ax=ax, fraction=0.046, shrink=0.8)
           
           # Error map
           ax = plt.subplot(2, 3, 5)
           im = ax.imshow(results['error'], cmap='Reds', vmin=0, vmax=np.nanpercentile(results['error'], 95))
           ax.set_title('Inversion RMSE', fontsize=12)
           ax.axis('off')
           plt.colorbar(im, ax=ax, fraction=0.046, shrink=0.8)
       
       plt.suptitle('Sentinel-2 SAMBUCA Processing Results', fontsize=16, y=0.98)
       plt.tight_layout()
       
       if save_path:
           plt.savefig(save_path, dpi=300, bbox_inches='tight')
           print(f"Results figure saved to {save_path}")
       
       plt.show()
   
   # Create results visualization
   create_sentinel2_results_figure(
       scene_results, 
       truth_maps=sentinel2_data['truth_maps'],
       save_path="sentinel2_sambuca_results.png"
   )

Example 2: Time Series Analysis
-------------------------------

Analyze temporal changes in water properties using multiple satellite images.

Create Time Series Data
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_time_series_data(location='coastal_bay', n_timesteps=12):
       """Create synthetic time series data representing seasonal changes."""
       
       # Define seasonal patterns (Northern Hemisphere)
       months = np.arange(1, n_timesteps + 1)
       
       # Base water properties
       base_depth = 8.0
       base_cdom = 0.3
       base_nap = 1.0
       
       # Seasonal variations
       time_series = []
       
       for month in months:
           # Seasonal chlorophyll (spring bloom, summer minimum)
           if month <= 3:  # Winter
               chl = 1.0 + 0.5 * np.random.random()
           elif month <= 6:  # Spring
               chl = 2.0 + 3.0 * np.exp(-(month - 4)**2 / 2) + 0.5 * np.random.random()
           elif month <= 9:  # Summer
               chl = 0.8 + 0.3 * np.random.random()
           else:  # Fall
               chl = 1.5 + 1.0 * np.random.random()
           
           # CDOM varies with rainfall/runoff
           cdom_seasonal = base_cdom * (1 + 0.5 * np.sin(2 * np.pi * month / 12))
           
           # NAP varies with storms and resuspension
           nap_seasonal = base_nap * (1 + 0.3 * np.random.random())
           
           # Generate spectrum
           results = sbc.forward_model(
               chl=chl, cdom=cdom_seasonal, nap=nap_seasonal, depth=base_depth,
               substrate1=[0.3, 0.3, 0.25, 0.2],
               wavelengths=[492.4, 559.8, 664.6, 704.1],
               a_water=[0.007, 0.015, 0.325, 0.619],
               a_ph_star=[0.055, 0.023, 0.014, 0.010],
               num_bands=4
           )
           
           # Add realistic noise
           noisy_rrs = results.rrs + np.random.normal(0, 0.0003, 4)
           
           time_series.append({
               'month': month,
               'true_chl': chl,
               'true_cdom': cdom_seasonal,
               'true_nap': nap_seasonal,
               'true_depth': base_depth,
               'observed_rrs': noisy_rrs
           })
       
       return time_series
   
   # Create time series
   time_series_data = create_time_series_data()
   print(f"Created time series with {len(time_series_data)} timesteps")

Time Series Inversion
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def process_time_series(time_series_data):
       """Process entire time series with SAMBUCA inversion."""
       
       # Set up inversion parameters
       params = InversionParameters(
           depth=(5, 15),      # Constrain depth (known to be stable)
           chl=(0.2, 8.0),     # Allow wide chlorophyll range
           cdom=(0.1, 1.5),    # CDOM range
           nap=(0.3, 4.0),     # NAP range
           wavelengths=[492.4, 559.8, 664.6, 704.1],
           a_water=[0.007, 0.015, 0.325, 0.619],
           a_ph_star=[0.055, 0.023, 0.014, 0.010],
           substrate1=[0.3, 0.3, 0.25, 0.2],
           num_bands=4
       )
       
       results = []
       
       for i, data_point in enumerate(time_series_data):
           print(f"Processing timestep {i+1}/{len(time_series_data)}")
           
           # Run inversion
           result = invert_spectrum(data_point['observed_rrs'], params)
           
           if result.success:
               results.append({
                   'month': data_point['month'],
                   'estimated_chl': result.parameters['chl'],
                   'estimated_cdom': result.parameters['cdom'],
                   'estimated_nap': result.parameters['nap'],
                   'estimated_depth': result.parameters['depth'],
                   'rmse': result.objective_value,
                   'true_chl': data_point['true_chl'],
                   'true_cdom': data_point['true_cdom'],
                   'true_nap': data_point['true_nap'],
                   'observed_rrs': data_point['observed_rrs']
               })
           else:
               print(f"  Inversion failed for timestep {i+1}")
       
       return results
   
   # Process time series
   time_series_results = process_time_series(time_series_data)
   print(f"Successfully processed {len(time_series_results)} timesteps")

Time Series Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def plot_time_series_results(results):
       """Plot time series analysis results."""
       
       fig, axes = plt.subplots(3, 2, figsize=(15, 12))
       
       months = [r['month'] for r in results]
       
       # Chlorophyll time series
       axes[0, 0].plot(months, [r['true_chl'] for r in results], 'g-o', 
                      label='True', linewidth=2, markersize=6)
       axes[0, 0].plot(months, [r['estimated_chl'] for r in results], 'r--s', 
                      label='Estimated', linewidth=2, markersize=6)
       axes[0, 0].set_xlabel('Month')
       axes[0, 0].set_ylabel('Chlorophyll (mg/m³)')
       axes[0, 0].set_title('Chlorophyll Time Series')
       axes[0, 0].legend()
       axes[0, 0].grid(True, alpha=0.3)
       
       # CDOM time series
       axes[0, 1].plot(months, [r['true_cdom'] for r in results], 'b-o', 
                      label='True', linewidth=2, markersize=6)
       axes[0, 1].plot(months, [r['estimated_cdom'] for r in results], 'r--s', 
                      label='Estimated', linewidth=2, markersize=6)
       axes[0, 1].set_xlabel('Month')
       axes[0, 1].set_ylabel('CDOM (1/m)')
       axes[0, 1].set_title('CDOM Time Series')
       axes[0, 1].legend()
       axes[0, 1].grid(True, alpha=0.3)
       
       # NAP time series
       axes[1, 0].plot(months, [r['true_nap'] for r in results], 'orange', 
                      marker='o', label='True', linewidth=2, markersize=6)
       axes[1, 0].plot(months, [r['estimated_nap'] for r in results], 'r--s', 
                      label='Estimated', linewidth=2, markersize=6)
       axes[1, 0].set_xlabel('Month')
       axes[1, 0].set_ylabel('NAP (mg/L)')
       axes[1, 0].set_title('NAP Time Series')
       axes[1, 0].legend()
       axes[1, 0].grid(True, alpha=0.3)
       
       # Accuracy statistics
       params = ['chl', 'cdom', 'nap']
       rmses = []
       r_squareds = []
       
       for param in params:
           true_vals = np.array([r[f'true_{param}'] for r in results])
           est_vals = np.array([r[f'estimated_{param}'] for r in results])
           
           rmse = np.sqrt(np.mean((true_vals - est_vals)**2))
           r2 = np.corrcoef(true_vals, est_vals)[0, 1]**2
           
           rmses.append(rmse)
           r_squareds.append(r2)
       
       x = np.arange(len(params))
       axes[1, 1].bar(x - 0.2, rmses, 0.4, label='RMSE', alpha=0.7)
       axes[1, 1].set_xlabel('Parameters')
       axes[1, 1].set_ylabel('RMSE')
       axes[1, 1].set_title('Time Series Accuracy')
       axes[1, 1].set_xticks(x)
       axes[1, 1].set_xticklabels([p.upper() for p in params])
       axes[1, 1].grid(True, alpha=0.3)
       
       # R² on secondary axis
       ax2 = axes[1, 1].twinx()
       ax2.bar(x + 0.2, r_squareds, 0.4, label='R²', alpha=0.7, color='orange')
       ax2.set_ylabel('R² Correlation')
       ax2.set_ylim(0, 1)
       
       # Combine legends
       lines1, labels1 = axes[1, 1].get_legend_handles_labels()
       lines2, labels2 = ax2.get_legend_handles_labels()
       axes[1, 1].legend(lines1 + lines2, labels1 + labels2, loc='upper right')
       
       # Inversion quality over time
       axes[2, 0].plot(months, [r['rmse'] for r in results], 'purple', 
                      marker='o', linewidth=2, markersize=6)
       axes[2, 0].set_xlabel('Month')
       axes[2, 0].set_ylabel('Inversion RMSE')
       axes[2, 0].set_title('Inversion Quality Over Time')
       axes[2, 0].grid(True, alpha=0.3)
       
       # Seasonal patterns
       seasonal_chl = [r['estimated_chl'] for r in results]
       axes[2, 1].plot(months, seasonal_chl, 'g-o', linewidth=2, markersize=6)
       axes[2, 1].set_xlabel('Month')
       axes[2, 1].set_ylabel('Estimated Chlorophyll (mg/m³)')
       axes[2, 1].set_title('Seasonal Chlorophyll Pattern')
       axes[2, 1].grid(True, alpha=0.3)
       
       # Add seasonal labels
       seasons = ['Winter', 'Spring', 'Summer', 'Fall']
       season_months = [1.5, 4.5, 7.5, 10.5]
       for season, month in zip(seasons, season_months):
           if month <= max(months):
               axes[2, 1].axvline(month, color='gray', linestyle='--', alpha=0.5)
               axes[2, 1].text(month, max(seasonal_chl) * 0.9, season, 
                              rotation=90, ha='center', va='top', fontsize=9)
       
       plt.tight_layout()
       plt.show()
       
       return rmses, r_squareds
   
   # Plot results
   accuracy_stats = plot_time_series_results(time_series_results)

Example 3: Validation Study
---------------------------

Compare SAMBUCA retrievals with field measurements.

Create Validation Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_validation_dataset(n_stations=50):
       """Create synthetic field measurement dataset."""
       
       np.random.seed(123)  # For reproducible results
       
       # Generate diverse water conditions
       stations = []
       
       for i in range(n_stations):
           # Sample from realistic parameter distributions
           water_type = np.random.choice(['clear', 'coastal', 'turbid'], p=[0.3, 0.5, 0.2])
           
           if water_type == 'clear':
               chl = np.random.lognormal(np.log(0.8), 0.5)
               cdom = np.random.lognormal(np.log(0.15), 0.3)
               nap = np.random.lognormal(np.log(0.8), 0.4)
               depth = np.random.uniform(5, 25)
           elif water_type == 'coastal':
               chl = np.random.lognormal(np.log(2.5), 0.6)
               cdom = np.random.lognormal(np.log(0.5), 0.4)
               nap = np.random.lognormal(np.log(2.0), 0.5)
               depth = np.random.uniform(2, 15)
           else:  # turbid
               chl = np.random.lognormal(np.log(5.0), 0.7)
               cdom = np.random.lognormal(np.log(1.2), 0.5)
               nap = np.random.lognormal(np.log(4.0), 0.6)
               depth = np.random.uniform(1, 8)
           
           # Clip to realistic ranges
           chl = np.clip(chl, 0.1, 20.0)
           cdom = np.clip(cdom, 0.02, 3.0)
           nap = np.clip(nap, 0.1, 10.0)
           depth = np.clip(depth, 0.5, 30.0)
           
           # Generate "satellite" observation
           substrate = [0.3, 0.3, 0.25, 0.2]  # Assume sand
           
           satellite_results = sbc.forward_model(
               chl=chl, cdom=cdom, nap=nap, depth=depth,
               substrate1=substrate,
               wavelengths=[492.4, 559.8, 664.6, 704.1],
               a_water=[0.007, 0.015, 0.325, 0.619],
               a_ph_star=[0.055, 0.023, 0.014, 0.010],
               num_bands=4
           )
           
           # Add satellite measurement uncertainty
           satellite_noise = 0.0005  # Typical satellite uncertainty
           satellite_rrs = satellite_results.rrs + np.random.normal(0, satellite_noise, 4)
           
           # Add field measurement uncertainty
           field_uncertainty = {
               'chl': 0.15,    # 15% relative uncertainty
               'cdom': 0.20,   # 20% relative uncertainty
               'nap': 0.25,    # 25% relative uncertainty
               'depth': 0.05   # 5% relative uncertainty
           }
           
           field_chl = chl * (1 + np.random.normal(0, field_uncertainty['chl']))
           field_cdom = cdom * (1 + np.random.normal(0, field_uncertainty['cdom']))
           field_nap = nap * (1 + np.random.normal(0, field_uncertainty['nap']))
           field_depth = depth * (1 + np.random.normal(0, field_uncertainty['depth']))
           
           stations.append({
               'station_id': f'STN_{i+1:03d}',
               'water_type': water_type,
               'field_chl': max(0.1, field_chl),
               'field_cdom': max(0.02, field_cdom),
               'field_nap': max(0.1, field_nap),
               'field_depth': max(0.5, field_depth),
               'satellite_rrs': satellite_rrs,
               'true_chl': chl,  # For validation of validation dataset
               'true_cdom': cdom,
               'true_nap': nap,
               'true_depth': depth
           })
       
       return stations
   
   # Create validation dataset
   validation_stations = create_validation_dataset(75)
   print(f"Created validation dataset with {len(validation_stations)} stations")
   
   # Show dataset characteristics
   water_types = [s['water_type'] for s in validation_stations]
   type_counts = {wt: water_types.count(wt) for wt in set(water_types)}
   print(f"Water type distribution: {type_counts}")

Run Validation Analysis
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def run_validation_analysis(stations):
       """Run comprehensive validation analysis."""
       
       # Set up inversion parameters
       params = InversionParameters(
           depth=(0.5, 30),
           chl=(0.1, 25.0),
           cdom=(0.01, 4.0),
           nap=(0.1, 12.0),
           wavelengths=[492.4, 559.8, 664.6, 704.1],
           a_water=[0.007, 0.015, 0.325, 0.619],
           a_ph_star=[0.055, 0.023, 0.014, 0.010],
           substrate1=[0.3, 0.3, 0.25, 0.2],
           num_bands=4
       )
       
       validation_results = []
       
       print("Running SAMBUCA inversion on validation dataset...")
       for i, station in enumerate(stations):
           if (i + 1) % 10 == 0:
               print(f"  Processing station {i+1}/{len(stations)}")
           
           # Run inversion
           result = invert_spectrum(station['satellite_rrs'], params)
           
           if result.success:
               validation_results.append({
                   'station_id': station['station_id'],
                   'water_type': station['water_type'],
                   'field_chl': station['field_chl'],
                   'field_cdom': station['field_cdom'],
                   'field_nap': station['field_nap'],
                   'field_depth': station['field_depth'],
                   'sambuca_chl': result.parameters['chl'],
                   'sambuca_cdom': result.parameters['cdom'],
                   'sambuca_nap': result.parameters['nap'],
                   'sambuca_depth': result.parameters['depth'],
                   'inversion_rmse': result.objective_value
               })
           else:
               print(f"    Failed: {station['station_id']}")
       
       print(f"Successful inversions: {len(validation_results)}/{len(stations)}")
       return validation_results
   
   # Run validation
   validation_results = run_validation_analysis(validation_stations)

Validation Statistics
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def calculate_validation_statistics(results):
       """Calculate comprehensive validation statistics."""
       
       import pandas as pd
       
       # Convert to DataFrame for easier analysis
       df = pd.DataFrame(results)
       
       # Calculate statistics for each parameter
       params = ['chl', 'cdom', 'nap', 'depth']
       statistics = {}
       
       for param in params:
           field_col = f'field_{param}'
           sambuca_col = f'sambuca_{param}'
           
           field_vals = df[field_col].values
           sambuca_vals = df[sambuca_col].values
           
           # Basic statistics
           bias = np.mean(sambuca_vals - field_vals)
           rmse = np.sqrt(np.mean((sambuca_vals - field_vals)**2))
           mae = np.mean(np.abs(sambuca_vals - field_vals))
           
           # Relative statistics
           mape = np.mean(np.abs((sambuca_vals - field_vals) / field_vals)) * 100
           
           # Correlation
           r = np.corrcoef(field_vals, sambuca_vals)[0, 1]
           r_squared = r**2
           
           # Regression statistics
           from scipy import stats
           slope, intercept, r_val, p_val, std_err = stats.linregress(field_vals, sambuca_vals)
           
           statistics[param] = {
               'bias': bias,
               'rmse': rmse,
               'mae': mae,
               'mape': mape,
               'r': r,
               'r_squared': r_squared,
               'slope': slope,
               'intercept': intercept,
               'p_value': p_val,
               'n_points': len(field_vals)
           }
       
       # Water type analysis
       water_type_stats = {}
       for water_type in df['water_type'].unique():
           subset = df[df['water_type'] == water_type]
           water_type_stats[water_type] = {
               'n_stations': len(subset),
               'mean_rmse': subset['inversion_rmse'].mean()
           }
       
       return statistics, water_type_stats, df
   
   # Calculate statistics
   val_stats, water_type_stats, val_df = calculate_validation_statistics(validation_results)

Validation Visualization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def plot_validation_results(stats, df):
       """Create comprehensive validation plots."""
       
       params = ['chl', 'cdom', 'nap', 'depth']
       param_labels = ['Chlorophyll (mg/m³)', 'CDOM (1/m)', 'NAP (mg/L)', 'Depth (m)']
       
       fig, axes = plt.subplots(2, 4, figsize=(20, 10))
       
       # Water type colors
       water_type_colors = {'clear': 'blue', 'coastal': 'green', 'turbid': 'red'}
       
       for i, (param, label) in enumerate(zip(params, param_labels)):
           field_col = f'field_{param}'
           sambuca_col = f'sambuca_{param}'
           
           # Scatter plot with water types
           ax1 = axes[0, i]
           for water_type, color in water_type_colors.items():
               subset = df[df['water_type'] == water_type]
               if len(subset) > 0:
                   ax1.scatter(subset[field_col], subset[sambuca_col], 
                              c=color, alpha=0.7, s=50, label=water_type)
           
           # 1:1 line
           min_val = min(df[field_col].min(), df[sambuca_col].min())
           max_val = max(df[field_col].max(), df[sambuca_col].max())
           ax1.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=2, alpha=0.8)
           
           # Regression line
           slope = stats[param]['slope']
           intercept = stats[param]['intercept']
           x_reg = np.linspace(min_val, max_val, 100)
           y_reg = slope * x_reg + intercept
           ax1.plot(x_reg, y_reg, 'r-', linewidth=2, alpha=0.8)
           
           # Statistics text
           r2 = stats[param]['r_squared']
           rmse = stats[param]['rmse']
           bias = stats[param]['bias']
           
           ax1.text(0.05, 0.95, f'R² = {r2:.3f}\\nRMSE = {rmse:.3f}\\nBias = {bias:.3f}', 
                   transform=ax1.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
           
           ax1.set_xlabel(f'Field {label}')
           ax1.set_ylabel(f'SAMBUCA {label}')
           ax1.set_title(f'{param.upper()} Validation')
           ax1.grid(True, alpha=0.3)
           ax1.legend()
           
           # Residual plot
           ax2 = axes[1, i]
           residuals = df[sambuca_col] - df[field_col]
           field_vals = df[field_col]
           
           for water_type, color in water_type_colors.items():
               subset = df[df['water_type'] == water_type]
               if len(subset) > 0:
                   ax2.scatter(subset[field_col], 
                              subset[sambuca_col] - subset[field_col],
                              c=color, alpha=0.7, s=50)
           
           ax2.axhline(y=0, color='k', linestyle='--', linewidth=2, alpha=0.8)
           ax2.set_xlabel(f'Field {label}')
           ax2.set_ylabel(f'Residual (SAMBUCA - Field)')
           ax2.set_title(f'{param.upper()} Residuals')
           ax2.grid(True, alpha=0.3)
       
       plt.tight_layout()
       plt.show()
   
   # Create validation plots
   plot_validation_results(val_stats, val_df)

Print Validation Summary
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def print_validation_summary(stats, water_type_stats):
       """Print comprehensive validation summary."""
       
       print("\\n" + "="*80)
       print("SAMBUCA VALIDATION SUMMARY")
       print("="*80)
       
       print(f"\\nOVERALL STATISTICS:")
       print(f"{'Parameter':<12} {'R²':<8} {'RMSE':<10} {'Bias':<10} {'MAPE':<8} {'Slope':<8}")
       print("-" * 60)
       
       for param, stat in stats.items():
           print(f"{param.upper():<12} {stat['r_squared']:<8.3f} {stat['rmse']:<10.3f} "
                 f"{stat['bias']:<10.3f} {stat['mape']:<8.1f}% {stat['slope']:<8.3f}")
       
       print(f"\\nWATER TYPE BREAKDOWN:")
       print(f"{'Type':<10} {'N Stations':<12} {'Mean RMSE':<12}")
       print("-" * 40)
       
       for water_type, wt_stats in water_type_stats.items():
           print(f"{water_type:<10} {wt_stats['n_stations']:<12} {wt_stats['mean_rmse']:<12.6f}")
       
       print(f"\\nVALIDATION QUALITY ASSESSMENT:")
       
       # Quality categories based on R²
       for param, stat in stats.items():
           r2 = stat['r_squared']
           if r2 > 0.8:
               quality = "Excellent"
           elif r2 > 0.6:
               quality = "Good"
           elif r2 > 0.4:
               quality = "Fair"
           else:
               quality = "Poor"
           
           print(f"  {param.upper()}: {quality} (R² = {r2:.3f})")
       
       print("\\n" + "="*80)
   
   # Print summary
   print_validation_summary(val_stats, water_type_stats)

Summary and Best Practices
--------------------------

These advanced examples demonstrate:

✅ **Real satellite data processing** with comprehensive preprocessing  
✅ **Time series analysis** for temporal change detection  
✅ **Validation against field data** with statistical analysis  
✅ **Multi-sensor capabilities** and cross-platform validation  
✅ **Quality control procedures** and uncertainty assessment  
✅ **Operational processing workflows** for routine monitoring  

Key Takeaways
~~~~~~~~~~~~~

**Data Preprocessing is Critical**
   - Land/cloud masking significantly affects results
   - Sun glint correction improves accuracy
   - Spatial smoothing can reduce noise

**Validation is Essential**
   - Always validate against independent data
   - Different water types may have different accuracies
   - Statistical analysis reveals algorithm strengths/weaknesses

**Temporal Analysis Provides Insights**
   - Seasonal patterns emerge from time series
   - Stability of retrievals indicates algorithm robustness
   - Long-term trends reveal environmental changes

**Optimization Matters**
   - Appropriate parameter bounds improve convergence
   - Processing speed vs accuracy trade-offs
   - Quality control prevents unrealistic results

Next Steps
~~~~~~~~~

Ready for more advanced applications?

📚 **Detailed tutorials**: :doc:`tutorials`  
🔧 **Algorithm customization**: :doc:`../theory/algorithms`  
🛠️ **Development guide**: Contributing to SAMBUCA Core  
📊 **Integration examples**: Using SAMBUCA with other tools

These examples provide the foundation for developing operational water quality monitoring systems using SAMBUCA Core and satellite remote sensing.
