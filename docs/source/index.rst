SAMBUCA Core Documentation
==========================

**Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment**

SAMBUCA processes Sentinel-2 satellite imagery to create bathymetry (depth) maps of shallow water areas using physics-based radiative transfer modeling.

.. image:: https://img.shields.io/badge/Python-3.8%2B-blue
   :alt: Python Version
   :target: https://python.org

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :alt: License
   :target: https://opensource.org/licenses/MIT

What SAMBUCA Does
-----------------

🌊 **Bathymetry Mapping**
   Extract water depth from Sentinel-2 imagery in shallow coastal areas

🚀 **Fast Processing**
   Optimized workflows with lookup tables for operational use

📊 **Water Quality**
   Estimate chlorophyll, CDOM, and suspended sediments alongside depth

🛰️ **Sentinel-2 Ready**
   Built specifically for Sentinel-2 Level-2A reflectance data

Quick Start
-----------

.. code-block:: python

   from sambuca.core.workflows import BathymetryWorkflow

   # Setup workflow
   workflow = BathymetryWorkflow("data/siops", sensor='sentinel2')
   
   # Process image
   result = workflow.process_image(
       image_path="my_sentinel2_image.tif",
       n_processes=4,
       progress_bar=True
   )
   
   # Save results
   result.save_all_parameters("output/", formats=['tiff', 'png'])

**That's it!** You now have bathymetry maps.

Installation
------------

.. code-block:: bash

   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git"

See :doc:`installation` for detailed setup instructions.

Scientific Background
---------------------

SAMBUCA implements the semi-analytical radiative transfer model based on Lee et al. (1999, 2001) for shallow water remote sensing. The model accounts for water column optical properties, bottom substrate reflectance, and sensor characteristics.

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
