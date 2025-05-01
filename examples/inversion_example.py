import os

import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from sambuca_core.inversion import InversionParameters, LookUpTable, process_image
from sambuca_core.inversion.pixel_processor import batch_process_image

input_ = r"D:\Projects\work\sambuca_core_remastered\data\input\example_groensund.tif"
output_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', "bathymetry_result.tif")

# Load the L2A image
with rasterio.open(input_) as src:
    # Read all bands
    image_int16 = src.read()
    metadata = src.meta

    # For Sentinel-2 L2A products, the scaling factor is typically 10_000
    # (Check your specific product documentation to confirm)
    scaling_factor = 10000.0

    # Convert INT16 to surface reflectance (dimensionless, 0-1)
    surface_reflectance = image_int16.astype(np.float32) / scaling_factor

    # Handle no-data values (typically 0 or negative values)
    # Set them to NaN for proper handling later
    no_data_mask = (image_int16 <= 0)
    surface_reflectance[no_data_mask] = np.nan
    rrs = surface_reflectance / np.pi
    rrs[rrs < 0] = 0
    rrs_image = np.transpose(rrs, (1, 2, 0))
# Step 2: Set up the sensor information
# The wavelengths should match your 5 bands (e.g., for Sentinel-2)
band_wavelengths = np.array([490, 560, 665, 705, 740])  # Adjust these to match your sensor's bands

# Step 3: Configure Sambuca parameters
# You'll need the following data (pre-calculated or from field measurements):
# - Water absorption coefficients at your band wavelengths
# - Phytoplankton specific absorption at your band wavelengths
# - Substrate reflectance spectra at your band wavelengths

# Example values (you should replace these with actual measurements/data)
a_water = np.array([0.016, 0.062, 0.401, 0.438, 0.465])  # Pure water absorption at your bands
a_ph_star = np.array([0.034, 0.023, 0.012, 0.008, 0.005])  # Specific phytoplankton absorption
substrate1 = np.array([0.10, 0.12, 0.08, 0.05, 0.03])  # e.g., sand reflectance
substrate2 = np.array([0.05, 0.25, 0.03, 0.01, 0.01])  # e.g., seagrass reflectance

# Create inversion parameters
params = InversionParameters(
    # Parameters to invert for
    depth=(0.1, 10.0),             # Water depth (m) - adjust min/max to expected range
    chl=(0.1, 10.0),               # Chlorophyll concentration
    substrate_fraction=(0.0, 1.0),  # Mix between two substrates
    
    # Fixed parameters
    fixed_cdom=0.5,                # Fixed CDOM concentration
    fixed_nap=1.0,                 # Fixed NAP concentration
    
    # Sensor and environment parameters
    wavelengths=band_wavelengths,  # Your 5 band centers 
    a_water=a_water,               # Water absorption coefficients
    a_ph_star=a_ph_star,           # Specific phytoplankton absorption
    substrate1=substrate1,         # First substrate reflectance
    substrate2=substrate2,         # Second substrate reflectance
)

# Step 4A: Use LUT approach for faster processing
print("Building lookup table...")
lut = LookUpTable(params)
lut.build_table(grid_size=[30, 15, 10])  # Resolution for depth, chl, substrate_fraction
lut.save("bathymetry_lut.pkl")

# Step 4B: Process the image
print("Processing image...")
results = process_image(
    rrs_image,
    params,
    mask=rrs_image[~np.isnan(rrs_image)],
  #  batch_size=(50, 50),  # Process in 100x100 pixel tiles
  #  overlap=10, # 10-pixel overlap between tiles
    lut=lut,
    n_processes=1,          # Single process
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