SIOP Management
===============

Spectral Inherent Optical Properties (SIOPs) are the fundamental building blocks of the SAMBUCA model. This guide covers how to organize, load, and manage spectral libraries effectively for different sensors and applications.

Understanding SIOPs
-------------------

What are SIOPs?
~~~~~~~~~~~~~~~

SIOPs define how different water constituents interact with light at specific wavelengths:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - SIOP Type
     - Symbol
     - Description
   * - **Absorption**
     - a(λ)
     - How strongly a constituent absorbs light [1/m]
   * - **Scattering**
     - b(λ)
     - How much light is scattered [1/m]
   * - **Backscatter**
     - bb(λ)
     - Fraction scattered backward [1/m]
   * - **Reflectance**
     - R(λ)
     - Bottom substrate reflectance [unitless]

Key SIOP Categories
~~~~~~~~~~~~~~~~~~~

**Water Constituents:**
- **Pure water** (H₂O): Well-known absorption and scattering
- **Phytoplankton** (CHL): Variable absorption, moderate scattering
- **CDOM**: Exponentially decreasing absorption
- **NAP**: Broad absorption and scattering

**Bottom Substrates:**
- **Sand**: High reflectance, spectrally flat
- **Seagrass**: Lower reflectance, green peak
- **Coral**: Variable, often high reflectance
- **Mud**: Low reflectance, red absorption

SIOP Manager Overview
---------------------

The :class:`SIOPManager` class provides:

✅ **Automatic library loading** from directory structures  
✅ **Sensor registration** with wavelength configurations  
✅ **Spectral interpolation** to match sensor bands  
✅ **Standard SIOP sets** for common applications  
✅ **Quality control** and validation  

Basic Setup
-----------

Initialize SIOP Manager
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np
   import matplotlib.pyplot as plt

   # Method 1: Initialize with automatic loading
   siop_manager = sbc.SIOPManager("path/to/spectral/libraries/")

   # Method 2: Initialize empty and load manually
   siop_manager = sbc.SIOPManager()
   siop_manager.load_libraries("path/to/spectral/libraries/")

   # Check what was loaded
   available_libraries = siop_manager.list_available_libraries()
   print(f"Loaded libraries: {available_libraries}")

Register Sensors
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Register common satellite sensors
   sensors = {
       "Sentinel-2": [492.4, 559.8, 664.6, 704.1],      # MSI bands
       "Landsat-8": [482.0, 561.5, 654.5, 864.5],       # OLI bands
       "MODIS": [469.0, 555.0, 645.0, 859.0],           # Ocean color bands
       "WorldView-3": [427, 482, 547, 608, 659, 722, 824, 914]  # Coastal/NIR
   }

   for sensor_name, wavelengths in sensors.items():
       siop_manager.register_sensor(sensor_name, wavelengths)
       print(f"Registered {sensor_name} with {len(wavelengths)} bands")

Get Standard SIOPs
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get automatically selected standard SIOPs
   try:
       siops = siop_manager.get_standard_siops("Sentinel-2")
       
       print(f"Standard SIOPs for Sentinel-2:")
       print(f"  Wavelengths: {siops['wavelengths']}")
       print(f"  Number of bands: {siops['num_bands']}")
       print(f"  Available SIOPs: {[k for k in siops.keys() if k not in ['wavelengths', 'num_bands']]}")
       
   except KeyError as e:
       print(f"Missing required SIOP: {e}")
       print("Check your spectral library organization")

Organizing Spectral Libraries
-----------------------------

Recommended Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organize your spectral libraries in a logical hierarchy:

.. code-block:: text

   spectral_data/
   ├── absorption/
   │   ├── water_absorption.csv
   │   ├── phytoplankton_absorption.csv
   │   ├── cdom_absorption.csv
   │   └── nap_absorption.csv
   ├── backscatter/
   │   ├── water_backscatter.csv
   │   ├── phytoplankton_backscatter.csv
   │   └── nap_backscatter.csv
   ├── substrates/
   │   ├── sand_substrate.csv
   │   ├── seagrass_substrate.csv
   │   ├── coral_substrate.csv
   │   └── mud_substrate.csv
   └── custom/
       ├── regional_phytoplankton.csv
       └── local_sediments.csv

File Naming Conventions
~~~~~~~~~~~~~~~~~~~~~~~

The SIOP Manager recognizes common naming patterns:

