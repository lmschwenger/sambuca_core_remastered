Radiative Transfer Theory
========================

This section provides the theoretical foundation of radiative transfer as implemented in SAMBUCA Core, covering the physics of light propagation in water and the mathematical frameworks used.

Introduction to Radiative Transfer
----------------------------------

Radiative transfer theory describes how electromagnetic radiation (light) propagates through a medium, accounting for:

- **Absorption**: Light energy converted to other forms (heat, photochemistry)
- **Scattering**: Light direction changes due to particle interactions
- **Emission**: Light generation within the medium (usually negligible in water)

Fundamental Equation
-------------------

The **Radiative Transfer Equation (RTE)** in its general form is:

.. math::

   \frac{1}{c}\frac{\partial L}{\partial t} + \hat{\Omega} \cdot \nabla L = -c(\mathbf{r}, t) L + \int_{4\pi} p(\hat{\Omega}', \hat{\Omega}) L(\mathbf{r}, t, \hat{\Omega}') d\Omega' + S(\mathbf{r}, t, \hat{\Omega})

Where:
- :math:`L(\mathbf{r}, t, \hat{\Omega})` = radiance at position :math:`\mathbf{r}`, time :math:`t`, direction :math:`\hat{\Omega}`
- :math:`c(\mathbf{r}, t)` = beam attenuation coefficient
- :math:`p(\hat{\Omega}', \hat{\Omega})` = scattering phase function
- :math:`S(\mathbf{r}, t, \hat{\Omega})` = source term

Simplifications for Aquatic Systems
-----------------------------------

For natural waters, we make several simplifying assumptions:

1. **Steady State**: :math:`\frac{\partial L}{\partial t} = 0`
2. **Plane-Parallel Medium**: Horizontal homogeneity
3. **No Internal Sources**: :math:`S = 0` (except solar input at surface)
4. **Elastic Scattering**: No wavelength changes

Inherent Optical Properties (IOPs)
----------------------------------

The medium's optical properties are characterized by **IOPs**:

Absorption Coefficient
~~~~~~~~~~~~~~~~~~~~~

The **absorption coefficient** :math:`a(\lambda)` describes light removal:

.. math::

   a(\lambda) = a_w(\lambda) + a_{ph}(\lambda) + a_{cdom}(\lambda) + a_{nap}(\lambda)

**Component Models:**

**Pure Water** :math:`a_w(\lambda)`:
   Well-known from laboratory measurements (Pope & Fry, 1997)

**Phytoplankton** :math:`a_{ph}(\lambda)`:
   .. math::
      a_{ph}(\lambda) = a_{ph}^*(\lambda) \cdot [CHL]
   
   Where :math:`a_{ph}^*(\lambda)` is the chlorophyll-specific absorption coefficient

**CDOM** :math:`a_{cdom}(\lambda)`:
   .. math::
      a_{cdom}(\lambda) = a_{cdom}(440) \exp[-S_{cdom}(\lambda - 440)]
   
   Where :math:`S_{cdom}` is the spectral slope (typically 0.01-0.02 nm⁻¹)

**Non-Algal Particles** :math:`a_{nap}(\lambda)`:
   .. math::
      a_{nap}(\lambda) = a_{nap}^*(\lambda) \cdot [NAP]

Scattering Coefficient
~~~~~~~~~~~~~~~~~~~~~

The **scattering coefficient** :math:`b(\lambda)` describes light redirection:

.. math::

   b(\lambda) = b_w(\lambda) + b_{ph}(\lambda) + b_{nap}(\lambda)

**Pure Water Scattering** (Rayleigh):
.. math::
   b_w(\lambda) = \frac{8.06 \times 10^{-6}}{2} \left(\frac{550}{\lambda}\right)^{4.32}

**Particle Scattering** (Power Law):
.. math::
   b_p(\lambda) = b_p(550) \left(\frac{550}{\lambda}\right)^{\gamma}

Where :math:`\gamma` typically ranges from 0.5 to 2.0.

Backscattering Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~

The **backscattering coefficient** :math:`b_b(\lambda)` is the fraction scattered backward:

.. math::

   b_b(\lambda) = \tilde{b}_{bw} b_w(\lambda) + \tilde{b}_{bp} b_p(\lambda)

Where :math:`\tilde{b}_{bw} = 0.5` for pure water and :math:`\tilde{b}_{bp}` varies with particle properties.

Apparent Optical Properties (AOPs)
----------------------------------

**AOPs** depend on both the medium properties and the light field:

Remote Sensing Reflectance
~~~~~~~~~~~~~~~~~~~~~~~~~~

The **remote sensing reflectance** is defined as:

