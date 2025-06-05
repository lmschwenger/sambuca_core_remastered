Theory & Background
==================

This section provides the theoretical foundation underlying SAMBUCA Core, covering the physics of radiative transfer, optical properties of water constituents, and computational algorithms.

.. toctree::
   :maxdepth: 2

   radiative_transfer
   optical_properties
   algorithms

Overview
--------

SAMBUCA is grounded in well-established physics and oceanographic principles:

**Radiative Transfer Theory**
   How light propagates through the water column and interacts with constituents

**Bio-Optical Modeling**
   Relationships between biological and optical properties of water

**Inverse Theory**
   Mathematical frameworks for parameter estimation from observations

**Computational Methods**
   Numerical algorithms for solving the forward and inverse problems

Key Theoretical Concepts
------------------------

Forward Model Foundation
~~~~~~~~~~~~~~~~~~~~~~~~

The SAMBUCA forward model implements the **radiative transfer equation** for shallow waters, building on the pioneering work of:

- **Albert & Mobley (2003)** - Radiative transfer theory for shallow waters
- **Lee et al. (1999, 2001)** - Semi-analytical approaches
- **Gordon et al. (1988)** - Ocean color remote sensing theory

**Core Equation:**

.. math::

   L_u(0^-, \lambda) = \int_0^{2\pi} \int_0^{\pi/2} L(\theta, \phi, \lambda) \cos\theta \sin\theta \, d\theta \, d\phi

Where :math:`L_u(0^-, \lambda)` is the upwelling radiance just below the water surface.

Inherent Optical Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~

SAMBUCA models the **inherent optical properties (IOPs)** of water constituents:

**Absorption Coefficient** :math:`a(\lambda)`
   - Pure water: :math:`a_w(\lambda)`
   - Phytoplankton: :math:`a_{ph}(\lambda) = a_{ph}^*(\lambda) \cdot CHL`
   - CDOM: :math:`a_{cdom}(\lambda) = a_{cdom}(440) \cdot e^{-S_{cdom}(\lambda - 440)}`
   - Non-algal particles: :math:`a_{nap}(\lambda) = a_{nap}^*(\lambda) \cdot NAP`

**Scattering Coefficient** :math:`b(\lambda)`
   - Water: :math:`b_w(\lambda) \propto \lambda^{-4.32}` (Rayleigh scattering)
   - Particles: :math:`b_p(\lambda) \propto \lambda^{-n}` where :math:`n \approx 0.5-2`

**Backscattering Coefficient** :math:`b_b(\lambda)`
   - :math:`b_b(\lambda) = \tilde{b}_b \cdot b(\lambda)`
   - Where :math:`\tilde{b}_b` is the backscattering probability

Semi-Analytical Approach
~~~~~~~~~~~~~~~~~~~~~~~~~

SAMBUCA uses **semi-analytical methods** that combine:

1. **Analytical solutions** where possible (e.g., exponential attenuation)
2. **Empirical relationships** for complex processes (e.g., path elongation)
3. **Parameterizations** based on field observations

This approach provides:
- **Computational efficiency** compared to full radiative transfer models
- **Physical interpretability** of parameters
- **Flexibility** for different water types and conditions

Shallow Water Modifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The key innovation in SAMBUCA is extending ocean color theory to **shallow waters** by:

1. **Bottom Contribution**: Adding substrate reflectance :math:`R_{bottom}(\lambda)`
2. **Path Elongation**: Accounting for multiple scattering effects
3. **Depth Dependence**: Modeling exponential attenuation with depth

**Shallow Water Equation:**

.. math::

   R_{rs}(\lambda) = R_{rs}^{deep}(\lambda) \cdot [1 - e^{-(\frac{1}{\cos\theta_w} + \frac{Du}{\cos\theta_0}) \kappa H}] + \frac{R_{bottom}(\lambda)}{\pi} e^{-(\frac{1}{\cos\theta_w} + \frac{Du_b}{\cos\theta_0}) \kappa H}

Inversion Theory
~~~~~~~~~~~~~~~

SAMBUCA inversion is based on **optimization theory**:

**Objective Function:**
.. math::

   \chi^2(\mathbf{p}) = \sum_{i=1}^{N} \left( \frac{R_{obs}(\lambda_i) - R_{model}(\lambda_i, \mathbf{p})}{\sigma_i} \right)^2

**Parameter Vector:** :math:`\mathbf{p} = [CHL, CDOM, NAP, H, ...]`

**Constraints:** Physical bounds and relationships between parameters

Scientific Validation
---------------------

SAMBUCA theory has been validated through:

1. **Synthetic Data Studies** - Testing with known parameters
2. **Field Measurements** - Comparison with in-situ data
3. **Inter-comparisons** - Consistency with other bio-optical models
4. **Sensitivity Analysis** - Understanding parameter interactions

Key Publications
----------------

**Foundational Works:**

1. **Lee, Z., et al. (1999)**. "Hyperspectral remote sensing for shallow waters: 2. Deriving bottom depths and water properties by optimization." *Applied Optics*, 38(18), 3831-3843.

2. **Mobley, C.D. (1994)**. "Light and Water: Radiative Transfer in Natural Waters." Academic Press.

3. **Gordon, H.R., et al. (1988)**. "A semianalytic radiance model of ocean color." *Journal of Geophysical Research*, 93(D9), 10909-10924.

**Recent Developments:**

4. **Brando, V.E., et al. (2009)**. "A physics based retrieval and quality assessment of bathymetry from suboptimal hyperspectral data." *Remote Sensing of Environment*, 113(4), 755-770.

5. **Lee, Z., et al. (2013)**. "Euphotic zone depth: Its derivation and implication to ocean-color remote sensing." *Journal of Geophysical Research: Oceans*, 118(12), 6329-6337.

Further Reading
---------------

For detailed theoretical development:

:doc:`radiative_transfer`
   Complete derivation of the radiative transfer equations used in SAMBUCA

:doc:`optical_properties`
   Detailed explanation of inherent and apparent optical properties

:doc:`algorithms`
   Mathematical algorithms and numerical methods implementation

**External Resources:**

- `Ocean Optics Web Book <https://www.oceanopticsbook.info/>`_ - Comprehensive reference
- `IOCCG Reports <https://ioccg.org/reports/>`_ - International Ocean Colour Coordinating Group
- `NASA Ocean Color <https://oceancolor.gsfc.nasa.gov/>`_ - Algorithms and validation

Application Areas
-----------------

SAMBUCA theory enables applications in:

🌊 **Coastal Monitoring**
   Water quality assessment in shallow coastal environments

🐠 **Habitat Mapping**
   Benthic habitat classification and monitoring

📊 **Bathymetric Mapping**
   Satellite-derived bathymetry for navigation and coastal management

🔬 **Biogeochemical Studies**
   Carbon cycling and primary productivity estimation

🏝️ **Coral Reef Assessment**
   Health monitoring and change detection

The following sections provide detailed mathematical development and practical implementation guidance for these theoretical concepts.
