import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, invert_spectrum, multi_start_inversion
from sambuca_core.utility.plotting import plot_inversion_results
from tqdm import tqdm
# Define paths
input_ = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'anholt_20170823_b02b09_clipped2.tif')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', 'inversion_results')
siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "siops")
os.makedirs(output_dir, exist_ok=True)

# Load the image
with rasterio.open(input_) as src:
    image_int16 = src.read()
    metadata = src.meta
    scaling_factor = 10000.0 if metadata['dtype'] != 'float32' else 1.0
    surface_reflectance = image_int16.astype(np.float32) / scaling_factor
    surface_reflectance[surface_reflectance <= 0] = np.nan
    rrs_image = np.transpose(surface_reflectance, (1, 2, 0))[..., :4]

# Define wavelengths and SIOP manager
wavelengths_used = [492.4, 559.8, 664.6, 704.1]  # Sentinel-2 bands B2, B3, B4, B5
siop_manager = sbc.SIOPManager(siop_dir)
siop_manager.register_sensor("Sentinel-2", wavelengths=wavelengths_used)

# Set inversion parameters
params = InversionParameters(
    depth=(0, 25),
    chl=(0.5, 3.3),
    cdom=(0.001, 0.42),
    nap=(0.1, 9.0),
    wavelengths=wavelengths_used
)
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# Prepare output arrays
height, width, _ = rrs_image.shape
depth_map = np.full((height, width), np.nan)
chl_map = np.full((height, width), np.nan)
cdom_map = np.full((height, width), np.nan)
nap_map = np.full((height, width), np.nan)
error_map = np.full((height, width), np.nan)

n_pixels = height * width
# Flatten the loop and use tqdm for progress tracking
for idx in tqdm(range(n_pixels), desc="Processing pixels"):
    y, x = divmod(idx, width)  # Convert flat index to 2D coordinates
    observed_rrs = rrs_image[y, x, :]
    if np.any(np.isnan(observed_rrs)):
        continue

    try:
        # Perform inversion
        result = multi_start_inversion(observed_rrs, params, n_starts=8)
        depth_map[y, x] = result.parameters['depth']
        chl_map[y, x] = result.parameters['chl']
        cdom_map[y, x] = result.parameters['cdom']
        nap_map[y, x] = result.parameters['nap']
        error_map[y, x] = result.objective_value
    except Exception as e:
        print(f"Failed to invert pixel ({y}, {x}): {e}")

# Save results as GeoTIFFs
output_meta = metadata.copy()
output_meta.update({'count': 1, 'dtype': 'float32', 'nodata': np.nan})

for param, data in zip(['depth', 'chl', 'cdom', 'nap', 'error'], [depth_map, chl_map, cdom_map, nap_map, error_map]):
    output_path = os.path.join(output_dir, f"{param}_map.tif")
    with rasterio.open(output_path, 'w', **output_meta) as dst:
        dst.write(data.astype('float32'), 1)
    print(f"Saved {param} map to {output_path}")

# Generate plots
plot_inversion_results(
    {'depth': depth_map, 'chl': chl_map, 'cdom': cdom_map, 'nap': nap_map, 'error': error_map},
    wavelengths=wavelengths_used,
    output_dir=output_dir,
    observed_spectra=rrs_image,
    sample_pixel=(height // 2, width // 2)
)
print(f"Plots saved to {output_dir}")