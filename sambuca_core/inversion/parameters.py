"""Enhanced Parameter definitions for the Sambuca inversion process."""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Union, Any

import numpy as np
from numpy.typing import NDArray


@dataclass
class InversionParameters:
    """Parameters for the inversion process.

    This class represents both the parameters to be inverted for and those that
    remain fixed during the inversion process. Enhanced to match the full
    SAMBUCA paper capabilities including substrate unmixing and SIOP optimization.

    Attributes:
        chl: Bounds for chlorophyll concentration if being inverted, or None if fixed.
        cdom: Bounds for CDOM concentration if being inverted, or None if fixed.
        nap: Bounds for NAP concentration if being inverted, or None if fixed.
        depth: Bounds for water depth if being inverted, or None if fixed.
        substrate_fraction: Bounds for substrate fraction if being inverted, or None if fixed.

        # NEW: SIOP Parameters (can now be optimized when field data is limited)
        a_cdom_slope: Bounds for CDOM absorption slope if being inverted.
        a_nap_slope: Bounds for NAP absorption slope if being inverted.
        bb_ph_slope: Bounds for phytoplankton backscatter slope if being inverted.
        bb_nap_slope: Bounds for NAP backscatter slope if being inverted.
        x_ph_lambda0x: Bounds for phytoplankton specific backscatter if being inverted.
        x_nap_lambda0x: Bounds for NAP specific backscatter if being inverted.
        a_cdom_lambda0cdom: Bounds for CDOM reference absorption if being inverted.
        a_nap_lambda0nap: Bounds for NAP reference absorption if being inverted.

        fixed_chl: Fixed value for chlorophyll concentration when not inverted.
        fixed_cdom: Fixed value for CDOM concentration when not inverted.
        fixed_nap: Fixed value for NAP concentration when not inverted.
        fixed_depth: Fixed value for water depth when not inverted.
        fixed_substrate_fraction: Fixed value for substrate fraction when not inverted.

        # NEW: Fixed SIOP values (used when not being optimized)
        fixed_a_cdom_slope: Fixed CDOM slope value.
        fixed_a_nap_slope: Fixed NAP slope value.
        fixed_bb_ph_slope: Fixed phytoplankton backscatter slope.
        fixed_bb_nap_slope: Fixed NAP backscatter slope.
        fixed_x_ph_lambda0x: Fixed phytoplankton specific backscatter.
        fixed_x_nap_lambda0x: Fixed NAP specific backscatter.
        fixed_a_cdom_lambda0cdom: Fixed CDOM reference absorption.
        fixed_a_nap_lambda0nap: Fixed NAP reference absorption.

        wavelengths: Central wavelengths of the spectral bands.
        a_water: Absorption coefficient of pure water.
        a_ph_star: Specific absorption of phytoplankton.
        substrate1: First benthic substrate reflectance.
        substrate2: Optional second benthic substrate reflectance.
        substrate3: Optional third benthic substrate reflectance (NEW).

        # Reference wavelengths and physical constants
        lambda0cdom: Reference wavelength for CDOM absorption.
        lambda0nap: Reference wavelength for NAP absorption.
        lambda0x: Backscattering reference wavelength.
        bb_lambda_ref: Reference wavelength for backscattering coefficient.
        water_refractive_index: Refractive index of water.
        theta_air: Solar zenith angle in degrees.
        off_nadir: Off-nadir angle in degrees.
        q_factor: Q value for producing R(0-) values.

        nedr: Noise equivalent delta reflectance for error weighting.
    """
    # === PRIMARY OPTIMIZATION PARAMETERS ===
    # Parameters that can be inverted for (None if fixed)
    chl: Optional[Tuple[float, float]] = None  # (min, max) bounds if inverted
    cdom: Optional[Tuple[float, float]] = None
    nap: Optional[Tuple[float, float]] = None
    depth: Optional[Tuple[float, float]] = None
    substrate_fraction: Optional[Tuple[float, float]] = None  # CRITICAL for SAMBUCA

    # === NEW: SIOP OPTIMIZATION PARAMETERS ===
    # These can be optimized when field data is limited (as per SAMBUCA paper)
    a_cdom_slope: Optional[Tuple[float, float]] = None      # CDOM absorption slope
    a_nap_slope: Optional[Tuple[float, float]] = None       # NAP absorption slope
    bb_ph_slope: Optional[Tuple[float, float]] = None       # Phytoplankton backscatter slope
    bb_nap_slope: Optional[Tuple[float, float]] = None      # NAP backscatter slope
    x_ph_lambda0x: Optional[Tuple[float, float]] = None     # Phytoplankton specific backscatter
    x_nap_lambda0x: Optional[Tuple[float, float]] = None    # NAP specific backscatter
    a_cdom_lambda0cdom: Optional[Tuple[float, float]] = None  # CDOM reference absorption
    a_nap_lambda0nap: Optional[Tuple[float, float]] = None    # NAP reference absorption

    nedr: Optional[Union[List[float], NDArray[np.float64]]] = None

    # === FIXED PARAMETER VALUES ===
    # Fixed parameter values (used when the corresponding bound is None)
    fixed_chl: float = 1.0
    fixed_cdom: float = 0.5
    fixed_nap: float = 1.0
    fixed_depth: float = 5.0
    fixed_substrate_fraction: float = 1.0

    # NEW: Fixed SIOP values (defaults from SAMBUCA paper)
    fixed_a_cdom_slope: float = 0.0168052
    fixed_a_nap_slope: float = 0.00977262
    fixed_bb_ph_slope: float = 0.878138
    fixed_bb_nap_slope: Optional[float] = None
    fixed_x_ph_lambda0x: float = 0.00157747
    fixed_x_nap_lambda0x: float = 0.0225353
    fixed_a_cdom_lambda0cdom: float = 1.0
    fixed_a_nap_lambda0nap: float = 0.00433

    # === ESSENTIAL PARAMETERS FOR THE FORWARD MODEL ===
    wavelengths: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    a_water: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    a_ph_star: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    substrate1: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    substrate2: Optional[Union[List[float], NDArray[np.float64]]] = None
    substrate3: Optional[Union[List[float], NDArray[np.float64]]] = None  # NEW: Third substrate

    # Other forward model parameters with default values
    lambda0cdom: float = 550.0
    lambda0nap: float = 550.0
    lambda0x: float = 546.0
    bb_lambda_ref: float = 550.0
    water_refractive_index: float = 1.33784
    theta_air: float = 30.0
    off_nadir: float = 0.0
    q_factor: float = np.pi

    def set_nedr(self, nedr_values: Union[List[float], NDArray[np.float64]]) -> 'InversionParameters':
        """Set NEDR values for the inversion.

        Args:
            nedr_values: NEDR values for each wavelength

        Returns:
            Self for method chaining

        Raises:
            ValueError: If NEDR values length doesn't match wavelengths
        """
        nedr_array = np.asarray(nedr_values)

        if len(nedr_array) != len(self.wavelengths):
            raise ValueError(
                f"NEDR values length ({len(nedr_array)}) must match wavelengths length ({len(self.wavelengths)})")

        self.nedr = nedr_array
        return self

    def get_parameter_bounds(self) -> List[Tuple[float, float]]:
        """Returns bounds for all parameters being inverted.

        Returns:
            List of (min, max) tuples for each parameter being inverted.
        """
        bounds = []

        # Primary parameters (original order maintained for compatibility)
        if self.chl is not None:
            bounds.append(self.chl)
        if self.cdom is not None:
            bounds.append(self.cdom)
        if self.nap is not None:
            bounds.append(self.nap)
        if self.depth is not None:
            bounds.append(self.depth)
        if self.substrate_fraction is not None:
            bounds.append(self.substrate_fraction)

        # NEW: SIOP parameters
        if self.a_cdom_slope is not None:
            bounds.append(self.a_cdom_slope)
        if self.a_nap_slope is not None:
            bounds.append(self.a_nap_slope)
        if self.bb_ph_slope is not None:
            bounds.append(self.bb_ph_slope)
        if self.bb_nap_slope is not None:
            bounds.append(self.bb_nap_slope)
        if self.x_ph_lambda0x is not None:
            bounds.append(self.x_ph_lambda0x)
        if self.x_nap_lambda0x is not None:
            bounds.append(self.x_nap_lambda0x)
        if self.a_cdom_lambda0cdom is not None:
            bounds.append(self.a_cdom_lambda0cdom)
        if self.a_nap_lambda0nap is not None:
            bounds.append(self.a_nap_lambda0nap)

        return bounds

    def get_inversion_parameter_names(self) -> List[str]:
        """Returns names of parameters being inverted.

        Returns:
            List of parameter names that are being inverted.
        """
        names = []

        # Primary parameters (original order maintained)
        if self.chl is not None:
            names.append("chl")
        if self.cdom is not None:
            names.append("cdom")
        if self.nap is not None:
            names.append("nap")
        if self.depth is not None:
            names.append("depth")
        if self.substrate_fraction is not None:
            names.append("substrate_fraction")

        # NEW: SIOP parameters
        if self.a_cdom_slope is not None:
            names.append("a_cdom_slope")
        if self.a_nap_slope is not None:
            names.append("a_nap_slope")
        if self.bb_ph_slope is not None:
            names.append("bb_ph_slope")
        if self.bb_nap_slope is not None:
            names.append("bb_nap_slope")
        if self.x_ph_lambda0x is not None:
            names.append("x_ph_lambda0x")
        if self.x_nap_lambda0x is not None:
            names.append("x_nap_lambda0x")
        if self.a_cdom_lambda0cdom is not None:
            names.append("a_cdom_lambda0cdom")
        if self.a_nap_lambda0nap is not None:
            names.append("a_nap_lambda0nap")

        return names

    def get_forward_model_params(self, x: List[float]) -> Dict[str, Any]:
        """Convert optimization parameters to forward model parameters.

        Args:
            x: Parameter values from the optimizer.

        Returns:
            Dictionary of parameters for the forward model.
        """
        # Ensure the wavelengths list is properly set
        if self.wavelengths is None:
            raise ValueError("Wavelengths must be specified for inversion")

        # Start with default fixed parameters
        params = {
            'chl': self.fixed_chl,
            'cdom': self.fixed_cdom,
            'nap': self.fixed_nap,
            'depth': self.fixed_depth,
            'substrate_fraction': self.fixed_substrate_fraction,
            'wavelengths': self.wavelengths,
            'a_water': self.a_water,
            'a_ph_star': self.a_ph_star,
            'substrate1': self.substrate1,
            'num_bands': len(self.wavelengths),

            # SIOP parameters with fixed defaults
            'a_cdom_slope': self.fixed_a_cdom_slope,
            'a_nap_slope': self.fixed_a_nap_slope,
            'bb_ph_slope': self.fixed_bb_ph_slope,
            'x_ph_lambda0x': self.fixed_x_ph_lambda0x,
            'x_nap_lambda0x': self.fixed_x_nap_lambda0x,
            'a_cdom_lambda0cdom': self.fixed_a_cdom_lambda0cdom,
            'a_nap_lambda0nap': self.fixed_a_nap_lambda0nap,

            # Reference wavelengths and constants
            'lambda0cdom': self.lambda0cdom,
            'lambda0nap': self.lambda0nap,
            'lambda0x': self.lambda0x,
            'bb_lambda_ref': self.bb_lambda_ref,
            'water_refractive_index': self.water_refractive_index,
            'theta_air': self.theta_air,
            'off_nadir': self.off_nadir,
            'q_factor': self.q_factor,
        }

        # Add optional substrates
        if self.substrate2 is not None:
            params['substrate2'] = self.substrate2
        if self.substrate3 is not None:
            params['substrate3'] = self.substrate3

        # Handle bb_nap_slope default
        if self.fixed_bb_nap_slope is not None:
            params['bb_nap_slope'] = self.fixed_bb_nap_slope

        # Override with parameters being optimized
        idx = 0
        param_names = self.get_inversion_parameter_names()

        for param_name in param_names:
            params[param_name] = x[idx]
            idx += 1

        return params

    def get_initial_values(self) -> List[float]:
        """Get initial values for the parameters being inverted.

        Returns midpoints of the parameter bounds as starting values.

        Returns:
            List of initial parameter values.
        """
        initial_values = []
        bounds = self.get_parameter_bounds()

        for bound in bounds:
            initial_values.append((bound[0] + bound[1]) / 2)

        return initial_values

    def update_from_siop_manager(self, siop_manager, sensor_name):
        """Update parameters from a SIOPManager for a specific sensor.

        Args:
            siop_manager: SIOPManager instance.
            sensor_name: Name of a registered sensor.

        Returns:
            Self for method chaining.

        Raises:
            KeyError: If required SIOPs cannot be found.
        """
        # Get standard SIOPs
        siops = siop_manager.get_standard_siops(sensor_name)

        # Update parameters
        self.wavelengths = siops['wavelengths']
        self.a_water = siops['a_water']
        self.a_ph_star = siops['a_ph_star']
        self.substrate1 = siops['substrate1']

        # Optional parameters
        if 'substrate2' in siops:
            self.substrate2 = siops['substrate2']
        if 'substrate3' in siops:
            self.substrate3 = siops['substrate3']

        return self

    # === NEW: CONFIGURATION METHODS FOR DIFFERENT SCENARIOS ===

    def configure_for_shallow_water(self, enable_substrate_unmixing: bool = True):
        """Configure parameters for typical shallow water applications (the main SAMBUCA use case).

        Args:
            enable_substrate_unmixing: Whether to enable substrate fraction optimization.
                                     Should almost always be True for shallow water.

        Returns:
            Self for method chaining.
        """
        # Enable primary parameters that are usually optimized in shallow water
        self.depth = (0.1, 20.0)  # Depth range for shallow water

        # CRITICAL: Substrate unmixing is fundamental to SAMBUCA
        if enable_substrate_unmixing:
            self.substrate_fraction = (0.0, 1.0)

        # Water quality parameters with typical shallow water ranges
        if self.chl is None:
            self.chl = (0.1, 10.0)    # Chlorophyll
        if self.cdom is None:
            self.cdom = (0, 0.03)   # CDOM
        if self.nap is None:
            self.nap = (0.001, 5.0)     # NAP

        return self

    def configure_for_deep_water(self):
        """Configure parameters for optically deep water applications.

        Returns:
            Self for method chaining.
        """
        # Don't optimize depth or substrate for deep water
        self.depth = None
        self.substrate_fraction = None

        # Focus on water column parameters with wider ranges
        if self.chl is None:
            self.chl = (0.01, 50.0)   # Wider chlorophyll range for deep water
        if self.cdom is None:
            self.cdom = (0.001, 5.0)  # CDOM
        if self.nap is None:
            self.nap = (0.01, 10.0)   # NAP

        return self

    def enable_siop_optimization(self, conservative: bool = True):
        """Enable optimization of SIOP parameters when field data is limited.

        This matches the SAMBUCA paper's approach of optimizing SIOPs when
        they are not well-known for the study area.

        Args:
            conservative: If True, use conservative ranges. If False, use wider ranges.

        Returns:
            Self for method chaining.
        """
        if conservative:
            # Conservative ranges based on literature
            self.a_cdom_slope = (0.014, 0.020)      # Narrower range around default
            self.bb_ph_slope = (0.7, 1.1)           # Conservative backscatter range
            self.x_ph_lambda0x = (0.001, 0.003)     # Conservative specific backscatter
        else:
            # Wider ranges for more uncertain conditions
            self.a_cdom_slope = (0.010, 0.025)      # Wider CDOM slope range
            self.a_nap_slope = (0.005, 0.015)       # NAP slope range
            self.bb_ph_slope = (0.5, 1.5)           # Wider backscatter slope range
            self.bb_nap_slope = (0.5, 1.5)          # NAP backscatter slope
            self.x_ph_lambda0x = (0.0005, 0.005)    # Wider specific backscatter range
            self.x_nap_lambda0x = (0.01, 0.05)      # NAP specific backscatter

        return self

    def disable_siop_optimization(self):
        """Disable SIOP optimization (use fixed values).

        Returns:
            Self for method chaining.
        """
        self.a_cdom_slope = None
        self.a_nap_slope = None
        self.bb_ph_slope = None
        self.bb_nap_slope = None
        self.x_ph_lambda0x = None
        self.x_nap_lambda0x = None
        self.a_cdom_lambda0cdom = None
        self.a_nap_lambda0nap = None

        return self

    def get_optimization_complexity(self) -> Dict[str, Any]:
        """Get information about the optimization complexity.

        Returns:
            Dictionary with optimization statistics.
        """
        param_names = self.get_inversion_parameter_names()
        n_params = len(param_names)
        n_bands = len(self.wavelengths) if self.wavelengths is not None else 0

        # Categorize parameters
        primary_params = [p for p in param_names if p in ['chl', 'cdom', 'nap', 'depth', 'substrate_fraction']]
        siop_params = [p for p in param_names if p not in primary_params]

        return {
            'total_parameters': n_params,
            'spectral_bands': n_bands,
            'overdetermined': n_bands > n_params,
            'primary_parameters': len(primary_params),
            'siop_parameters': len(siop_params),
            'parameter_names': param_names,
            'substrate_unmixing_enabled': self.substrate_fraction is not None,
            'siop_optimization_enabled': len(siop_params) > 0,
            'recommended_min_bands': n_params + 3,  # Rule of thumb: params + 3
        }