.. code-block:: text

   # Absorption spectra
   water_absorption.csv       → 'water_absorption'
   phytoplankton_absorption.csv → 'phytoplankton_absorption'
   cdom_absorption.csv        → 'cdom_absorption'
   
   # Substrate reflectance
   sand_substrate.csv         → 'sand_substrate'
   seagrass_substrate.csv     → 'seagrass_substrate'
   
   # Multi-column files
   substrates_all.csv         → 'substrates_all_sand', 'substrates_all_seagrass', etc.

CSV File Formats
~~~~~~~~~~~~~~~~

**Two-column format:**

.. code-block:: text

   wavelength,absorption
   400,0.00663
   410,0.00473
   420,0.00454
   430,0.00450
   ...

**Multi-column format:**

.. code-block:: text

   wavelength,sand,seagrass,coral,mud
   400,0.25,0.12,0.35,0.08
   410,0.26,0.13,0.36,0.08
   420,0.27,0.14,0.37,0.09
   430,0.28,0.15,0.38,0.09
   ...

**Header variations (all supported):**

.. code-block:: text

   # Acceptable header names
   wavelength,value          # Basic format
   lambda,absorption         # Greek lambda
   wl,refl                  # Abbreviated
   nm,reflectance           # Units specified

Working with Spectral Libraries
-------------------------------

Loading and Inspecting Libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Load libraries and inspect contents
   siop_manager = sbc.SIOPManager("spectral_data/")

   # List all available libraries
   all_libraries = siop_manager.list_available_libraries()
   print(f"Total libraries loaded: {len(all_libraries)}")

   # Group by type
   library_types = siop_manager.get_common_library_types()
   
   print(f"\\nLibrary breakdown:")
   for category, libs in library_types.items():
       print(f"  {category}: {len(libs)} libraries")
       for lib in libs:
           print(f"    - {lib}")

Examining Spectral Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Access raw library data
   raw_libraries = siop_manager.raw_libraries

   # Plot raw spectral libraries
   fig, axes = plt.subplots(2, 2, figsize=(15, 10))

   # Absorption spectra
   axes[0,0].set_title('Absorption Spectra')
   for lib_name, (wavelengths, values) in raw_libraries.items():
       if 'absorption' in lib_name:
           axes[0,0].plot(wavelengths, values, label=lib_name.replace('_absorption', ''), linewidth=2)
   axes[0,0].set_xlabel('Wavelength (nm)')
   axes[0,0].set_ylabel('Absorption (1/m)')
   axes[0,0].legend()
   axes[0,0].set_yscale('log')
   axes[0,0].grid(True, alpha=0.3)

   # Backscatter spectra  
   axes[0,1].set_title('Backscatter Spectra')
   for lib_name, (wavelengths, values) in raw_libraries.items():
       if 'backscatter' in lib_name:
           axes[0,1].plot(wavelengths, values, label=lib_name.replace('_backscatter', ''), linewidth=2)
   axes[0,1].set_xlabel('Wavelength (nm)')
   axes[0,1].set_ylabel('Backscatter (1/m)')
   axes[0,1].legend()
   axes[0,1].set_yscale('log')
   axes[0,1].grid(True, alpha=0.3)

   # Substrate reflectance
   axes[1,0].set_title('Substrate Reflectance')
   for lib_name, (wavelengths, values) in raw_libraries.items():
       if 'substrate' in lib_name:
           axes[1,0].plot(wavelengths, values, label=lib_name.replace('_substrate', ''), linewidth=2)
   axes[1,0].set_xlabel('Wavelength (nm)')
   axes[1,0].set_ylabel('Reflectance')
   axes[1,0].legend()
   axes[1,0].grid(True, alpha=0.3)

   # Wavelength coverage
   axes[1,1].set_title('Wavelength Coverage')
   for lib_name, (wavelengths, values) in raw_libraries.items():
       wl_min, wl_max = min(wavelengths), max(wavelengths)
       axes[1,1].barh(lib_name, wl_max - wl_min, left=wl_min, alpha=0.7)
   axes[1,1].set_xlabel('Wavelength (nm)')
   axes[1,1].set_ylabel('Library')
   axes[1,1].grid(True, alpha=0.3)

   plt.tight_layout()
   plt.show()

Sensor-Specific SIOPs
---------------------

Getting SIOPs for Registered Sensors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Register sensor
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])

   # Get all SIOPs interpolated to sensor wavelengths
   sentinel2_siops = siop_manager.get_siops_for_sensor("Sentinel-2")

   print(f"Sentinel-2 SIOPs:")
   print(f"  Wavelengths: {sentinel2_siops['wavelengths']}")
   print(f"  Number of bands: {sentinel2_siops['num_bands']}")

   # Display available SIOPs
   siop_names = [k for k in sentinel2_siops.keys() if k not in ['wavelengths', 'num_bands']]
   print(f"  Available SIOPs: {siop_names}")

   # Access individual SIOPs
   if 'water_absorption' in sentinel2_siops:
       print(f"  Water absorption: {sentinel2_siops['water_absorption']}")

