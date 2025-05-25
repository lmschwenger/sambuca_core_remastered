import numpy as np
import rasterio
from typing import Optional, Tuple
from .base import ImageData


class ImagePreprocessor:
    """Additional preprocessing utilities for images."""

    @staticmethod
    def apply_water_mask(image_data: ImageData,
                         mask_path: Optional[str] = None,
                         mask_threshold: float = 0.0) -> np.ndarray:
        """
        Apply water mask to image data.

        Args:
            image_data: ImageData object
            mask_path: Path to mask file (e.g., NDWI mask)
            mask_threshold: Threshold for mask values (pixels > threshold is water)

        Returns:
            Boolean mask where True = water pixels to process
        """
        if mask_path is None:
            # No mask provided, return all valid (non-NaN) pixels
            if image_data.is_bands_last:
                return ~np.any(np.isnan(image_data.data), axis=2)
            else:
                return ~np.any(np.isnan(image_data.data), axis=0)

        # Load mask file
        with rasterio.open(mask_path) as src:
            if src.count == 1:
                mask_data = src.read(1)
            else:
                # If multiple bands, assume water mask is in the last band
                mask_data = src.read(src.count)

        # Apply a threshold
        water_mask = mask_data > mask_threshold

        # Combine with valid data mask
        if image_data.is_bands_last:
            valid_mask = ~np.any(np.isnan(image_data.data), axis=2)
        else:
            valid_mask = ~np.any(np.isnan(image_data.data), axis=0)

        return water_mask & valid_mask

    @staticmethod
    def extract_pixel_spectrum(image_data: ImageData,
                               y: int, x: int) -> np.ndarray:
        """
        Extract spectrum for a single pixel.

        Args:
            image_data: ImageData object
            y: Row coordinate
            x: Column coordinate

        Returns:
            1D array of pixel spectrum
        """
        if image_data.is_bands_last:
            return image_data.data[y, x, :]
        else:
            return image_data.data[:, y, x]

    @staticmethod
    def create_rgb_preview(image_data: ImageData,
                           rgb_bands: Tuple[int, int, int] = (2, 1, 0),
                           stretch_percentiles: Tuple[float, float] = (2, 98)) -> np.ndarray:
        """
        Create RGB preview image for visualization.

        Args:
            image_data: ImageData object
            rgb_bands: Band indices for R, G, B (0-based)
            stretch_percentiles: Percentiles for contrast stretching

        Returns:
            RGB image array (height, width, 3) with values 0-1
        """
        if not image_data.is_bands_last:
            # Convert to bands-last format temporarily
            data = np.transpose(image_data.data, (1, 2, 0))
        else:
            data = image_data.data

        # Extract RGB bands
        rgb = np.zeros((data.shape[0], data.shape[1], 3), dtype=np.float32)

        for i, band_idx in enumerate(rgb_bands):
            if band_idx < data.shape[2]:
                band = data[:, :, band_idx]

                # Remove NaN for percentile calculation
                valid_pixels = band[np.isfinite(band)]

                if len(valid_pixels) > 0:
                    vmin, vmax = np.percentile(valid_pixels, stretch_percentiles)
                    # Stretch and clip
                    rgb[:, :, i] = np.clip((band - vmin) / (vmax - vmin + 1e-8), 0, 1)

        return rgb