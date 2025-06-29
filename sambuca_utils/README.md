# SAMBUCA Utils

Utility package for SAMBUCA with data fetching capabilities.

## Overview

This package provides data fetching utilities for the SAMBUCA ecosystem, including support for downloading satellite data from various sources like Sentinel-3 OLCI.

## Features

- **Sentinel-3 OLCI Data Fetching**: Download water quality parameters (chlorophyll, suspended matter, CDOM) from Copernicus Marine Service
- **Professional Visualization**: Advanced plotting and visualization tools for SAMBUCA inversion results
- **Flexible AOI Support**: Bounding boxes, WKT polygons, or shapefiles
- **Multiple Data Sources**: Automatic fallback between different dataset versions
- **Professional Data Processing**: Outputs calibrated GeoTIFF files ready for analysis

## Installation

Install from source:

```bash
# Navigate to package directory
cd sambuca_utils

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

## Usage

### Basic Data Fetching

```python
from sambuca_utils.data_fetchers import DataFetcherFactory

# Create a Sentinel-3 data fetcher
fetcher = DataFetcherFactory.create('sentinel3')

# Fetch data for an area of interest
results = fetcher.fetch_data(
    aoi="-122.5,-37.8,-122.3,-37.6",  # San Francisco Bay bbox
    date="2023-06-15",
    parameters=["chl", "nap", "cdom"]
)

# Results contain paths to downloaded GeoTIFF files
print(f"Chlorophyll data: {results['chl']}")
print(f"Suspended matter data: {results['nap']}")
print(f"CDOM data: {results['cdom']}")
```

### Advanced Usage

```python
# Use WKT polygon for AOI
aoi_polygon = "POLYGON((-122.5 -37.8, -122.3 -37.8, -122.3 -37.6, -122.5 -37.6, -122.5 -37.8))"

# Custom output directory and date range
results = fetcher.fetch_data(
    aoi=aoi_polygon,
    date="2023-06-15",
    parameters=["chl"],
    output_dir="./data/satellite",
    date_range_days=10  # Search ±10 days for available data
)
```

### Authentication

For Copernicus Marine Service data, set environment variables:

```bash
export COP_MARINE_USER="your_username"
export COP_MARINE_PASS="your_password"
```

### Result Visualization

Visualize SAMBUCA inversion results with professional plotting tools:

```python
from sambuca.core.results import ImageInversionResult
from sambuca_utils.visualization import ResultVisualizer

# Assuming you have an inversion result
result = ImageInversionResult(...)  # From your SAMBUCA inversion

# Create visualizer
viz = ResultVisualizer(result)

# Plot individual parameters
fig1 = viz.plot_parameter('depth', colormap='viridis')
fig2 = viz.plot_parameter('chl', colormap='YlGn')

# Create comprehensive summary plot
summary_fig = viz.create_summary_plot(figsize=(15, 10))

# Save plots
summary_fig.savefig('inversion_summary.png', dpi=300, bbox_inches='tight')
```

### Advanced Visualization

```python
# Custom visualization with specific parameters
fig = viz.plot_parameter(
    'depth', 
    figsize=(12, 8),
    colormap='plasma',
    vmin=0, vmax=10  # Custom value range
)

# Create publication-ready plots
summary = viz.create_summary_plot(figsize=(20, 12))
summary.savefig(
    'results_for_publication.pdf', 
    dpi=300, 
    bbox_inches='tight',
    facecolor='white'
)
```

## Development

To contribute to this package:

```bash
# Install with development dependencies
pip install -e .[dev]

# Run tests (when available)
pytest

# Format code
black sambuca_utils/
isort sambuca_utils/

# Type checking
mypy sambuca_utils/
```

## Requirements

- Python >= 3.8
- numpy >= 1.20.0
- matplotlib >= 3.5.0
- copernicusmarine >= 1.0.0
- xarray >= 0.20.0
- rasterio >= 1.2.0
- geopandas >= 0.12.0
- shapely >= 1.8.0
- pandas >= 1.3.0
- scipy >= 1.7.0

### Module Dependencies

- **Data Fetching**: copernicusmarine, xarray, rasterio, geopandas, shapely
- **Visualization**: matplotlib, numpy
- **Core Utilities**: pandas, scipy

### Supported Data Sources

- **Sentinel-3 OLCI**: Chlorophyll, Total Suspended Matter, CDOM via Copernicus Marine Service
- **Parameters Available**: 
  - `chl`: Chlorophyll-a concentration
  - `nap`: Non-algal particles / Total Suspended Matter
  - `cdom`: Colored Dissolved Organic Matter
  - `kd`: Diffuse attenuation coefficient

## License

MIT License - see the main project repository for details.

## Related Packages

This package is part of the SAMBUCA ecosystem:
- [sambuca-core](https://github.com/lmschwenger/sambuca_core_remastered) - Main SAMBUCA package

## Contributing

This package follows standard Python development practices. Please refer to the main repository for contribution guidelines.
