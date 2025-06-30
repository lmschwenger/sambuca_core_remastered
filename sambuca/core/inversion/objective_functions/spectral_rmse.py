"""Spectral RMSE objective function.

Root Mean Square Error between observed and modeled remote sensing reflectance.
"""

from typing import Dict, Any, List, Union, Optional
import numpy as np
from numpy.typing import NDArray

from .base import ForwardModelObjectiveFunction
from .. import InversionParameters


class SpectralRMSE(ForwardModelObjectiveFunction):
    """Standard Root Mean Square Error between observed and modeled reflectance."""
    
    def __init__(self, error_weight: Optional[NDArray[np.float64]] = None):
        """Initialize the RMSE objective function.
        
        Args:
            error_weight: Optional weights for different wavelengths.
        """
        self.error_weight = error_weight
    
    @property
    def name(self) -> str:
        return "spectral_rmse"
    
    @property 
    def description(self) -> str:
        return "Root Mean Square Error between observed and modeled reflectance"
    
    def __call__(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        error_weight: Optional[NDArray[np.float64]] = None,
        return_modeled_spectra: bool = False
    ) -> Union[float, Dict[str, Any]]:
        """Calculate RMSE between observed and modeled remote sensing reflectance.
        
        Args:
            params: Optimization parameters.
            observed_rrs: Observed remote sensing reflectance.
            inversion_parameters: Parameters for the inversion process.
            error_weight: Optional weights (overrides instance weight).
            return_modeled_spectra: If True, return detailed results.
            
        Returns:
            RMSE value, or detailed results dictionary.
        """
        self.validate_inputs(params, observed_rrs, inversion_parameters)
        
        # Use provided weight or instance weight
        weight = error_weight if error_weight is not None else self.error_weight
        
        # Run forward model
        results = self.run_forward_model(params, inversion_parameters)
        
        # Calculate RMSE
        if weight is not None:
            diff_squared = weight * (results.rrs - observed_rrs) ** 2
            error = np.sqrt(np.mean(diff_squared))
        else:
            error = np.sqrt(np.mean((results.rrs - observed_rrs) ** 2))
        
        if return_modeled_spectra:
            return self.create_detailed_result(
                error=error,
                modeled_rrs=results.rrs,
                forward_results=results,
                weights_used=weight is not None
            )
        
        return error
