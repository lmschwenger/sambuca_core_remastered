"""Pixel processing package for Sambuca inversion.

This package provides object-oriented pixel processing functionality for
hyperspectral image analysis using the Sambuca inversion process.
"""

# Public API - maintains backward compatibility
from .pixel_processor import PixelProcessor
from .image_processor import ImageProcessor
from .validators import StandardPixelValidator, ThresholdPixelValidator
from .strategies import LUTProcessingStrategy, OptimizationProcessingStrategy, MultiStartProcessingStrategy
from .result_handlers import StandardResultHandler

# Backward-compatible functions
def process_pixel(pixel_spectra, inversion_parameters, lut=None, refinement=True, 
                 use_multi_start=False, n_starts=5, **kwargs):
    """Process a single pixel spectrum - backward compatible function.
    
    Args:
        pixel_spectra: Observed remote sensing reflectance for one pixel.
        inversion_parameters: Parameters for the inversion process.
        lut: Optional look-up table for faster inversion.
        refinement: Whether to refine LUT results with optimization.
        use_multi_start: Whether to use multi-start inversion.
        n_starts: Number of starting points for multi-start inversion.
        **kwargs: Additional arguments.
        
    Returns:
        Dictionary with inverted parameters and metadata.
    """
    processor = PixelProcessor.create_standard_processor(
        inversion_parameters=inversion_parameters,
        lut=lut,
        refinement=refinement,
        use_multi_start=use_multi_start,
        n_starts=n_starts
    )
    return processor.process_pixel(pixel_spectra, **kwargs)


def process_image(image, inversion_parameters, mask=None, lut=None, n_processes=None,
                 progress_bar=True, chunk_size=500, use_threads=True, 
                 use_multi_start=False, n_starts=5, **kwargs):
    """Process an entire image - backward compatible function.
    
    Args:
        image: Hyperspectral image.
        inversion_parameters: Parameters for the inversion process.
        mask: Optional binary mask of valid pixels.
        lut: Optional look-up table.
        n_processes: Number of parallel processes/threads.
        progress_bar: Whether to show a progress bar.
        chunk_size: Number of pixels to process in each batch.
        use_threads: Whether to use threads vs processes.
        use_multi_start: Whether to use multi-start inversion.
        n_starts: Number of starting points.
        **kwargs: Additional arguments.
        
    Returns:
        Dictionary mapping parameter names to image arrays.
    """
    processor = ImageProcessor(
        n_processes=n_processes,
        progress_bar=progress_bar,
        chunk_size=chunk_size,
        use_threads=use_threads
    )
    
    pixel_processor = PixelProcessor.create_standard_processor(
        inversion_parameters=inversion_parameters,
        lut=lut,
        refinement=True,
        use_multi_start=use_multi_start,
        n_starts=n_starts
    )
    
    return processor.process_image(
        image=image,
        pixel_processor=pixel_processor,
        inversion_parameters=inversion_parameters,
        mask=mask,
        **kwargs
    )


__all__ = [
    'PixelProcessor',
    'ImageProcessor', 
    'StandardPixelValidator',
    'ThresholdPixelValidator',
    'LUTProcessingStrategy',
    'OptimizationProcessingStrategy',
    'MultiStartProcessingStrategy',
    'StandardResultHandler',
    'process_pixel',
    'process_image'
]