Custom Wavelength Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define custom wavelengths (e.g., for atmospheric windows)
   custom_wavelengths = [443, 490, 510, 560, 620, 665, 681, 709, 754, 779]

   # Get SIOPs without registering a sensor
   custom_siops = siop_manager.get_siops_for_wavelengths(custom_wavelengths)

   print(f"Custom configuration:")
   print(f"  Wavelengths: {custom_siops['wavelengths']}")
   print(f"  Number of bands: {custom_siops['num_bands']}")

   # Visualize interpolation quality
   plt.figure(figsize=(12, 8))

   # Example: Compare original vs interpolated water absorption
   if 'water_absorption' in siop_manager.raw_libraries:
       orig_wl, orig_abs = siop_manager.raw_libraries['water_absorption']
       
       plt.subplot(2, 2, 1)
       plt.plot(orig_wl, orig_abs, 'b-', label='Original', linewidth=1)
       plt.plot(custom_siops['wavelengths'], custom_siops['water_absorption'], 
                'ro', label='Interpolated', markersize=8)
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Water Absorption (1/m)')
       plt.title('Interpolation Quality')
       plt.legend()
       plt.yscale('log')
       plt.grid(True, alpha=0.3)

   plt.tight_layout()
   plt.show()

Multi-Sensor Comparison
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def compare_sensors():
       """Compare how different sensors sample the same spectral libraries."""
       
       sensors = {
           "Sentinel-2": [492.4, 559.8, 664.6, 704.1],
           "Landsat-8": [482.0, 561.5, 654.5, 864.5],
           "MODIS": [469.0, 555.0, 645.0, 859.0]
       }
       
       # Register all sensors
       for sensor_name, wavelengths in sensors.items():
           siop_manager.register_sensor(sensor_name, wavelengths)
       
       # Compare water absorption across sensors
       plt.figure(figsize=(15, 10))
       
       # Get original high-resolution data
       if 'water_absorption' in siop_manager.raw_libraries:
           orig_wl, orig_abs = siop_manager.raw_libraries['water_absorption']
           
           plt.subplot(2, 2, 1)
           plt.plot(orig_wl, orig_abs, 'k-', label='Original', linewidth=2, alpha=0.7)
           
           colors = ['blue', 'red', 'green']
           for i, (sensor_name, color) in enumerate(zip(sensors.keys(), colors)):
               sensor_siops = siop_manager.get_siops_for_sensor(sensor_name)
               plt.plot(sensor_siops['wavelengths'], sensor_siops['water_absorption'],
                       'o-', color=color, label=sensor_name, linewidth=2, markersize=8)
           
           plt.xlabel('Wavelength (nm)')
           plt.ylabel('Water Absorption (1/m)')
           plt.title('Water Absorption: Sensor Comparison')
           plt.legend()
           plt.yscale('log')
           plt.grid(True, alpha=0.3)
       
       # Compare substrate reflectance
       if 'sand_substrate' in siop_manager.raw_libraries:
           orig_wl, orig_refl = siop_manager.raw_libraries['sand_substrate']
           
           plt.subplot(2, 2, 2)
           plt.plot(orig_wl, orig_refl, 'k-', label='Original', linewidth=2, alpha=0.7)
           
           for i, (sensor_name, color) in enumerate(zip(sensors.keys(), colors)):
               sensor_siops = siop_manager.get_siops_for_sensor(sensor_name)
               if 'sand_substrate' in sensor_siops:
                   plt.plot(sensor_siops['wavelengths'], sensor_siops['sand_substrate'],
                           'o-', color=color, label=sensor_name, linewidth=2, markersize=8)
           
           plt.xlabel('Wavelength (nm)')
           plt.ylabel('Sand Reflectance')
           plt.title('Sand Substrate: Sensor Comparison')
           plt.legend()
           plt.grid(True, alpha=0.3)
       
       # Band positioning comparison
       plt.subplot(2, 2, 3)
       y_positions = range(len(sensors))
       for i, (sensor_name, wavelengths) in enumerate(sensors.items()):
           colors_bands = ['blue', 'green', 'red', 'darkred'][:len(wavelengths)]
           for j, (wl, color) in enumerate(zip(wavelengths, colors_bands)):
               plt.scatter(wl, i, c=color, s=100, alpha=0.8)
               plt.text(wl, i + 0.1, f'{wl:.0f}', ha='center', va='bottom', fontsize=8)
       
       plt.yticks(y_positions, list(sensors.keys()))
       plt.xlabel('Wavelength (nm)')
       plt.title('Band Positioning Comparison')
       plt.grid(True, alpha=0.3)
       
       # Spectral sampling density
       plt.subplot(2, 2, 4)
       for sensor_name, wavelengths in sensors.items():
           if len(wavelengths) > 1:
               band_spacing = np.diff(wavelengths)
               plt.plot(wavelengths[1:], band_spacing, 'o-', label=sensor_name, linewidth=2, markersize=6)
       
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Band Spacing (nm)')
       plt.title('Spectral Sampling Density')
       plt.legend()
       plt.grid(True, alpha=0.3)
       
       plt.tight_layout()
       plt.show()

   # Run sensor comparison
   compare_sensors()

