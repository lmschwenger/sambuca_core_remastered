import os
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import numpy as np

try:
    from sentinelsat import SentinelAPI
    import xarray as xr
    import rasterio
    from rasterio.warp import transform

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from .base import BaseDataFetcher


class Sentinel3OLCIFetcher(BaseDataFetcher):
    """Fetcher for Sentinel-3 OLCI water quality parameters."""

    def __init__(self, username: str = None, password: str = None):
        """Initialize Sentinel-3 OLCI data fetcher.

        Args:
            username: Copernicus Hub username (or set COPERNICUS_USER env var)
            password: Copernicus Hub password (or set COPERNICUS_PASSWORD env var)
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "Required dependencies not available. Install with: "
                "pip install sentinelsat xarray rasterio"
            )

        # Get credentials from environment if not provided
        self.username = username or os.getenv('COPERNICUS_USER')
        self.password = password or os.getenv('COPERNICUS_PASSWORD')

        if not self.username or not self.password:
            raise ValueError(
                "Copernicus Hub credentials required. Set COPERNICUS_USER and "
                "COPERNICUS_PASSWORD environment variables or pass to constructor."
            )

        # Initialize API
        self.api = SentinelAPI(self.username, self.password, 'https://scihub.copernicus.eu/dhus')

        # Parameter mapping from OLCI product names to our parameter names
        self.parameter_mapping = {
            'chl': 'CHL_OC4ME',  # Chlorophyll concentration (mg/m³)
            'cdom': 'ADG443_NN',  # Absorption detritus+gelbstoff at 443nm (m⁻¹)
            'nap': 'TSM_NN',  # Total suspended matter (g/m³)
        }

    def fetch_water_parameters(
            self,
            lat: float,
            lon: float,
            date: datetime,
            search_days: int = 3,
            max_cloud_cover: float = 20.0,
            buffer_km: float = 5.0
    ) -> Dict[str, float]:
        """Fetch water quality parameters from Sentinel-3 OLCI.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            date: Target date
            search_days: Days to search before/after target date
            max_cloud_cover: Maximum cloud cover percentage
            buffer_km: Search buffer around point in kilometers

        Returns:
            Dictionary with 'chl', 'cdom', 'nap' values

        Raises:
            ValueError: If no suitable data found
            RuntimeError: If data extraction fails
        """
        print(f"Searching for Sentinel-3 OLCI data near ({lat:.4f}, {lon:.4f}) on {date.date()}")

        # Create search area (simple box around point)
        lat_buffer = buffer_km / 111.0  # Rough km to degrees conversion
        lon_buffer = buffer_km / (111.0 * np.cos(np.radians(lat)))

        bbox = (
            lon - lon_buffer,  # West
            lat - lat_buffer,  # South
            lon + lon_buffer,  # East
            lat + lat_buffer  # North
        )

        # Define search period
        start_date = date - timedelta(days=search_days)
        end_date = date + timedelta(days=search_days)

        # Search for products
        products = self.api.query(
            area=bbox,
            date=(start_date, end_date),
            platformname='Sentinel-3',
            producttype='OL_2_WFR___',  # OLCI Level-2 Water Full Resolution
            cloudcoverpercentage=(0, max_cloud_cover)
        )

        if not products:
            raise ValueError(
                f"No Sentinel-3 OLCI data found for location ({lat}, {lon}) "
                f"between {start_date.date()} and {end_date.date()}"
            )

        print(f"Found {len(products)} potential products")

        # Sort by date proximity and try to extract data
        products_df = self.api.to_dataframe(products)
        products_df['date_diff'] = abs((products_df['beginposition'] - date).dt.total_seconds())
        products_df = products_df.sort_values('date_diff')

        for idx, product in products_df.iterrows():
            try:
                print(f"Trying product: {product['title']}")
                params = self._extract_parameters_from_product(idx, lat, lon)
                if params:
                    print(f"Successfully extracted parameters: {params}")
                    return params
            except Exception as e:
                print(f"Failed to extract from {product['title']}: {e}")
                continue

        raise ValueError("Could not extract water parameters from any available products")

    def _extract_parameters_from_product(
            self,
            product_id: str,
            lat: float,
            lon: float
    ) -> Optional[Dict[str, float]]:
        """Extract parameter values from a specific product."""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Download product
            print(f"Downloading product {product_id}")
            self.api.download(product_id, temp_dir)

            # Find downloaded file
            downloaded_files = list(Path(temp_dir).glob("*.zip"))
            if not downloaded_files:
                raise RuntimeError("No downloaded file found")

            zip_file = downloaded_files[0]

            # Extract and process
            with zipfile.ZipFile(zip_file, 'r') as zf:
                # Extract to temporary directory
                extract_dir = Path(temp_dir) / "extracted"
                zf.extractall(extract_dir)

                # Find .SEN3 product directory
                sen3_dirs = list(extract_dir.glob("*.SEN3"))
                if not sen3_dirs:
                    raise RuntimeError("No .SEN3 directory found in product")

                sen3_dir = sen3_dirs[0]

                # Extract parameters
                parameters = {}
                for param_name, file_prefix in self.parameter_mapping.items():
                    try:
                        value = self._extract_value_at_location(sen3_dir, file_prefix, lat, lon)
                        if value is not None and not np.isnan(value):
                            parameters[param_name] = float(value)
                    except Exception as e:
                        print(f"Warning: Could not extract {param_name}: {e}")

                # Check if we got at least some parameters
                if len(parameters) >= 2:  # Need at least 2 out of 3 parameters
                    # Fill missing parameters with defaults if needed
                    defaults = {'chl': 1.0, 'cdom': 0.1, 'nap': 0.5}
                    for param in ['chl', 'cdom', 'nap']:
                        if param not in parameters:
                            parameters[param] = defaults[param]
                            print(f"Using default value for {param}: {defaults[param]}")

                    return parameters

                return None

    def _extract_value_at_location(
            self,
            sen3_dir: Path,
            file_prefix: str,
            lat: float,
            lon: float
    ) -> Optional[float]:
        """Extract parameter value at specific location from OLCI product."""

        # Find the netCDF file for this parameter
        nc_files = list(sen3_dir.glob(f"{file_prefix}.nc"))
        if not nc_files:
            raise FileNotFoundError(f"No file found for {file_prefix}")

        nc_file = nc_files[0]

        # Open with xarray
        with xr.open_dataset(nc_file) as ds:
            # OLCI uses row/col indexing, need to find closest pixel
            # This is a simplified approach - for production use, proper
            # georeferencing would be needed

            if 'lat' in ds and 'lon' in ds:
                # Direct lat/lon coordinates
                lat_data = ds['lat'].values
                lon_data = ds['lon'].values
            else:
                # May need to use tie points and interpolate
                # For simplicity, assume tie points are available
                if 'latitude' in ds and 'longitude' in ds:
                    lat_data = ds['latitude'].values
                    lon_data = ds['longitude'].values
                else:
                    raise ValueError("Could not find coordinate information")

            # Find closest pixel
            dist = np.sqrt((lat_data - lat) ** 2 + (lon_data - lon) ** 2)
            row, col = np.unravel_index(np.argmin(dist), dist.shape)

            # Get the main variable (usually the first data variable)
            data_vars = [var for var in ds.data_vars if not var.endswith('_err')]
            if not data_vars:
                raise ValueError(f"No data variables found in {nc_file}")

            main_var = data_vars[0]
            value = ds[main_var].values[row, col]

            return value if not np.isnan(value) else None

    def is_available(self, lat: float, lon: float, date: datetime) -> bool:
        """Check if Sentinel-3 OLCI data is available."""
        try:
            # Quick search to see if any products exist
            buffer = 0.1  # Small buffer for availability check
            products = self.api.query(
                area=(lon - buffer, lat - buffer, lon + buffer, lat + buffer),
                date=(date - timedelta(days=7), date + timedelta(days=7)),
                platformname='Sentinel-3',
                producttype='OL_2_WFR___'
            )
            return len(products) > 0
        except:
            return False
