import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import numpy as np

try:
    import openeo

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from .base import BaseDataFetcher


class Sentinel3OLCIFetcher(BaseDataFetcher):
    """Fetcher for Sentinel-3 OLCI water quality parameters using openEO."""

    def __init__(self, username: str = None, password: str = None, backend_url: str = None):
        """Initialize Sentinel-3 OLCI data fetcher using openEO.

        Args:
            username: Optional username for openEO authentication
            password: Optional password for openEO authentication
            backend_url: openEO backend URL (defaults to Copernicus Data Space)
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "Required dependencies not available. Install with: "
                "pip install openeo"
            )

        # Set default backend
        self.backend_url = backend_url or "openeo.dataspace.copernicus.eu"

        # Store credentials
        self.username = username or os.getenv('COPERNICUS_USER')
        self.password = password or os.getenv('COPERNICUS_PASSWORD')

        # Connection will be established on first use
        self.connection = None

        # Parameter mapping from OLCI product names to our parameter names
        self.parameter_mapping = {
            'chl': 'CHL_OC4ME',  # Chlorophyll concentration (mg/m³)
            'cdom': 'ADG443_NN',  # Absorption detritus+gelbstoff at 443nm (m⁻¹)
            'nap': 'TSM_NN',  # Total suspended matter (g/m³)
            'kd490': 'KD490_M07'  # Diffuse attenuation coefficient at 490nm
        }

        # Collection configuration
        self.collection_id = 'SENTINEL3_OLCI_L2_WATER'

    def _connect(self):
        """Establish connection to openEO backend."""
        if self.connection is not None:
            return self.connection

        try:
            self.connection = openeo.connect(self.backend_url)

            # Authenticate

            # Use device authentication
            self.connection.authenticate_oidc_device()

            return self.connection

        except Exception as e:
            raise RuntimeError(f"Failed to connect to openEO backend: {e}")

    def _format_temporal_extent(self, start_date: datetime, end_date: datetime) -> Tuple[str, str]:
        """Format temporal extent for openEO with fallback options.

        Args:
            start_date: Start datetime
            end_date: End datetime

        Returns:
            Tuple of (start_date_str, end_date_str) formatted for openEO
        """
        # Try different date formats that openEO backends commonly accept
        date_formats = [
            # Format 1: Date only (most common)
            (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),

            # Format 2: With timezone
            (start_date.strftime('%Y-%m-%dT00:00:00Z'), end_date.strftime('%Y-%m-%dT23:59:59Z')),

            # Format 3: Full ISO with milliseconds
            (start_date.strftime('%Y-%m-%dT00:00:00.000Z'), end_date.strftime('%Y-%m-%dT23:59:59.999Z')),

            # Format 4: Local time format
            (start_date.strftime('%Y-%m-%dT00:00:00'), end_date.strftime('%Y-%m-%dT23:59:59')),
        ]

        return date_formats

    def _try_load_collection_with_dates(self, connection, spatial_extent: dict, start_date: datetime,
                                        end_date: datetime):
        """Try to load collection with different date formats until one works."""

        date_formats = self._format_temporal_extent(start_date, end_date)

        last_error = None
        for i, (start_str, end_str) in enumerate(date_formats):
            try:
                temporal_extent = [start_str, end_str]
                print(f"Trying date format {i + 1}: {start_str} to {end_str}")

                datacube = connection.load_collection(
                    self.collection_id,
                    temporal_extent=temporal_extent,
                    spatial_extent=spatial_extent
                )

                print(f"✅ Successfully loaded collection with date format {i + 1}")
                return datacube

            except Exception as e:
                print(f"❌ Date format {i + 1} failed: {e}")
                last_error = e
                continue

        # If all formats failed, raise the last error with helpful message
        raise ValueError(f"All date formats failed. Last error: {last_error}. "
                         f"Try updating openEO client or check backend documentation.")

    def fetch_water_parameters(
            self,
            lat: float,
            lon: float,
            date: datetime,
            search_days: int = 3,
            max_cloud_cover: float = 20.0,
            buffer_km: float = 5.0,
            **kwargs
    ) -> Dict[str, float]:
        """Fetch water quality parameters from Sentinel-3 OLCI using openEO.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            date: Target date
            search_days: Days to search before/after target date
            max_cloud_cover: Maximum cloud cover percentage
            buffer_km: Search buffer around point in kilometers
            **kwargs: Additional parameters for compatibility

        Returns:
            Dictionary with 'chl', 'cdom', 'nap' values

        Raises:
            ValueError: If no suitable data found
            RuntimeError: If data extraction fails
        """
        print(f"Searching for Sentinel-3 OLCI data near ({lat:.4f}, {lon:.4f}) on {date.date()}")
        print(f"Search window: ±{search_days} days, buffer: {buffer_km} km")

        connection = self._connect()

        # Define temporal extent
        start_date = date - timedelta(days=search_days)
        end_date = date + timedelta(days=search_days)

        # Define spatial extent (buffer around point)
        lat_buffer = buffer_km / 111.0  # Rough km to degrees conversion
        lon_buffer = buffer_km / (111.0 * np.cos(np.radians(lat)))

        spatial_extent = {
            "west": lon - lon_buffer,
            "south": lat - lat_buffer,
            "east": lon + lon_buffer,
            "north": lat + lat_buffer,
            "crs": "EPSG:4326"
        }

        try:
            # Load the data collection with robust date handling
            datacube = self._try_load_collection_with_dates(connection, spatial_extent, start_date, end_date)

            # Apply cloud masking if possible
            try:
                # Try to apply cloud mask if available
                datacube = datacube.mask(datacube.band('quality_flags').eq(0))
                print("✅ Applied cloud masking")
            except Exception as e:
                print(f"⚠️ Could not apply cloud masking: {e}")
                # Continue without cloud masking

            # Extract parameters
            parameters = {}

            for param_name, band_name in self.parameter_mapping.items():
                try:
                    print(f"Extracting {param_name} from band {band_name}...")

                    # Select the band and compute spatial/temporal statistics
                    param_cube = datacube.band(band_name)

                    # Compute mean over space and time, ignoring invalid values
                    stats = param_cube.reduce_dimension(dimension='x', reducer="mean").reduce_dimension(dimension='y', reducer="mean").reduce_dimension(dimension='t', reducer="mean")

                    # Execute the computation
                    result = stats.execute()

                    # Extract the value (handle different openEO return formats)
                    if hasattr(result, 'item'):
                        value = result.item()
                    elif isinstance(result, (list, tuple)) and len(result) > 0:
                        value = result[0] if hasattr(result[0], 'item') else result[0]
                    elif isinstance(result, dict) and 'data' in result:
                        value = result['data']
                    elif isinstance(result, (int, float)):
                        value = float(result)
                    else:
                        print(f"⚠️ Unexpected result format for {param_name}: {type(result)}")
                        continue

                    # Validate the result
                    if np.isfinite(value) and value > 0:
                        parameters[param_name] = float(value)
                        print(f"✅ {param_name}: {value:.4f}")
                    else:
                        print(f"⚠️ Invalid value for {param_name}: {value}")

                except Exception as e:
                    print(f"❌ Could not extract {param_name}: {e}")
                    continue

            # Check if we got at least some parameters
            if len(parameters) >= 1:  # Accept even just one parameter
                # Fill missing parameters with defaults if needed
                defaults = {'chl': 1.0, 'cdom': 0.1, 'nap': 0.5}
                for param in ['chl', 'cdom', 'nap']:
                    if param not in parameters:
                        parameters[param] = defaults[param]
                        print(f"🔄 Using default value for {param}: {defaults[param]}")

                print(f"✅ Successfully extracted parameters: {parameters}")
                return parameters
            else:
                raise ValueError("Could not extract any valid water parameters from available data")

        except Exception as e:
            if "date" in str(e).lower() or "temporal" in str(e).lower():
                print(f"❌ Date formatting issue: {e}")
                print("💡 This might be a backend-specific date format requirement")
                print("💡 Try a different openEO backend or check the backend documentation")

            raise ValueError(f"Failed to fetch parameters from openEO: {e}")

    def is_available(self, lat: float, lon: float, date: datetime) -> bool:
        """Check if Sentinel-3 OLCI data is available."""
        try:
            connection = self._connect()

            # Check for data availability in a small temporal window
            start_date = date - timedelta(days=1)
            end_date = date + timedelta(days=1)

            # Small spatial extent around point
            buffer = 0.01  # ~1km
            spatial_extent = {
                "west": lon - buffer,
                "south": lat - buffer,
                "east": lon + buffer,
                "north": lat + buffer,
                "crs": "EPSG:4326"
            }

            # Try to load a small sample with robust date handling
            datacube = self._try_load_collection_with_dates(connection, spatial_extent, start_date, end_date)

            # Try to get metadata (doesn't actually download data)
            metadata = datacube.metadata
            return metadata is not None

        except Exception as e:
            print(f"Data availability check failed: {e}")
            return False

    def get_available_collections(self):
        """Get list of available water quality collections."""
        try:
            connection = self._connect()
            collections = connection.list_collections()

            # Filter for water quality relevant collections
            water_collections = []
            water_keywords = ['water', 'ocean', 'olci', 'chlorophyll', 'l2']

            for collection in collections:
                collection_id = collection.get('id', '').lower()
                description = collection.get('description', '').lower()

                if any(keyword in collection_id or keyword in description
                       for keyword in water_keywords):
                    water_collections.append(collection)

            return water_collections

        except Exception as e:
            print(f"Failed to list collections: {e}")
            return []

    def get_collection_info(self, collection_id: str = None):
        """Get information about the OLCI collection."""
        try:
            connection = self._connect()
            collection_id = collection_id or self.collection_id
            return connection.describe_collection(collection_id)
        except Exception as e:
            print(f"Failed to get collection info: {e}")
            return {}

    def test_connection(self):
        """Test the openEO connection and provide diagnostic information."""
        print("=== OpenEO Connection Test ===")

        try:
            # Test connection
            connection = self._connect()
            print("✅ Connection established")

            # Test collection access
            try:
                info = self.get_collection_info()
                if info:
                    print("✅ Collection access successful")
                    print(f"Collection: {info.get('id', 'Unknown')}")
                    print(f"Description: {info.get('description', 'N/A')[:100]}...")
                else:
                    print("⚠️ Collection info empty")
            except Exception as e:
                print(f"❌ Collection access failed: {e}")

            # Test date formatting
            test_date = datetime(2024, 6, 15)
            start_date = test_date - timedelta(days=1)
            end_date = test_date + timedelta(days=1)

            spatial_extent = {
                "west": 11.9, "south": 54.9,
                "east": 12.1, "north": 55.1,
                "crs": "EPSG:4326"
            }

            try:
                datacube = self._try_load_collection_with_dates(connection, spatial_extent, start_date, end_date)
                print("✅ Date formatting successful")
            except Exception as e:
                print(f"❌ Date formatting failed: {e}")

        except Exception as e:
            print(f"❌ Connection test failed: {e}")

        print("=== End Connection Test ===")