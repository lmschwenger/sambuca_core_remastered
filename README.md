# Sambuca Core

[![Python Tests](https://github.com/csiro-aquatic-remote-sensing/sambuca_core/actions/workflows/python-tests.yml/badge.svg)](https://github.com/lmschwenger/sambuca_core_remastered/actions/workflows/python-tests.yml)
[![Documentation Status](https://readthedocs.org/projects/sambuca-core/badge/?version=latest)](https://sambuca-core.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/sambuca-core.svg)](https://badge.fury.io/py/sambuca-core)

Core model components for the Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment (SAMBUCA).
This repository is heavily inspired by the older https://github.com/csiro-aquatic-remote-sensing/sambuca_core/tree/master/sambuca_core
## Description

Sambuca is a sensor-agnostic physics-based inversion model developed by CSIRO for estimating water column composition, bathymetry, and bottom substrate composition from remote sensing data. This package contains the core model components for Sambuca.

## Features

- Forward model for spectral calculations
- Sensor filter handling and application
- Spectra operations and conversions
- Support for various data formats (ENVI, CSV, Excel)

## Installation

```bash
pip install sambuca-core
```

## Usage

Basic usage example:

```python
import sambuca_core as sbc

# Load spectra
siop_directory = "path/to/siop_directory"
siops = sbc.load_all_spectral_libraries(siop_directory)

# Forward model example
wavelengths = siops["water_absorption"][0]
a_water = siops["water_absorption"][1]
a_ph_star = siops["phytoplankton_absorption"][1]
substrate1 = siops["sand_substrate"][1]

# Run forward model
results = sbc.forward_model(
    chl=1.5,             # Chlorophyll concentration
    cdom=0.5,            # CDOM concentration
    nap=2.0,             # Non-algal particulate concentration
    depth=5.0,           # Water depth in meters
    substrate1=substrate1,
    wavelengths=wavelengths,
    a_water=a_water,
    a_ph_star=a_ph_star,
    num_bands=len(wavelengths)
)

# Access results
print(results.rrs)  # Remote sensing reflectance
print(results.kd)   # Diffuse attenuation coefficient
```