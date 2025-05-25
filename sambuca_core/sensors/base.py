from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class BaseSensor(ABC):
    """Abstract base class for satellite sensors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Sensor name."""
        pass

    @property
    @abstractmethod
    def band_wavelengths(self) -> Dict[str, float]:
        """Dictionary mapping band names to central wavelengths."""
        pass

    @property
    @abstractmethod
    def standard_band_sets(self) -> Dict[str, List[str]]:
        """Predefined band combinations for common applications."""
        pass

    def get_wavelengths(self, bands: List[str]) -> List[float]:
        """Get wavelengths for specified bands."""
        return [self.band_wavelengths[band] for band in bands]

    def get_standard_config(self, config_name: str = 'default') -> Tuple[List[str], List[float]]:
        """Get bands and wavelengths for a standard configuration."""
        bands = self.standard_band_sets[config_name]
        wavelengths = self.get_wavelengths(bands)
        return bands, wavelengths