Integration with Forward Model
------------------------------

Using Managed SIOPs in Forward Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Complete workflow: SIOP management + forward modeling
   
   # 1. Setup SIOP manager
   siop_manager = sbc.SIOPManager("spectral_data/")
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
   
   print(f"Forward model with managed SIOPs:")
   print(f"  Modeled reflectance: {results.rrs}")
   print(f"  Using {siops['num_bands']} bands")

Integration with Inversion
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sambuca_core.inversion import InversionParameters, invert_spectrum

   # Setup inversion with managed SIOPs
   params = InversionParameters(
       depth=(0, 20),
       chl=(0.1, 10.0),
       cdom=(0.01, 2.0),
       nap=(0.1, 5.0),
       wavelengths=siops['wavelengths']
   )

   # Update parameters with SIOPs from manager
   params.update_from_siop_manager(siop_manager, "Sentinel-2")

   # Run inversion
   observed_rrs = [0.012, 0.015, 0.008, 0.006]
   result = invert_spectrum(observed_rrs, params)

   print(f"Inversion with managed SIOPs:")
   print(f"  Estimated depth: {result.parameters['depth']:.2f} m")
   print(f"  Estimated chlorophyll: {result.parameters['chl']:.2f} mg/m³")

Quality Control and Validation
------------------------------

SIOP Quality Checks
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def validate_siop_libraries(siop_manager):
       """Comprehensive validation of SIOP libraries."""
       
       print("SIOP Library Validation")
       print("=" * 50)
       
       raw_libraries = siop_manager.raw_libraries
       issues = []
       
       for lib_name, (wavelengths, values) in raw_libraries.items():
           print(f"\\nValidating {lib_name}:")
           
           # Check wavelength range
           wl_min, wl_max = min(wavelengths), max(wavelengths)
           print(f"  Wavelength range: {wl_min:.1f} - {wl_max:.1f} nm")
           
           if wl_max - wl_min < 200:
               issues.append(f"{lib_name}: Narrow wavelength range")
               print(f"    WARNING: Narrow spectral range")
           
           # Check for monotonic wavelengths
           if not all(wavelengths[i] <= wavelengths[i+1] for i in range(len(wavelengths)-1)):
               issues.append(f"{lib_name}: Non-monotonic wavelengths")
               print(f"    ERROR: Wavelengths not monotonically increasing")
           
           # Check for valid values
           if np.any(values < 0):
               issues.append(f"{lib_name}: Negative values")
               print(f"    ERROR: Negative values found")
           
           if np.any(np.isnan(values)):
               issues.append(f"{lib_name}: NaN values")
               print(f"    ERROR: NaN values found")
           
           # Check reasonable ranges
           if 'absorption' in lib_name:
               if np.max(values) > 100:
                   issues.append(f"{lib_name}: Very high absorption")
                   print(f"    WARNING: Very high absorption values (>{100})")
           
           elif 'substrate' in lib_name:
               if np.max(values) > 1.0:
                   issues.append(f"{lib_name}: Reflectance > 1")
                   print(f"    WARNING: Reflectance values > 1.0")
               if np.min(values) < 0:
                   issues.append(f"{lib_name}: Negative reflectance")
                   print(f"    ERROR: Negative reflectance values")
           
           # Check spectral resolution
           if len(wavelengths) > 1:
               avg_spacing = (wl_max - wl_min) / (len(wavelengths) - 1)
               print(f"  Average spacing: {avg_spacing:.1f} nm")
               
               if avg_spacing > 50:
                   issues.append(f"{lib_name}: Coarse spectral resolution")
                   print(f"    WARNING: Coarse spectral resolution")
       
       print(f"\\nValidation Summary:")
       print(f"  Total libraries: {len(raw_libraries)}")
       print(f"  Issues found: {len(issues)}")
       
       if issues:
           print(f"\\nIssues:")
           for issue in issues:
               print(f"  - {issue}")
       else:
           print(f"  All libraries passed validation!")
       
       return len(issues) == 0

   # Run validation
   is_valid = validate_siop_libraries(siop_manager)

