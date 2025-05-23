"""Parameter definitions for the Sambuca inversion process."""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Union, Any

import numpy as np
from numpy.typing import NDArray


@dataclass
class InversionParameters:
    """Parameters for the inversion process.

    This class represents both the parameters to be inverted for and those that
    remain fixed during the inversion process.

    Attributes:
        chl: Bounds for chlorophyll concentration if being inverted, or None if fixed.
        cdom: Bounds for CDOM concentration if being inverted, or None if fixed.
        nap: Bounds for NAP concentration if being inverted, or None if fixed.
        depth: Bounds for water depth if being inverted, or None if fixed.
        substrate_fraction: Bounds for substrate fraction if being inverted, or None if fixed.

        fixed_chl: Fixed value for chlorophyll concentration when not inverted.
        fixed_cdom: Fixed value for CDOM concentration when not inverted.
        fixed_nap: Fixed value for NAP concentration when not inverted.
        fixed_depth: Fixed value for water depth when not inverted.
        fixed_substrate_fraction: Fixed value for substrate fraction when not inverted.

        wavelengths: Central wavelengths of the spectral bands.
        a_water: Absorption coefficient of pure water.
        a_ph_star: Specific absorption of phytoplankton.
        substrate1: First benthic substrate reflectance.
        substrate2: Optional second benthic substrate reflectance.

        a_cdom_slope: Slope of CDOM absorption.
        a_nap_slope: Slope of NAP absorption.
        bb_ph_slope: Power law exponent for phytoplankton backscattering.
        bb_nap_slope: Power law exponent for NAP backscattering.
        lambda0cdom: Reference wavelength for CDOM absorption.
        lambda0nap: Reference wavelength for NAP absorption.
        lambda0x: Backscattering reference wavelength.
        x_ph_lambda0x: Specific backscatter of chlorophyll at lambda0x.
        x_nap_lambda0x: Specific backscatter of NAP at lambda0x.
        a_cdom_lambda0cdom: Absorption of CDOM at lambda0cdom.
        a_nap_lambda0nap: Absorption of NAP at lambda0nap.
        bb_lambda_ref: Reference wavelength for backscattering coefficient.
        water_refractive_index: Refractive index of water.
        theta_air: Solar zenith angle in degrees.
        off_nadir: Off-nadir angle in degrees.
        q_factor: Q value for producing R(0-) values.
    """
    # Parameters that can be inverted for (None if fixed)
    chl: Optional[Tuple[float, float]] = None  # (min, max) bounds if inverted
    cdom: Optional[Tuple[float, float]] = None
    nap: Optional[Tuple[float, float]] = None
    depth: Optional[Tuple[float, float]] = None
    substrate_fraction: Optional[Tuple[float, float]] = None
    nedr: Optional[Union[List[float], NDArray[np.float64]]] = None

    # Fixed parameter values (used when the corresponding bound is None)
    fixed_chl: float = 1.0
    fixed_cdom: float = 0.5
    fixed_nap: float = 1.0
    fixed_depth: float = 5.0
    fixed_substrate_fraction: float = 1.0

    # Essential parameters for the forward model
    wavelengths: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    a_water: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    a_ph_star: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    substrate1: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    substrate2: Optional[Union[List[float], NDArray[np.float64]]] = None

    # Other forward model parameters with default values
    a_cdom_slope: float = 0.0168052
    a_nap_slope: float = 0.00977262
    bb_ph_slope: float = 0.878138
    bb_nap_slope: Optional[float] = None
    lambda0cdom: float = 550.0
    lambda0nap: float = 550.0
    lambda0x: float = 546.0
    x_ph_lambda0x: float = 0.00157747
    x_nap_lambda0x: float = 0.0225353
    a_cdom_lambda0cdom: float = 1.0
    a_nap_lambda0nap: float = 0.00433
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
        return bounds

    def get_inversion_parameter_names(self) -> List[str]:
        """Returns names of parameters being inverted.

        Returns:
            List of parameter names that are being inverted.
        """
        names = []
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
            'a_cdom_slope': self.a_cdom_slope,
            'a_nap_slope': self.a_nap_slope,
            'bb_ph_slope': self.bb_ph_slope,
            'lambda0cdom': self.lambda0cdom,
            'lambda0nap': self.lambda0nap,
            'lambda0x': self.lambda0x,
            'x_ph_lambda0x': self.x_ph_lambda0x,
            'x_nap_lambda0x': self.x_nap_lambda0x,
            'a_cdom_lambda0cdom': self.a_cdom_lambda0cdom,
            'a_nap_lambda0nap': self.a_nap_lambda0nap,
            'bb_lambda_ref': self.bb_lambda_ref,
            'water_refractive_index': self.water_refractive_index,
            'theta_air': self.theta_air,
            'off_nadir': self.off_nadir,
            'q_factor': self.q_factor,
        }

        # Add optional parameters if they exist
        if self.substrate2 is not None:
            params['substrate2'] = self.substrate2
        if self.bb_nap_slope is not None:
            params['bb_nap_slope'] = self.bb_nap_slope

        # Override with parameters being optimized
        idx = 0
        if self.chl is not None:
            params['chl'] = x[idx]
            idx += 1
        if self.cdom is not None:
            params['cdom'] = x[idx]
            idx += 1
        if self.nap is not None:
            params['nap'] = x[idx]
            idx += 1
        if self.depth is not None:
            params['depth'] = x[idx]
            idx += 1
        if self.substrate_fraction is not None:
            params['substrate_fraction'] = x[idx]
            idx += 1

        return params

    def get_initial_values(self) -> List[float]:
        """Get initial values for the parameters being inverted.

        Returns midpoints of the parameter bounds as starting values.

        Returns:
            List of initial parameter values.
        """
        initial_values = []

        if self.chl is not None:
            initial_values.append((self.chl[0] + self.chl[1]) / 2)
        if self.cdom is not None:
            initial_values.append((self.cdom[0] + self.cdom[1]) / 2)
        if self.nap is not None:
            initial_values.append((self.nap[0] + self.nap[1]) / 2)
        if self.depth is not None:
            initial_values.append((self.depth[0] + self.depth[1]) / 2)
        if self.substrate_fraction is not None:
            initial_values.append((self.substrate_fraction[0] + self.substrate_fraction[1]) / 2)

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

        return self

    def get_adaptive_initial_values(self, observed_rrs: Optional[NDArray] = None) -> List[float]:
        """Get adaptive initial values based on spectral characteristics.

        Args:
            observed_rrs: Observed reflectance spectrum for adaptive initialization

        Returns:
            List of initial parameter values.
        """
        initial_values = []

        # Adaptive initialization based on spectral characteristics
        if observed_rrs is not None and len(observed_rrs) >= 3:
            # Estimate chlorophyll from blue-green ratio (approximate)
            if len(observed_rrs) >= 3:
                blue_green_ratio = observed_rrs[0] / observed_rrs[2] if observed_rrs[2] > 0 else 1.0
                estimated_chl = max(0.1, min(5.0, 2.0 / blue_green_ratio))
            else:
                estimated_chl = 1.0

            # Estimate depth from overall magnitude
            magnitude = np.mean(observed_rrs)
            if magnitude < 0.005:  # Very low reflectance suggests deep water
                estimated_depth = 8.0
            elif magnitude > 0.02:  # High reflectance suggests shallow water
                estimated_depth = 2.0
            else:
                estimated_depth = 5.0
        else:
            estimated_chl = 1.0
            estimated_depth = 5.0

        # Set initial values for parameters being inverted
        if self.chl is not None:
            # Constrain to bounds
            chl_init = max(self.chl[0], min(self.chl[1], estimated_chl))
            initial_values.append(chl_init)

        if self.cdom is not None:
            # CDOM often correlates with chlorophyll in coastal waters
            cdom_init = max(self.cdom[0], min(self.cdom[1], estimated_chl * 0.3))
            initial_values.append(cdom_init)

        if self.nap is not None:
            # NAP estimation - start conservatively
            nap_init = (self.nap[0] + self.nap[1]) / 2
            initial_values.append(nap_init)

        if self.depth is not None:
            depth_init = max(self.depth[0], min(self.depth[1], estimated_depth))
            initial_values.append(depth_init)

        if self.substrate_fraction is not None:
            # Start with pure substrate 1
            initial_values.append(1.0)

        return initial_values


