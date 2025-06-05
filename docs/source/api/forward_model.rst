Forward Model
=============

.. automodule:: sambuca_core.forward_model
   :members:
   :undoc-members:
   :show-inheritance:

The forward model module implements the semi-analytical Lee/Sambuca radiative transfer model for simulating water-leaving reflectance.

Forward Model Function
----------------------

.. autofunction:: sambuca_core.forward_model
   :noindex:

The forward model is the core computational engine of SAMBUCA. It simulates the spectral reflectance that a satellite sensor would observe given specific water column and bottom properties.

Mathematical Foundation
~~~~~~~~~~~~~~~~~~~~~~~

The forward model implements the radiative transfer equations based on Lee et al. (1999, 2001):

.. math::

   R_{rs} = R_{rs}^{dp} \cdot [1 - e^{-(\frac{1}{\cos\theta_w} + \frac{Du}{\cos\theta_0}) \kappa H}] + \frac{R_{bottom}}{\pi} e^{-(\frac{1}{\cos\theta_w} + \frac{Du_b}{\cos\theta_0}) \kappa H}

Where:

- :math:`R_{rs}` = Remote sensing reflectance
- :math:`R_{rs}^{dp}` = Optically deep water reflectance  
- :math:`\kappa` = Total attenuation coefficient (absorption + backscatter)
- :math:`H` = Water depth
- :math:`\theta_w` = Sub-surface solar zenith angle
- :math:`\theta_0` = Sub-surface viewing angle
- :math:`Du` = Path elongation factor for water column
- :math:`Du_b` = Path elongation factor for bottom
- :math:`R_{bottom}` = Bottom reflectance

Results Class
-------------

.. autoclass:: sambuca_core.ForwardModelResults
   :members:
   :undoc-members:
   :show-inheritance:

The :class:`ForwardModelResults` class contains all outputs from the forward model calculation, providing access to:

**Primary Outputs:**
   - ``rrs``: Modeled remote sensing reflectance
   - ``r_substratum``: Combined substrate reflectance

**Optical Coefficients:**
   - ``a``: Total absorption coefficient
   - ``bb``: Total backscatter coefficient
   - ``kd``: Diffuse attenuation coefficient

**Component Contributions:**
   - ``a_ph``, ``a_cdom``, ``a_nap``: Absorption by phytoplankton, CDOM, and NAP
   - ``bb_ph``, ``bb_nap``: Backscatter by phytoplankton and NAP

Parameters
----------

Required Parameters
~~~~~~~~~~~~~~~~~~~

The forward model requires these essential parameters:

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Parameter
     - Type
     - Description
   * - ``chl``
     - float
     - Chlorophyll concentration [mg/m³]
   * - ``cdom``
     - float
     - CDOM absorption coefficient [1/m]
   * - ``nap``
     - float
     - Non-algal particle concentration [mg/L]
   * - ``depth``
     - float
     - Water column depth [m]
   * - ``substrate1``
     - Sequence[float]
     - Primary substrate reflectance spectrum
   * - ``wavelengths``
     - Sequence[float]
     - Wavelength array [nm]
   * - ``a_water``
     - Sequence[float]
     - Pure water absorption [1/m]
   * - ``a_ph_star``
     - Sequence[float]
     - Specific phytoplankton absorption [m²/mg]
   * - ``num_bands``
     - int
     - Number of spectral bands

Optional Parameters
~~~~~~~~~~~~~~~~~~~