Interpolation Quality Assessment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def assess_interpolation_quality(siop_manager, sensor_name):
       """Assess quality of spectral interpolation for a sensor."""
       
       if sensor_name not in siop_manager.sensor_configs:
           print(f"Sensor {sensor_name} not registered")
           return
       
       target_wavelengths = siop_manager.sensor_configs[sensor_name]
       interpolated_siops = siop_manager.get_siops_for_sensor(sensor_name)
       
       print(f"Interpolation Quality Assessment: {sensor_name}")
       print("=" * 50)
       
       for lib_name, (orig_wavelengths, orig_values) in siop_manager.raw_libraries.items():
           if lib_name in interpolated_siops:
               interp_values = interpolated_siops[lib_name]
               
               print(f"\\n{lib_name}:")
               
               # Check wavelength coverage
               orig_min, orig_max = min(orig_wavelengths), max(orig_wavelengths)
               target_min, target_max = min(target_wavelengths), max(target_wavelengths)
               
               print(f"  Original range: {orig_min:.1f} - {orig_max:.1f} nm")
               print(f"  Target range: {target_min:.1f} - {target_max:.1f} nm")
               
               # Check for extrapolation
               extrapolation_needed = target_min < orig_min or target_max > orig_max
               if extrapolation_needed:
                   print(f"  WARNING: Extrapolation required")
                   if target_min < orig_min:
                       print(f"    Extrapolating below {orig_min:.1f} nm")
                   if target_max > orig_max:
                       print(f"    Extrapolating above {orig_max:.1f} nm")
               else:
                   print(f"  OK: Full interpolation within original range")
               
               # Calculate interpolation errors (for bands within original range)
               from scipy.interpolate import interp1d
               
               valid_targets = [w for w in target_wavelengths if orig_min <= w <= orig_max]
               if valid_targets:
                   # Create interpolator
                   interp_func = interp1d(orig_wavelengths, orig_values, kind='linear')
                   
                   # Compare interpolated values
                   ref_values = interp_func(valid_targets)
                   interp_subset = [interp_values[i] for i, w in enumerate(target_wavelengths) if w in valid_targets]
                   
                   rmse = np.sqrt(np.mean((np.array(ref_values) - np.array(interp_subset))**2))
                   max_error = np.max(np.abs(np.array(ref_values) - np.array(interp_subset)))
                   
                   print(f"  Interpolation RMSE: {rmse:.6f}")
                   print(f"  Max interpolation error: {max_error:.6f}")

   # Run interpolation quality assessment
   assess_interpolation_quality(siop_manager, "Sentinel-2")

Creating Custom SIOP Libraries
------------------------------

Building Regional Libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_regional_phytoplankton_library():
       """Example: Create region-specific phytoplankton absorption library."""
       
       # Define wavelength grid
       wavelengths = np.arange(400, 801, 5)  # 400-800nm, 5nm steps
       
       # Create absorption spectra for different phytoplankton types
       phyto_types = {
           'diatoms': {
               'peaks': [440, 675],  # Blue and red peaks
               'magnitudes': [0.08, 0.06],
               'baseline': 0.01
           },
           'cyanobacteria': {
               'peaks': [440, 620, 675],  # Blue, phycocyanin, chlorophyll
               'magnitudes': [0.06, 0.04, 0.05],
               'baseline': 0.008
           },
           'dinoflagellates': {
               'peaks': [440, 470, 675],  # Broad blue, carotenoids, chlorophyll
               'magnitudes': [0.07, 0.03, 0.055],
               'baseline': 0.012
           }
       }
       
       # Generate absorption spectra
       absorption_data = {'wavelength': wavelengths}
       
       for phyto_type, params in phyto_types.items():
           absorption = np.full_like(wavelengths, params['baseline'], dtype=float)
           
           # Add Gaussian peaks
           for peak_wl, magnitude in zip(params['peaks'], params['magnitudes']):
               peak_contribution = magnitude * np.exp(-((wavelengths - peak_wl) / 30)**2)
               absorption += peak_contribution
           
           absorption_data[phyto_type] = absorption
       
       # Save to CSV
       import pandas as pd
       df = pd.DataFrame(absorption_data)
       df.to_csv('regional_phytoplankton_absorption.csv', index=False)
       
       print("Created regional phytoplankton library")
       print(f"  Wavelengths: {len(wavelengths)} points")
       print(f"  Phytoplankton types: {list(phyto_types.keys())}")
       
       # Visualize
       plt.figure(figsize=(10, 6))
       for phyto_type in phyto_types.keys():
           plt.plot(wavelengths, absorption_data[phyto_type], 
                   label=phyto_type, linewidth=2)
       
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Absorption (m²/mg)')
       plt.title('Regional Phytoplankton Absorption Library')
       plt.legend()
       plt.grid(True, alpha=0.3)
       plt.show()
       
       return df

   # Create custom library
   regional_phyto = create_regional_phytoplankton_library()

