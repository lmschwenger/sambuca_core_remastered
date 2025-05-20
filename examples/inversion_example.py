import os
import warnings

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import time
from datetime import datetime

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, LookUpTable, process_image
from sambuca_core.utility.plotting import plot_inversion_results

warnings.filterwarnings('ignore', category=RuntimeWarning)

# Add the new imports for NEDR support
from sambuca_core.inversion.objective_functions import spectral_rmse_with_nedr

# Define paths
input_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'anholt_20170823_b02b09_clipped2.tif')
siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
output_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', f"sdb_nedr_{os.path.basename(input_)}")
mask_input = os.path.join(os.path.dirname(input_), 'S2_L2A_20180508_B01-B05_ndwi_clipped2.tif')
sensor_filter_input = os.path.join(os.path.dirname(input_), '..', 'sensor_filters', 'sensor_filters.csv')
# Define the path to your NEDR CSV file
nedr_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'nedr', 's2testc.csv')

# Load NEDR values from CSV
nedr_df = pd.read_csv(nedr_csv)

# Load the L2A image
with rasterio.open(input_) as src:
    # Read all bands
    image_int16 = src.read()
    metadata = src.meta

    # For Sentinel-2 L2A products, the scaling factor is typically 10_000
    # (Check your specific product documentation to confirm)
    if metadata['dtype'] == 'float32':
        scaling_factor = 1.0
    else:
        scaling_factor = 10000.0
    print(f"{scaling_factor = }")
    # Convert INT16 to surface reflectance (dimensionless, 0-1)
    surface_reflectance = image_int16.astype(np.float32) / scaling_factor

    # Handle no-data values (typically 0 or negative values)
    # Set them to NaN for proper handling later
    no_data_mask = (image_int16 <= 0)
    surface_reflectance[no_data_mask] = np.nan
    rrs = surface_reflectance / np.pi
    rrs[rrs < 0] = 0
    rrs_image = np.transpose(rrs, (1, 2, 0))[..., :4]
 #   rrs_image = (2 * rrs_image) / ((3 * rrs_image) + 1)

# Step 2: Set up the sensor information and mask
if mask_input is not None and mask_input != '':
    with rasterio.open(mask_input) as src:
        mask_image = src.read()
        data_mask = (mask_image[2, ...] > 0.75)
else:
    data_mask = np.ones_like(rrs_image[..., 0], dtype=bool)

siop_manager = sbc.SIOPManager(siop_dir)

sentinel2_wavelengths = {
    "B1": 442.7,  # Coastal aerosol
    "B2": 492.4,  # Blue
    "B3": 559.8,  # Green
    "B4": 664.6,  # Red
    "B5": 704.1,  # Vegetation red edge
    "B6": 740.5,  # Vegetation red edge
    "B7": 782.8,  # Vegetation red edge
    "B8": 832.8,  # NIR
    "B8A": 864.7,  # Narrow NIR
    "B9": 945.1,  # Water vapour
    "B10": 1373.5,  # SWIR - Cirrus
    "B11": 1613.7,  # SWIR
    "B12": 2202.4  # SWIR
}

bands_used = ["B2", "B3", "B4", "B5"]
wavelengths_used = [sentinel2_wavelengths[w] for w in bands_used]

# Register the sensors you work with
siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)

# Create inversion parameters for a specific sensor
params = InversionParameters(
    # Parameters to invert for
    depth=(0.1, 10.0),
   # chl=(0.5, 3),
 #   cdom=(0.0005, 0.01),
 #   nap=(0.01, 0.5)
)

# Load SIOPs for this sensor
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# Step 3: Add NEDR values to the inversion parameters
# Extract NEDR values in the same order as the wavelengths
nedr_values = []
for wl in wavelengths_used:
    # Round to closest integer for comparison, since CSV might have slightly different values
    closest_wl = nedr_df['wl'].iloc[(nedr_df['wl'] - wl).abs().argsort()[0]]
    nedr_value = nedr_df.loc[nedr_df['wl'] == closest_wl, 'rrs'].values[0]
    nedr_values.append(nedr_value)

# Convert to array and add to parameters
nedr_values = np.array(nedr_values)

# Now set NEDR values
params.set_nedr(nedr_values)

# Print inversion settings
print("\n" + "="*50)
print("INVERSION SETTINGS:")
print("="*50)
print(f"Wavelengths: {wavelengths_used} nm")
print(f"Parameters to invert: {params.get_inversion_parameter_names()}")
print(f"Depth range: {params.depth}")
print(f"Chlorophyll range: {params.chl}")
if hasattr(params, 'cdom') and params.cdom is not None:
    print(f"CDOM range: {params.cdom}")
