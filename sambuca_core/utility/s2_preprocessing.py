import os
import numpy as np
import rasterio
from rasterio.windows import Window
import pandas as pd
from scipy import ndimage
from typing import Dict, Tuple, Optional, List
import warnings


def load_sentinel2_l2a_with_quality(
        l2a_path: str,
        scl_path: Optional[str] = None,
        bands_to_load: List[str] = None
) -> Dict[str, np.ndarray]:
    """
    Load Sentinel-2 L2A data with quality flags.

    Args:
        l2a_path: Path to L2A image
        scl_path: Path to Scene Classification Layer (SCL) - quality flags
        bands_to_load: List of band names to load (e.g., ['B02', 'B03', 'B04', 'B05'])

    Returns:
        Dictionary with image data and quality information
    """

    if bands_to_load is None:
        bands_to_load = ['B02', 'B03', 'B04', 'B05', 'B06']  # Blue, Green, Red, RedEdge1, RedEdge2

    print(f"Loading Sentinel-2 L2A: {l2a_path}")

    # Load main image
    with rasterio.open(l2a_path) as src:
        # Read selected bands
        if src.count == len(bands_to_load):
            # If file has exact number of bands we want
            image_data = src.read()
            metadata = src.meta
        else:
            # If it's a multi-band file, select specific bands
            # This assumes band order B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B11, B12
            band_indices = []
            band_map = {
                'B01': 1, 'B02': 2, 'B03': 3, 'B04': 4, 'B05': 5, 'B06': 6,
                'B07': 7, 'B08': 8, 'B8A': 9, 'B09': 10, 'B11': 11, 'B12': 12
            }

            for band in bands_to_load:
                if band in band_map and band_map[band] <= src.count:
                    band_indices.append(band_map[band])

            if band_indices:
                image_data = src.read(band_indices)
            else:
                # Fallback: read first N bands
                image_data = src.read(list(range(1, min(len(bands_to_load) + 1, src.count + 1))))

            metadata = src.meta

    # Load quality flags if available
    quality_mask = None
    if scl_path and os.path.exists(scl_path):
        print(f"Loading quality flags: {scl_path}")
        with rasterio.open(scl_path) as scl_src:
            scl_data = scl_src.read(1)

            # Sentinel-2 SCL classes:
            # 0: No Data, 1: Saturated/Defective, 2: Dark Area Pixels, 3: Cloud Shadows,
            # 4: Vegetation, 5: Not Vegetated, 6: Water, 7: Unclassified, 8: Cloud Medium,
            # 9: Cloud High, 10: Thin Cirrus, 11: Snow/Ice

            # Create quality mask (True = good quality)
            good_quality_classes = [4, 5, 6, 7]  # Vegetation, Not Vegetated, Water, Unclassified
            quality_mask = np.isin(scl_data, good_quality_classes)

            # Water mask from SCL
            water_mask_scl = (scl_data == 6)
    else:
        print("⚠️  No quality flags provided - proceeding without quality filtering")
        water_mask_scl = None

    return {
        'image_data': image_data,
        'metadata': metadata,
        'quality_mask': quality_mask,
        'water_mask_scl': water_mask_scl,
        'bands_loaded': bands_to_load
    }


