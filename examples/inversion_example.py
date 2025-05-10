import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
import pandas as pd

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, LookUpTable, process_image

# Define paths
input_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'anholt_20170823_b02b09_clipped2.tif')
siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
sensor_filters_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sensor_filters")
output_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', f"sdb_{os.path.basename(input_)}")
mask_input = os.path.join(os.path.dirname(input_), 'S2_L2A_20180508_B01-B05_ndwi_clipped2.tif')


# Custom function to load sensor filters from CSV
def load_sensor_filters_csv(filepath, normalise=False):
    """Load sensor filters from a CSV file with comma as separator."""
    try:
        # Read the CSV file
        df = pd.read_csv(filepath, sep=',')

        # Assume first column is wavelength and set as index
        wavelength_column = df.columns[0]
        df.set_index(wavelength_column, inplace=True)

        # Extract wavelengths as numpy array
        wavelengths = np.array(df.index)

        # Extract response functions as numpy array
        response_matrix = df.values.T  # Transpose to get bands as rows

        # Normalize if requested
        if normalise:
            # Normalize each band (row) individually
            row_maxes = response_matrix.max(axis=1, keepdims=True)
            # Avoid division by zero
            row_maxes[row_maxes == 0] = 1.0
            response_matrix = response_matrix / row_maxes

        # Use the file basename as the sensor name (without extension)
        sensor_name = os.path.splitext(os.path.basename(filepath))[0]

        # Return dictionary with sensor name as key
        return {sensor_name: (wavelengths, response_matrix)}

    except Exception as e:
        print(f"Error loading sensor filter from {filepath}: {e}")
        return {}


# Load the L2A image
with rasterio.open(input_) as src:
    # Read all bands
    image_int16 = src.read()
    metadata = src.meta

    # For Sentinel-2 L2A products, the scaling factor is typically 10_000
    if metadata['dtype'] == 'float32':
        scaling_factor = 1.0
    else:
        scaling_factor = 10000.0
    print(f"{scaling_factor = }")

    # Convert to surface reflectance and handle no-data values
    surface_reflectance = image_int16.astype(np.float32) / scaling_factor
    no_data_mask = (image_int16 <= 0)
    surface_reflectance[no_data_mask] = np.nan
    rrs = surface_reflectance / np.pi
    rrs[rrs < 0] = 0
    rrs_image = np.transpose(rrs, (1, 2, 0))[..., :5]

# Create mask if available
if mask_input is not None and mask_input != '':
    with rasterio.open(mask_input) as src:
        mask_image = src.read()
        data_mask = (mask_image[2, ...] > 0.75)
else:
    data_mask = np.ones_like(rrs_image[..., 0], dtype=bool)

# Load sensor filters using our custom function
csv_path = os.path.join(sensor_filters_dir, 'sensor_filters.csv')
if os.path.exists(csv_path):
    print(f"Loading sensor filters from {csv_path}")
    sensor_filters = load_sensor_filters_csv(csv_path, normalise=True)

    if sensor_filters:
        print(f"Loaded {len(sensor_filters)} sensor filters")
        for filter_name, filter_data in sensor_filters.items():
            wave_length, filter_matrix = filter_data
            print(f"  - {filter_name}: {len(wave_length)} wavelengths, {filter_matrix.shape} filter matrix")
    else:
        print("No sensor filters loaded!")
else:
    print(f"Sensor filter file not found: {csv_path}")
    sensor_filters = {}

# Define Sentinel-2 wavelengths as a fallback
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

# The bands in your input image
bands_used = ["B1", "B2", "B3", "B4", "B5"]

# Initialize SIOP manager
siop_manager = sbc.SIOPManager(siop_dir)

# Determine which filter to use (look for any key, since we should only have one)
sensor_filter_key = next(iter(sensor_filters.keys())) if sensor_filters else None

# Register sensor wavelengths
if sensor_filter_key:
    # Use wavelengths from the sensor filter
    filter_wavelengths, filter_matrix = sensor_filters[sensor_filter_key]
    print(f"Using wavelengths from sensor filter '{sensor_filter_key}'")

    # Extract wavelengths for bands with non-zero response
    non_zero_bands = []
    for i, band_response in enumerate(filter_matrix):
        max_response = band_response.max()
        if max_response > 0:
            # Find the wavelength at maximum response
            max_idx = np.argmax(band_response)
            non_zero_bands.append(filter_wavelengths[max_idx])

    if non_zero_bands:
        print(f"Using peak wavelengths: {non_zero_bands}")
        siop_manager.register_sensor("Sentinel-2", wavelengths=non_zero_bands)
    else:
        print("No non-zero bands found in filter, using default wavelengths")
        wavelengths_used = [sentinel2_wavelengths[w] for w in bands_used]
        siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)
else:
    # Fallback to using central wavelengths
    wavelengths_used = [sentinel2_wavelengths[w] for w in bands_used]
    print(f"Using central wavelengths: {wavelengths_used}")
    siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)

# Print available libraries to verify SIOPs are loaded
print(f"Available SIOP libraries: {siop_manager.list_available_libraries()}")

# Create inversion parameters
params = InversionParameters(
    # Parameters to invert for
    depth=(0.1, 10.0),
    chl=(0.01, 2.0),
    cdom=(0.0005, 0.01),
    nap=(0.2, 1.5),
)

# Load SIOPs for this sensor
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# Print the loaded parameters to verify
print(f"Loaded SIOP wavelengths: {params.wavelengths}")
print(f"Number of wavelengths: {len(params.wavelengths)}")
print(f"First few a_water values: {params.a_water[:5]}")
print(f"First few substrate1 values: {params.substrate1[:5]}")

# LUT setup
use_lut = False
if use_lut:
    print("Building lookup table...")
    lut = LookUpTable(params)
    lut.build_table(grid_size=[30, 15])
    lut.save("bathymetry_lut.pkl")
else:
    lut = None

# Process the image
print("Processing image...")
results = process_image(
    rrs_image,
    params,
    mask=data_mask,
    lut=lut,
    n_processes=4,
    progress_bar=True
)

# Save depth results as a new GeoTIFF
depth_map = results['depth']
depth_meta = metadata.copy()
depth_meta.update({
    'count': 1,
    'dtype': 'float32',
    'nodata': np.nan
})

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