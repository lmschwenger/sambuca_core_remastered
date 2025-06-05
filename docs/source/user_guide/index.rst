User Guide
==========

This comprehensive user guide will walk you through all aspects of using SAMBUCA Core, from basic concepts to advanced applications.

.. toctree::
   :maxdepth: 2

   getting_started
   forward_modeling  
   inversion
   siop_management
   image_processing
   configuration

Getting Started
---------------

If you're new to SAMBUCA Core, start here:

:doc:`getting_started`
   Essential concepts, installation verification, and your first forward model

:doc:`forward_modeling`
   Understanding and using the radiative transfer forward model

:doc:`siop_management` 
   Managing Spectral Inherent Optical Properties for different sensors

Core Workflows
--------------

Learn the main SAMBUCA workflows:

:doc:`inversion`
   Estimating water properties from satellite observations

:doc:`image_processing`
   Processing entire satellite scenes to create parameter maps

Advanced Topics
---------------

:doc:`configuration`
   Detailed parameter reference and optimization strategies

Quick Navigation
----------------

**I want to...**

📊 **Model satellite reflectance**
   → :doc:`forward_modeling`

🔍 **Estimate water properties from spectra**  
   → :doc:`inversion`

🗺️ **Process satellite images**
   → :doc:`image_processing`

⚙️ **Manage spectral libraries**
   → :doc:`siop_management`

🎛️ **Customize model parameters**
   → :doc:`configuration`

**By Application**

🌊 **Shallow Water Mapping**
   Forward modeling + inversion for bathymetry and water quality

🛰️ **Satellite Data Processing**
   Large-scale image processing workflows

🔬 **Research Applications**
   Parameter sensitivity studies and method development

📈 **Validation Studies**
   Comparing model results with field measurements

Prerequisites
-------------

Before diving into the user guide, make sure you have:

✅ **Installed SAMBUCA Core** (see :doc:`../installation`)  
✅ **Basic Python knowledge** (NumPy, basic plotting)  
✅ **Understanding of remote sensing concepts** (reflectance, wavelengths)  
✅ **Familiarity with water optics** (helpful but not required)

Key Concepts
------------

**Forward Model**
   Simulates satellite observations given water properties (depth, chlorophyll, etc.)

**Inversion**
   Estimates water properties from observed satellite reflectance

**SIOPs**
   Spectral Inherent Optical Properties - fundamental optical properties of water constituents

**Sensors**
   Satellite instruments with specific wavelength configurations (Sentinel-2, Landsat, etc.)

**Substrates**
   Bottom types (sand, seagrass, coral) that influence shallow water reflectance

Learning Path
-------------

**Beginner** (New to SAMBUCA)
   1. :doc:`getting_started` - Basic concepts and first examples
   2. :doc:`forward_modeling` - Understanding the physics
   3. :doc:`siop_management` - Working with spectral libraries

**Intermediate** (Familiar with basics)
   1. :doc:`inversion` - Parameter estimation techniques
   2. :doc:`image_processing` - Working with satellite data
   3. :doc:`configuration` - Optimizing performance

**Advanced** (Research/Development)
   1. Custom sensor configurations
   2. Algorithm modifications
   3. Performance optimization
   4. Integration with other tools

Examples by Use Case
--------------------

**Water Quality Monitoring**

.. code-block:: python

   # Estimate chlorophyll from Sentinel-2 pixel
   from sambuca_core.inversion import InversionParameters, invert_spectrum
   
   observed_rrs = [0.012, 0.015, 0.008, 0.006]  # Sentinel-2 reflectance
   
   params = InversionParameters(
       chl=(0.1, 20.0),    # Focus on chlorophyll estimation
       depth=(1, 30),      # Known shallow water
       cdom=(0.01, 1.0),   # Typical CDOM range
   )
   
   result = invert_spectrum(observed_rrs, params)
   print(f"Chlorophyll: {result.parameters['chl']:.2f} mg/m³")

**Bathymetric Mapping**

.. code-block:: python

   # Focus on accurate depth estimation
   params = InversionParameters(
       depth=(0, 25),      # Primary focus on depth
       chl=(0.5, 5.0),     # Constrain chlorophyll
       substrate_fraction=(0, 1),  # Allow substrate mixing
   )
   
   depth_map = process_image(sentinel2_image, params)['depth']

**Substrate Classification**

.. code-block:: python

   # Estimate substrate composition
   params = InversionParameters(
       substrate_fraction=(0, 1),  # Sand vs seagrass mixing
       depth=(2, 15),              # Known depth range
   )
   
   substrate_map = process_image(image, params)['substrate_fraction']

Getting Help
------------

If you need assistance:

📖 **Documentation**: Browse the complete :doc:`../api/index`  
💬 **Discussions**: Join `GitHub Discussions <https://github.com/lmschwenger/sambuca_core_remastered/discussions>`_  
🐛 **Issues**: Report bugs on `GitHub Issues <https://github.com/lmschwenger/sambuca_core_remastered/issues>`_  
📧 **Contact**: Reach out to the development team

Related Resources
-----------------

**Scientific Background**
   :doc:`../theory/index` - Theoretical foundation and equations

**Practical Examples**  
   :doc:`../examples/index` - Complete working examples and tutorials

**API Reference**
   :doc:`../api/index` - Detailed function and class documentation

**Installation**
   :doc:`../installation` - Setup instructions for all platforms

Next Steps
----------

Ready to start? Begin with :doc:`getting_started` for a gentle introduction to SAMBUCA Core's capabilities.

For experienced users, jump directly to the section most relevant to your needs using the navigation above.
