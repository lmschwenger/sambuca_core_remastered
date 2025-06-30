"""Spectral Relative RMSE objective function.

Relative RMSE - less sensitive to absolute magnitude differences.
"""

from typing import Dict, Any, List, Union, Optional
import numpy as np
from numpy.typing import NDArray

from .base import ForwardModelObjectiveFunction
from .. import InversionParameters


class SpectralRelativeRMSE(ForwardModelObjectiveFunction):
    """Relative RMSE - less sensitive to absolute magnitude differences."""
    
    def __init__(self, epsilon: float = 1e-6):
        """Initialize the relative RMSE objective function.
        
        Args:
            epsilon: Small number to avoid division by zero.
        """
        self.epsilon = epsilon
    
    @property
    def name(self) -> str:
        return "spectral_relative_rmse"
    
    @property
    def description(self) -> str:
        return "Relative RMSE - normalized by observed values"
    
    def __call__(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        epsilon: Optional[float] = None,
        return_modeled_spectra: bool = False
    ) -> Union[float, Dict[str, Any]]:
        """Calculate relative RMSE between observed and modeled reflectance.
        
        Args:
            params: Optimization parameters.
            observed_rrs: Observed remote sensing reflectance.
            inversion_parameters: Parameters for the inversion process.
            epsilon: Small number to avoid division by zero (overrides instance value).
            return_modeled_spectra: If True, return detailed results.
            
        Returns:
            Relative RMSE value, or detailed results dictionary.
        """
        self.validate_inputs(params, observed_rrs, inversion_parameters)
        
        eps = epsilon if epsilon is not None else self.epsilon
        
        # Run forward model
        results = self.run_forward_model(params, inversion_parameters)
        
        # Calculate relative error
        relative_diff = (results.rrs - observed_rrs) / (observed_rrs + eps)
        error = np.sqrt(np.mean(relative_diff ** 2))
        
        if return_modeled_spectra:
            return self.create_detailed_result(
                error=error,
                modeled_rrs=results.rrs,
                forward_results=results,
                epsilon_used=eps
            )
        
        return error
