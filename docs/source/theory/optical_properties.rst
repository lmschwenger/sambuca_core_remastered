Optical Properties of Water
===========================

This section provides detailed coverage of the optical properties that govern light behavior in natural waters, forming the foundation for SAMBUCA's bio-optical models.

Overview of Optical Properties
------------------------------

Natural waters contain various **optically active constituents (OACs)** that interact with light:

**Pure Water** (H₂O)
   The background medium with well-known optical properties

**Phytoplankton** (Algae)
   Microscopic plants containing chlorophyll and other pigments

**Colored Dissolved Organic Matter (CDOM)**
   Dissolved organic compounds that absorb light

**Non-Algal Particles (NAP)**
   Suspended inorganic particles (sediments, detritus)

Classification of Optical Properties
-----------------------------------

Inherent vs Apparent Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Inherent Optical Properties (IOPs)**
   - Depend only on the medium
   - Independent of ambient light field
   - Examples: absorption, scattering coefficients

**Apparent Optical Properties (AOPs)**
   - Depend on both medium and light field
   - Vary with illumination conditions
   - Examples: reflectance, attenuation coefficients

Fundamental vs Derived Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Fundamental Properties**
   - Directly measurable
   - Primary descriptors of light-matter interaction
   - Absorption and scattering coefficients

**Derived Properties**
   - Calculated from fundamental properties
   - Often more directly related to remote sensing observations
   - Remote sensing reflectance, diffuse attenuation

Absorption Properties
--------------------

Physical Basis
~~~~~~~~~~~~~

Absorption occurs when photon energy is converted to other forms:
- **Electronic transitions** in molecules
- **Vibrational excitation** in molecular bonds
- **Heat generation** through non-radiative decay

Pure Water Absorption
~~~~~~~~~~~~~~~~~~~~

**Spectral Characteristics:**
- Very low in blue-green (400-500 nm)
- Increases dramatically in red-NIR (>700 nm)
- Well-characterized by laboratory measurements

**Mathematical Form:**
.. math::
   a_w(\lambda) = \text{tabulated values from Pope \& Fry (1997)}

**Key Features:**
- Minimum around 420 nm (~0.005 m⁻¹)
- Rapid increase beyond 600 nm
- Dominates total absorption in clear waters

Phytoplankton Absorption
~~~~~~~~~~~~~~~~~~~~~~~

**Pigment Basis:**
Phytoplankton absorption is due to photosynthetic pigments:

- **Chlorophyll-a**: Primary pigment (blue and red peaks)
- **Chlorophyll-b**: Accessory pigment (broader blue absorption)
- **Carotenoids**: Photoprotective pigments (blue absorption)
- **Phycobilins**: Found in cyanobacteria (green-orange absorption)

**Spectral Model:**
.. math::
   a_{ph}(\lambda) = a_{ph}^*(\lambda) \cdot [CHL]

Where :math:`a_{ph}^*(\lambda)` is the chlorophyll-specific absorption coefficient.

**Typical Spectral Shape:**
- Strong blue peak around 440 nm
- Red peak around 675 nm
- Minimum in green (500-600 nm)
- Variable shoulder around 470 nm (accessory pigments)

**Factors Affecting Variability:**
- **Pigment composition**: Varies with species and environment
- **Package effect**: Intracellular pigment concentration
- **Cell size**: Larger cells show stronger package effect
- **Nutritional status**: Affects pigment ratios

CDOM Absorption
~~~~~~~~~~~~~~

**Chemical Basis:**
CDOM consists of complex organic molecules:
- **Humic substances**: From terrestrial plant decomposition
- **Fulvic acids**: Smaller, more soluble molecules
- **Protein-like compounds**: From biological processes

**Spectral Model:**
.. math::
   a_{cdom}(\lambda) = a_{cdom}(\lambda_0) \exp[-S_{cdom}(\lambda - \lambda_0)]

Where:
- :math:`a_{cdom}(\lambda_0)` = absorption at reference wavelength (usually 440 nm)
- :math:`S_{cdom}` = spectral slope (typically 0.01-0.02 nm⁻¹)

**Spectral Characteristics:**
- Decreases exponentially with wavelength
- No specific absorption peaks
- Strongest in UV and blue
- Negligible beyond 600 nm

