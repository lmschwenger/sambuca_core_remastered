Quick Start Guide
=================

Get SAMBUCA working with Sentinel-2 data in 5 minutes.

Installation
------------

.. code-block:: bash

   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git"

What SAMBUCA Does
-----------------

SAMBUCA processes Sentinel-2 satellite imagery to create bathymetry (depth) maps of shallow water areas.

Basic Usage - Process Sentinel-2 Image
---------------------------------------

**Get bathymetry from a Sentinel-2 image:**

.. code-block:: python

   from sambuca.core.workflows import BathymetryWorkflow
   from pathlib import Path

   # Setup workflow
   workflow = BathymetryWorkflow("data/siops", sensor='sentinel2')
   
   # Optional: customize parameters
   workflow.customize_parameters(
       depth=(0, 25),
       fixed_chl=0.5,
       fixed_nap=0.001,
       fixed_cdom=0.0025
   )
   
   # Process image
   result = workflow.process_image(
       image_path="my_sentinel2_image.tif",
       n_processes=4,
       progress_bar=True
   )
   
   # Save results
   result.save_all_parameters("output/", formats=['tiff', 'png'])
   result.plot_summary(save_path="output/summary.png")
   
   print(f"Results saved to: output/")

**That's it!** You now have bathymetry maps.

Fast Processing with Lookup Tables
----------------------------------

**For large images or repeated processing:**

.. code-block:: python

   from sambuca.core.inversion import LookUpTable

   # Build LUT once
   lut = LookUpTable(workflow.inversion_params)
   lut.build_table(grid_size=200, progress_bar=True)
   
   # Process multiple images quickly
   from sambuca.core.inversion import process_image
   results = process_image(
       image_data,
       workflow.inversion_params,
       lut=lut,  # Much faster!
       n_processes=4
   )

**Note:** LUT processing can be 10-100x faster for repeated processing.

Lower-Level API
---------------

**If you need more control over the processing:**

.. code-block:: python

   import sambuca.core as sbc
   
   # Forward model (simulate satellite observation)
   results = sbc.forward_model(
       chl=1.5, cdom=0.5, nap=2.0, depth=5.0,
       substrate1=[0.3, 0.3, 0.25, 0.2],  # Sand bottom
       wavelengths=[492.4, 559.8, 664.6, 704.1],  # Sentinel-2 bands
       a_water=[0.007, 0.015, 0.325, 0.619],
       a_ph_star=[0.055, 0.023, 0.014, 0.010],
       num_bands=4
   )
   print(f"Modeled reflectance: {results.rrs}")
   
   # Single pixel inversion
   from sambuca.core.inversion import InversionParameters, invert_spectrum
   
   params = InversionParameters(
       depth=(0, 25), chl=(0.1, 10.0), cdom=(0.01, 2.0),
       # ... other parameters
   )
   result = invert_spectrum(observed_rrs, params)
   print(f"Estimated depth: {result.parameters['depth']:.1f} m")

Data Requirements
-----------------

**You need:**

1. **Sentinel-2 image** - atmospherically corrected reflectance (Level-2A)
2. **SIOP data** - spectral optical properties (download from [TBD])

**Sentinel-2 bands used:**
- B2 (Blue, 490nm)
- B3 (Green, 560nm) 
- B4 (Red, 665nm)
- B8A (NIR, 705nm)

Next Steps
----------

- **Examples**: Check `examples/` directory for real use cases
- **API Reference**: See documentation for complete function details
- **Sample Data**: Download test images and SIOP data from [TBD]

**Need help?** Open an issue on GitHub.

**Note:** SAMBUCA works best in shallow, clear waters (< 25m depth). Results in turbid or very deep water may be unreliable.