# Add to parameters.py for adaptive bounds based on water conditions

def create_adaptive_inversion_parameters(
        wavelengths,
        siop_manager,
        sensor_name,
        water_type="coastal",  # "coastal", "oceanic", or "inland"
        max_depth=None,
        image_stats=None  # Optional: statistics from the image for adaptive bounds
):
    """Create InversionParameters with adaptive bounds based on water type and image characteristics.

    Args:
        wavelengths: Sensor wavelengths
        siop_manager: SIOPManager instance
        sensor_name: Registered sensor name
        water_type: Type of water body ("coastal", "oceanic", "inland")
        max_depth: Maximum expected depth (if known)
        image_stats: Optional dictionary with image statistics for adaptive bounds

    Returns:
        InversionParameters with appropriate bounds for the water type
    """

    # Base parameter bounds by water type
    bounds_by_type = {
        "oceanic": {
            "chl": (0.01, 3.0),
            "cdom": (0.001, 0.2),
            "nap": (0.001, 0.5),
            "depth": (5.0, 50.0)
        },
        "coastal": {
            "chl": (0.1, 20.0),
            "cdom": (0.01, 1.5),
            "nap": (0.01, 5.0),
            "depth": (0.5, 30.0)
        },
        "inland": {
            "chl": (0.5, 100.0),
            "cdom": (0.05, 5.0),
            "nap": (0.1, 20.0),
            "depth": (0.5, 25.0)
        }
    }

    # Get base bounds for water type
    base_bounds = bounds_by_type.get(water_type, bounds_by_type["coastal"])

    # Adjust bounds based on image statistics if provided
    if image_stats:
        # Adjust depth bounds based on overall image brightness
        mean_reflectance = image_stats.get('mean_reflectance', 0.01)
        if mean_reflectance < 0.005:  # Very dark image suggests deeper water
            base_bounds["depth"] = (base_bounds["depth"][0], min(base_bounds["depth"][1] * 2, 100.0))
        elif mean_reflectance > 0.02:  # Bright image suggests shallower water
            base_bounds["depth"] = (0.1, min(base_bounds["depth"][1], 15.0))

    # Apply maximum depth constraint if provided
    if max_depth:
        base_bounds["depth"] = (base_bounds["depth"][0], min(base_bounds["depth"][1], max_depth))

    # Create InversionParameters
    params = InversionParameters(
        chl=base_bounds["chl"],
        cdom=base_bounds["cdom"],
        nap=base_bounds["nap"],
        depth=base_bounds["depth"],
        substrate_fraction=(0.0, 1.0),  # Always allow full range for substrate mixing
    )

    # Update with SIOPs
    params.update_from_siop_manager(siop_manager, sensor_name)

    return params


def calculate_image_statistics(image, mask=None):
    """Calculate statistics from the image to help with adaptive bounds.

    Args:
        image: Hyperspectral image (height, width, bands)
        mask: Optional mask of valid pixels

    Returns:
        Dictionary with image statistics
    """
    if mask is not None:
        valid_pixels = image[mask]
    else:
        valid_pixels = image[~np.isnan(image).any(axis=2)]

    if len(valid_pixels) == 0:
        return {'mean_reflectance': 0.01}

    # Calculate mean reflectance across all bands
    mean_reflectance = np.mean(valid_pixels)

    # Calculate band-specific statistics
    band_means = np.mean(valid_pixels, axis=0)

    # Calculate some water-type indicators
    blue_green_ratio = band_means[0] / band_means[1] if len(band_means) > 1 and band_means[1] > 0 else 1.0

    return {
        'mean_reflectance': mean_reflectance,
        'band_means': band_means,
        'blue_green_ratio': blue_green_ratio,
        'overall_brightness': np.percentile(valid_pixels.flatten(), 95)  # 95th percentile
    }