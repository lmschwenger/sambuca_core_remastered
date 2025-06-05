SIOP Manager
============

.. automodule:: sambuca_core.siop_manager
   :members:
   :undoc-members:
   :show-inheritance:

The SIOP Manager handles Spectral Inherent Optical Properties (SIOPs) for different sensors, providing automatic interpolation and management of spectral libraries.

SIOPManager Class
-----------------

.. autoclass:: sambuca_core.SIOPManager
   :members:
   :undoc-members:
   :show-inheritance:

The :class:`SIOPManager` class is the central component for managing spectral libraries and sensor configurations. It provides:

- **Automatic library loading** from directory structures
- **Sensor registration** with wavelength configurations  
- **Spectral interpolation** to match sensor bands
- **Standard SIOP retrieval** for common use cases

Core Functionality
------------------

Library Loading
~~~~~~~~~~~~~~~

The SIOP manager automatically loads spectral libraries from CSV files:

.. code-block:: python

   # Initialize with automatic loading
   siop_manager = SIOPManager("path/to/spectral/data/")
   
   # Or load manually
   siop_manager = SIOPManager()
   siop_manager.load_libraries("path/to/spectral/data/")

**Supported File Formats:**

- **Two-column CSV**: wavelength, value
- **Multi-column CSV**: wavelength, value1, value2, ...
- **Nested directories**: Automatic recursive discovery

**File Naming Conventions:**

The manager recognizes common naming patterns:

- ``water_absorption.csv`` → ``water_absorption``
- ``phytoplankton_absorption.csv`` → ``phytoplankton_absorption``
- ``sand_substrate.csv`` → ``sand_substrate``
- ``seagrass_substrate.csv`` → ``seagrass_substrate``

Sensor Registration
~~~~~~~~~~~~~~~~~~~

Register sensors with their central wavelengths:

.. code-block:: python

   # Sentinel-2 MSI
   sentinel2_wavelengths = [492.4, 559.8, 664.6, 704.1]
   siop_manager.register_sensor("Sentinel-2", sentinel2_wavelengths)
   
   # Landsat 8 OLI
   landsat8_wavelengths = [482.0, 561.5, 654.5, 864.5]
   siop_manager.register_sensor("Landsat-8", landsat8_wavelengths)
   
   # Custom hyperspectral sensor
   hyper_wavelengths = list(range(400, 801, 10))  # 400-800nm, 10nm steps
   siop_manager.register_sensor("Hyperspectral", hyper_wavelengths)

Spectral Interpolation
~~~~~~~~~~~~~~~~~~~~~~

Automatic interpolation to match sensor wavelengths:

.. code-block:: python

   # Get all SIOPs interpolated for Sentinel-2
   siops = siop_manager.get_siops_for_sensor("Sentinel-2")
   
   print(f"Wavelengths: {siops['wavelengths']}")
   print(f"Available libraries: {[k for k in siops.keys() if k not in ['wavelengths', 'num_bands']]}")

Standard SIOP Retrieval
~~~~~~~~~~~~~~~~~~~~~~~

Get a standard set of SIOPs for forward modeling:

.. code-block:: python

   # Automatically select standard libraries
   standard_siops = siop_manager.get_standard_siops("Sentinel-2")
   
   # Contains: wavelengths, num_bands, a_water, a_ph_star, substrate1, [substrate2]
   print(f"Standard SIOPs: {list(standard_siops.keys())}")

Methods Reference
-----------------

Initialization Methods
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: sambuca_core.SIOPManager.__init__
   :noindex:

.. automethod:: sambuca_core.SIOPManager.load_libraries
   :noindex:

Sensor Management
~~~~~~~~~~~~~~~~~

.. automethod:: sambuca_core.SIOPManager.register_sensor
   :noindex:

.. automethod:: sambuca_core.SIOPManager.get_siops_for_sensor
   :noindex:

.. automethod:: sambuca_core.SIOPManager.get_siops_for_wavelengths
   :noindex:

Library Access
~~~~~~~~~~~~~~

.. automethod:: sambuca_core.SIOPManager.list_available_libraries
   :noindex:

.. automethod:: sambuca_core.SIOPManager.get_common_library_types
   :noindex:

.. automethod:: sambuca_core.SIOPManager.get_standard_siops
   :noindex:

Usage Examples
--------------