Additional parameters for model customization:

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Parameter
     - Default
     - Description
   * - ``substrate_fraction``
     - 1.0
     - Mixing fraction for two substrates
   * - ``substrate2``
     - None
     - Optional second substrate spectrum
   * - ``a_cdom_slope``
     - 0.0168052
     - CDOM absorption slope [1/nm]
   * - ``a_nap_slope``
     - 0.00977262
     - NAP absorption slope [1/nm]
   * - ``bb_ph_slope``
     - 0.878138
     - Phytoplankton backscatter slope
   * - ``bb_nap_slope``
     - None
     - NAP backscatter slope (defaults to bb_ph_slope)
   * - ``lambda0cdom``
     - 550.0
     - CDOM reference wavelength [nm]
   * - ``lambda0nap``
     - 550.0
     - NAP reference wavelength [nm]
   * - ``lambda0x``
     - 546.0
     - Backscatter reference wavelength [nm]
   * - ``x_ph_lambda0x``
     - 0.00157747
     - Phytoplankton backscatter at reference [m²/mg]
   * - ``x_nap_lambda0x``
     - 0.0225353
     - NAP backscatter at reference [m²/g]
   * - ``theta_air``
     - 30.0
     - Solar zenith angle [degrees]
   * - ``off_nadir``
     - 0.0
     - Off-nadir viewing angle [degrees]
   * - ``q_factor``
     - π
     - Q factor for R(0-) conversion

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   import numpy as np
   
   # Define basic spectral properties
   wavelengths = [492.4, 559.8, 664.6, 704.1]  # Sentinel-2 bands
   a_water = [0.007, 0.015, 0.325, 0.619]      # Water absorption
   a_ph_star = [0.055, 0.023, 0.014, 0.010]    # Phytoplankton absorption
   substrate = [0.3, 0.3, 0.25, 0.2]           # Sand reflectance
   
   # Run forward model
   results = sbc.forward_model(
       chl=2.0,          # 2 mg/m³ chlorophyll
       cdom=0.5,         # 0.5 m⁻¹ CDOM
       nap=1.5,          # 1.5 mg/L particles
       depth=10.0,       # 10 m depth
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   print(f"Reflectance: {results.rrs}")
   print(f"Absorption: {results.a}")
   print(f"Backscatter: {results.bb}")

Advanced Usage with Two Substrates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define two substrate types
   sand = [0.3, 0.3, 0.25, 0.2]
   seagrass = [0.1, 0.15, 0.2, 0.25]
   
   # Mix substrates: 70% sand, 30% seagrass
   results = sbc.forward_model(
       chl=1.0, cdom=0.3, nap=1.0, depth=5.0,
       substrate1=sand,
       substrate2=seagrass,
       substrate_fraction=0.7,  # 70% substrate1 (sand)
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )
   
   print(f"Mixed substrate reflectance: {results.r_substratum}")

Custom Optical Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Customize CDOM and NAP slopes
   results = sbc.forward_model(
       chl=1.5, cdom=0.8, nap=2.0, depth=8.0,
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths),
       a_cdom_slope=0.020,    # Steeper CDOM slope
       a_nap_slope=0.012,     # Different NAP slope
       bb_ph_slope=0.85,      # Custom phytoplankton slope
       bb_nap_slope=1.2       # Different NAP backscatter slope
   )

Viewing Geometry Effects
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Model with different viewing geometry
   results = sbc.forward_model(
       chl=2.0, cdom=0.5, nap=1.5, depth=6.0,
       substrate1=substrate,
       wavelengths=wavelengths,
       a_water=a_water,
       a_ph_star=a_ph_star,
       num_bands=len(wavelengths),
       theta_air=45.0,        # 45° solar zenith
       off_nadir=15.0         # 15° off-nadir viewing
   )

Analyzing Results
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Examine detailed results
   results = sbc.forward_model(...)
   
   # Total absorption and its components
   print(f"Total absorption: {results.a}")
   print(f"Water: {results.a_water}")
   print(f"Phytoplankton: {results.a_ph}")
   print(f"CDOM: {results.a_cdom}")
   print(f"NAP: {results.a_nap}")
   
   # Attenuation coefficients
   print(f"Diffuse attenuation: {results.kd}")
   print(f"Water column upwelling: {results.kuc}")
   print(f"Bottom upwelling: {results.kub}")
   
   # Reflectance products
   print(f"Modeled RRS: {results.rrs}")
   print(f"Deep water RRS: {results.rrsdp}")
   print(f"R(0-): {results.r_0_minus}")

Performance Considerations
--------------------------

Vectorization
~~~~~~~~~~~~~

The forward model is fully vectorized and optimized for performance:

.. code-block:: python

   # All array operations are vectorized
   results = sbc.forward_model(...)  # Processes all bands simultaneously

Memory Usage
~~~~~~~~~~~~

For typical applications:

- **Single spectrum**: ~1KB memory
- **1000x1000 image**: ~16MB per band
- **Large scenes**: Memory scales linearly with image size

Computational Complexity
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Time complexity**: O(n) where n = number of spectral bands
- **Typical performance**: ~0.1ms per spectrum on modern hardware
- **Batch processing**: Highly efficient for multiple spectra

Error Handling
--------------

The forward model includes comprehensive input validation:

.. code-block:: python

   try:
       results = sbc.forward_model(
           chl=-1.0,  # Invalid: negative chlorophyll
           ...
       )
   except AssertionError as e:
       print(f"Invalid input: {e}")

Common validation checks:

- Array length consistency
- Non-negative concentrations  
- Valid wavelength ranges
- Proper substrate reflectance values (0-1)

Scientific References
---------------------

The forward model implementation is based on:

1. **Lee, Z., et al. (1999)**. Hyperspectral remote sensing for shallow waters: 2. Deriving bottom depths and water properties by optimization. *Applied Optics*, 38(18), 3831-3843.

2. **Lee, Z., et al. (2001)**. Properties of the water column and bottom derived from Hyperion data. *IEEE Transactions on Geoscience and Remote Sensing*, 39(11), 2331-2336.

3. **Mobley, C.D. (1994)**. Light and Water: Radiative Transfer in Natural Waters. Academic Press.

4. **Brando, V.E., et al. (2009)**. A physics based retrieval and quality assessment of bathymetry from suboptimal hyperspectral data. *Remote Sensing of Environment*, 113(4), 755-770.

See Also
--------

- :doc:`siop_manager` for managing spectral libraries
- :doc:`inversion` for parameter estimation
- :doc:`../theory/radiative_transfer` for theoretical background
- :doc:`../user_guide/forward_modeling` for detailed tutorials