**Environmental Variability:**
- **Terrestrial CDOM**: Steeper slopes (S = 0.015-0.020 nm⁻¹)
- **Marine CDOM**: Gentler slopes (S = 0.012-0.018 nm⁻¹)
- **Photobleaching**: UV exposure increases slope

Non-Algal Particle Absorption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Composition:**
- **Mineral particles**: Clays, silts, sands
- **Organic detritus**: Dead plant and animal matter
- **Anthropogenic particles**: Pollutants, microplastics

**Spectral Model:**
.. math::
   a_{nap}(\lambda) = a_{nap}^*(\lambda) \cdot [NAP]

Alternative power-law form:
.. math::
   a_{nap}(\lambda) = a_{nap}(\lambda_0) \left(\frac{\lambda_0}{\lambda}\right)^{S_{nap}}

**Spectral Characteristics:**
- Generally featureless
- Decreases with wavelength (power law)
- Iron oxides may show absorption around 500 nm
- Organic detritus may have weak chlorophyll features

Scattering Properties
--------------------

Physical Basis
~~~~~~~~~~~~~

Scattering occurs due to refractive index variations:
- **Rayleigh scattering**: Particles << wavelength
- **Mie scattering**: Particles ~ wavelength
- **Geometric scattering**: Particles >> wavelength

Phase Function
~~~~~~~~~~~~~

The **scattering phase function** :math:`\beta(\theta)` describes angular distribution:

.. math::
   \int_0^{2\pi} \int_0^{\pi} \beta(\theta) \sin\theta \, d\theta \, d\phi = b(\lambda)

Where :math:`b(\lambda)` is the total scattering coefficient.

**Backscattering Coefficient:**
.. math::
   b_b(\lambda) = 2\pi \int_{\pi/2}^{\pi} \beta(\theta) \sin\theta \, d\theta

Pure Water Scattering
~~~~~~~~~~~~~~~~~~~~

**Rayleigh Scattering:**
Pure water exhibits molecular (Rayleigh) scattering:

.. math::
   b_w(\lambda) = \frac{8.06 \times 10^{-6}}{2} \left(\frac{550}{\lambda}\right)^{4.32}

**Characteristics:**
- Strong wavelength dependence (:math:`\lambda^{-4}`)
- Isotropic scattering pattern
- Backscattering ratio: :math:`\tilde{b}_{bw} = 0.5`
- Well-defined and invariant

Particle Scattering
~~~~~~~~~~~~~~~~~~

**Size Distribution:**
Natural particle assemblages follow power-law size distributions:

.. math::
   n(D) \propto D^{-\xi}

Where :math:`\xi` typically ranges from 3-5.

**Spectral Dependence:**
.. math::
   b_p(\lambda) = b_p(\lambda_0) \left(\frac{\lambda_0}{\lambda}\right)^{\gamma}

Where :math:`\gamma` depends on size distribution and composition:
- **Small particles** (algae): :math:`\gamma \approx 0.5-1.0`
- **Large particles** (sediments): :math:`\gamma \approx 1.5-2.0`

**Backscattering:**
The backscattering ratio :math:`\tilde{b}_{bp} = b_{bp}/b_p` varies with:
- **Particle size**: Smaller particles → higher :math:`\tilde{b}_{bp}`
- **Refractive index**: Higher contrast → higher :math:`\tilde{b}_{bp}`
- **Particle shape**: Non-spherical particles affect phase function

Phytoplankton Scattering
~~~~~~~~~~~~~~~~~~~~~~~

**Size and Shape Effects:**
- **Cell size**: 1-100 μm (Mie scattering regime)
- **Internal structure**: Chloroplasts, vacuoles affect scattering
- **Cell shape**: Spherical, elongated, chain-forming

**Spectral Model:**
.. math::
   b_{ph}(\lambda) = b_{ph}^*(\lambda) \cdot [CHL]

**Typical Values:**
- :math:`b_{ph}^*(550)` ≈ 0.3-0.8 m²/mg CHL
- Spectral slope :math:`\gamma_{ph}` ≈ 0.5-1.0
- Backscattering ratio :math:`\tilde{b}_{bph}` ≈ 0.01-0.02