def convert_surface_to_water_leaving_reflectance(
        surface_reflectance: np.ndarray,
        wavelengths: List[float],
        solar_zenith_angle: float = 30.0,
        viewing_zenith_angle: float = 0.0,
        relative_azimuth_angle: float = 90.0
) -> np.ndarray:
    """
    Convert surface reflectance to water-leaving reflectance.

    This is CRITICAL - your current division by π is incorrect!

    Args:
        surface_reflectance: Surface reflectance from L2A (0-1)
        wavelengths: Wavelengths of the bands
        solar_zenith_angle: Solar zenith angle in degrees
        viewing_zenith_angle: Viewing zenith angle in degrees
        relative_azimuth_angle: Relative azimuth angle in degrees

    Returns:
        Water-leaving reflectance (equivalent to Rrs)
    """

    print("Converting surface reflectance to water-leaving reflectance...")

    # Convert angles to radians
    theta_s = np.radians(solar_zenith_angle)
    theta_v = np.radians(viewing_zenith_angle)
    phi = np.radians(relative_azimuth_angle)

    # Calculate cosines
    cos_theta_s = np.cos(theta_s)
    cos_theta_v = np.cos(theta_v)

    # Surface reflection correction factors
    # These account for the air-water interface

    # Fresnel reflectance (approximate)
    n_water = 1.34  # Refractive index of water

    # Fresnel reflectance for nadir viewing (approximate)
    r_fresnel = ((1 - n_water) / (1 + n_water)) ** 2

    # For non-nadir viewing, adjust Fresnel reflectance
    if viewing_zenith_angle > 0:
        # Simplified angular dependence
        r_fresnel *= (1 + 0.5 * np.sin(theta_v) ** 2)

    # Geometry factor
    geometry_factor = cos_theta_s / (cos_theta_s + cos_theta_v)

    # Convert surface reflectance to water-leaving reflectance
    # This removes the surface reflection component
    water_leaving_reflectance = np.zeros_like(surface_reflectance)

    for i in range(surface_reflectance.shape[0]):  # For each band
        # Remove surface reflection effects
        rho_surface = surface_reflectance[i, :, :]

        # Account for geometry and interface effects
        # This is a simplified model - for high accuracy, use full radiative transfer
        rho_water = (rho_surface - r_fresnel) / (1 - r_fresnel * rho_surface)

        # Apply geometry correction
        rho_water *= geometry_factor

        # Ensure physical values
        rho_water = np.clip(rho_water, 0, 1)

        water_leaving_reflectance[i, :, :] = rho_water

    print(f"✅ Converted surface reflectance to water-leaving reflectance")
    print(f"   Surface reflectance range: {np.nanmin(surface_reflectance):.6f} - {np.nanmax(surface_reflectance):.6f}")
    print(
        f"   Water-leaving range: {np.nanmin(water_leaving_reflectance):.6f} - {np.nanmax(water_leaving_reflectance):.6f}")

    return water_leaving_reflectance