Substrate Library Creation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_substrate_library():
       """Create comprehensive substrate reflectance library."""
       
       wavelengths = np.arange(400, 801, 10)
       
       # Define substrate types with characteristic spectral shapes
       substrates = {
           'quartz_sand': {
               'base_refl': 0.6,
               'red_edge': 0.1,  # Increase in red/NIR
               'fe_absorption': (500, 0.05)  # Iron absorption around 500nm
           },
           'carbonate_sand': {
               'base_refl': 0.7,
               'red_edge': 0.15,
               'fe_absorption': None
           },
           'posidonia_seagrass': {
               'base_refl': 0.15,
               'green_peak': (550, 0.08),
               'red_absorption': (675, 0.05),
               'nir_plateau': (750, 0.25)
           },
           'zostera_seagrass': {
               'base_refl': 0.12,
               'green_peak': (560, 0.06),
               'red_absorption': (675, 0.04),
               'nir_plateau': (750, 0.22)
           },
           'coral_acropora': {
               'base_refl': 0.4,
               'pink_reflectance': (500, 0.1),
               'variable_spectrum': True
           },
           'mud_organic': {
               'base_refl': 0.08,
               'red_slope': 0.0002,  # Slight increase toward red
               'low_overall': True
           }
       }
       
       # Generate reflectance spectra
       substrate_data = {'wavelength': wavelengths}
       
       for substrate_name, params in substrates.items():
           reflectance = np.full_like(wavelengths, params['base_refl'], dtype=float)
           
           # Apply spectral features
           if 'red_edge' in params:
               # Linear increase in red/NIR
               red_increase = params['red_edge'] * np.maximum(0, (wavelengths - 650) / 150)
               reflectance += red_increase
           
           if 'green_peak' in params:
               peak_wl, peak_mag = params['green_peak']
               green_peak = peak_mag * np.exp(-((wavelengths - peak_wl) / 40)**2)
               reflectance += green_peak
           
           if 'red_absorption' in params:
               abs_wl, abs_mag = params['red_absorption']
               red_abs = -abs_mag * np.exp(-((wavelengths - abs_wl) / 30)**2)
               reflectance += red_abs
           
           if 'nir_plateau' in params:
               plateau_wl, plateau_refl = params['nir_plateau']
               nir_mask = wavelengths >= plateau_wl
               reflectance[nir_mask] = plateau_refl
           
           if 'fe_absorption' in params and params['fe_absorption']:
               abs_wl, abs_mag = params['fe_absorption']
               fe_abs = -abs_mag * np.exp(-((wavelengths - abs_wl) / 50)**2)
               reflectance += fe_abs
           
           if 'red_slope' in params:
               slope_effect = params['red_slope'] * (wavelengths - 400)
               reflectance += slope_effect
           
           # Ensure realistic range
           reflectance = np.clip(reflectance, 0.01, 0.95)
           
           substrate_data[substrate_name] = reflectance
       
       # Save to CSV
       df = pd.DataFrame(substrate_data)
       df.to_csv('comprehensive_substrate_library.csv', index=False)
       
       print("Created comprehensive substrate library")
       print(f"  Substrates: {list(substrates.keys())}")
       
       # Visualize
       plt.figure(figsize=(12, 8))
       
       colors = plt.cm.tab10(np.linspace(0, 1, len(substrates)))
       for i, substrate_name in enumerate(substrates.keys()):
           plt.plot(wavelengths, substrate_data[substrate_name], 
                   label=substrate_name.replace('_', ' ').title(), 
                   linewidth=2, color=colors[i])
       
       plt.xlabel('Wavelength (nm)')
       plt.ylabel('Reflectance')
       plt.title('Comprehensive Substrate Reflectance Library')
       plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
       plt.grid(True, alpha=0.3)
       plt.tight_layout()
       plt.show()
       
       return df

   # Create substrate library
   substrate_lib = create_substrate_library()

Advanced SIOP Operations
------------------------

