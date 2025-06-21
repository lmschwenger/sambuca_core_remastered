# SAMBUCA Core

[![Documentation Status](https://readthedocs.org/projects/sambuca-core-remastered/badge/?version=latest)](https://sambuca-core-remastered.readthedocs.io/en/latest/?badge=latest)

**Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment (SAMBUCA)**

SAMBUCA Core is a modernized Python implementation of the physics-based radiative transfer model for deriving water column properties and bathymetry from remote sensing data. This version builds upon the original SAMBUCA model developed by CSIRO's Oceans and Atmosphere team, providing enhanced performance, improved usability, and modern Python packaging.

> **🏛️ Original Work**: This implementation is heavily inspired by and builds upon the original [SAMBUCA model](https://github.com/csiro-aquatic-remote-sensing/sambuca_core) developed by CSIRO. We gratefully acknowledge the foundational work of the original development team.

## ✨ Key Features

- **🌊 Physics-Based Forward Model**: Semi-analytical radiative transfer modeling based on Lee et al.
- **🎯 Flexible Inversion Methods**: Multiple optimization approaches including scipy-based optimization and lookup tables
- **🛰️ Multi-Sensor Support**: Built-in support for Sentinel-2, Landsat, MODIS, and custom sensors
- **📊 SIOP Management**: Comprehensive handling of Spectral Inherent Optical Properties with automatic interpolation
- **🚀 High Performance**: Optimized for large-scale image processing with parallel computing support
- **📈 Uncertainty Quantification**: NEDR-weighted inversions and error analysis capabilities

## 🚀 Quick Start

### Installation

**Clone and install from source:**

```bash
git clone https://github.com/lmschwenger/sambuca_core_remastered.git
cd sambuca_core_remastered

# Basic installation
pip install -e .

# Or with GUI support
pip install -e .[gui]

# Or complete installation with all features
pip install -e .[complete]
```

**Or install directly from GitHub:**

```bash
# Basic installation
pip install git+https://github.com/lmschwenger/sambuca_core_remastered.git

# With GUI support
pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[gui]"
```

### Basic Usage

```python
import sambuca_core as sbc
import numpy as np

# 1. Set up SIOP manager and load spectral libraries
siop_manager = sbc.SIOPManager("data/")  # Use included spectral libraries
siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])

# 2. Get standard SIOPs for Sentinel-2
siops = siop_manager.get_standard_siops("Sentinel-2")

# 3. Run forward model
results = sbc.forward_model(
    chl=1.5,           # Chlorophyll concentration (mg/m³)
    cdom=0.5,          # CDOM absorption (1/m)
    nap=2.0,           # Non-algal particles (mg/L)
    depth=5.0,         # Water depth (m)
    substrate1=siops['substrate1'],
    wavelengths=siops['wavelengths'],
    a_water=siops['a_water'],
    a_ph_star=siops['a_ph_star'],
    num_bands=siops['num_bands']
)

print(f"Modeled reflectance: {results.rrs}")
print(f"Number of bands: {siops['num_bands']}")
```

### Single Pixel Inversion

```python
from sambuca_core.inversion import InversionParameters, invert_spectrum

# Observed reflectance (e.g., from Sentinel-2 pixel)
observed_rrs = np.array([0.012, 0.015, 0.008, 0.006])

# Set up inversion parameters
params = InversionParameters(
    depth=(0, 25),      # Invert for depth (0-25m range)
    chl=(0.1, 10.0),    # Invert for chlorophyll (0.1-10 mg/m³)
    cdom=(0.01, 2.0),   # Invert for CDOM (0.01-2.0 m⁻¹)
    wavelengths=siops['wavelengths']
)

# Update with SIOPs from manager
params.update_from_siop_manager(siop_manager, "Sentinel-2")

# Run inversion
result = invert_spectrum(observed_rrs, params)

print(f"Estimated depth: {result.parameters['depth']:.2f} m")
print(f"Estimated chlorophyll: {result.parameters['chl']:.2f} mg/m³")
print(f"Estimation error (RMSE): {result.objective_value:.6f}")
```

### Image Processing

```python
from sambuca_core.inversion import process_image

# Load Sentinel-2 image (assuming pre-processed reflectance data)
# Image should be in shape (height, width, 4) for the 4 Sentinel-2 bands
# You can use rasterio, numpy, or other tools to load your data
import numpy as np

# Example: Load your preprocessed Sentinel-2 reflectance image
# image = your_image_loading_function("sentinel2_reflectance.tif")
# For demo purposes, create synthetic data:
image = np.random.random((100, 100, 4)) * 0.05  # Shape: (height, width, bands)

# Process entire image
results = process_image(
    image,
    params,
    n_processes=4,      # Parallel processing
    progress_bar=True
)

# Access parameter maps
depth_map = results['depth']         # Bathymetry map
chlorophyll_map = results['chl']     # Chlorophyll concentration map
error_map = results['error']         # Inversion error map
```

## 📊 What Can SAMBUCA Derive?

SAMBUCA can simultaneously estimate multiple water column and benthic properties:

| Parameter | Description | Units |
|-----------|-------------|-------|
| **Depth** | Water column depth | meters (m) |
| **Chlorophyll** | Phytoplankton concentration | mg/m³ |
| **CDOM** | Colored dissolved organic matter | m⁻¹ |
| **NAP** | Non-algal particulate matter | mg/L |
| **Substrate** | Bottom composition (sand, seagrass, coral, etc.) | reflectance |

## 🛰️ Supported Sensors

- **Sentinel-2** (MSI) - 10-60m resolution
- **Custom sensors** - Define your own wavelengths

## 🎯 Working Examples

The repository includes working examples to help you get started:

### GUI Application
```bash
# Launch the graphical interface
sambuca-gui
# or
python run_gui.py
```

### Basic Examples
Check the `examples/` directory for:
- **Forward Model Demo** - Run the radiative transfer model
- **SIOP Management** - Load and interpolate spectral libraries  
- **Single Pixel Inversion** - Estimate water properties from a spectrum

### Advanced Usage
- **Image Processing** - Process full Sentinel-2 scenes
- **Custom Sensors** - Define your own wavelength configurations
- **Parameter Studies** - Explore model sensitivity

## 📚 Getting Started

### Quick Test
```bash
# Verify installation
python test_installation.py

# Test core functionality
python -m sambuca_core

# Launch GUI
sambuca-gui
```

### Example Workflow
1. **Install** the package with GUI support: `pip install -e .[gui]`
2. **Launch GUI** to explore the interface: `sambuca-gui`
3. **Check examples** directory for code samples
4. **Load your data** and start processing Sentinel-2 imagery
## 🔬 Scientific Background

SAMBUCA implements the semi-analytical radiative transfer model described in:

- **Lee et al. (1999)** - Hyperspectral remote sensing for shallow waters
- **Lee et al. (2001)** - Properties of the water column and bottom derived from Hyperion data
- **Brando et al. (2009)** - A physics based retrieval and quality assessment of bathymetry from suboptimal hyperspectral data

The model accounts for:
- Water column absorption and scattering (pure water, phytoplankton, CDOM, sediments)
- Bottom substrate reflectance and mixing
- Sensor-specific spectral response functions
- Atmospheric effects (when coupled with atmospheric correction)

## ⚡ Performance Features

- **Parallel Processing**: Multi-core image processing with configurable worker count
- **Memory Optimization**: Efficient handling of large satellite images
- **Lookup Tables**: Pre-computed model results for rapid inversion
- **Sensor Filters**: Automatic spectral resampling for different sensors
- **Progress Tracking**: Real-time progress bars for long-running processes

## 🔧 Installation & Requirements

### Requirements
- Python 3.8+
- NumPy >= 1.20.0
- SciPy >= 1.7.0
- Pandas >= 1.3.0
- Matplotlib >= 3.5.0 (required for GUI)

### Installation Options

```bash
# Core functionality only
pip install -e .

# With GUI support
pip install -e .[gui]

# With raster processing capabilities
pip install -e .[raster]  # Includes rasterio, gdal

# Complete installation with all features
pip install -e .[complete]

# Development installation
pip install -e .[dev]  # Includes testing, linting tools
```

### Development Installation

**For development and contributing:**

```bash
git clone https://github.com/lmschwenger/sambuca_core_remastered.git
cd sambuca_core_remastered

# Install with development dependencies
pip install -e .[dev]

# Run tests
python test_installation.py
pytest tests/
```

## 📖 Documentation

- **[📚 Complete Documentation](https://sambuca-core-remastered.readthedocs.io/en/latest/)** - Full documentation on Read the Docs
- **[API Reference](docs/api/)** - Complete function documentation
- **[Theory Guide](docs/theory/)** - Scientific background and equations
- **[Tutorials](tutorials/)** - Jupyter notebook tutorials
- **[FAQ](docs/faq.md)** - Common questions and solutions

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/lmschwenger/sambuca_core_remastered.git
cd sambuca_core_remastered
pip install -e ".[dev]"
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original SAMBUCA Model**: This work builds upon the [original SAMBUCA implementation](https://github.com/csiro-aquatic-remote-sensing/sambuca_core) developed by CSIRO's Oceans and Atmosphere team
- **[SAMBUCA Scientific Papers](https://doi.org/10.4225/08/5866a187b7a3c)** - Key scientific publication
- **[SWAMpy](https://github.com/stevesagar/SWAMpy/tree/master)** - Continued work by Steve Sagar has also been an invaluable source of inspiration 
- **[Ocean Optics Web Book](https://www.oceanopticsbook.info/)** - Invaluable resource of information

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/lmschwenger/sambuca_core_remastered/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lmschwenger/sambuca_core_remastered/discussions)
- **Original SAMBUCA**: For questions about the original implementation, see the [CSIRO repository](https://github.com/csiro-aquatic-remote-sensing/sambuca_core)

---

*SAMBUCA Core Remastered - Building on CSIRO's foundation to turn satellite pixels into oceanographic insights* 🌊🛰️

**Original SAMBUCA**: [github.com/csiro-aquatic-remote-sensing/sambuca_core](https://github.com/csiro-aquatic-remote-sensing/sambuca_core)