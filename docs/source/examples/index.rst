Examples
========

Practical examples showing how to use SAMBUCA with real data.

Basic Bathymetry Processing
---------------------------

**Simple workflow for bathymetry mapping:**

.. code-block:: python

   from sambuca.core.workflows import BathymetryWorkflow
   from pathlib import Path

   # Setup paths
   siop_dir = Path("../data/siops")
   image_path = Path("../data/input/example_groensund.tif")
   output_dir = Path("../data/output/example_groensund")

   # Create workflow
   workflow = BathymetryWorkflow(str(siop_dir), sensor='sentinel2')

   # Optional: customize parameters
   workflow.customize_parameters(
       depth=(0, 25),
       fixed_chl=0.5,
       fixed_nap=0.001,
       fixed_cdom=0.0025,
       fixed_substrate_fraction=1,
   )

   workflow.wavelengths = [492.4, 559.8, 664.6, 704.1]
   workflow.bands = [2, 3, 4, 5]

   # Process image
   result = workflow.process_image(
       image_path=str(image_path),
       n_processes=4,
       progress_bar=True
   )

   # Save results
   result.print_summary()
   result.plot_summary(save_path=str(output_dir / "summary.png"))
   result.save_all_parameters(str(output_dir), formats=['tiff', 'png'])

Fast Processing with Lookup Tables
----------------------------------

**For repeated processing or large images:**

.. code-block:: python

   from sambuca.core.workflows import BathymetryWorkflow
   from sambuca.core.inversion import LookUpTable, process_image
   from pathlib import Path

   # Setup
   workflow = BathymetryWorkflow("../data/siops", sensor='sentinel2')
   
   # Configure for depth-only inversion (fastest)
   workflow.customize_parameters(
       depth=(0, 25),
       fixed_chl=5.6,
       fixed_nap=0.001,
       fixed_cdom=0.09,
       fixed_substrate_fraction=1,
   )

   # Build LUT
   lut = LookUpTable(workflow.inversion_params)
   lut.build_table(
       grid_size=200,
       progress_bar=True,
       use_kdtree=True
   )

   # Load and process image
   image_data = workflow.image_loader.load("my_image.tif", bands=[2, 3, 4, 5])
   
   results = process_image(
       image_data.data,
       workflow.inversion_params,
       lut=lut,  # Use LUT for speed
       n_processes=4,
       progress_bar=True,
       refinement=False  # Pure LUT lookup
   )

   print(f"Processing complete. Depth range: {results['depth'].min():.1f} - {results['depth'].max():.1f} m")

Environmental Data Integration
-----------------------------

**Using Sentinel-3 water quality data:**

.. code-block:: python

   from sambuca.core.workflows import BathymetryWorkflow
   from scripts.sambuca_sentinel3_integration import SambucaSentinel3Integration

   # Fetch Sentinel-3 environmental data
   integration = SambucaSentinel3Integration()
   
   s3_data = integration.fetch_and_prepare_data(
       aoi="145.7781,-16.2839,145.8000,-16.2700",  # Great Barrier Reef area
       date="2024-06-15",
       parameters=['chl', 'nap', 'cdom']
   )

   # Extract values for a specific location
   point_values = integration.extract_point_values(
       s3_data, 
       lon=145.78, 
       lat=-16.27
   )

   # Use in SAMBUCA workflow
   workflow = BathymetryWorkflow("data/siops", sensor='sentinel2')
   
   # Incorporate S3 values as priors or validation
   print(f"Sentinel-3 chlorophyll: {point_values['chl']:.2f} mg/m³")

Data Requirements
----------------

**Input files needed:**

1. **Sentinel-2 Level-2A image** - atmospherically corrected reflectance
2. **SIOP files** - located in `data/siops/` directory

**File structure:**
::

   data/
   ├── siops/                    # Spectral optical properties
   │   ├── a_cdom.txt
   │   ├── a_nap.txt
   │   ├── a_ph_star.txt
   │   └── ...
   ├── input/
   │   └── my_sentinel2_image.tif
   └── output/                   # Results saved here

**Sentinel-2 bands:**
- B2 (Blue, 490nm)
- B3 (Green, 560nm)
- B4 (Red, 665nm)
- B8A (NIR, 705nm)

Common Patterns
--------------

**Standard Sentinel-2 processing:**

.. code-block:: python

   workflow = BathymetryWorkflow("data/siops", sensor='sentinel2')
   workflow.wavelengths = [492.4, 559.8, 664.6, 704.1]
   workflow.bands = [2, 3, 4, 5]  # B2, B3, B4, B8A

**Depth-only mapping (fastest):**

.. code-block:: python

   workflow.customize_parameters(
       depth=(0, 25),           # Only estimate depth
       fixed_chl=1.0,           # Fix other parameters
       fixed_nap=0.5,
       fixed_cdom=0.1
   )

**Full water quality mapping:**

.. code-block:: python

   workflow.customize_parameters(
       depth=(0, 25),
       chl=(0.1, 10.0),         # Estimate all parameters
       nap=(0.1, 5.0),
       cdom=(0.01, 2.0)
   )

Tips for Success
---------------

- **Use Level-2A data** - atmospherically corrected Sentinel-2 only
- **Shallow water only** - SAMBUCA works best in < 25m depth
- **Clear water preferred** - turbid water reduces accuracy
- **Build LUTs once** - reuse for multiple images
- **Start simple** - fix most parameters, estimate depth only
- **Validate results** - compare with field measurements when possible

Troubleshooting
--------------

**Common issues:**

- **All NaN results**: Check image format and band order
- **Unrealistic depths**: Adjust depth range in parameters
- **Slow processing**: Use lookup tables or reduce image size
- **Poor accuracy**: Validate SIOP data for your study area

**Performance tips:**

- Use `n_processes=4` or match your CPU cores
- Build LUTs for repeated processing
- Process image tiles for very large files
- Use `refinement=False` with LUTs for maximum speed

See the `examples/` directory for complete working scripts.
