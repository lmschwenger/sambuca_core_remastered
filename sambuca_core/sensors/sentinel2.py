from typing import Dict, List

from .base import BaseSensor


class Sentinel2Sensor(BaseSensor):
    """Sentinel-2 MSI sensor configuration."""

    @property
    def name(self) -> str:
        return "Sentinel-2"

    @property
    def band_wavelengths(self) -> Dict[str, float]:
        return {
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

    @property
    def standard_band_sets(self) -> Dict[str, List[str]]:
        return {
            'visible': ['B2', 'B3', 'B4'],
            'bathymetry': ['B2', 'B3', 'B4', 'B5'],
            'water_quality': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8'],
            'full_optical': ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A'],
            'default': ['B2', 'B3', 'B4', 'B5']
        }