Non-Algal Particle Scattering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Mineral Particles:**
- **Quartz, feldspars**: Low refractive index contrast
- **Clay minerals**: Small size, high surface area
- **Iron oxides**: Higher refractive index, reddish color

**Spectral Model:**
.. math::
   b_{nap}(\lambda) = b_{nap}^*(\lambda) \cdot [NAP]

**Typical Characteristics:**
- Stronger wavelength dependence than phytoplankton
- Higher backscattering ratios (:math:`\tilde{b}_{bnap}` ≈ 0.02-0.05)
- Variable with mineral composition

Combined Optical Properties
--------------------------

Total Absorption
~~~~~~~~~~~~~~~

.. math::
   a(\lambda) = a_w(\lambda) + a_{ph}(\lambda) + a_{cdom}(\lambda) + a_{nap}(\lambda)

**Relative Contributions:**
- **Clear waters**: Water dominates at most wavelengths
- **Productive waters**: Phytoplankton important in blue/red
- **CDOM-rich waters**: CDOM dominates blue absorption
- **Turbid waters**: NAP contributes significantly

Total Scattering
~~~~~~~~~~~~~~~

.. math::
   b(\lambda) = b_w(\lambda) + b_{ph}(\lambda) + b_{nap}(\lambda)

**Water vs Particles:**
- Water scattering dominates in very clear waters
- Particle scattering usually dominates in coastal waters

Attenuation Coefficient
~~~~~~~~~~~~~~~~~~~~~~

.. math::
   c(\lambda) = a(\lambda) + b(\lambda)

The attenuation coefficient determines exponential light decay.

Single Scattering Albedo
~~~~~~~~~~~~~~~~~~~~~~~

.. math::
   \omega_0(\lambda) = \frac{b(\lambda)}{c(\lambda)} = \frac{b(\lambda)}{a(\lambda) + b(\lambda)}

This dimensionless parameter indicates scattering vs absorption dominance.

Bio-Optical Relationships
-------------------------

Empirical Models
~~~~~~~~~~~~~~~

**Case 1 Waters** (Phytoplankton-dominated):
Optical properties covary with chlorophyll concentration.

**Case 2 Waters** (Multiple constituents):
Independent variation of different components.

Chlorophyll Algorithms
~~~~~~~~~~~~~~~~~~~~~

**Blue-Green Ratio:**
.. math::
   [CHL] = a_0 \left(\frac{R_{rs}(443)}{R_{rs}(555)}\right)^{a_1}

**Multi-Band Algorithms:**
More sophisticated algorithms use multiple wavelengths and account for CDOM/NAP.

Regional Variations
------------------

Oceanic Waters
~~~~~~~~~~~~~

**Characteristics:**
- Low chlorophyll (0.01-1 mg/m³)
- Low CDOM and NAP
- Optical properties dominated by water and phytoplankton

**SIOP Ranges:**
- :math:`a_{ph}^*(440)`: 0.04-0.06 m²/mg
- :math:`S_{cdom}`: 0.017-0.021 nm⁻¹
- Clear, blue waters

Coastal Waters
~~~~~~~~~~~~~

**Characteristics:**
- Higher productivity
- Terrestrial inputs (CDOM, sediments)
- More complex optical relationships

**SIOP Variations:**
- Variable pigment composition
- Higher CDOM concentrations
- Resuspended sediments

Inland Waters
~~~~~~~~~~~~

**Extreme Variations:**
- Very high CDOM (humic lakes)
- High turbidity (clay-rich lakes)
- Hypereutrophic conditions

**Special Considerations:**
- Non-algal pigments
- Tripton (non-living particles)
- Benthic algae contributions

Measurement Techniques
---------------------

In-Situ Methods
~~~~~~~~~~~~~~

**Absorption:**
- Filter pad techniques
- In-water absorption meters
- PSICAM (Point Source Integrating Cavity Absorption Meter)

**Scattering:**
- Nephelometers
- Volume scattering functions (VSF)
- Beam attenuation meters

**Backscattering:**
- Backscattering sensors (bb-meters)
- LISST (Laser In-Situ Scattering and Transmissometry)

Laboratory Methods
~~~~~~~~~~~~~~~~~

