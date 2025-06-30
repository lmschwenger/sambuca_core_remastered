"""Processing strategy classes for different pixel processing approaches."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import numpy as np
from numpy.typing import NDArray

from ..parameters import InversionParameters
from ..lut import LookUpTable


class ProcessingError(Exception):
    """Exception raised during pixel processing."""
    pass


class ProcessingStrategy(ABC):
    """Abstract base class for pixel processing strategies."""
    
    @abstractmethod
    def process(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process a single pixel spectrum.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional processing arguments.
            
        Returns:
            Dictionary with processing results.
            
        Raises:
            ProcessingError: If processing fails.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the processing strategy."""
        pass
    
    @property
    def priority(self) -> int:
        """Priority of this strategy (lower numbers = higher priority)."""
        return 100  # Default priority


class LUTProcessingStrategy(ProcessingStrategy):
    """Look-up table processing strategy."""
    
    def __init__(self, lut: LookUpTable, refinement: bool = True):
        """Initialize LUT processing strategy.
        
        Args:
            lut: Look-up table for inversion.
            refinement: Whether to refine LUT results with optimization.
        """
        self.lut = lut
        self.refinement = refinement
    
    def process(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process pixel using Look-Up Table.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional arguments passed to LUT.invert().
            
        Returns:
            Dictionary with LUT processing results.
            
        Raises:
            ProcessingError: If LUT processing fails.
        """
        try:
            # Setup NEDR if available in kwargs
            lut_kwargs = kwargs.copy()
            if 'inversion_parameters' in kwargs:
                inv_params = kwargs['inversion_parameters']
                if hasattr(inv_params, 'nedr') and inv_params.nedr is not None:
                    lut_kwargs['nedr'] = inv_params.nedr
            
            result = self.lut.invert(pixel_spectra, refine=self.refinement, **lut_kwargs)
            return result
            
        except Exception as e:
            raise ProcessingError(f"LUT processing failed: {e}")
    
    @property
    def name(self) -> str:
        return f"lut_processing_{'refined' if self.refinement else 'direct'}"
    
    @property
    def priority(self) -> int:
        # LUT processing is typically faster, so higher priority
        return 10 if self.refinement else 5


class OptimizationProcessingStrategy(ProcessingStrategy):
    """Standard optimization processing strategy."""
    
    def __init__(self, inversion_parameters: InversionParameters):
        """Initialize optimization strategy.
        
        Args:
            inversion_parameters: Parameters for the inversion process.
        """
        self.inversion_parameters = inversion_parameters
    
    def process(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process pixel using standard optimization.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional arguments passed to invert_spectrum().
            
        Returns:
            Dictionary with optimization results.
            
        Raises:
            ProcessingError: If optimization fails.
        """
        try:
            # Import here to avoid circular imports
            from ..optimization import invert_spectrum
            
            opt_kwargs = kwargs.copy()
            
            # Setup NEDR objective function if needed
            if hasattr(self.inversion_parameters, 'nedr') and self.inversion_parameters.nedr is not None:
                from ..objective_functions import SpectralRMSEWithNEDR
                opt_kwargs['objective_function'] = SpectralRMSEWithNEDR()
            
            result = invert_spectrum(pixel_spectra, self.inversion_parameters, **opt_kwargs)
            
            return {
                'parameters': result.parameters,
                'error': result.objective_value,
                'modeled_spectra': result.modeled_spectra,
                'convergence': result.convergence_status,
            }
            
        except Exception as e:
            raise ProcessingError(f"Optimization failed: {e}")
    
    @property
    def name(self) -> str:
        return "optimization"
    
    @property
    def priority(self) -> int:
        # Standard optimization has medium priority
        return 50


class MultiStartProcessingStrategy(ProcessingStrategy):
    """Multi-start optimization processing strategy."""
    
    def __init__(self, inversion_parameters: InversionParameters, n_starts: int = 5):
        """Initialize multi-start optimization strategy.
        
        Args:
            inversion_parameters: Parameters for the inversion process.
            n_starts: Number of starting points for optimization.
        """
        self.inversion_parameters = inversion_parameters
        self.n_starts = n_starts
    
    def process(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process pixel using multi-start optimization.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional arguments passed to multi_start_inversion().
            
        Returns:
            Dictionary with multi-start optimization results.
            
        Raises:
            ProcessingError: If multi-start optimization fails.
        """
        try:
            # Import here to avoid circular imports
            from ..optimization import multi_start_inversion
            
            opt_kwargs = kwargs.copy()
            
            # Setup NEDR objective function if needed
            if hasattr(self.inversion_parameters, 'nedr') and self.inversion_parameters.nedr is not None:
                from ..objective_functions import SpectralRMSEWithNEDR
                opt_kwargs['objective_function'] = SpectralRMSEWithNEDR()
            
            result = multi_start_inversion(
                pixel_spectra, 
                self.inversion_parameters, 
                n_starts=self.n_starts, 
                **opt_kwargs
            )
            
            return {
                'parameters': result.parameters,
                'error': result.objective_value,
                'modeled_spectra': result.modeled_spectra,
                'convergence': result.convergence_status,
            }
            
        except Exception as e:
            raise ProcessingError(f"Multi-start optimization failed: {e}")
    
    @property
    def name(self) -> str:
        return f"multi_start_{self.n_starts}"
    
    @property
    def priority(self) -> int:
        # Multi-start is more robust but slower, so lower priority
        return 75


class HybridProcessingStrategy(ProcessingStrategy):
    """Hybrid strategy that combines LUT with multi-start optimization."""
    
    def __init__(self, lut: LookUpTable, inversion_parameters: InversionParameters, 
                 n_starts: int = 5):
        """Initialize hybrid processing strategy.
        
        Args:
            lut: Look-up table for initial estimation.
            inversion_parameters: Parameters for the inversion process.
            n_starts: Number of starting points for multi-start optimization.
        """
        self.lut = lut
        self.inversion_parameters = inversion_parameters
        self.n_starts = n_starts
    
    def process(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process pixel using hybrid LUT + multi-start approach.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional arguments.
            
        Returns:
            Dictionary with hybrid processing results.
            
        Raises:
            ProcessingError: If hybrid processing fails.
        """
        try:
            # Import here to avoid circular imports
            from ..optimization import multi_start_inversion
            
            # First, get LUT result (without refinement)
            lut_kwargs = kwargs.copy()
            if hasattr(self.inversion_parameters, 'nedr') and self.inversion_parameters.nedr is not None:
                lut_kwargs['nedr'] = self.inversion_parameters.nedr
            
            lut_result = self.lut.invert(pixel_spectra, refine=False, **lut_kwargs)
            
            # Then, use multi-start optimization with LUT result as one starting point
            opt_kwargs = kwargs.copy()
            
            # Setup NEDR objective function if needed
            if hasattr(self.inversion_parameters, 'nedr') and self.inversion_parameters.nedr is not None:
                from ..objective_functions import SpectralRMSEWithNEDR
                opt_kwargs['objective_function'] = SpectralRMSEWithNEDR()
            
            # Use LUT result as initial guess (if available)
            if 'parameters' in lut_result and isinstance(lut_result['parameters'], dict):
                param_names = self.inversion_parameters.get_inversion_parameter_names()
                initial_guess = [lut_result['parameters'].get(name, 1.0) for name in param_names]
                opt_kwargs['initial_guess'] = initial_guess
            
            result = multi_start_inversion(
                pixel_spectra, 
                self.inversion_parameters, 
                n_starts=self.n_starts, 
                **opt_kwargs
            )
            
            return {
                'parameters': result.parameters,
                'error': result.objective_value,
                'modeled_spectra': result.modeled_spectra,
                'convergence': result.convergence_status,
                'lut_result': lut_result,  # Keep LUT result for comparison
            }
            
        except Exception as e:
            raise ProcessingError(f"Hybrid processing failed: {e}")
    
    @property
    def name(self) -> str:
        return f"hybrid_lut_multistart_{self.n_starts}"
    
    @property
    def priority(self) -> int:
        # Hybrid approach is comprehensive but slower
        return 80


class FallbackProcessingStrategy(ProcessingStrategy):
    """Fallback strategy that tries multiple approaches in sequence."""
    
    def __init__(self, strategies: list[ProcessingStrategy]):
        """Initialize fallback strategy.
        
        Args:
            strategies: List of strategies to try in order.
        """
        self.strategies = strategies
        if not strategies:
            raise ValueError("At least one strategy must be provided")
    
    def process(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process pixel using fallback strategy sequence.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional arguments.
            
        Returns:
            Dictionary with results from first successful strategy.
            
        Raises:
            ProcessingError: If all strategies fail.
        """
        errors = []
        
        for strategy in self.strategies:
            try:
                result = strategy.process(pixel_spectra, **kwargs)
                # Add information about which strategy succeeded
                result['successful_strategy'] = strategy.name
                return result
            except ProcessingError as e:
                errors.append(f"{strategy.name}: {e}")
                continue
        
        # All strategies failed
        error_msg = "All fallback strategies failed: " + "; ".join(errors)
        raise ProcessingError(error_msg)
    
    @property
    def name(self) -> str:
        strategy_names = [s.name for s in self.strategies]
        return f"fallback_{'_'.join(strategy_names[:3])}"  # Limit name length
    
    @property
    def priority(self) -> int:
        # Fallback strategy has lowest priority since it tries multiple approaches
        return 200
