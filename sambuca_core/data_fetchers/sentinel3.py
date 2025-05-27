from datetime import datetime, timedelta
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np

try:
    import openeo

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from .base import BaseDataFetcher


class Sentinel3OLCIFetcher(BaseDataFetcher):
    """Modern Sentinel-3 OLCI data fetcher using updated openEO Python client."""

    def __init__(self, backend_url: str = None):
        """Initialize Sentinel-3 OLCI data fetcher using modern openEO.

        Args:
            backend_url: openEO backend URL (defaults to Copernicus Data Space Ecosystem)
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "Required dependencies not available. Install with: "
                "pip install openeo"
            )

        # Use the main CDSE endpoint (not federated)
        self.backend_url = backend_url or "openeo.dataspace.copernicus.eu"

        # Connection will be established on first use
        self.connection = None

        # Updated parameter mapping for modern OLCI products
        self.parameter_mapping = {
            'chl': ['CHL_NN', 'CHL_OC4ME'],  # Multiple options for chlorophyll
            'cdom': ['ADG443_NN', 'KD490_M07'],  # CDOM/absorption products
            'nap': ['TSM_NN', 'SPM'],  # Total suspended matter/particles
            'turbidity': ['TURB_NN'],  # Turbidity
        }

        # Try different collection names (they change between updates)
        self.collection_candidates = [
            'SENTINEL3_OLCI_L2_WFR',  # Full resolution water products
            'SENTINEL3_OLCI_L2_WRR',  # Reduced resolution water products
            'SENTINEL-3_OLCI_L2_WFR',  # Alternative naming
            'S3_OLCI_L2_WFR',  # Short naming
        ]

    def _connect(self):
        """Establish connection to openEO backend with modern authentication."""
        if self.connection is not None:
            try:
                # Test if connection is still valid
                self.connection.list_collection_ids()
                return self.connection
            except:
                # Connection expired, reconnect
                self.connection = None

        try:
            print(f"Connecting to openEO backend: {self.backend_url}")
            self.connection = openeo.connect(self.backend_url)

            # Modern authentication - much simpler now
            print("Authenticating with OIDC...")
            self.connection.authenticate_oidc()

            print("✅ Successfully connected and authenticated")
            return self.connection

        except Exception as e:
            raise RuntimeError(f"Failed to connect to openEO backend: {e}")

    def _find_available_collection(self) -> str:
        """Find the first available Sentinel-3 OLCI collection."""
        connection = self._connect()

        available_collections = connection.list_collection_ids()

        for candidate in self.collection_candidates:
            if candidate in available_collections:
                print(f"✅ Found collection: {candidate}")
                return candidate

        # Look for any OLCI-related collection
        olci_collections = [c for c in available_collections if 'SENTINEL3_OLCI_L2_WATER' in c.upper()]
        if olci_collections:
            print(f"✅ Found OLCI collection: {olci_collections[0]}")
            return olci_collections[0]

        raise ValueError(f"No suitable Sentinel-3 OLCI collection found. Available: {available_collections}")

    def fetch_water_parameters(
            self,
            lat: float,
            lon: float,
            date: datetime,
            search_days: int = 7,
            buffer_km: float = 5.0,
            **kwargs
    ) -> Dict[str, float]:
        """Fetch water quality parameters using modern openEO approach.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            date: Target date
            search_days: Days to search before/after target date
            buffer_km: Search buffer around point in kilometers

        Returns:
            Dictionary with 'chl', 'cdom', 'nap' values

        Raises:
            ValueError: If no suitable data found
            RuntimeError: If data extraction fails
        """
        print(f"🔍 Searching for Sentinel-3 OLCI data near ({lat:.4f}, {lon:.4f}) on {date.date()}")
        print(f"Search window: ±{search_days} days, buffer: {buffer_km} km")

        connection = self._connect()
        collection_id = self._find_available_collection()

        # Define temporal extent with simple date strings
        start_date = date - timedelta(days=search_days)
        end_date = date + timedelta(days=search_days)

        temporal_extent = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        # Define spatial extent (buffer around point)
        lat_buffer = buffer_km / 111.0  # Rough km to degrees conversion
        lon_buffer = buffer_km / (111.0 * np.cos(np.radians(lat)))

        spatial_extent = {
            "west": lon - lon_buffer,
            "south": lat - lat_buffer,
            "east": lon + lon_buffer,
            "north": lat + lat_buffer
        }

        try:
            print(f"📡 Loading collection {collection_id}...")

            # Load the data collection with modern approach
            datacube = connection.load_collection(
                collection_id,
                spatial_extent=spatial_extent,
                temporal_extent=temporal_extent
            )

            print("✅ Data collection loaded successfully")

            # Extract parameters using modern aggregation
            parameters = {}

            for param_name, band_candidates in self.parameter_mapping.items():
                print(f"🔍 Extracting {param_name}...")

                value = None
                for band_name in band_candidates:
                    try:
                        # Filter for specific band
                        param_cube = datacube.filter_bands([band_name])

                        # Aggregate spatially (mean over the area)
                        spatial_mean = param_cube.aggregate_spatial(
                            geometries={
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            reducer="mean"
                        )

                        # Execute the computation
                        result = spatial_mean.execute()
                        values = []
                        test = True
                        if test:
                            for date, val in result.items():
                                if val[0][0] is None:
                                    continue
                                values.append(val[0][0])

                            value = np.mean(values)
                        else:
                            # Extract the value from result
                            if isinstance(result, dict) and 'data' in result:
                                value = result['data']
                            elif hasattr(result, 'item'):
                                value = result.item()
                            elif isinstance(result, (list, tuple)) and len(result) > 0:
                                value = result[0]
                            elif isinstance(result, (int, float)):
                                value = float(result)
                            else:
                                # Try to get the first valid value
                                if hasattr(result, 'values'):
                                    flat_values = result.values.flatten()
                                    valid_values = flat_values[np.isfinite(flat_values)]
                                    if len(valid_values) > 0:
                                        value = float(valid_values[0])

                        if value is not None and np.isfinite(value) and value > 0:
                            parameters[param_name] = float(value)
                            print(f"✅ {param_name} ({band_name}): {value:.4f}")
                            break

                    except Exception as e:
                        print(f"⚠️ Could not extract {param_name} from {band_name}: {e}")
                        continue

                if param_name not in parameters:
                    print(f"⚠️ Could not extract {param_name} from any band")

            # Apply fallback values and parameter mapping
            final_parameters = self._apply_parameter_mapping(parameters)

            if len(final_parameters) >= 1:
                print(f"✅ Successfully extracted parameters: {final_parameters}")
                return final_parameters
            else:
                raise ValueError("Could not extract any valid water parameters")

        except Exception as e:
            print(f"❌ Failed to fetch parameters: {e}")
            raise ValueError(f"Failed to fetch parameters from openEO: {e}")

    def _apply_parameter_mapping(self, raw_parameters: Dict[str, float]) -> Dict[str, float]:
        """Apply parameter mapping and fill missing values with defaults."""
        # Parameter mapping and unit conversions
        final_params = {}

        # Chlorophyll (mg/m³)
        if 'chl' in raw_parameters:
            final_params['chl'] = raw_parameters['chl']

        # CDOM (1/m) - may need conversion depending on source
        if 'cdom' in raw_parameters:
            cdom_value = raw_parameters['cdom']
            # If we got KD490, convert to approximate CDOM absorption
            if cdom_value > 1.0:  # Likely KD490
                final_params['cdom'] = cdom_value * 0.1  # Rough conversion
            else:
                final_params['cdom'] = cdom_value

        # NAP/TSM (mg/L or g/m³)
        if 'nap' in raw_parameters:
            nap_value = raw_parameters['nap']
            # Convert from g/m³ to mg/L if needed
            if nap_value > 10:  # Likely in mg/m³, convert to g/m³
                final_params['nap'] = nap_value / 1000.0
            else:
                final_params['nap'] = nap_value

        # Fill missing parameters with reasonable defaults
        defaults = {
            'chl': 1.0,
            'cdom': 0.1,
            'nap': 0.5
        }

        for param, default_value in defaults.items():
            if param not in final_params:
                final_params[param] = default_value
                print(f"🔄 Using default value for {param}: {default_value}")

        return final_params

    def is_available(self, lat: float, lon: float, date: datetime) -> bool:
        """Check if Sentinel-3 OLCI data is available."""
        try:
            connection = self._connect()
            collection_id = self._find_available_collection()

            # Try to load a small sample
            start_date = date - timedelta(days=1)
            end_date = date + timedelta(days=1)

            buffer = 0.01  # ~1km
            spatial_extent = {
                "west": lon - buffer,
                "south": lat - buffer,
                "east": lon + buffer,
                "north": lat + buffer
            }

            temporal_extent = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

            # Try to load the collection
            datacube = connection.load_collection(
                collection_id,
                spatial_extent=spatial_extent,
                temporal_extent=temporal_extent
            )

            # If we can create the datacube, data is available
            return True

        except Exception as e:
            print(f"Data availability check failed: {e}")
            return False

    def get_available_collections(self) -> List[str]:
        """Get list of available OLCI-related collections."""
        try:
            connection = self._connect()
            all_collections = connection.list_collection_ids()

            # Filter for OLCI collections
            olci_collections = [
                c for c in all_collections
                if 'olci' in c.lower() or 'sentinel' in c.lower()
            ]

            return olci_collections

        except Exception as e:
            print(f"Failed to list collections: {e}")
            return []

    def test_connection(self):
        """Test the openEO connection and provide diagnostic information."""
        print("=== Modern openEO Connection Test ===")

        try:
            # Test connection
            connection = self._connect()
            print("✅ Connection established")

            # Test collection access
            try:
                collections = self.get_available_collections()
                if collections:
                    print(f"✅ Found {len(collections)} OLCI-related collections")
                    for col in collections[:5]:  # Show first 5
                        print(f"  - {col}")
                else:
                    print("⚠️ No OLCI collections found")
            except Exception as e:
                print(f"❌ Collection listing failed: {e}")

            # Test simple data loading
            try:
                collection_id = self._find_available_collection()

                # Test with a small area and recent date
                test_date = datetime(2024, 6, 15)
                spatial_extent = {
                    "west": 11.9, "south": 54.9,
                    "east": 12.1, "north": 55.1
                }
                temporal_extent = [
                    (test_date - timedelta(days=1)).strftime('%Y-%m-%d'),
                    (test_date + timedelta(days=1)).strftime('%Y-%m-%d')
                ]

                datacube = connection.load_collection(
                    collection_id,
                    spatial_extent=spatial_extent,
                    temporal_extent=temporal_extent
                )
                print(f"✅ Data loading test successful with {collection_id}")

            except Exception as e:
                print(f"❌ Data loading test failed: {e}")

        except Exception as e:
            print(f"❌ Connection test failed: {e}")

        print("=== End Connection Test ===")