if hasattr(params, 'nap') and params.nap is not None:
    print(f"NAP range: {params.nap}")
print(f"Number of processes: 4")
print(f"Number of starts: 10")
print(f"Using NEDR weighting: Yes")
print(f"NEDR values: {nedr_values}")
print("="*50)

# Create output directory for plots
output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', 'plots')
os.makedirs(output_dir, exist_ok=True)

# Record start time
start_time = time.time()
print(f"\nProcessing image with NEDR weighting... Started at {datetime.now().strftime('%H:%M:%S')}")

sensor_filter = sbc.load_sensor_filter_from_csv(filename=sensor_filter_input)

# Process the image
results_with_nedr = process_image(
    rrs_image,
    params,  # This now has NEDR values
    mask=data_mask,
    lut=None,
    n_processes=4,
    sensor_filter=sensor_filter,
    progress_bar=True,
    n_starts=2,  # Use NEDR-weighted objective function
)

# Record end time and calculate elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Processing completed at {datetime.now().strftime('%H:%M:%S')}")
print(f"Total processing time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")

# Step 6: Save the final NEDR-based depth results
depth_map = results_with_nedr['depth']

# Create a copy of the metadata and update for single band output
depth_meta = metadata.copy()
depth_meta.update({
    'count': 1,
    'dtype': 'float32',
    'nodata': np.nan
})

# Save depth results as a new GeoTIFF
with rasterio.open(output_, 'w', **depth_meta) as dst:
    dst.write(depth_map.astype('float32'), 1)
print(f"Depth map saved to {output_}")

# Print comprehensive statistics for all parameters
print("\n" + "="*50)
print("INVERSION RESULTS STATISTICS:")
print("="*50)

# Get all parameter names
param_names = [key for key in results_with_nedr.keys() 
              if key not in ['error', 'convergence', 'status']]

# Calculate and print statistics for each parameter
for param in param_names:
    data = results_with_nedr[param]
    valid_data = data[~np.isnan(data)]

    if len(valid_data) > 0:
        print(f"\n{param.upper()} STATISTICS:")
        print(f"  Valid pixels: {len(valid_data)} of {np.size(data)} ({len(valid_data)/np.size(data)*100:.1f}%)")
        print(f"  Min: {np.min(valid_data):.4f}")
        print(f"  Max: {np.max(valid_data):.4f}")
        print(f"  Mean: {np.mean(valid_data):.4f}")
        print(f"  Median: {np.median(valid_data):.4f}")
        print(f"  Std Dev: {np.std(valid_data):.4f}")

# Print error statistics
error_data = results_with_nedr['error']
valid_error = error_data[~np.isnan(error_data)]
if len(valid_error) > 0:
    print("\nERROR STATISTICS:")
    print(f"  Min error: {np.min(valid_error):.6f}")
    print(f"  Max error: {np.max(valid_error):.6f}")
    print(f"  Mean error: {np.mean(valid_error):.6f}")
    print(f"  Median error: {np.median(valid_error):.6f}")

# Print convergence statistics
if 'convergence' in results_with_nedr:
    converged = np.sum(results_with_nedr['convergence'])
    total = np.size(results_with_nedr['convergence'])
    print(f"\nCONVERGENCE STATISTICS:")
    print(f"  Converged pixels: {converged} of {total} ({converged/total*100:.1f}%)")

print("="*50)

# Create comprehensive plots
print("\nGenerating plots...")

# Find a good sample pixel for spectrum plot
# Look for a pixel with valid depth in the middle region of the image
h, w = depth_map.shape
center_y, center_x = h // 2, w // 2
search_radius = min(h, w) // 4

sample_pixel = None
for r in range(search_radius):
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            if abs(dy) + abs(dx) == r:  # Diamond search pattern
                y, x = center_y + dy, center_x + dx
                if (0 <= y < h and 0 <= x < w and 
                    not np.isnan(depth_map[y, x])):
                    sample_pixel = (y, x)
                    break
        if sample_pixel:
            break
    if sample_pixel:
        break

if not sample_pixel:
    # If no pixel found in center region, find any valid pixel
    valid_coords = np.where(~np.isnan(depth_map))
    if len(valid_coords[0]) > 0:
        idx = len(valid_coords[0]) // 2  # Middle of valid pixels
        sample_pixel = (valid_coords[0][idx], valid_coords[1][idx])

# Generate comprehensive plots
figures = plot_inversion_results(
    results_with_nedr,
    wavelengths=wavelengths_used,
    output_dir=output_dir,
    prefix='inversion_result',
    figsize=(14, 10),
    dpi=300,
    show=True,
    sample_pixel=sample_pixel,
    observed_spectra=rrs_image
)

print(f"Plots saved to {output_dir}")
print("\nInversion process completed successfully!")