.. math::

   R_{rs}(\lambda) = \frac{L_w(\lambda)}{E_d(\lambda)}

Where:
- :math:`L_w(\lambda)` = water-leaving radiance
- :math:`E_d(\lambda)` = downwelling irradiance

Relationship to IOPs
~~~~~~~~~~~~~~~~~~~

For optically deep waters, the relationship between :math:`R_{rs}` and IOPs is:

.. math::

   R_{rs}(\lambda) \approx 0.52 \frac{f}{Q} \frac{b_b(\lambda)}{a(\lambda) + b_b(\lambda)}

Where:
- :math:`f` = backscattering shape factor (~0.3)
- :math:`Q` = radiance distribution factor (~4-5)

Shallow Water Modifications
---------------------------

SAMBUCA extends the deep water theory to shallow waters by accounting for:

Bottom Boundary Condition
~~~~~~~~~~~~~~~~~~~~~~~~~

The substrate contributes upwelling radiance:

.. math::

   L_u^{bottom} = \frac{\rho_{bottom}(\lambda)}{\pi} E_d^{bottom}

Where :math:`\rho_{bottom}(\lambda)` is the bottom reflectance.

Exponential Attenuation
~~~~~~~~~~~~~~~~~~~~~~

Light attenuation follows Beer's law:

.. math::

   E_d(z) = E_d(0^-) \exp(-K_d z)

Where :math:`K_d` is the diffuse attenuation coefficient:

.. math::

   K_d(\lambda) \approx \frac{a(\lambda) + b_b(\lambda)}{\cos \theta_w}

Path Elongation Effects
~~~~~~~~~~~~~~~~~~~~~~

Multiple scattering increases the optical path length:

.. math::

   Du = 1.03(1 + 2.4u)^{0.5}

Where :math:`u = \frac{b_b}{a + b_b}` is the single scattering albedo.

The Complete Shallow Water Model
--------------------------------

Combining all effects, the shallow water reflectance is:

.. math::

   R_{rs}(\lambda) = R_{rs}^{\infty}(\lambda)[1 - \exp(-(\frac{1}{\cos\theta_w} + \frac{Du}{\cos\theta_o})\kappa H)] + \frac{\rho_{bottom}(\lambda)}{\pi}\exp(-(\frac{1}{\cos\theta_w} + \frac{Du_b}{\cos\theta_o})\kappa H)

Where:
- :math:`R_{rs}^{\infty}(\lambda)` = optically deep water reflectance
- :math:`\kappa = a + b_b` = total attenuation coefficient
- :math:`H` = water depth
- :math:`\theta_w` = sub-surface solar zenith angle
- :math:`\theta_o` = sub-surface viewing angle
- :math:`Du_b` = path elongation for bottom-reflected light

Numerical Implementation
-----------------------

Spectral Sampling
~~~~~~~~~~~~~~~~

SAMBUCA operates on discrete wavelength bands. Key considerations:

**Wavelength Selection**:
- Match sensor bands for satellite applications
- Include key absorption features
- Balance spectral resolution with computational cost

**Interpolation**:
- Linear interpolation for most SIOPs
- Exponential interpolation for CDOM
- Careful handling of absorption edges

Geometric Considerations
~~~~~~~~~~~~~~~~~~~~~~~

**Solar Zenith Angle** :math:`\theta_s`:
   Varies with latitude, season, and time of day

**Viewing Geometry**:
   Affects path length and scattering phase function

**Refraction at Surface**:
   .. math::
      \sin \theta_w = \frac{\sin \theta_s}{n_w}
   
   Where :math:`n_w \approx 1.34` is the refractive index of water.

Boundary Conditions
~~~~~~~~~~~~~~~~~~

**Air-Water Interface**:
   Fresnel reflectance affects light transmission

**Water-Bottom Interface**:
   Lambertian reflection assumed for most substrates

Validation and Accuracy
-----------------------

Model Validation
~~~~~~~~~~~~~~~

SAMBUCA has been validated against:

1. **Synthetic Data**: Monte Carlo radiative transfer models
2. **Laboratory Measurements**: Controlled tank experiments
3. **Field Data**: In-situ radiometric measurements
4. **Satellite Observations**: Matchup analyses

Accuracy Assessment
~~~~~~~~~~~~~~~~~~

Typical accuracies for well-calibrated systems:

- **Depth**: ±10-20% for depths < 20m
- **Chlorophyll**: ±30-50% in coastal waters
- **CDOM**: ±20-40% depending on concentration
- **Bottom Type**: 80-90% classification accuracy

Sources of Error
~~~~~~~~~~~~~~~

**Model Limitations**:
- Plane-parallel assumption
- Lambertian bottom reflection
- Simplified scattering phase functions

