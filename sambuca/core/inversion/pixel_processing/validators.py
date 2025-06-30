"""Pixel validation classes for the Sambuca inversion process."""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from numpy.typing import NDArray


class PixelValidator(ABC):
    """Abstract base class for pixel validation strategies."""
    
    @abstractmethod
    def is_valid(self, pixel_spectra: NDArray[np.float64]) -> bool:
        """Check if a pixel spectrum contains valid data.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            
        Returns:
            True if pixel is valid, False otherwise.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the validation strategy."""
        pass


class StandardPixelValidator(PixelValidator):
    """Standard validation for NaN and negative values."""
    
    def is_valid(self, pixel_spectra: NDArray[np.float64]) -> bool:
        """Check if pixel contains no NaN or negative values.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            
        Returns:
            True if pixel contains no NaN or negative values.
        """
        return not (np.any(np.isnan(pixel_spectra)) or np.any(pixel_spectra < 0))
    
    @property
    def name(self) -> str:
        return "standard_validation"


class ThresholdPixelValidator(PixelValidator):
    """Validation with custom thresholds for pixel values."""
    
    def __init__(self, min_value: float = 0.0, max_value: float = 1.0, 
                 allow_nan: bool = False):
        """Initialize threshold validator.
        
        Args:
            min_value: Minimum allowed pixel value.
            max_value: Maximum allowed pixel value.
            allow_nan: Whether to allow NaN values.
        """
        self.min_value = min_value
        self.max_value = max_value
        self.allow_nan = allow_nan
    
    def is_valid(self, pixel_spectra: NDArray[np.float64]) -> bool:
        """Check if pixel values are within specified thresholds.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            
        Returns:
            True if all pixel values are within thresholds.
        """
        # Check for NaN values
        has_nan = np.any(np.isnan(pixel_spectra))
        if has_nan and not self.allow_nan:
            return False
        
        # Check thresholds on non-NaN values
        if has_nan:
            valid_values = pixel_spectra[~np.isnan(pixel_spectra)]
        else:
            valid_values = pixel_spectra
        
        if len(valid_values) == 0:
            return self.allow_nan  # All NaN case
        
        return np.all((valid_values >= self.min_value) & (valid_values <= self.max_value))
    
    @property
    def name(self) -> str:
        return f"threshold_validation_{self.min_value}_{self.max_value}"


class CustomPixelValidator(PixelValidator):
    """Custom validation using a user-provided function."""
    
    def __init__(self, validation_func: callable, validator_name: str = "custom"):
        """Initialize custom validator.
        
        Args:
            validation_func: Function that takes pixel_spectra and returns bool.
            validator_name: Name for this validator.
        """
        self.validation_func = validation_func
        self.validator_name = validator_name
    
    def is_valid(self, pixel_spectra: NDArray[np.float64]) -> bool:
        """Check if pixel is valid using custom function.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            
        Returns:
            True if custom validation function returns True.
        """
        try:
            return bool(self.validation_func(pixel_spectra))
        except Exception:
            return False
    
    @property
    def name(self) -> str:
        return self.validator_name


class CompositePixelValidator(PixelValidator):
    """Composite validator that combines multiple validators."""
    
    def __init__(self, validators: list[PixelValidator], require_all: bool = True):
        """Initialize composite validator.
        
        Args:
            validators: List of validators to combine.
            require_all: If True, all validators must pass. If False, any validator can pass.
        """
        self.validators = validators
        self.require_all = require_all
        
        if not validators:
            raise ValueError("At least one validator must be provided")
    
    def is_valid(self, pixel_spectra: NDArray[np.float64]) -> bool:
        """Check if pixel is valid according to composite rules.
        
        Args:
            pixel_spectra: Observed remote sensing reflectance for one pixel.
            
        Returns:
            True if validation criteria are met.
        """
        results = [validator.is_valid(pixel_spectra) for validator in self.validators]
        
        if self.require_all:
            return all(results)
        else:
            return any(results)
    
    @property
    def name(self) -> str:
        validator_names = [v.name for v in self.validators]
        operator = "AND" if self.require_all else "OR"
        return f"composite_{operator}_" + "_".join(validator_names)
