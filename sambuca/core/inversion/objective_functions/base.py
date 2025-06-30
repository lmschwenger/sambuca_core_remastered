"""Base classes for objective functions.

This module provides the foundation for all objective functions used in SAMBUCA inversions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
import numpy as np
from numpy.typing import NDArray

from .. import InversionParameters
from ...forward_model import forward_model


class ObjectiveFunction(ABC):
    """Abstract base class for all objective functions."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the objective function."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this objective function measures."""
        pass
    
    @abstractmethod
    def __call__(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        **kwargs
    ) -> Union[float, Dict[str, Any]]:
        """Calculate the objective function value.
        
        Args:
            params: Optimization parameters being fitted.
            observed_rrs: Observed remote sensing reflectance.
            inversion_parameters: Parameters controlling the inversion.
            **kwargs: Additional function-specific parameters.
            
        Returns:
            Error value, or dict with error and additional info if requested.
        """
        pass
    
    def validate_inputs(
        self,
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters'
    ) -> None:
        """Validate inputs to the objective function.
        
        Raises:
            ValueError: If inputs are invalid.
        """
        if len(params) != len(inversion_parameters.get_parameter_bounds()):
            raise ValueError(
                f"params length ({len(params)}) must match number of parameters "
                f"being inverted ({len(inversion_parameters.get_parameter_bounds())})"
            )
        
        if len(observed_rrs) != len(inversion_parameters.wavelengths):
            raise ValueError(
                f"observed_rrs length ({len(observed_rrs)}) must match "
                f"wavelengths length ({len(inversion_parameters.wavelengths)})"
            )
        
        if np.any(np.isnan(observed_rrs)) or np.any(observed_rrs < 0):
            raise ValueError("observed_rrs contains invalid values (NaN or negative)")


class ForwardModelObjectiveFunction(ObjectiveFunction):
    """Base class for objective functions that use the forward model."""
    
    def run_forward_model(
        self,
        params: List[float],
        inversion_parameters: 'InversionParameters'
    ):
        """Run the forward model with given parameters."""
        forward_model_params = inversion_parameters.get_forward_model_params(params)
        return forward_model(**forward_model_params)
    
    def create_detailed_result(
        self,
        error: float,
        modeled_rrs: NDArray[np.float64],
        forward_results,
        **additional_info
    ) -> Dict[str, Any]:
        """Create detailed result dictionary."""
        result = {
            'error': error,
            'modeled_spectra': modeled_rrs,
            'forward_model_results': forward_results,
            'objective_function': self.name
        }
        result.update(additional_info)
        return result
