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

    # Fixed parameter values (used when corresponding bound is None)
    fixed_chl: float = 1.0  # ug/L
    fixed_cdom: float = 0.05 # ratio # https://doi.pangaea.de/10.1594/PANGAEA.921534
    fixed_nap: float = 1.0  # mg/L
    fixed_depth: float = 5.0  # meter
    fixed_substrate_fraction: float = 1.0  # ratio

    # Essential parameters for the forward model
    wavelengths: Union[List[float], NDArray[np.float64]] = field(default_factory=list)  # nanometers
    a_water: Union[List[float], NDArray[np.float64]] = field(default_factory=list)  # m^-1
    a_ph_star: Union[List[float], NDArray[np.float64]] = field(default_factory=list)  # m^-1
    substrate1: Union[List[float], NDArray[np.float64]] = field(default_factory=list)
    substrate2: Optional[Union[List[float], NDArray[np.float64]]] = None

    # Other forward model parameters with default values
    a_cdom_slope: float = 0.0168052  # nm^-1
    a_nap_slope: float = -0.0118  # nm^-1  # swampy do -0.0118 ... originally was 0.00977262
    bb_ph_slope: float = 0.878138
    bb_nap_slope: Optional[float] = None
    lambda0cdom: float = 550.0
    lambda0nap: float = 550.0
    lambda0x: float = 546.0
    x_ph_lambda0x: float = 0.00157747  # m^2/g -- backscatter coefficient
    x_nap_lambda0x: float = 0.0225353  # m^2/g  -- 0.01 in swampy ... backscatter coefficient ... originally, 0.0225
    a_cdom_lambda0cdom: float = 1.0  # m^-1
    a_nap_lambda0nap: float = 0.00433  # m^-1
    bb_lambda_ref: float = 550.0
    water_refractive_index: float = 1.33784
    theta_air: float = 30.0
    off_nadir: float = 0.0
    q_factor: float = np.pi

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