"""Result handling classes for pixel processing results."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import numpy as np
from numpy.typing import NDArray

from ..parameters import InversionParameters


class ResultHandler(ABC):
    """Abstract base class for result handling strategies."""
    
    @abstractmethod
    def format_result(self, raw_result: Dict[str, Any], **metadata) -> Dict[str, Any]:
        """Format a successful processing result.
        
        Args:
            raw_result: Raw result from processing strategy.
            **metadata: Additional metadata to include.
            
        Returns:
            Formatted result dictionary.
        """
        pass
    
    @abstractmethod
    def format_invalid_pixel_result(self, pixel_spectra: NDArray[np.float64]) -> Dict[str, Any]:
        """Format result for invalid pixels.
        
        Args:
            pixel_spectra: The invalid pixel spectrum.
            
        Returns:
            Result dictionary with appropriate invalid pixel values.
        """
        pass
    
    @abstractmethod
    def format_failed_result(self, pixel_spectra: NDArray[np.float64], 
                           error: Exception, **metadata) -> Dict[str, Any]:
        """Format result for processing failures.
        
        Args:
            pixel_spectra: The pixel spectrum that failed processing.
            error: The exception that occurred.
            **metadata: Additional metadata about the failure.
            
        Returns:
            Result dictionary with appropriate failure values.
        """
        pass


class StandardResultHandler(ResultHandler):
    """Standard result handler for Sambuca inversion results."""
    
    def __init__(self, inversion_parameters: InversionParameters):
        """Initialize result handler.
        
        Args:
            inversion_parameters: Parameters containing parameter names and metadata.
        """
        self.inversion_parameters = inversion_parameters
        self.param_names = inversion_parameters.get_inversion_parameter_names()
    
    def format_result(self, raw_result: Dict[str, Any], **metadata) -> Dict[str, Any]:
        """Format a successful processing result.
        
        Args:
            raw_result: Raw result from processing strategy.
            **metadata: Additional metadata to include.
            
        Returns:
            Formatted result dictionary.
        """
        result = {
            'parameters': raw_result.get('parameters', {}),
            'error': raw_result.get('error', float('nan')),
            'modeled_spectra': raw_result.get('modeled_spectra', np.array([])),
            'convergence': raw_result.get('convergence', False),
            'status': metadata.get('status', 'success'),
        }
        
        # Add strategy information
        if 'strategy_name' in metadata:
            result['strategy_used'] = metadata['strategy_name']
        
        # Add any additional metadata
        for key, value in metadata.items():
            if key not in result and not key.startswith('_'):
                result[key] = value
        
        # Copy any additional fields from raw result
        for key, value in raw_result.items():
            if key not in result:
                result[key] = value
        
        return result
    
    def format_invalid_pixel_result(self, pixel_spectra: NDArray[np.float64]) -> Dict[str, Any]:
        """Format result for invalid pixels.
        
        Args:
            pixel_spectra: The invalid pixel spectrum.
            
        Returns:
            Result dictionary with NaN values for invalid pixel.
        """
        return {
            'parameters': {p: float('nan') for p in self.param_names},
            'error': float('nan'),
            'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
            'convergence': False,
            'status': 'invalid_pixel',
        }
    
    def format_failed_result(self, pixel_spectra: NDArray[np.float64], 
                           error: Exception, **metadata) -> Dict[str, Any]:
        """Format result for processing failures.
        
        Args:
            pixel_spectra: The pixel spectrum that failed processing.
            error: The exception that occurred.
            **metadata: Additional metadata about the failure.
            
        Returns:
            Result dictionary with NaN values and error information.
        """
        result = {
            'parameters': {p: float('nan') for p in self.param_names},
            'error': float('nan'),
            'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
            'convergence': False,
            'status': metadata.get('status', 'processing_failed'),
            'error_message': str(error),
        }
        
        # Add any additional metadata
        for key, value in metadata.items():
            if key not in result and not key.startswith('_'):
                result[key] = value
        
        return result


class DetailedResultHandler(StandardResultHandler):
    """Result handler that includes additional diagnostic information."""
    
    def __init__(self, inversion_parameters: InversionParameters, 
                 include_diagnostics: bool = True):
        """Initialize detailed result handler.
        
        Args:
            inversion_parameters: Parameters containing parameter names and metadata.
            include_diagnostics: Whether to include detailed diagnostic information.
        """
        super().__init__(inversion_parameters)
        self.include_diagnostics = include_diagnostics
    
    def format_result(self, raw_result: Dict[str, Any], **metadata) -> Dict[str, Any]:
        """Format result with additional diagnostic information.
        
        Args:
            raw_result: Raw result from processing strategy.
            **metadata: Additional metadata to include.
            
        Returns:
            Formatted result dictionary with diagnostics.
        """
        result = super().format_result(raw_result, **metadata)
        
        if self.include_diagnostics:
            # Add parameter bounds information
            bounds = self.inversion_parameters.get_parameter_bounds()
            result['parameter_bounds'] = {
                name: bounds[i] for i, name in enumerate(self.param_names)
            }
            
            # Add parameter validation info
            if 'parameters' in result:
                result['parameters_in_bounds'] = self._check_parameters_in_bounds(
                    result['parameters'], bounds
                )
            
            # Add wavelength information
            result['wavelengths'] = self.inversion_parameters.wavelengths
            
            # Add processing timestamp
            import time
            result['processing_timestamp'] = time.time()
        
        return result
    
    def _check_parameters_in_bounds(self, parameters: Dict[str, float], 
                                  bounds: list) -> Dict[str, bool]:
        """Check if parameters are within their bounds.
        
        Args:
            parameters: Dictionary of parameter values.
            bounds: List of (min, max) tuples for each parameter.
            
        Returns:
            Dictionary indicating whether each parameter is in bounds.
        """
        in_bounds = {}
        for i, param_name in enumerate(self.param_names):
            if param_name in parameters and i < len(bounds):
                value = parameters[param_name]
                min_val, max_val = bounds[i]
                in_bounds[param_name] = min_val <= value <= max_val
            else:
                in_bounds[param_name] = False
        
        return in_bounds


class CompactResultHandler(ResultHandler):
    """Compact result handler that only returns essential information."""
    
    def __init__(self, inversion_parameters: InversionParameters, 
                 include_modeled_spectra: bool = False):
        """Initialize compact result handler.
        
        Args:
            inversion_parameters: Parameters containing parameter names.
            include_modeled_spectra: Whether to include modeled spectra in results.
        """
        self.inversion_parameters = inversion_parameters
        self.param_names = inversion_parameters.get_inversion_parameter_names()
        self.include_modeled_spectra = include_modeled_spectra
    
    def format_result(self, raw_result: Dict[str, Any], **metadata) -> Dict[str, Any]:
        """Format result with only essential information.
        
        Args:
            raw_result: Raw result from processing strategy.
            **metadata: Additional metadata to include.
            
        Returns:
            Compact result dictionary.
        """
        result = {
            'parameters': raw_result.get('parameters', {}),
            'error': raw_result.get('error', float('nan')),
            'convergence': raw_result.get('convergence', False),
        }
        
        if self.include_modeled_spectra:
            result['modeled_spectra'] = raw_result.get('modeled_spectra', np.array([]))
        
        return result
    
    def format_invalid_pixel_result(self, pixel_spectra: NDArray[np.float64]) -> Dict[str, Any]:
        """Format compact result for invalid pixels.
        
        Args:
            pixel_spectra: The invalid pixel spectrum.
            
        Returns:
            Compact result dictionary for invalid pixel.
        """
        result = {
            'parameters': {p: float('nan') for p in self.param_names},
            'error': float('nan'),
            'convergence': False,
        }
        
        if self.include_modeled_spectra:
            result['modeled_spectra'] = np.full_like(pixel_spectra, float('nan'))
        
        return result
    
    def format_failed_result(self, pixel_spectra: NDArray[np.float64], 
                           error: Exception, **metadata) -> Dict[str, Any]:
        """Format compact result for processing failures.
        
        Args:
            pixel_spectra: The pixel spectrum that failed processing.
            error: The exception that occurred.
            **metadata: Additional metadata about the failure.
            
        Returns:
            Compact result dictionary for failed processing.
        """
        result = {
            'parameters': {p: float('nan') for p in self.param_names},
            'error': float('nan'),
            'convergence': False,
        }
        
        if self.include_modeled_spectra:
            result['modeled_spectra'] = np.full_like(pixel_spectra, float('nan'))
        
        return result
