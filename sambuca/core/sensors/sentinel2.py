"""Band enums for satellite sensors."""

from enum import Enum
from typing import NamedTuple


class BandInfo(NamedTuple):
    """Band information tuple."""
    wavelength: float
    description: str
    resolution: int = 10  # Default resolution in meters


class S2(Enum):
    """Sentinel-2 MSI bands with enhanced metadata."""

    # Wavelengths from your current system
    B01 = BandInfo(442.7, "Coastal aerosol", 60)
    B02 = BandInfo(492.4, "Blue", 10)
    B03 = BandInfo(559.8, "Green", 10)
    B04 = BandInfo(664.6, "Red", 10)
    B05 = BandInfo(704.1, "Vegetation red edge", 20)
    B06 = BandInfo(740.5, "Vegetation red edge", 20)
    B07 = BandInfo(782.8, "Vegetation red edge", 20)
    B08 = BandInfo(832.8, "NIR", 10)
    B8A = BandInfo(864.7, "Narrow NIR", 20)
    B09 = BandInfo(945.1, "Water vapour", 60)
    B10 = BandInfo(1373.5, "SWIR - Cirrus", 60)
    B11 = BandInfo(1613.7, "SWIR", 20)
    B12 = BandInfo(2202.4, "SWIR", 20)

    @property
    def wavelength(self) -> float:
        """Central wavelength in nanometers."""
        return self.value.wavelength

    @property
    def description(self) -> str:
        """Band description."""
        return self.value.description

    @property
    def resolution(self) -> int:
        """Spatial resolution in meters."""
        return self.value.resolution

    @property
    def band_name(self) -> str:
        """Band name (e.g., 'B02')."""
        return self.name