Spectral Mixing and Unmixing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def spectral_mixing_example():
       """Example of spectral mixing for substrate composition analysis."""
       
       # Load substrate library (assuming it exists)
       siop_manager.register_sensor("Hyperspectral", list(range(400, 801, 10)))
       hyper_siops = siop_manager.get_siops_for_sensor("Hyperspectral")
       
       if 'sand_substrate' in hyper_siops and 'seagrass_substrate' in hyper_siops:
           wavelengths = hyper_siops['wavelengths']
           sand_refl = hyper_siops['sand_substrate']
           seagrass_refl = hyper_siops['seagrass_substrate']
           
           # Create mixed spectra with different fractions
           fractions = np.arange(0, 1.1, 0.2)  # 0%, 20%, 40%, 60%, 80%, 100%
           
           plt.figure(figsize=(12, 8))
           
           for i, fraction in enumerate(fractions):
               # Linear spectral mixing
               mixed_spectrum = (1 - fraction) * sand_refl + fraction * seagrass_refl
               
               plt.subplot(2, 2, 1)
               plt.plot(wavelengths, mixed_spectrum, 
                       label=f'{fraction*100:.0f}% seagrass', linewidth=2)
           
           plt.xlabel('Wavelength (nm)')
           plt.ylabel('Reflectance')
           plt.title('Sand-Seagrass Spectral Mixing')
           plt.legend()
           plt.grid(True, alpha=0.3)
           
           # Analyze spectral indices for unmixing
           plt.subplot(2, 2, 2)
           # NDVI-like index for vegetation
           red_idx = np.argmin(np.abs(np.array(wavelengths) - 675))
           nir_idx = np.argmin(np.abs(np.array(wavelengths) - 750))
           
           ndvi_values = []
           for fraction in fractions:
               mixed_spectrum = (1 - fraction) * sand_refl + fraction * seagrass_refl
               red_val = mixed_spectrum[red_idx]
               nir_val = mixed_spectrum[nir_idx]
               ndvi = (nir_val - red_val) / (nir_val + red_val)
               ndvi_values.append(ndvi)
           
           plt.plot(fractions * 100, ndvi_values, 'go-', linewidth=2, markersize=8)
           plt.xlabel('Seagrass Coverage (%)')
           plt.ylabel('NDVI')
           plt.title('NDVI vs Seagrass Coverage')
           plt.grid(True, alpha=0.3)
           
           plt.tight_layout()
           plt.show()
           
           return fractions, ndvi_values

   # Run mixing example
   mixing_results = spectral_mixing_example()

Temporal SIOP Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def seasonal_siop_analysis():
       """Analyze seasonal variations in SIOPs."""
       
       # Simulate seasonal phytoplankton changes
       months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
       
       # Seasonal chlorophyll patterns (Northern hemisphere temperate)
       seasonal_chl = [1.5, 2.0, 3.5, 4.0, 2.5, 1.8, 1.2, 1.0, 1.3, 2.2, 2.8, 2.0]
       
       # Get standard SIOPs
       siops = siop_manager.get_standard_siops("Sentinel-2")
       wavelengths = siops['wavelengths']
       
       # Calculate seasonal forward model results
       seasonal_results = []
       
       for month, chl in zip(months, seasonal_chl):
           results = sbc.forward_model(
               chl=chl, cdom=0.5, nap=1.5, depth=8.0,
               substrate1=siops['substrate1'],
               wavelengths=wavelengths,
               a_water=siops['a_water'],
               a_ph_star=siops['a_ph_star'],
               num_bands=siops['num_bands']
           )
           seasonal_results.append({
               'month': month,
               'chl': chl,
               'rrs': results.rrs,
               'a_total': results.a,
               'bb_total': results.bb
           })
       
       # Visualize seasonal patterns
       fig, axes = plt.subplots(2, 2, figsize=(15, 10))
       
       # Chlorophyll concentration
       axes[0,0].plot(months, seasonal_chl, 'go-', linewidth=2, markersize=8)
       axes[0,0].set_ylabel('Chlorophyll (mg/m³)')
       axes[0,0].set_title('Seasonal Chlorophyll Pattern')
       axes[0,0].grid(True, alpha=0.3)
       axes[0,0].tick_params(axis='x', rotation=45)
       
       # Reflectance at different bands
       band_names = ['Blue', 'Green', 'Red', 'NIR']
       colors = ['blue', 'green', 'red', 'darkred']
       
       for i, (band_name, color) in enumerate(zip(band_names, colors)):
           rrs_values = [result['rrs'][i] for result in seasonal_results]
           axes[0,1].plot(months, rrs_values, 'o-', color=color, 
                         label=f'{band_name} ({wavelengths[i]:.0f}nm)', 
                         linewidth=2, markersize=6)
       
       axes[0,1].set_ylabel('Remote Sensing Reflectance')
       axes[0,1].set_title('Seasonal Reflectance Variation')
       axes[0,1].legend()
       axes[0,1].grid(True, alpha=0.3)
       axes[0,1].tick_params(axis='x', rotation=45)
       
       # Total absorption
       for i, (band_name, color) in enumerate(zip(band_names, colors)):
           abs_values = [result['a_total'][i] for result in seasonal_results]
           axes[1,0].plot(months, abs_values, 'o-', color=color, 
                         label=f'{band_name}', linewidth=2, markersize=6)
       
       axes[1,0].set_ylabel('Total Absorption (1/m)')
       axes[1,0].set_title('Seasonal Absorption Variation')
       axes[1,0].legend()
       axes[1,0].set_yscale('log')
       axes[1,0].grid(True, alpha=0.3)
       axes[1,0].tick_params(axis='x', rotation=45)
       
       # Blue/Green ratio (water quality indicator)
       blue_green_ratio = []
       for result in seasonal_results:
           ratio = result['rrs'][0] / result['rrs'][1]  # Blue/Green
           blue_green_ratio.append(ratio)
       
       axes[1,1].plot(months, blue_green_ratio, 'mo-', linewidth=2, markersize=8)
       axes[1,1].set_ylabel('Blue/Green Ratio')
       axes[1,1].set_title('Seasonal Blue/Green Reflectance Ratio')
       axes[1,1].grid(True, alpha=0.3)
       axes[1,1].tick_params(axis='x', rotation=45)
       
       plt.tight_layout()
       plt.show()
       
       return seasonal_results

   # Run seasonal analysis
   seasonal_data = seasonal_siop_analysis()