Basic Setup
~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   
   # Initialize SIOP manager
   siop_manager = sbc.SIOPManager("data/spectral_libraries/")
   
   # Check what libraries were loaded
   libraries = siop_manager.list_available_libraries()
   print(f"Loaded libraries: {libraries}")
   
   # Group by type
   types = siop_manager.get_common_library_types()
   print(f"Absorption libraries: {types['absorption']}")
   print(f"Substrate libraries: {types['substrate']}")

Multi-Sensor Workflow
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Register multiple sensors
   sensors = {
       "Sentinel-2": [492.4, 559.8, 664.6, 704.1],
       "Landsat-8": [482.0, 561.5, 654.5, 864.5],
       "MODIS": [469.0, 555.0, 645.0, 859.0]
   }
   
   for sensor_name, wavelengths in sensors.items():
       siop_manager.register_sensor(sensor_name, wavelengths)
   
   # Get SIOPs for each sensor
   all_sensor_siops = {}
   for sensor_name in sensors.keys():
       all_sensor_siops[sensor_name] = siop_manager.get_standard_siops(sensor_name)
       print(f"{sensor_name}: {all_sensor_siops[sensor_name]['num_bands']} bands")

Custom Wavelength Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define custom wavelengths (e.g., for atmospheric windows)
   custom_wavelengths = [443, 490, 510, 560, 620, 665, 681, 709, 754, 761, 764, 767, 779]
   
   # Get SIOPs without registering a sensor
   custom_siops = siop_manager.get_siops_for_wavelengths(custom_wavelengths)
   
   # Use in forward model
   results = sbc.forward_model(
       chl=1.5, cdom=0.5, nap=2.0, depth=8.0,
       substrate1=custom_siops['sand_substrate'],
       wavelengths=custom_siops['wavelengths'],
       a_water=custom_siops['water_absorption'],
       a_ph_star=custom_siops['phytoplankton_absorption'],
       num_bands=custom_siops['num_bands']
   )

Working with Specific Libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get specific libraries for analysis
   all_siops = siop_manager.get_siops_for_sensor("Sentinel-2")
   
   # Extract specific components
   water_abs = all_siops['water_absorption']
   ph_abs = all_siops['phytoplankton_absorption']
   sand_refl = all_siops['sand_substrate']
   seagrass_refl = all_siops.get('seagrass_substrate', None)
   
   # Analyze spectral shapes
   import matplotlib.pyplot as plt
   
   wavelengths = all_siops['wavelengths']
   
   plt.figure(figsize=(12, 4))
   
   plt.subplot(1, 3, 1)
   plt.plot(wavelengths, water_abs, 'b-', label='Water')
   plt.plot(wavelengths, ph_abs, 'g-', label='Phytoplankton')
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Absorption (1/m)')
   plt.title('Absorption Spectra')
   plt.legend()
   plt.yscale('log')
   
   plt.subplot(1, 3, 2)
   plt.plot(wavelengths, sand_refl, 'brown', label='Sand')
   if seagrass_refl is not None:
       plt.plot(wavelengths, seagrass_refl, 'green', label='Seagrass')
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Reflectance')
   plt.title('Substrate Reflectance')
   plt.legend()
   
   plt.tight_layout()
   plt.show()

Integration with Forward Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Complete workflow: SIOP management + forward modeling
   
   # 1. Setup
   siop_manager = sbc.SIOPManager("data/")
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])
   
   # 2. Get standard SIOPs
   siops = siop_manager.get_standard_siops("Sentinel-2")
   
   # 3. Run forward model with managed SIOPs
   results = sbc.forward_model(
       chl=2.0, cdom=0.8, nap=1.5, depth=6.0,
       substrate1=siops['substrate1'],
       wavelengths=siops['wavelengths'],
       a_water=siops['a_water'],
       a_ph_star=siops['a_ph_star'],
       num_bands=siops['num_bands']
   )
   
   print(f"Modeled reflectance: {results.rrs}")

File Organization
-----------------

Recommended Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For optimal automatic loading, organize spectral libraries as:

.. code-block:: text

   data/
   ├── absorption/
   │   ├── water_absorption.csv
   │   ├── phytoplankton_absorption.csv
   │   ├── cdom_absorption.csv
   │   └── nap_absorption.csv
   ├── backscatter/
   │   ├── water_backscatter.csv
   │   ├── phytoplankton_backscatter.csv
   │   └── nap_backscatter.csv
   └── substrates/
       ├── sand_substrate.csv
       ├── seagrass_substrate.csv
       ├── coral_substrate.csv
       └── mud_substrate.csv

