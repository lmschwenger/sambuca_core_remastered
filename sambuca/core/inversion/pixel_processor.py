"""Backward compatibility module for pixel processing.

This module maintains the original API while delegating to the new class-based implementation.
All original functions are preserved for backward compatibility.
"""

# Import backward-compatible functions from the new package
from .pixel_processing import process_pixel, process_image

# Also expose the new classes for users who want to use them directly
from .pixel_processing import (
    PixelProcessor,
    ImageProcessor,
    StandardPixelValidator,
    ThresholdPixelValidator,
    LUTProcessingStrategy,
    OptimizationProcessingStrategy,
    MultiStartProcessingStrategy,
    StandardResultHandler
)

# Legacy function that was in the original module (if it existed)
def _process_pixel_batch(batch_data):
    """Legacy batch processing function for backward compatibility.
    
    This function maintains compatibility with existing code that might
    import this function directly.
    
    Args:
        batch_data: Tuple containing batch processing data.
        
    Returns:
        List of processing results.
    """
    # Delegate to the new ImageProcessor implementation
    pixel_indices, pixel_coords, image_data, inversion_parameters, lut, kwargs = batch_data
    
    # Create a pixel processor for this batch
    processor = PixelProcessor.create_standard_processor(
        inversion_parameters=inversion_parameters,
        lut=lut,
        **kwargs
    )
    
    results = []
    for i, idx in enumerate(pixel_indices):
        y, x = pixel_coords[i]
        pixel_spectra = image_data[y, x, :]
        result = processor.process_pixel(pixel_spectra, **kwargs)
        results.append((idx, result))
    
    return results


# Export all the original function names for backward compatibility
__all__ = [
    'process_pixel',
    'process_image',
    '_process_pixel_batch',
    'PixelProcessor',
    'ImageProcessor',
    'StandardPixelValidator',
    'ThresholdPixelValidator', 
    'LUTProcessingStrategy',
    'OptimizationProcessingStrategy',
    'MultiStartProcessingStrategy',
    'StandardResultHandler'
]
