"""Sentinel-3 data fetcher for SAMBUCA Core."""

import logging
import os
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import BaseDataFetcher

# Suppress warnings from external libraries
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class Sentinel3DataFetcher(BaseDataFetcher):
    """
    Fetches Sentinel-3 OLCI derived water quality products from Copernicus Marine Service.
    
    This fetcher requires additional dependencies:
    - copernicus-marine-toolbox
    - xarray
    - rasterio
    - geopandas
    - shapely
    """

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the fetcher with output directory."""
        # Set default output directory
        if output_dir is None:
            # Default to current working directory + data/input/sentinel3
            self.output_dir = Path.cwd() / "data" / "input" / "sentinel3"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load credentials from environment variables
        self.username = os.getenv('COP_MARINE_USER')
        self.password = os.getenv('COP_MARINE_PASS')

        # Dataset configurations
        self._setup_datasets()

    def _setup_datasets(self):
        """Setup dataset IDs and variable mappings."""
        # Multi-year datasets (primary choice)
        self.datasets = {
            'chl': 'cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D',
            'nap': 'cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D',
            'kd': 'cmems_obs-oc_glo_bgc-optics_my_l3-multi-4km_P1D',
            'cdom': 'cmems_obs-oc_glo_bgc-optics_my_l3-multi-4km_P1D'
        }

        # Near Real-Time datasets (fallback for recent data)
        self.datasets_nrt = {
            'chl': 'cmems_obs-oc_glo_bgc-plankton_nrt_l3-multi-4km_P1D',
            'nap': 'cmems_obs-oc_glo_bgc-plankton_nrt_l3-multi-4km_P1D',
            'kd': 'cmems_obs-oc_glo_bgc-optics_nrt_l3-multi-4km_P1D',
            'cdom': 'cmems_obs-oc_glo_bgc-optics_nrt_l3-multi-4km_P1D'
        }

        # Alternative high-resolution OLCI datasets (fallback)
        self.datasets_olci = {
            'chl': 'cmems_obs-oc_glo_bgc-plankton_my_l3-olci-300m_P1D',
            'nap': 'cmems_obs-oc_glo_bgc-plankton_my_l3-olci-300m_P1D',
            'kd': 'cmems_obs-oc_glo_bgc-optics_my_l3-multi-4km_P1D',
            'cdom': 'cmems_obs-oc_glo_bgc-optics_my_l3-multi-4km_P1D'
        }

        # Variable names in the datasets
        self.variables = {
            'chl': 'CHL',  # Chlorophyll concentration
            'kd': 'KD490',  # Diffuse attenuation coefficient
            'nap': 'TSM',  # Total Suspended Matter (equivalent to NAP)
            'cdom': 'CDM'  # Colored Dissolved Matter
        }

    @property
    def name(self) -> str:
        return "Sentinel-3 OLCI"

    @property
    def supported_parameters(self) -> List[str]:
        return list(self.variables.keys())

    @property
    def required_dependencies(self) -> List[str]:
        return [
            'copernicusmarine',
            'xarray',
            'rasterio',
            'geopandas',
            'shapely',
            'numpy'
        ]

    def is_available(self) -> bool:
        """Check if all required dependencies are installed."""
        try:
            import copernicusmarine
            import xarray
            import rasterio
            import geopandas
            import shapely
            import numpy
            return True
        except ImportError as e:
            logger.warning(f"Sentinel-3 fetcher not available: {e}")
            return False

    def _check_dependencies(self):
        """Raise exception if dependencies are not available."""
        if not self.is_available():
            missing = []
            for dep in self.required_dependencies:
                try:
                    __import__(dep)
                except ImportError:
                    missing.append(dep)

            raise RuntimeError(
                f"Sentinel-3 fetcher requires missing dependencies: {missing}. "
                f"Install with: pip install {' '.join(missing)}"
            )

    def _setup_authentication(self):
        """Set up authentication for Copernicus Marine Service."""
        if self.username and self.password:
            os.environ['COPERNICUSMARINE_SERVICE_USERNAME'] = self.username
            os.environ['COPERNICUSMARINE_SERVICE_PASSWORD'] = self.password
            logger.info("Set up Copernicus Marine authentication from environment variables")
            return True
        else:
            logger.info("Using existing Copernicus Marine authentication (if any)")
            return False

    def _parse_aoi(self, aoi_input: str) -> Tuple[float, float, float, float]:
        """
        Parse AOI input in various formats.
        
        Args:
            aoi_input: AOI as WKT, bbox string, or shapefile path
            
        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        try:
            # Try parsing as bbox: "min_lon,min_lat,max_lon,max_lat"
            if ',' in aoi_input and not aoi_input.upper().startswith('POLYGON'):
                coords = [float(x.strip()) for x in aoi_input.split(',')]
                if len(coords) == 4:
                    return tuple(coords)

            # Try parsing as WKT
            if aoi_input.upper().startswith('POLYGON'):
                from shapely.wkt import loads as wkt_loads
                geom = wkt_loads(aoi_input)
                return geom.bounds

            # Try as shapefile path
            if os.path.exists(aoi_input):
                import geopandas as gpd
                gdf = gpd.read_file(aoi_input)
                bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
                return tuple(bounds)

        except Exception as e:
            logger.error(f"Error parsing AOI: {e}")
            raise ValueError(f"Could not parse AOI: {aoi_input}")

        raise ValueError(f"Unsupported AOI format: {aoi_input}")

    def _find_nearest_date(self, target_date: datetime, date_range_days: int = 7) -> Tuple[str, str]:
        """Find the best date range around the target date for data availability."""
        start_date = target_date - timedelta(days=date_range_days)
        end_date = target_date + timedelta(days=date_range_days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    def _fetch_data_copernicusmarine(self,
                                     parameter: str,
                                     bbox: Tuple[float, float, float, float],
                                     start_date: str,
                                     end_date: str):
        """Fetch data using copernicus-marine-toolbox."""
        import copernicusmarine

        self._setup_authentication()

        # Try datasets in order of preference
        datasets_to_try = [
            (self.datasets[parameter], "Multi-year L3 (4km resolution)"),
            (self.datasets_nrt[parameter], "Near Real-Time L3 (4km resolution)"),
            (self.datasets_olci[parameter], "Multi-year L3 (300m OLCI resolution)")
        ]

        for dataset_id, dataset_type in datasets_to_try:
            try:
                variable = self.variables[parameter]

                logger.info(f"Trying {dataset_type} dataset: {dataset_id}")
                logger.info(f"Fetching {parameter} data from {start_date} to {end_date}")
                logger.info(f"Bbox: {bbox}")

                ds = copernicusmarine.open_dataset(
                    dataset_id=dataset_id,
                    variables=[variable],
                    minimum_longitude=bbox[0],
                    maximum_longitude=bbox[2],
                    minimum_latitude=bbox[1],
                    maximum_latitude=bbox[3],
                    start_datetime=start_date,
                    end_datetime=end_date
                )

                logger.info(f"Successfully fetched data from {dataset_type}")
                return ds

            except Exception as e:
                logger.warning(f"Failed to fetch from {dataset_type} ({dataset_id}): {e}")
                continue

        logger.error(f"Failed to fetch {parameter} data from all available datasets")
        return None

    def _process_and_save_data(self,
                               ds,
                               parameter: str,
                               bbox: Tuple[float, float, float, float],
                               target_date: str) -> Optional[str]:
        """Process the downloaded data and save as GeoTIFF."""
        import numpy as np
        import rasterio
        from rasterio.transform import from_bounds
        from rasterio.crs import CRS

        try:
            var_name = self.variables[parameter]

            if var_name not in ds.variables:
                logger.error(f"Variable {var_name} not found in dataset")
                return None

            # Get the data variable
            data_var = ds[var_name]

            # Find the best time slice (closest to target date with valid data)
            if 'time' in data_var.dims:
                target_dt = datetime.strptime(target_date, '%Y-%m-%d')
                time_diff = np.abs(ds.time - np.datetime64(target_dt))

                # Sort indices by time difference to target
                sorted_time_indices = time_diff.argsort()

                best_data_slice = None
                best_valid_count = 0
                used_time_idx = None

                # Check up to 5 closest time slices to find one with valid data
                for i in range(min(5, len(sorted_time_indices))):
                    time_idx = sorted_time_indices[i]
                    test_slice = data_var.isel(time=time_idx)
                    test_array = test_slice.values

                    # Count valid (non-NaN) values
                    valid_count = np.sum(np.isfinite(test_array))
                    time_value = ds.time.values[time_idx]

                    logger.info(f"Time slice {i + 1}: {time_value}, valid pixels: {valid_count}/{test_array.size}")

                    # Use this slice if it has more valid data
                    if valid_count > best_valid_count:
                        best_data_slice = test_slice
                        best_valid_count = valid_count
                        used_time_idx = time_idx

                # Check if we found any valid data
                if best_data_slice is None or best_valid_count == 0:
                    logger.error(f"No valid data found in any time slice for {parameter}")
                    return None

                data_slice = best_data_slice
                used_time = ds.time.values[used_time_idx]
                logger.info(f"Using time slice: {used_time} with {best_valid_count} valid pixels")

            else:
                data_slice = data_var
                # Check for valid data in non-temporal case
                test_array = data_slice.values
                valid_count = np.sum(np.isfinite(test_array))
                if valid_count == 0:
                    logger.error(f"No valid data found for {parameter} (no time dimension)")
                    return None
                logger.info(f"Found {valid_count} valid pixels (no time dimension)")

            # Convert to numpy array
            data_array = data_slice.values

            # Handle NaN values
            data_array = np.where(np.isfinite(data_array), data_array, -9999)

            # Create output filename
            date_str = target_date.replace('-', '')
            output_file = self.output_dir / f"S3_{parameter.upper()}_{date_str}.tif"

            # Get spatial information
            if 'longitude' in ds.coords and 'latitude' in ds.coords:
                lons = ds.longitude.values
                lats = ds.latitude.values
            elif 'lon' in ds.coords and 'lat' in ds.coords:
                lons = ds.lon.values
                lats = ds.lat.values
            else:
                logger.error("Could not find longitude/latitude coordinates")
                return None

            # Create transform
            lon_res = (lons.max() - lons.min()) / (len(lons) - 1)
            lat_res = (lats.max() - lats.min()) / (len(lats) - 1)

            transform = from_bounds(
                lons.min() - lon_res / 2,
                lats.min() - lat_res / 2,
                lons.max() + lon_res / 2,
                lats.max() + lat_res / 2,
                data_array.shape[1],
                data_array.shape[0]
            )

            # Save as GeoTIFF
            with rasterio.open(
                    output_file,
                    'w',
                    driver='GTiff',
                    height=data_array.shape[0],
                    width=data_array.shape[1],
                    count=1,
                    dtype=data_array.dtype,
                    crs=CRS.from_epsg(4326),
                    transform=transform,
                    nodata=-9999
            ) as dst:
                dst.write(data_array, 1)

                # Add metadata
                dst.update_tags(
                    parameter=parameter,
                    source='Sentinel-3 OLCI',
                    date=target_date,
                    units=getattr(data_var, 'units', 'unknown')
                )

            logger.info(f"Saved {parameter} data to {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Error processing {parameter} data: {e}")
            return None

    def fetch_data(self,
                   aoi: str,
                   date: str,
                   parameters: List[str] = None,
                   output_dir: Optional[str] = None,
                   date_range_days: int = 7,
                   **kwargs) -> Dict[str, str]:
        """
        Fetch Sentinel-3 data for the given AOI and date.
        
        Args:
            aoi: Area of Interest (bbox "min_lon,min_lat,max_lon,max_lat", WKT polygon, or shapefile path)
            date: Target date in YYYY-MM-DD format
            parameters: List of parameters to fetch. Default: ['chl', 'nap', 'cdom']
            output_dir: Directory to save files (overrides instance setting)
            date_range_days: Number of days before/after to search for data
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Dictionary mapping parameter names to saved file paths
        """
        # Check dependencies
        self._check_dependencies()

        # Set default parameters
        if parameters is None:
            parameters = ['chl', 'nap', 'cdom']

        # Validate parameters
        self.validate_parameters(parameters)

        # Set output directory if provided
        if output_dir is not None:
            original_output_dir = self.output_dir
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Parse inputs
            bbox = self._parse_aoi(aoi)
            target_date = datetime.strptime(date, '%Y-%m-%d')
            start_date, end_date = self._find_nearest_date(target_date, date_range_days)

            logger.info(f"Fetching Sentinel-3 data for AOI: {bbox}")
            logger.info(f"Target date: {date}, Search window: {start_date} to {end_date}")

            results = {}

            for param in parameters:
                logger.info(f"Processing {param.upper()}...")

                # Fetch data
                ds = self._fetch_data_copernicusmarine(param, bbox, start_date, end_date)

                if ds is not None:
                    # Process and save
                    output_file = self._process_and_save_data(ds, param, bbox, date)
                    if output_file:
                        results[param] = output_file

                    # Clean up
                    ds.close()
                else:
                    logger.warning(f"Failed to fetch {param} data")

            return results

        finally:
            # Restore original output directory if it was changed
            if output_dir is not None:
                self.output_dir = original_output_dir
