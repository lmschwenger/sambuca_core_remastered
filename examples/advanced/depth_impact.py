import os
import matplotlib.pyplot as plt
import numpy as np
import rasterio

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters

input_ = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'input', 'anholt_20170823_b02b09.tif')
siop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', "data", "siops")

with rasterio.open(input_) as src:
    # Read all bands
    image_int16 = src.read()
    metadata = src.meta

    # For Sentinel-2 L2A products, the scaling factor is typically 10_000
    if metadata['dtype'] == 'float32':
        scaling_factor = 1.0
    else:
        scaling_factor = 10000.0
    # Convert INT16 to surface reflectance (dimensionless, 0-1)
    surface_reflectance = image_int16.astype(np.float32) / scaling_factor

    # Handle no-data values (typically 0 or negative values)
    no_data_mask = (image_int16 <= 0)
    surface_reflectance[no_data_mask] = np.nan
    rrs = surface_reflectance / np.pi
    rrs[rrs < 0] = 0
    rrs_image = np.transpose(rrs, (1, 2, 0))[..., :4]
#   rrs_image = (2 * rrs_image) / ((3 * rrs_image) + 1)

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

# --- User settings ---
pixel_y, pixel_x = 1000, 950  # <-- Set your pixel indices here
depths_to_test = np.linspace(1, 25, 5)  # <-- Set depths to test
fixed_params = {
    'chl': 0.5,  # Set typical/median values for other parameters
    'cdom': 0.005,
    'nap': 0.1,
}
# ---------------------

# Extract observed Rrs at the chosen pixel
observed_rrs = rrs_image[pixel_y, pixel_x, :]

# Prepare to store modeled spectra
modeled_rrs = []

# Set up inversion parameters and update from SIOP manager
params = InversionParameters(
    depth=(0, 25),
    chl=(0.5, 3.30),
    cdom=(0.001, 0.42),
    nap=(0.1, 9.0),
    fixed_substrate_fraction=0.95,
    wavelengths=wavelengths_used
)
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# For each depth, run the forward model with fixed parameters
for depth in depths_to_test:
    chl = fixed_params['chl']
    cdom = fixed_params['cdom']
    nap = fixed_params['nap']

    modeled = sbc.forward_model(
        chl=chl,
        depth=depth,
        nap=nap,
        cdom=cdom,
        wavelengths=params.wavelengths,
        substrate1=params.substrate1,
        a_water=params.a_water,
        a_ph_star=params.a_ph_star,
        num_bands=len(params.wavelengths)
    )

    if hasattr(modeled, 'rrs'):
        modeled_rrs.append(modeled.rrs)
    else:
        modeled_rrs.append(modeled)
modeled_rrs = np.array(modeled_rrs)

# --- Plotting: 1,2 subplot with image and depth impact plot ---

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: RGB image with highlighted pixel
ax_img = axes[0]
rgb = np.zeros((rrs_image.shape[0], rrs_image.shape[1], 3), dtype=np.float32)
for i, b in enumerate(range(3)):
    band = rrs_image[..., b]
    vmin, vmax = np.nanpercentile(band, [2, 98])
    rgb[..., 2-i] = np.clip((band - vmin) / (vmax - vmin + 1e-8), 0, 1)
ax_img.imshow(rgb)
ax_img.plot(pixel_x, pixel_y, 'ro', markersize=10, label='Chosen pixel')
ax_img.set_title(f"RGB (B2,B3,B4) with pixel ({pixel_y},{pixel_x})")
ax_img.axis('off')
ax_img.legend(loc='lower right')

# Right: Observed vs. Modeled Rrs for different depths
ax_rrs = axes[1]
ax_rrs.plot(wavelengths_used, observed_rrs, 'ko-', label='Observed Rrs')
for i, depth in enumerate(depths_to_test):
    ax_rrs.plot(wavelengths_used, modeled_rrs[i], '-o', label=f'Modeled Rrs (depth={depth} m)')
ax_rrs.set_xlabel('Wavelength (nm)')
ax_rrs.set_ylabel('Rrs')
ax_rrs.set_title('Observed vs. Modeled Rrs at different depths')
ax_rrs.legend()
ax_rrs.grid(True)

plt.tight_layout()
plt.show()
