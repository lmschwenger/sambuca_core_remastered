from datetime import datetime
from typing import List, Optional

from .parameters import InversionParameters


class ParameterFetcher:
    """Helper class to fetch and set fixed parameters for inversion using modern openEO."""

    def __init__(self, fetcher_type: str = 'sentinel3', **fetcher_kwargs):
        """Initialize parameter fetcher.

        Args:
            fetcher_type: Type of data fetcher ('sentinel3')
            **fetcher_kwargs: Arguments passed to the fetcher constructor
        """
        # Only support sentinel3 with modern openEO
        from ..data_fetchers import Sentinel3OLCIFetcher
        self.fetcher = Sentinel3OLCIFetcher(**fetcher_kwargs)

    def update_parameters_from_satellite(
            self,
            inversion_params: InversionParameters,
            lat: float,
            lon: float,
            date: datetime,
            parameters_to_fetch: list = None,
            **fetch_kwargs
    ) -> InversionParameters:
        """Update InversionParameters with satellite-derived fixed values.

        Args:
            inversion_params: InversionParameters object to update
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            date: Date for satellite data
            parameters_to_fetch: List of parameters to fetch ['chl', 'cdom', 'nap']
                                If None, fetches all available
            **fetch_kwargs: Additional arguments for fetcher

        Returns:
            Updated InversionParameters object

        Raises:
            ValueError: If satellite data not available
        """
        if parameters_to_fetch is None:
            parameters_to_fetch = ['chl', 'cdom', 'nap']

        print(f"🛰️ Fetching satellite parameters: {parameters_to_fetch}")

        # Set defaults for openEO fetching
        fetch_kwargs.setdefault('search_days', 7)
        fetch_kwargs.setdefault('buffer_km', 10.0)

        # Fetch satellite data
        try:
            sat_params = self.fetcher.fetch_water_parameters(lat, lon, date, **fetch_kwargs)
        except Exception as e:
            raise ValueError(f"Failed to fetch satellite data: {e}")

        # Create a copy of the original parameters to avoid modifying the input
        updated_params = inversion_params

        for param in parameters_to_fetch:
            if param in sat_params:
                value = sat_params[param]

                if param == 'chl':
                    # Remove chl from inversion bounds and set as fixed
                    updated_params.chl = None
                    updated_params.fixed_chl = value
                    print(f"📊 Set fixed chlorophyll: {value:.3f} mg/m³")

                elif param == 'cdom':
                    # CDOM absorption coefficient
                    updated_params.cdom = None
                    updated_params.fixed_cdom = value
                    print(f"📊 Set fixed CDOM: {value:.4f} m⁻¹")

                elif param == 'nap':
                    # Non-algal particles
                    updated_params.nap = None
                    updated_params.fixed_nap = value
                    print(f"📊 Set fixed NAP: {value:.3f} g/m³")

        return updated_params

    def is_available(self, lat: float, lon: float, date: datetime) -> bool:
        """Check if satellite data is available."""
        try:
            return self.fetcher.is_available(lat, lon, date)
        except:
            return False

    def test_fetcher(self) -> bool:
        """Test the fetcher connection and functionality."""
        try:
            self.fetcher.test_connection()
            return True
        except Exception as e:
            print(f"❌ Fetcher test failed: {e}")
            return False

    def get_available_collections(self) -> List[str]:
        """Get list of available collections from the fetcher."""
        try:
            return self.fetcher.get_available_collections()
        except Exception as e:
            print(f"❌ Failed to get collections: {e}")
            return []