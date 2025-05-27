from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
import numpy as np


class BaseDataFetcher(ABC):
    """Abstract base class for satellite data fetchers."""

    @abstractmethod
    def fetch_water_parameters(
            self,
            lat: float,
            lon: float,
            date: datetime,
            **kwargs
    ) -> Dict[str, float]:
        """Fetch water quality parameters for a location and date.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            date: Date for data acquisition
            **kwargs: Additional parameters

        Returns:
            Dictionary with parameter names and values
        """
        pass

    @abstractmethod
    def is_available(self, lat: float, lon: float, date: datetime) -> bool:
        """Check if data is available for given location and date."""
        pass