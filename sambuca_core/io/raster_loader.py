from typing import Dict, Optional, List

import rasterio
import numpy as np
from pathlib import Path

from numpy.typing import NDArray

from .base import BaseImageLoader, ImageData


class RasterImageLoader(BaseImageLoader):
    """Loader for raster images using rasterio."""

    def __init__(self,
                 auto_scale: bool = True,
                 convert_to_rrs: bool = True,
                 handle_nodata: bool = True,
                 bands_last: bool = True):
        """
        Initialize raster loader.

        Args:
            auto_scale: Automatically detect and apply scaling factor
            convert_to_rrs: Convert surface reflectance to remote sensing reflectance
            handle_nodata: Convert no-data values to NaN
            bands_last: Reshape to (height, width, bands) format
        """
        self.auto_scale = auto_scale
        self.convert_to_rrs = convert_to_rrs
        self.handle_nodata = handle_nodata
        self.bands_last = bands_last

    def load(self, filepath: str, bands: Optional[List] = None) -> ImageData:
        """
        Load raster image with automatic preprocessing.

        Args:
            filepath: Path to raster file
            bands: Band indices to load (1-based) if None loads all

        Returns:
            ImageData object with preprocessed data
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Image file not found: {filepath}")

        with rasterio.open(filepath) as src:
            # Load data
            if bands is not None:
                data = src.read(bands)
            else:
                data = src.read()

            metadata = src.meta.copy()

        # Preprocess
        processed_data = self._preprocess(data, metadata)

        # Reshape if needed
        if self.bands_last and len(processed_data.shape) == 3:
            # Convert from (bands, height, width) to (height, width, bands)
            processed_data = np.transpose(processed_data, (1, 2, 0))

        return ImageData(
            data=processed_data,
            metadata=metadata,
            filepath=str(filepath),
            bands=bands
        )

    def _preprocess(self, data: NDArray, metadata: Dict) -> NDArray[np.float32]:
        """Apply preprocessing steps to raw image data."""
        # Convert to float32
        data = data.astype(np.float32)

        # Handle no-data values first
        if self.handle_nodata:
            data = self._handle_nodata(data, metadata)

        # Apply scaling
        if self.auto_scale:
            data = self._apply_scaling(data, metadata)

        # Convert to RRS
        if self.convert_to_rrs:
            data = self._convert_to_rrs(data)

        return data

    @staticmethod
    def _handle_nodata(data: NDArray, metadata: Dict) -> NDArray:
        """Convert no-data values to NaN."""
        # Handle typical no-data values
        nodata_mask = (data <= 0) | (data >= 65535)  # Common no-data values

        # Use metadata no-data value if available
        if 'nodata' in metadata and metadata['nodata'] is not None:
            nodata_mask |= (data == metadata['nodata'])

        data[nodata_mask] = np.nan
        return data

    @staticmethod
    def _apply_scaling(data: NDArray, metadata: Dict) -> NDArray:
        """Auto-detect and apply a scaling factor."""
        # Check if data looks like it needs scaling
        if metadata.get('dtype') in ['uint16', 'int16']:
            # Typical Sentinel-2 L2A scaling
            scaling_factor = 10000.0
        elif np.max(data[np.isfinite(data)]) > 10:
            # Data looks like it's in digital numbers, not reflectance
            scaling_factor = 10000.0
        else:
            # Data already looks like reflectance
            scaling_factor = 1.0

        return data / scaling_factor

    @staticmethod
    def _convert_to_rrs(surface_reflectance: NDArray) -> NDArray:
        """Convert surface reflectance to remote sensing reflectance."""
        return surface_reflectance # / np.pi --- doesnt work