**Input Uncertainties**:
- SIOP variability
- Atmospheric correction errors
- Substrate heterogeneity

**Environmental Factors**:
- Sun glint
- Whitecaps and foam
- Internal waves

Advanced Topics
--------------

Inelastic Scattering
~~~~~~~~~~~~~~~~~~~

For highly productive waters, consider:

**Raman Scattering**:
   Water molecules cause spectral shifts

**Fluorescence**:
   Chlorophyll fluorescence affects red/NIR bands

Polarization Effects
~~~~~~~~~~~~~~~~~~~

Polarized radiative transfer for:
- Improved atmospheric correction
- Enhanced bottom detection
- Reduced sun glint sensitivity

Spectral Shape Analysis
~~~~~~~~~~~~~~~~~~~~~~

Advanced algorithms use:
- Derivative analysis
- Principal component analysis
- Machine learning approaches

Coupled Atmosphere-Water Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For atmospheric correction:
- Simultaneous retrieval of atmosphere and water properties
- Accounting for multiple scattering between surface and atmosphere

Implementation in SAMBUCA
-------------------------

Forward Model Structure
~~~~~~~~~~~~~~~~~~~~~~

SAMBUCA implements the shallow water equations using:

1. **Modular SIOP calculation**
2. **Efficient spectral interpolation**
3. **Vectorized operations for speed**
4. **Comprehensive error checking**

Key Algorithms
~~~~~~~~~~~~~

.. code-block:: python

   def calculate_rrs_shallow(chl, cdom, nap, depth, substrate, wavelengths):
       """
       Calculate shallow water remote sensing reflectance.
       
       This implements the core radiative transfer equations
       with all the physics described in this section.
       """
       
       # Calculate IOPs
       a_total = calculate_absorption(chl, cdom, nap, wavelengths)
       bb_total = calculate_backscatter(chl, nap, wavelengths)
       
       # Deep water reflectance
       rrs_deep = calculate_deep_water_rrs(a_total, bb_total)
       
       # Path elongation
       u = bb_total / (a_total + bb_total)
       Du = 1.03 * (1 + 2.4 * u)**0.5
       
       # Shallow water equation
       kappa = a_total + bb_total
       exponential_term = np.exp(-(1/cos_theta_w + Du/cos_theta_o) * kappa * depth)
       
       rrs_shallow = (rrs_deep * (1 - exponential_term) + 
                     substrate/np.pi * exponential_term)
       
       return rrs_shallow

Optimization Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

For computational efficiency:
- Pre-compute wavelength-independent terms
- Use lookup tables for expensive functions
- Vectorize operations across wavelengths
- Cache frequently used SIOP values

Scientific References
--------------------

**Foundational Works**:

1. **Mobley, C.D. (1994)**. "Light and Water: Radiative Transfer in Natural Waters." Academic Press.

2. **Preisendorfer, R.W. (1976)**. "Hydrologic Optics." NOAA.

3. **Kirk, J.T.O. (2011)**. "Light and Photosynthesis in Aquatic Ecosystems." Cambridge University Press.

**Key Papers**:

4. **Lee, Z., et al. (1999)**. "Hyperspectral remote sensing for shallow waters: 2. Deriving bottom depths and water properties by optimization." *Applied Optics*, 38(18), 3831-3843.

5. **Gordon, H.R., et al. (1988)**. "A semianalytic radiance model of ocean color." *Journal of Geophysical Research*, 93(D9), 10909-10924.

6. **Maritorena, S., et al. (2002)**. "Optimization of a semianalytical ocean color model for global-scale applications." *Applied Optics*, 41(15), 2705-2714.

**Recent Developments**:

7. **Lee, Z., et al. (2013)**. "Euphotic zone depth: Its derivation and implication to ocean-color remote sensing." *Journal of Geophysical Research: Oceans*, 118(12), 6329-6337.

8. **Brando, V.E., et al. (2009)**. "A physics based retrieval and quality assessment of bathymetry from suboptimal hyperspectral data." *Remote Sensing of Environment*, 113(4), 755-770.

Further Reading
--------------

For deeper understanding:

**Online Resources**:
- `Ocean Optics Web Book <https://www.oceanopticsbook.info/>`_
- `IOCCG Report Series <https://ioccg.org/reports/>`_
- `NASA Ocean Color <https://oceancolor.gsfc.nasa.gov/>`_

**Specialized Topics**:
- Monte Carlo radiative transfer models
- Polarized light in water
- Fluorescence and inelastic scattering
- Coupled atmosphere-ocean radiative transfer

This theoretical foundation enables SAMBUCA to provide physically meaningful retrievals of water column and bottom properties from satellite observations.
