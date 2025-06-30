"""Spectral Chi-Square objective function.

Chi-square statistic weighted by measurement uncertainty.
"""

from typing import Dict, Any, List, Union, Optional
import numpy as np
from numpy.typing import NDArray

from .base import ForwardModelObjectiveFunction
from .. import InversionParameters


class SpectralChiSquare(ForwardModelObjectiveFunction):
    """Chi-square statistic weighted by measurement uncertainty."""
    
    def __init__(self, uncertainty: Optional[NDArray[np.float64]] = None):
        """Initialize chi-square objective function.
        
        Args:
            uncertainty: Uncertainty (standard deviation) for each wavelength.
        """
        self.uncertainty = uncertainty
    
    @property
    def name(self) -> str:
        return "spectral_chi_square"
    
    @property
    def description(self) -> str:
        return "Chi-square statistic weighted by measurement uncertainty"
    
    def __call__(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        uncertainty: Optional[NDArray[np.float64]] = None,
        return_modeled_spectra: bool = False
    ) -> Union[float, Dict[str, Any]]:
        """Calculate chi-square statistic between observed and modeled reflectance.
        
        Args:
            params: Optimization parameters.
            observed_rrs: Observed remote sensing reflectance.
            inversion_parameters: Parameters for the inversion process.
            uncertainty: Uncertainty values (overrides instance values).
            return_modeled_spectra: If True, return detailed results.
            
        Returns:
            Chi-square statistic, or detailed results dictionary.
        """
        self.validate_inputs(params, observed_rrs, inversion_parameters)
        
        uncertainty_values = uncertainty if uncertainty is not None else self.uncertainty
        
        # Run forward model
        results = self.run_forward_model(params, inversion_parameters)
        
        # Set default uncertainty if not provided
        if uncertainty_values is None:
            uncertainty_values = np.full_like(observed_rrs, 0.001)
        
        # Calculate chi-square
        chi_square = np.sum(((results.rrs - observed_rrs) / uncertainty_values) ** 2)
        
        if return_modeled_spectra:
            return self.create_detailed_result(
                error=chi_square,
                modeled_rrs=results.rrs,
                forward_results=results,
                uncertainty_used=uncertainty_values
            )
        
        return chi_square
