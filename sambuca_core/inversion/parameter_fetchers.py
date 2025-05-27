from datetime import datetime

from .parameters import InversionParameters
from ..data_fetchers import Sentinel3OLCIFetcher


class ParameterFetcher:
    """Helper class to fetch and set fixed parameters for inversion."""

    def __init__(self, fetcher_type: str = 'sentinel3', **fetcher_kwargs):
        """Initialize parameter fetcher.

        Args:
            fetcher_type: Type of data fetcher ('sentinel3')
            **fetcher_kwargs: Arguments passed to the fetcher constructor
        """
        if fetcher_type == 'sentinel3':
            self.fetcher = Sentinel3OLCIFetcher(**fetcher_kwargs)
        else:
            raise ValueError(f"Unknown fetcher type: {fetcher_type}")

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

        print(f"Fetching satellite parameters: {parameters_to_fetch}")

        # Fetch satellite data
        try:
            sat_params = self.fetcher.fetch_water_parameters(lat, lon, date, **fetch_kwargs)
        except Exception as e:
            raise ValueError(f"Failed to fetch satellite data: {e}")

        # Update inversion parameters
        updated_params = inversion_params

        for param in parameters_to_fetch:
            if param in sat_params:
                value = sat_params[param]

                if param == 'chl':
                    # Remove chl from inversion bounds and set as fixed
                    updated_params.chl = None
                    updated_params.fixed_chl = value
                    print(f"Set fixed chlorophyll: {value:.3f} mg/m³")

                elif param == 'cdom':
                    # For CDOM, satellite gives absorption at 443nm
                    # Convert to concentration if needed based on your model
                    updated_params.cdom = None
                    updated_params.fixed_cdom = value
                    print(f"Set fixed CDOM: {value:.3f} m⁻¹")

                elif param == 'nap':
                    # TSM from satellite, convert to NAP if needed
                    updated_params.nap = None
                    updated_params.fixed_nap = value / 1000.0  # g/m³ to kg/m³ if needed
                    print(f"Set fixed NAP: {value:.3f} g/m³")

        return updated_params
