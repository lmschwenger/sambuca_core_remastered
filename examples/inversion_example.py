import os

import matplotlib.pyplot as plt
import numpy as np
import rasterio

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, LookUpTable, process_image
from sambuca_core.utility.outputs import visualize_sambuca_results

input_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'anholt_20170823_b02b09.tif')
siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
output_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', f"sdb_{os.path.basename(input_)}")
mask_input = os.path.join(os.path.dirname(input_), 'anholt_20250403_NDWI.tiff')

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
    "B8A": 864.7, # Narrow NIR
    "B9": 945.1,  # Water vapour
    "B10": 1373.5, # SWIR - Cirrus
    "B11": 1613.7, # SWIR
    "B12": 2202.4  # SWIR
}

bands_used = ["B2", "B3", "B4"]
wavelengths_used = [sentinel2_wavelengths[w] for w in bands_used]
# Register the sensors you work with
siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)
siop_manager.plot_siops(sensor_name="Sentinel-2", save_path=os.path.join(os.path.dirname(__file__), '..', 'data', 'output', 'siops.png'))

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
    rrs = surface_reflectance / np.pi
    rrs[rrs < 0] = np.nan
    rrs_image = np.transpose(rrs, (1, 2, 0))[..., :len(wavelengths_used)]
# Step 2: Set up the sensor information
# The wavelengths should match your 5 bands (e.g., for Sentinel-2)
if mask_input is not None and mask_input != '':
    with rasterio.open(mask_input) as src:
        mask_image = src.read()
        data_mask = (mask_image[2, ...] > 0.75)
else:
    data_mask = np.ones_like(rrs_image[..., 0], dtype=bool)


# Create inversion parameters for a specific sensor
params = sbc.inversion.InversionParameters(
    # Parameters to invert for (with bounds optimized for Danish waters)
    depth=(0.1, 10),  # Depth range: 0.1-30m for coastal waters
    chl=(0.1, 30),
    cdom=(0.05, 5),
    nap=(0.05, 5.5),
    substrate_fraction=(0.1, 1),

    # Other forward model parameters - can be tuned for Danish waters
    theta_air=40.55, # 20170823 10:30 Anholt
)

# Update with sensor-specific SIOPs
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# Step 4A: Use LUT approach for faster processing
print("Building lookup table...")
lut = LookUpTable(params)
lut.build_table(grid_size=[50, 50, 10, 50, 50])  # Resolution for depth, chl, substrate_fraction
lut.save("bathymetry_lut.pkl")

# Step 4B: Process the image
print("Processing image...")
results = process_image(
    rrs_image,
    params,
    mask=data_mask,
    #batch_size=(50, 50),  # Process in 100x100 pixel tiles
    #  overlap=10, # 10-pixel overlap between tiles
    lut=lut,
    n_processes=4,  # Single process
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
plt.title('Derived Bathymetry')
plt.savefig('bathymetry_map.png', dpi=300)
plt.show()

# Calculate some statistics on the results
valid_depths = depth_map[~np.isnan(depth_map)]
print(f"Depth statistics:")
print(f"  Min depth: {np.min(valid_depths):.2f} m")
print(f"  Max depth: {np.max(valid_depths):.2f} m")
print(f"  Mean depth: {np.mean(valid_depths):.2f} m")
print(f"  Median depth: {np.median(valid_depths):.2f} m")

visualize_sambuca_results(results, os.path.dirname(output_), os.path.basename(input_))