"""Spectral Angle Mapper objective function.

Measures spectral shape similarity regardless of intensity.
"""

from typing import Dict, Any, List, Union
import numpy as np
from numpy.typing import NDArray

from .base import ForwardModelObjectiveFunction
from .. import InversionParameters


class SpectralAngleMapper(ForwardModelObjectiveFunction):
    """Spectral Angle Mapper - measures spectral shape similarity."""
    
    @property
    def name(self) -> str:
        return "spectral_angle_mapper"
    
    @property
    def description(self) -> str:
        return "Spectral angle between observed and modeled spectra (shape similarity)"
    
    def __call__(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        return_modeled_spectra: bool = False
    ) -> Union[float, Dict[str, Any]]:
        """Calculate spectral angle between observed and modeled spectra.
        
        Args:
            params: Optimization parameters.
            observed_rrs: Observed remote sensing reflectance.
            inversion_parameters: Parameters for the inversion process.
            return_modeled_spectra: If True, return detailed results.
            
        Returns:
            Spectral angle in radians, or detailed results dictionary.
        """
        self.validate_inputs(params, observed_rrs, inversion_parameters)
        
        # Run forward model
        results = self.run_forward_model(params, inversion_parameters)
        
        # Calculate spectral angle
        dot_product = np.sum(results.rrs * observed_rrs)
        norm_product = np.sqrt(np.sum(results.rrs ** 2) * np.sum(observed_rrs ** 2))
        
        # Avoid division by zero
        if norm_product < 1e-10:
            angle = np.pi / 2  # Maximum angle (90 degrees)
        else:
            angle = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))
        
        if return_modeled_spectra:
            return self.create_detailed_result(
                error=angle,
                modeled_rrs=results.rrs,
                forward_results=results,
                angle_degrees=np.degrees(angle),
                cosine_similarity=np.cos(angle) if norm_product >= 1e-10 else 0.0
            )
        
        return angle