Best Practices
--------------

SIOP Library Management
~~~~~~~~~~~~~~~~~~~~~~

1. **Organize systematically** - Use consistent directory structure and naming
2. **Document sources** - Keep metadata about where SIOPs came from
3. **Version control** - Track changes to spectral libraries
4. **Validate regularly** - Check for data quality issues
5. **Regional customization** - Adapt libraries to your study area

Quality Assurance
~~~~~~~~~~~~~~~~~

1. **Check wavelength coverage** - Ensure libraries span sensor ranges
2. **Validate interpolation** - Assess interpolation quality
3. **Cross-compare sensors** - Verify consistency across platforms
4. **Physical realism** - Ensure SIOPs are physically reasonable
5. **Field validation** - Compare with in-situ measurements when possible

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Cache interpolated SIOPs** - Avoid repeated calculations
2. **Use appropriate resolution** - Balance accuracy vs computational cost
3. **Precompute standard sets** - Create sensor-specific SIOP packages
4. **Memory management** - Consider memory usage for large libraries

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue**: "Missing required library" error

**Solution**: Check file naming and directory structure

.. code-block:: python

   # Debug library loading
   available = siop_manager.list_available_libraries()
   print(f"Available: {available}")
   
   required = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
   missing = [lib for lib in required if lib not in available]
   print(f"Missing: {missing}")

**Issue**: Wavelength extrapolation warnings

**Solution**: Ensure spectral libraries cover sensor wavelength ranges

.. code-block:: python

   # Check wavelength coverage
   for lib_name, (wl, values) in siop_manager.raw_libraries.items():
       print(f"{lib_name}: {min(wl):.1f} - {max(wl):.1f} nm")

**Issue**: Unrealistic interpolated values

**Solution**: Check original data quality and interpolation method

.. code-block:: python

   # Visualize interpolation for problematic libraries
   lib_name = 'problematic_library'
   if lib_name in siop_manager.raw_libraries:
       orig_wl, orig_val = siop_manager.raw_libraries[lib_name]
       plt.plot(orig_wl, orig_val, 'o-', label='Original')
       # Add sensor points...
       plt.show()

Next Steps
----------

Now that you understand SIOP management:

🎯 **For parameter estimation**: :doc:`inversion`  
🗺️ **For large-scale processing**: :doc:`image_processing`  
🎛️ **For advanced configuration**: :doc:`configuration`  
🔬 **For theoretical background**: :doc:`../theory/optical_properties`

**Practice Exercises:**

1. **Create a regional library** specific to your study area
2. **Compare different sensors** for your application
3. **Validate interpolation quality** for your wavelength requirements
4. **Build custom substrate libraries** from field measurements
5. **Analyze seasonal variations** in your region

Advanced SIOP techniques and case studies can be found in :doc:`../examples/advanced_examples`.