**Spectrophotometry:**
- High spectral resolution
- Controlled conditions
- Quantitative measurements

**Flow Cytometry:**
- Single cell analysis
- Size and pigment content
- Phytoplankton community structure

Remote Sensing Approaches
~~~~~~~~~~~~~~~~~~~~~~~~~

**Ocean Color:**
- Multi-spectral satellite sensors
- Airborne hyperspectral
- Algorithm development

**Lidar:**
- Depth-resolved measurements
- Particle layer detection
- Complementary to passive sensors

Temporal and Spatial Variability
-------------------------------

Seasonal Cycles
~~~~~~~~~~~~~~

**Phytoplankton Blooms:**
- Spring blooms in temperate waters
- Monsoon-driven productivity
- Seasonal pigment composition changes

**CDOM Variations:**
- River discharge patterns
- Photobleaching in summer
- Storm-driven resuspension

Diel Variations
~~~~~~~~~~~~~~

**Biological Processes:**
- Diel vertical migration
- Photoacclimation
- Cell division cycles

**Physical Processes:**
- Tidal resuspension
- Wind-driven mixing
- Temperature stratification

Spatial Heterogeneity
~~~~~~~~~~~~~~~~~~~~

**Coastal Gradients:**
- River plumes
- Upwelling zones
- Frontal boundaries

**Microscale Variability:**
- Phytoplankton patches
- Particle aggregates
- Turbulent mixing

Quality Control and Validation
-----------------------------

Data Quality Assessment
~~~~~~~~~~~~~~~~~~~~~~

**Consistency Checks:**
- Mass balance considerations
- Physical constraints
- Intercalibration exercises

**Uncertainty Analysis:**
- Measurement errors
- Temporal aliasing
- Spatial representativeness

Model Validation
~~~~~~~~~~~~~~~

**Closure Experiments:**
Compare measured and calculated AOPs using measured IOPs.

**Intercomparison Studies:**
Cross-validate different measurement techniques and algorithms.

Applications in SAMBUCA
-----------------------

SIOP Parameterization
~~~~~~~~~~~~~~~~~~~

SAMBUCA uses regionally-appropriate SIOP models:

.. code-block:: python

   def calculate_phytoplankton_absorption(chl, wavelengths, region='global'):
       """
       Calculate phytoplankton absorption using regional SIOPs.
       """
       if region == 'global':
           a_ph_star = global_ph_siops(wavelengths)
       elif region == 'coastal':
           a_ph_star = coastal_ph_siops(wavelengths)
       
       return a_ph_star * chl

Forward Model Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The optical property models are implemented in the forward model:

.. code-block:: python

   def calculate_total_absorption(chl, cdom, nap, wavelengths):
       """
       Calculate total absorption from constituent concentrations.
       """
       a_water = water_absorption(wavelengths)
       a_ph = phytoplankton_absorption(chl, wavelengths)
       a_cdom = cdom_absorption(cdom, wavelengths)
       a_nap = nap_absorption(nap, wavelengths)
       
       return a_water + a_ph + a_cdom + a_nap

Uncertainty Propagation
~~~~~~~~~~~~~~~~~~~~~~

SIOP uncertainties propagate through the forward model:

.. code-block:: python

   def propagate_siop_uncertainty(parameters, siop_errors):
       """
       Propagate SIOP uncertainties through forward model.
       """
       # Monte Carlo approach
       results = []
       for i in range(n_iterations):
           perturbed_siops = add_noise(siops, siop_errors)
           result = forward_model(parameters, perturbed_siops)
           results.append(result)
       
       return analyze_uncertainty(results)

Future Directions
----------------

Advanced SIOP Models
~~~~~~~~~~~~~~~~~~~

- **Size-fractionated** approaches
- **Functional group** models
- **Machine learning** parameterizations

Hyperspectral Applications
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Full spectral** SIOP retrieval
- **Derivative analysis** techniques
- **Feature detection** algorithms

Climate Applications
~~~~~~~~~~~~~~~~~~~

- **Long-term trends** in optical properties
- **Carbon cycle** implications
- **Ecosystem health** indicators

This comprehensive understanding of optical properties enables SAMBUCA to provide accurate and physically meaningful retrievals across diverse aquatic environments.