CSV File Format
~~~~~~~~~~~~~~~

**Two-column format:**

.. code-block:: text

   wavelength,absorption
   400,0.00663
   410,0.00473
   420,0.00454
   ...

**Multi-column format:**

.. code-block:: text

   wavelength,sand,seagrass,coral
   400,0.25,0.12,0.35
   410,0.26,0.13,0.36
   420,0.27,0.14,0.37
   ...

Error Handling
--------------

The SIOP manager includes robust error handling:

.. code-block:: python

   try:
       # This will raise KeyError if sensor not registered
       siops = siop_manager.get_siops_for_sensor("Unknown-Sensor")
   except KeyError as e:
       print(f"Sensor not found: {e}")
   
   try:
       # This will raise KeyError if required libraries missing
       standard_siops = siop_manager.get_standard_siops("Sentinel-2")
   except KeyError as e:
       print(f"Missing required library: {e}")

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Libraries not loading automatically

**Solution**: Check file names and directory structure

.. code-block:: python

   # Debug library loading
   siop_manager = sbc.SIOPManager()
   siop_manager.load_libraries("data/")  # Should print loading status
   
   available = siop_manager.list_available_libraries()
   print(f"Loaded: {available}")

**Issue**: Wavelength range warnings

**Solution**: Ensure spectral libraries cover sensor wavelengths

.. code-block:: python

   # Check wavelength coverage
   libraries = siop_manager.list_available_libraries()
   for lib_name in libraries:
       lib_data = siop_manager.raw_libraries[lib_name]
       wl_min, wl_max = min(lib_data[0]), max(lib_data[0])
       print(f"{lib_name}: {wl_min}-{wl_max} nm")

**Issue**: Missing standard libraries

**Solution**: Ensure required libraries are present

.. code-block:: python

   # Check for required libraries
   required = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
   available = siop_manager.list_available_libraries()
   
   missing = [lib for lib in required if lib not in available]
   if missing:
       print(f"Missing required libraries: {missing}")

Performance Considerations
--------------------------

Loading Performance
~~~~~~~~~~~~~~~~~~~

- **Small libraries** (<100 entries): ~1ms load time
- **Large libraries** (>1000 entries): ~10ms load time  
- **Many files**: Linear scaling with number of files

Interpolation Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Linear interpolation**: ~0.1ms per library per sensor
- **Memory usage**: ~1KB per spectral library
- **Caching**: Results cached automatically for repeated access

Best Practices
--------------

1. **Organize files logically** by optical property type
2. **Use descriptive filenames** for automatic recognition
3. **Ensure wavelength coverage** spans all sensor bands
4. **Register sensors once** and reuse configurations
5. **Cache standard SIOPs** for repeated use

Integration Examples
--------------------

With Inversion Workflow
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca_core.inversion import InversionParameters, invert_spectrum
   
   # Setup SIOPs
   siop_manager = sbc.SIOPManager("data/")
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])
   
   # Setup inversion with SIOPs
   params = InversionParameters(
       depth=(0, 20), chl=(0.1, 10.0), cdom=(0.01, 2.0),
       wavelengths=[492.4, 559.8, 664.6, 704.1]
   )
   params.update_from_siop_manager(siop_manager, "Sentinel-2")
   
   # Run inversion
   observed_rrs = [0.012, 0.015, 0.008, 0.006]
   result = invert_spectrum(observed_rrs, params)

With Satellite Data Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import rasterio
   
   # Load satellite image
   with rasterio.open("sentinel2_reflectance.tif") as src:
       image = src.read()  # Shape: (bands, height, width)
       image = np.transpose(image, (1, 2, 0))  # Shape: (height, width, bands)
   
   # Setup SIOPs for the sensor
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])
   siops = siop_manager.get_standard_siops("Sentinel-2")
   
   # Process image (see inversion module for details)
   # results = process_image(image, inversion_params)

See Also
--------

- :doc:`forward_model` for using SIOPs in forward modeling
- :doc:`inversion` for integration with inversion algorithms  
- :doc:`../user_guide/siop_management` for detailed tutorials
- :doc:`../theory/optical_properties` for theoretical background
