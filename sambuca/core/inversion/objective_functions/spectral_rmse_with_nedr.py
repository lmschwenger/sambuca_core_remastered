"""Spectral RMSE with NEDR weighting objective function.

NEDR-weighted RMSE for sensor-specific noise modeling.
"""

from typing import Dict, Any, List, Union, Optional
import numpy as np
from numpy.typing import NDArray

from .base import ForwardModelObjectiveFunction
from .. import InversionParameters


class SpectralRMSEWithNEDR(ForwardModelObjectiveFunction):
    """NEDR-weighted RMSE for sensor-specific noise modeling."""
    
    def __init__(self, nedr: Optional[NDArray[np.float64]] = None):
        """Initialize NEDR-weighted RMSE.
        
        Args:
            nedr: Noise Equivalent Difference in Reflectance for each band.
        """
        self.nedr = nedr
    
    @property
    def name(self) -> str:
        return "spectral_rmse_with_nedr"
    
    @property
    def description(self) -> str:
        return "NEDR-weighted RMSE accounting for sensor noise characteristics"
    
    def __call__(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        nedr: Optional[NDArray[np.float64]] = None,
        return_modeled_spectra: bool = False
    ) -> Union[float, Dict[str, Any]]:
        """Calculate NEDR-weighted RMSE.
        
        Args:
            params: Optimization parameters.
            observed_rrs: Observed remote sensing reflectance.
            inversion_parameters: Parameters for the inversion process.
            nedr: NEDR values for each band (overrides instance values).
            return_modeled_spectra: If True, return detailed results.
            
        Returns:
            NEDR-weighted RMSE, or detailed results dictionary.
        """
        self.validate_inputs(params, observed_rrs, inversion_parameters)
        
        nedr_values = nedr if nedr is not None else self.nedr
        
        # Try to get NEDR from inversion parameters if not provided
        if nedr_values is None and hasattr(inversion_parameters, 'nedr') and inversion_parameters.nedr is not None:
            nedr_values = inversion_parameters.nedr
        
        # Run forward model
        results = self.run_forward_model(params, inversion_parameters)
        
        # Calculate NEDR-weighted error
        if nedr_values is not None:
            # Weight by inverse variance (1/sigma^2)
            weights = 1.0 / (nedr_values ** 2)
            weighted_squared_diff = weights * ((results.rrs - observed_rrs) ** 2)
            error = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
        else:
            # Standard RMSE if no NEDR provided
            error = np.sqrt(np.mean((results.rrs - observed_rrs) ** 2))
        
        if return_modeled_spectra:
            return self.create_detailed_result(
                error=error,
                modeled_rrs=results.rrs,
                forward_results=results,
                nedr_used=nedr_values is not None,
                nedr_values=nedr_values
            )
        
        return error
