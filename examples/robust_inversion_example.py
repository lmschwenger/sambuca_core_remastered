import os

import matplotlib.pyplot as plt
import numpy as np
import rasterio

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, process_image, LookUpTable

input_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'anholt_clipout.tif')
siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
output_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', f"robust_sdb_{os.path.basename(input_)}")
mask_input = os.path.join(os.path.dirname(input_), 'anholt_ndwi_clipout.tif')

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

    rrs = surface_reflectance / np.pi
    rrs[rrs < 0] = 0
    rrs_image = np.transpose(rrs, (1, 2, 0))[..., 1:4]
# Step 2: Set up the sensor information
# The wavelengths should match your bands
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

bands_used = ["B2", "B3", "B4"]
wavelengths_used = [sentinel2_wavelengths[w] for w in bands_used]
# Register the sensors you work with
siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)

# Create inversion parameters for a specific sensor
params = InversionParameters(
    # Parameters to invert for
    depth=(0.1, 10.0),
    chl=(0.1, 10.0),
    cdom=(0.1, 30.0),
    nap=(0.1, 30.0),
)

# Load SIOPs for this sensor
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# Step 4A: Use LUT approach for faster processing
print("Building lookup table...")
lut = LookUpTable(params)
lut.build_table(grid_size=[50, 20, 10, 20, 20])  # Resolution for depth, chl, substrate_fraction
lut.save("bathymetry_lut.pkl")


# Process the image with robust inversion
print("Processing image with robust inversion...")
results = process_image(
    rrs_image,
    params,
    mask=data_mask,
    use_robust_inversion=True,  # Use the robust inversion to avoid midpoint issues
    use_spectral_angle_f=True,  # Use the combined spectral angle metric
    use_scaling=True,  # Use parameter scaling for better optimization
    lut=lut,
    n_starts=3,  # Number of starting points
    n_processes=4,
    progress_bar=True
)

# Step 5: Save and visualize depth results
depth_map = results['depth']

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

# Visualize the results
plt.figure(figsize=(12, 8))
plt.imshow(depth_map, cmap='viridis')
plt.colorbar(label='Depth (m)')
plt.title('Derived Bathymetry (Robust Inversion)')
plt.savefig('robust_bathymetry_map.png', dpi=300)
plt.show()

# Calculate some statistics on the results
valid_depths = depth_map[~np.isnan(depth_map)]
print(f"Depth statistics:")
print(f"  Min depth: {np.min(valid_depths):.2f} m")
print(f"  Max depth: {np.max(valid_depths):.2f} m")
print(f"  Mean depth: {np.mean(valid_depths):.2f} m")
print(f"  Median depth: {np.median(valid_depths):.2f} m")

# Check parameter distributions to see if they're stuck at midpoints
for param_name in results:
    if param_name in ['depth', 'chl', 'cdom', 'nap']:
        param_values = results[param_name][~np.isnan(results[param_name])]
        if len(param_values) > 0:
            print(f"\n{param_name} distribution:")
            print(f"  Min: {np.min(param_values):.4f}")
            print(f"  Max: {np.max(param_values):.4f}")
            print(f"  Mean: {np.mean(param_values):.4f}")
            print(f"  Median: {np.median(param_values):.4f}")

            # Calculate histogram to check if values are stuck at midpoint
            hist, bins = np.histogram(param_values, bins=10)
            print(f"  Histogram:")
            for i in range(len(hist)):
                print(
                    f"    {bins[i]:.2f}-{bins[i + 1]:.2f}: {hist[i]} pixels ({hist[i] / len(param_values) * 100:.1f}%)")