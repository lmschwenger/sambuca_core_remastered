SAMBUCA Core Remastered Documentation
=====================================

**Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment**

Welcome to the comprehensive documentation for SAMBUCA Core Remastered, a modernized Python implementation of the physics-based radiative transfer model for deriving water column properties and bathymetry from remote sensing data.

.. image:: https://img.shields.io/badge/Python-3.8%2B-blue
   :alt: Python Version
   :target: https://python.org

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :alt: License
   :target: https://opensource.org/licenses/MIT

Overview
--------

SAMBUCA Core is a powerful tool for analyzing shallow water environments using satellite imagery. It combines advanced radiative transfer modeling with modern Python infrastructure to provide:

🌊 **Physics-Based Forward Model**
   Semi-analytical radiative transfer modeling based on Lee et al. for accurate water column simulation

🎯 **Flexible Inversion Methods**
   Multiple optimization approaches including scipy-based optimization and lookup tables

🛰️ **Multi-Sensor Support**
   Built-in support for Sentinel-2, Landsat, MODIS, and custom sensors

📊 **SIOP Management**
   Comprehensive handling of Spectral Inherent Optical Properties with automatic interpolation

🚀 **High Performance**
   Optimized for large-scale image processing with parallel computing support

📈 **Uncertainty Quantification**
   NEDR-weighted inversions and error analysis capabilities

What Can SAMBUCA Derive?
------------------------

SAMBUCA can simultaneously estimate multiple water column and benthic properties:

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Parameter
     - Description
     - Units
   * - **Depth**
     - Water column depth
     - meters (m)
   * - **Chlorophyll**
     - Phytoplankton concentration
     - mg/m³
   * - **CDOM**
     - Colored dissolved organic matter
     - m⁻¹
   * - **NAP**
     - Non-algal particulate matter
     - mg/L
   * - **Substrate**
     - Bottom composition (sand, seagrass, coral, etc.)
     - reflectance

Quick Start
-----------

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np

   # 1. Set up SIOP manager and load spectral libraries
   siop_manager = sbc.SIOPManager("data/")
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

Installation
------------

Install SAMBUCA Core Remastered directly from GitHub:

.. code-block:: bash

   # Basic installation
   pip install git+https://github.com/lmschwenger/sambuca_core_remastered.git

   # With GUI support
   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[gui]"

   # Complete installation with all features
   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

For development installation, see the :doc:`installation` guide.

Scientific Background
---------------------

SAMBUCA implements the semi-analytical radiative transfer model described in:

- **Lee et al. (1999)** - Hyperspectral remote sensing for shallow waters
- **Lee et al. (2001)** - Properties of the water column and bottom derived from Hyperion data
- **Brando et al. (2009)** - A physics based retrieval and quality assessment of bathymetry from suboptimal hyperspectral data

The model accounts for:

- Water column absorption and scattering (pure water, phytoplankton, CDOM, sediments)
- Bottom substrate reflectance and mixing
- Sensor-specific spectral response functions
- Atmospheric effects (when coupled with atmospheric correction)

Documentation Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/index
   user_guide/getting_started
   user_guide/forward_modeling
   user_guide/inversion
   user_guide/siop_management
   user_guide/image_processing
   user_guide/configuration

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/core
   api/forward_model
   api/siop_manager
   api/inversion
   api/gui

.. toctree::
   :maxdepth: 2
   :caption: Theory & Background

   theory/index
   theory/radiative_transfer
   theory/optical_properties
   theory/algorithms

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/index
   examples/basic_usage
   examples/advanced_examples
   examples/tutorials

Acknowledgments
===============

This project builds upon the original `SAMBUCA implementation <https://github.com/csiro-aquatic-remote-sensing/sambuca_core>`_ 
developed by CSIRO's Oceans and Atmosphere team. We gratefully acknowledge the foundational work of the original development team.

Key References:

- **Original SAMBUCA Model**: `CSIRO SAMBUCA Core <https://github.com/csiro-aquatic-remote-sensing/sambuca_core>`_
- **SWAMpy**: `Continued work by Steve Sagar <https://github.com/stevesagar/SWAMpy/tree/master>`_
- **Ocean Optics Web Book**: `Invaluable resource <https://www.oceanopticsbook.info/>`_

License
=======

This project is licensed under the MIT License. See the `LICENSE <https://github.com/lmschwenger/sambuca_core_remastered/blob/main/LICENSE>`_ file for details.

Support & Contributing
=====================

- **Issues**: `GitHub Issues <https://github.com/lmschwenger/sambuca_core_remastered/issues>`_
- **Discussions**: `GitHub Discussions <https://github.com/lmschwenger/sambuca_core_remastered/discussions>`_
- **Original SAMBUCA**: `CSIRO repository <https://github.com/csiro-aquatic-remote-sensing/sambuca_core>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
