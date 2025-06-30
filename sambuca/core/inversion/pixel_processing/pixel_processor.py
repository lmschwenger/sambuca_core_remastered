"""Main pixel processor class for orchestrating pixel-level processing."""

from typing import Dict, Any, Optional, List

import numpy as np
from numpy.typing import NDArray

from .validators import PixelValidator, StandardPixelValidator
from .strategies import ProcessingStrategy, ProcessingError, LUTProcessingStrategy, OptimizationProcessingStrategy, MultiStartProcessingStrategy, HybridProcessingStrategy
from .result_handlers import ResultHandler, StandardResultHandler
from ..parameters import InversionParameters
from ..lut import LookUpTable


class PixelProcessor:
    """Main pixel processor that orchestrates validation, processing, and result handling."""
    
    def __init__(self, validator: PixelValidator, strategies: List[ProcessingStrategy], 
                 result_handler: ResultHandler, fallback_on_failure: bool = True):
        """Initialize pixel processor.
        
        Args:
            validator: Pixel validation strategy.
            strategies: List of processing strategies to try.
            result_handler: Result formatting handler.
            fallback_on_failure: Whether to try next strategy if current one fails.
        """
        self.validator = validator
        self.strategies = strategies
        self.result_handler = result_handler
        self.fallback_on_failure = fallback_on_failure
        
        if not strategies:
            raise ValueError("At least one processing strategy must be provided")
        
        # Sort strategies by priority (lower numbers = higher priority)
        self.strategies.sort(key=lambda x: x.priority)
    
    def process_pixel(self, pixel_spectra: NDArray[np.float64], **kwargs) -> Dict[str, Any]:
        """Process a single pixel spectrum.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            **kwargs: Additional arguments passed to processing strategies.
            
        Returns:
            Dictionary with inverted parameters and metadata.
        """
        # Validate pixel
        if not self.validator.is_valid(pixel_spectra):
            return self.result_handler.format_invalid_pixel_result(pixel_spectra)
        
        # Try strategies in priority order
        last_error = None
        strategy_attempts = []
        
        for strategy in self.strategies:
            try:
                raw_result = strategy.process(pixel_spectra, **kwargs)
                
                # Format successful result
                return self.result_handler.format_result(
                    raw_result,
                    strategy_name=strategy.name,
                    status=f"{strategy.name}_success",
                    validator_used=self.validator.name,
                    strategy_attempts=len(strategy_attempts) + 1
                )
                
            except ProcessingError as e:
                last_error = e
                strategy_attempts.append(strategy.name)
                
                if not self.fallback_on_failure:
                    break
                continue
        
        # All strategies failed
        return self.result_handler.format_failed_result(
            pixel_spectra,
            error=last_error or ProcessingError("Unknown processing error"),
            strategy_attempts=strategy_attempts,
            validator_used=self.validator.name
        )
    
    def add_strategy(self, strategy: ProcessingStrategy) -> 'PixelProcessor':
        """Add a processing strategy to the processor.
        
        Args:
            strategy: Processing strategy to add.
            
        Returns:
            Self for method chaining.
        """
        self.strategies.append(strategy)
        # Re-sort by priority
        self.strategies.sort(key=lambda x: x.priority)
        return self
    
    def remove_strategy(self, strategy_name: str) -> 'PixelProcessor':
        """Remove a processing strategy by name.
        
        Args:
            strategy_name: Name of strategy to remove.
            
        Returns:
            Self for method chaining.
        """
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
        return self
    
    def get_strategy_names(self) -> List[str]:
        """Get names of all configured strategies.
        
        Returns:
            List of strategy names in priority order.
        """
        return [s.name for s in self.strategies]
    
    @classmethod
    def create_standard_processor(
        cls,
        inversion_parameters: InversionParameters,
        lut: Optional[LookUpTable] = None,
        refinement: bool = True,
        use_multi_start: bool = False,
        n_starts: int = 5
    ) -> 'PixelProcessor':
        """Create a standard pixel processor configuration.
        
        Args:
            inversion_parameters: Parameters for the inversion process.
            lut: Optional look-up table for faster processing.
            refinement: Whether to refine LUT results with optimization.
            use_multi_start: Whether to use multi-start optimization.
            n_starts: Number of starting points for multi-start optimization.
            
        Returns:
            Configured PixelProcessor instance.
        """
        validator = StandardPixelValidator()
        strategies = []
        
        # Add LUT strategy if available
        if lut is not None:
            strategies.append(LUTProcessingStrategy(lut, refinement=refinement))
        
        # Add optimization strategies
        if use_multi_start:
            strategies.append(MultiStartProcessingStrategy(inversion_parameters, n_starts))
        else:
            strategies.append(OptimizationProcessingStrategy(inversion_parameters))
        
        result_handler = StandardResultHandler(inversion_parameters)
        
        return cls(validator, strategies, result_handler, fallback_on_failure=True)
    
    @classmethod
    def create_fast_processor(
        cls,
        inversion_parameters: InversionParameters,
        lut: LookUpTable
    ) -> 'PixelProcessor':
        """Create a fast LUT-only processor.
        
        Args:
            inversion_parameters: Parameters for the inversion process.
            lut: Look-up table for processing.
            
        Returns:
            Configured PixelProcessor for fast processing.
        """
        validator = StandardPixelValidator()
        strategies = [LUTProcessingStrategy(lut, refinement=False)]
        result_handler = StandardResultHandler(inversion_parameters)
        
        return cls(validator, strategies, result_handler, fallback_on_failure=False)
    
    @classmethod
    def create_robust_processor(
        cls,
        inversion_parameters: InversionParameters,
        lut: Optional[LookUpTable] = None,
        n_starts: int = 5
    ) -> 'PixelProcessor':
        """Create a robust processor with multiple fallback strategies.
        
        Args:
            inversion_parameters: Parameters for the inversion process.
            lut: Optional look-up table.
            n_starts: Number of starting points for multi-start optimization.
            
        Returns:
            Configured PixelProcessor for robust processing.
        """
        validator = StandardPixelValidator()
        strategies = []
        
        # Add all available strategies for maximum robustness
        if lut is not None:
            strategies.extend([
                LUTProcessingStrategy(lut, refinement=True),
                HybridProcessingStrategy(lut, inversion_parameters, n_starts)
            ])
        
        strategies.extend([
            MultiStartProcessingStrategy(inversion_parameters, n_starts),
            OptimizationProcessingStrategy(inversion_parameters)
        ])
        
        result_handler = StandardResultHandler(inversion_parameters)
        
        return cls(validator, strategies, result_handler, fallback_on_failure=True)
    
    @classmethod
    def create_accuracy_processor(
        cls,
        inversion_parameters: InversionParameters,
        lut: Optional[LookUpTable] = None,
        n_starts: int = 10
    ) -> 'PixelProcessor':
        """Create a processor optimized for accuracy.
        
        Args:
            inversion_parameters: Parameters for the inversion process.
            lut: Optional look-up table.
            n_starts: Number of starting points for multi-start optimization.
            
        Returns:
            Configured PixelProcessor optimized for accuracy.
        """
        validator = StandardPixelValidator()
        strategies = []
        
        # Prioritize multi-start optimization for best accuracy
        strategies.append(MultiStartProcessingStrategy(inversion_parameters, n_starts))
        
        # Add hybrid approach if LUT is available
        if lut is not None:
            strategies.append(HybridProcessingStrategy(lut, inversion_parameters, n_starts))
        
        result_handler = StandardResultHandler(inversion_parameters)
        
        return cls(validator, strategies, result_handler, fallback_on_failure=True)
    
    @classmethod
    def create_custom_processor(
        cls,
        validator: PixelValidator,
        strategies: List[ProcessingStrategy],
        result_handler: ResultHandler,
        fallback_on_failure: bool = True
    ) -> 'PixelProcessor':
        """Create a custom processor with user-defined components.
        
        Args:
            validator: Custom pixel validation strategy.
            strategies: Custom list of processing strategies.
            result_handler: Custom result formatting handler.
            fallback_on_failure: Whether to try next strategy on failure.
            
        Returns:
            Configured PixelProcessor with custom components.
        """
        return cls(validator, strategies, result_handler, fallback_on_failure)