def correct_sun_glint(
        reflectance: np.ndarray,
        nir_band_idx: int = -1,
        glint_threshold: float = 0.02,
        correction_factor: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simple sun glint correction using NIR band.

    Args:
        reflectance: Water-leaving reflectance
        nir_band_idx: Index of NIR band (use -1 for last band)
        glint_threshold: Threshold for detecting glint in NIR
        correction_factor: Factor for glint removal

    Returns:
        Corrected reflectance and glint mask
    """

    print("Applying sun glint correction...")

    corrected_reflectance = reflectance.copy()

    # Use NIR band to detect glint (water should be dark in NIR)
    nir_band = reflectance[nir_band_idx, :, :]

    # Pixels with high NIR are likely affected by glint
    glint_mask = nir_band > glint_threshold
    glint_pixels = np.sum(glint_mask)

    if glint_pixels > 0:
        print(f"   Detected glint in {glint_pixels} pixels ({glint_pixels / nir_band.size * 100:.1f}%)")

        # Simple correction: subtract a fraction of NIR from all bands
        for i in range(reflectance.shape[0]):
            # Only correct where glint is detected
            correction = correction_factor * nir_band * glint_mask
            corrected_reflectance[i, :, :] -= correction

            # Ensure no negative values
            corrected_reflectance[i, :, :] = np.maximum(corrected_reflectance[i, :, :], 0)
    else:
        print("   No significant glint detected")

    return corrected_reflectance, glint_mask


def enhanced_sentinel2_preprocessing(
        l2a_image_path: str,
        scl_path: Optional[str] = None,
        ndwi_mask_path: Optional[str] = None,
        bands_to_use: List[str] = None,
        solar_zenith: float = 30.0,
        output_path: Optional[str] = None
) -> Dict[str, np.ndarray]:
    """
    Complete enhanced preprocessing pipeline for Sentinel-2 L2A data.

    Args:
        l2a_image_path: Path to L2A image
        scl_path: Path to Scene Classification Layer
        ndwi_mask_path: Path to existing NDWI mask
        bands_to_use: Bands to process
        solar_zenith: Solar zenith angle in degrees
        output_path: Optional path to save processed data

    Returns:
        Dictionary with processed data ready for SAMBUCA
    """

    print("🌊 ENHANCED SENTINEL-2 L2A PREPROCESSING FOR SHALLOW WATER")
    print("=" * 70)

    if bands_to_use is None:
        bands_to_use = ['B02', 'B03', 'B04', 'B05']  # Blue, Green, Red, RedEdge
        wavelengths = [492.4, 559.8, 664.6, 704.1]
    else:
        # Map band names to wavelengths
        band_wavelengths = {
            'B01': 442.7, 'B02': 492.4, 'B03': 559.8, 'B04': 664.6,
            'B05': 704.1, 'B06': 740.5, 'B07': 782.8, 'B08': 832.8,
            'B8A': 864.7, 'B09': 945.1, 'B11': 1613.7, 'B12': 2202.4
        }
        wavelengths = [band_wavelengths[band] for band in bands_to_use]

    # Step 1: Load data with quality flags
    data = load_sentinel2_l2a_with_quality(l2a_image_path, scl_path, bands_to_use)
    image_data = data['image_data']
    metadata = data['metadata']
    quality_mask = data['quality_mask']
    scl_water_mask = data['water_mask_scl']

    # Step 2: Scale to surface reflectance
    print(f"\n📏 Scaling to surface reflectance...")
    if metadata['dtype'] == 'float32':
        scaling_factor = 1.0
    else:
        scaling_factor = 10000.0

    surface_reflectance = image_data.astype(np.float32) / scaling_factor

    # Handle no-data values
    no_data_mask = (image_data <= 0) | (image_data >= 65535)
    surface_reflectance[no_data_mask] = np.nan

    print(f"   Surface reflectance range: {np.nanmin(surface_reflectance):.6f} - {np.nanmax(surface_reflectance):.6f}")

    # Step 3: Convert to water-leaving reflectance (CRITICAL!)
    water_leaving_refl = convert_surface_to_water_leaving_reflectance(
        surface_reflectance, wavelengths, solar_zenith
    )

    # Step 4: Sun glint correction
    corrected_refl, glint_mask = correct_sun_glint(
        water_leaving_refl, nir_band_idx=-1  # Use last band as NIR proxy
    )

    # Step 5: Load existing NDWI mask if provided
    ndwi_mask = None
    if ndwi_mask_path and os.path.exists(ndwi_mask_path):
        print(f"\n🗺️  Loading existing NDWI mask...")
        with rasterio.open(ndwi_mask_path) as src:
            mask_image = src.read()
            ndwi_mask = (mask_image[2, ...] > 0.75)

    # Step 7: Convert to remote sensing reflectance for SAMBUCA
    # Note: This is different from your original π division!
    rrs = corrected_refl / np.pi  # This is now correct since we converted properly

    # Transpose to (height, width, bands) for SAMBUCA
    rrs_image = np.transpose(rrs, (1, 2, 0))

    print(f"\n📊 FINAL STATISTICS:")
    print(f"   Image shape: {rrs_image.shape}")
    print(f"   Valid water pixels: {np.sum(ndwi_mask)}")
    print(f"   RRS range: {np.nanmin(rrs_image):.6f} - {np.nanmax(rrs_image):.6f}")
    print(f"   Wavelengths: {wavelengths}")

    # Step 9: Save if requested
    if output_path:
        print(f"\n💾 Saving processed data to {output_path}")
        # Update metadata for output
        output_meta = metadata.copy()
        output_meta.update({
            'count': len(bands_to_use),
            'dtype': 'float32',
            'nodata': np.nan
        })

        with rasterio.open(output_path, 'w', **output_meta) as dst:
            dst.write(rrs.astype('float32'))

    return {
        'rrs_image': rrs_image,
        'water_mask': ndwi_mask,
        'wavelengths': wavelengths,
        'bands_used': bands_to_use,
        'glint_mask': glint_mask,
        'quality_mask': quality_mask,
        'metadata': metadata,
        'processing_stats': {
            'surface_refl_range': (np.nanmin(surface_reflectance), np.nanmax(surface_reflectance)),
            'water_leaving_range': (np.nanmin(water_leaving_refl), np.nanmax(water_leaving_refl)),
            'final_rrs_range': (np.nanmin(rrs_image), np.nanmax(rrs_image)),
            'valid_pixels': np.sum(ndwi_mask),
            'glint_pixels': np.sum(glint_mask)
        }
    }