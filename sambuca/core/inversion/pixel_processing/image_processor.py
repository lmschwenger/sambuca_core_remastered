"""Image processor class for batch processing of hyperspectral images."""

import concurrent.futures
import os
import time
from typing import Dict, Tuple, Optional, Any

import numpy as np
from numpy.typing import NDArray
from tqdm import tqdm

from .pixel_processor import PixelProcessor
from ..parameters import InversionParameters


class ImageProcessor:
    """Handles image-level processing with batching and parallelization."""
    
    def __init__(self, n_processes: Optional[int] = None, progress_bar: bool = True, 
                 chunk_size: int = 500, use_threads: bool = True):
        """Initialize image processor.
        
        Args:
            n_processes: Number of parallel processes/threads. None uses CPU count - 1.
            progress_bar: Whether to show progress bar during processing.
            chunk_size: Number of pixels to process in each batch.
            use_threads: Whether to use threads (True) vs processes (False).
        """
        self.n_processes = n_processes if n_processes is not None else max(1, os.cpu_count() - 1)
        self.progress_bar = progress_bar
        self.chunk_size = chunk_size
        self.use_threads = use_threads
    
    def process_image(
        self,
        image: NDArray[np.float64],
        pixel_processor: PixelProcessor,
        inversion_parameters: InversionParameters,
        mask: Optional[NDArray[np.bool_]] = None,
        **kwargs: Any
    ) -> Dict[str, NDArray]:
        """Process an entire hyperspectral image.
        
        Args:
            image: Hyperspectral image with shape (height, width, bands) or (bands, height, width).
            pixel_processor: Configured pixel processor for individual pixels.
            inversion_parameters: Parameters for the inversion process.
            mask: Optional binary mask of valid pixels to process (True = process).
            **kwargs: Additional arguments passed to pixel processor.
            
        Returns:
            Dictionary mapping parameter names to image arrays.
            
        Raises:
            ValueError: If image dimensions are invalid.
        """
        start_time = time.time()
        
        # Validate and normalize image dimensions
        height, width, bands, normalized_image = self._validate_image_dimensions(
            image, inversion_parameters
        )
        
        # Validate mask and prepare pixel coordinates
        validated_mask, y_indices, x_indices, n_pixels = self._validate_and_prepare_mask(
            mask, height, width
        )
        
        print(f"Processing {n_pixels} pixels from image of shape {normalized_image.shape}")
        
        # Initialize output arrays
        param_names = inversion_parameters.get_inversion_parameter_names()
        output = self._initialize_output_arrays(param_names, height, width, bands)
        
        # Prepare pixel batches for parallel processing
        batched_data = self._prepare_pixel_batches(
            y_indices, x_indices, normalized_image, pixel_processor, kwargs
        )
        
        # Process pixels in parallel
        all_results = self._process_batches_parallel(batched_data)
        
        # Fill output arrays with results
        self._fill_output_arrays(output, all_results, y_indices, x_indices)
        
        # Print processing statistics
        elapsed_time = time.time() - start_time
        self._print_processing_statistics(output, n_pixels, elapsed_time)
        
        return output
    
    def _validate_image_dimensions(
        self, 
        image: NDArray[np.float64], 
        inversion_parameters: InversionParameters
    ) -> Tuple[int, int, int, NDArray[np.float64]]:
        """Validate and normalize image dimensions.
        
        Args:
            image: Input hyperspectral image.
            inversion_parameters: Parameters containing wavelength information.
            
        Returns:
            Tuple of (height, width, bands, normalized_image)
            
        Raises:
            ValueError: If image dimensions are invalid.
        """
        # Check image dimensions
        if len(image.shape) != 3:
            raise ValueError(f"Image must have 3 dimensions, got {len(image.shape)}")

        # Handle different band dimension orders
        if image.shape[0] == len(inversion_parameters.wavelengths):
            # Bands first format (bands, height, width)
            bands, height, width = image.shape
            # Transpose to (height, width, bands) for easier pixel access
            image = np.transpose(image, (1, 2, 0))
        elif image.shape[2] == len(inversion_parameters.wavelengths):
            # Bands last format (height, width, bands)
            height, width, bands = image.shape
        else:
            raise ValueError(
                f"Image band dimension ({image.shape}) does not match wavelengths length "
                f"({len(inversion_parameters.wavelengths)})"
            )
        
        return height, width, bands, image
    
    def _validate_and_prepare_mask(
        self, 
        mask: Optional[NDArray[np.bool_]], 
        height: int, 
        width: int
    ) -> Tuple[NDArray[np.bool_], NDArray[np.intp], NDArray[np.intp], int]:
        """Validate mask and prepare pixel coordinates.
        
        Args:
            mask: Optional binary mask of valid pixels.
            height: Image height.
            width: Image width.
            
        Returns:
            Tuple of (validated_mask, y_indices, x_indices, n_pixels)
            
        Raises:
            ValueError: If mask dimensions don't match image or no pixels to process.
        """
        # Create mask if not provided
        if mask is None:
            mask = np.ones((height, width), dtype=bool)
        elif mask.shape != (height, width):
            raise ValueError(f"Mask shape {mask.shape} does not match image shape ({height}, {width})")

        # Get masked pixel coordinates
        y_indices, x_indices = np.where(mask)
        n_pixels = len(y_indices)

        if n_pixels == 0:
            raise ValueError("No pixels to process (empty mask)")
        
        return mask, y_indices, x_indices, n_pixels
    
    def _initialize_output_arrays(
        self, 
        param_names: list, 
        height: int, 
        width: int, 
        bands: int
    ) -> Dict[str, NDArray]:
        """Initialize output arrays for image processing results.
        
        Args:
            param_names: List of parameter names to invert.
            height: Image height.
            width: Image width.
            bands: Number of spectral bands.
            
        Returns:
            Dictionary of initialized output arrays.
        """
        output = {}
        for param in param_names:
            output[param] = np.full((height, width), np.nan)

        output['error'] = np.full((height, width), np.nan)
        output['convergence'] = np.full((height, width), False)
        output['status'] = np.full((height, width), '', dtype=object)
        output['modeled_spectra'] = np.full((height, width, bands), np.nan)
        
        return output
    
    def _prepare_pixel_batches(
        self,
        y_indices: NDArray[np.intp], 
        x_indices: NDArray[np.intp], 
        image: NDArray[np.float64],
        pixel_processor: PixelProcessor,
        kwargs: Dict[str, Any]
    ) -> list:
        """Prepare pixel batches for parallel processing.
        
        Args:
            y_indices: Y coordinates of pixels to process.
            x_indices: X coordinates of pixels to process.
            image: The image data.
            pixel_processor: Configured pixel processor.
            kwargs: Additional processing arguments.
            
        Returns:
            List of batch data tuples for parallel processing.
        """
        n_pixels = len(y_indices)
        pixel_coords = list(zip(y_indices, x_indices))

        # Create batches of pixels for processing
        batch_indices = [list(range(i, min(i + self.chunk_size, n_pixels)))
                         for i in range(0, n_pixels, self.chunk_size)]

        # Create lists of batched data to avoid pickling issues on Windows
        batched_data = []
        for indices in batch_indices:
            coords = [pixel_coords[i] for i in indices]
            batch = (indices, coords, image, pixel_processor, kwargs)
            batched_data.append(batch)
        
        return batched_data
    
    def _process_pixel_batch(self, batch_data):
        """Process a batch of pixels.

        Args:
            batch_data: Tuple containing (pixel_indices, pixel_coords, image_data,
                        pixel_processor, kwargs)

        Returns:
            List of (index, result) tuples
        """
        pixel_indices, pixel_coords, image_data, pixel_processor, kwargs = batch_data
        results = []

        for i, idx in enumerate(pixel_indices):
            y, x = pixel_coords[i]
            pixel_spectra = image_data[y, x, :]
            result = pixel_processor.process_pixel(pixel_spectra, **kwargs)
            results.append((idx, result))

        return results
    
    def _process_batches_parallel(self, batched_data: list) -> list:
        """Process all pixel batches in parallel.
        
        Args:
            batched_data: List of batch data for parallel processing.
            
        Returns:
            List of all processing results.
        """
        executor_class = (concurrent.futures.ThreadPoolExecutor if self.use_threads 
                         else concurrent.futures.ProcessPoolExecutor)

        with executor_class(max_workers=self.n_processes) as executor:
            # Submit all batches
            if self.progress_bar:
                futures = list(tqdm(
                    executor.map(self._process_pixel_batch, batched_data),
                    total=len(batched_data),
                    desc=f"Processing pixel batches ({'threads' if self.use_threads else 'processes'})"
                ))
            else:
                futures = list(executor.map(self._process_pixel_batch, batched_data))

            # Collect results
            all_results = []
            for batch_results in futures:
                all_results.extend(batch_results)
        
        return all_results
    
    def _fill_output_arrays(
        self,
        output: Dict[str, NDArray],
        all_results: list,
        y_indices: NDArray[np.intp],
        x_indices: NDArray[np.intp]
    ) -> None:
        """Fill output arrays with processing results.
        
        Args:
            output: Dictionary of output arrays to fill.
            all_results: List of (index, result) tuples from processing.
            y_indices: Y coordinates of processed pixels.
            x_indices: X coordinates of processed pixels.
        """
        # Sort results by original index
        all_results.sort(key=lambda x: x[0])
        
        for idx, result in all_results:
            y, x = y_indices[idx], x_indices[idx]

            for param, value in result['parameters'].items():
                output[param][y, x] = value

            output['error'][y, x] = result.get('error', np.nan)
            output['convergence'][y, x] = result.get('convergence', False)
            output['status'][y, x] = result.get('status', 'unknown')

            # Add modeled spectra if available
            if 'modeled_spectra' in result:
                output['modeled_spectra'][y, x, :] = result['modeled_spectra']
    
    def _print_processing_statistics(
        self, 
        output: Dict[str, NDArray], 
        n_pixels: int, 
        elapsed_time: float
    ) -> None:
        """Print processing statistics.
        
        Args:
            output: Dictionary of processing results.
            n_pixels: Total number of pixels processed.
            elapsed_time: Time taken for processing.
        """
        print(f"Image processing completed in {elapsed_time:.2f} seconds")

        # Calculate statistics on processed pixels if depth is present
        if 'depth' in output:
            valid_mask = ~np.isnan(output['depth'])
            valid_depths = output['depth'][valid_mask]
            if len(valid_depths) > 0:
                print(f"Depth statistics:")
                print(f"  Valid pixels: {len(valid_depths)} of {n_pixels} ({len(valid_depths) / n_pixels * 100:.1f}%)")
                print(f"  Min depth: {np.min(valid_depths):.2f} m")
                print(f"  Max depth: {np.max(valid_depths):.2f} m")
                print(f"  Mean depth: {np.mean(valid_depths):.2f} m")
                print(f"  Median depth: {np.median(valid_depths):.2f} m")
        
        # Print convergence statistics
        if 'convergence' in output:
            converged_pixels = np.sum(output['convergence'])
            convergence_rate = converged_pixels / n_pixels * 100
            print(f"Convergence statistics:")
            print(f"  Converged pixels: {converged_pixels} of {n_pixels} ({convergence_rate:.1f}%)")
        
        # Print status summary
        if 'status' in output:
            unique_statuses, counts = np.unique(output['status'].flatten(), return_counts=True)
            print(f"Processing status summary:")
            for status, count in zip(unique_statuses, counts):
                if status:  # Skip empty strings
                    percentage = count / n_pixels * 100
                    print(f"  {status}: {count} pixels ({percentage:.1f}%)")


class BatchImageProcessor(ImageProcessor):
    """Extended image processor for processing multiple images in batch."""
    
    def process_multiple_images(
        self,
        images: list[NDArray[np.float64]],
        pixel_processor: PixelProcessor,
        inversion_parameters: InversionParameters,
        masks: Optional[list[NDArray[np.bool_]]] = None,
        **kwargs: Any
    ) -> list[Dict[str, NDArray]]:
        """Process multiple images in batch.
        
        Args:
            images: List of hyperspectral images to process.
            pixel_processor: Configured pixel processor.
            inversion_parameters: Parameters for the inversion process.
            masks: Optional list of masks for each image.
            **kwargs: Additional arguments passed to pixel processor.
            
        Returns:
            List of result dictionaries for each image.
        """
        if masks is None:
            masks = [None] * len(images)
        elif len(masks) != len(images):
            raise ValueError(f"Number of masks ({len(masks)}) must match number of images ({len(images)})")
        
        results = []
        total_start_time = time.time()
        
        for i, (image, mask) in enumerate(zip(images, masks)):
            print(f"\nProcessing image {i + 1} of {len(images)}...")
            
            result = self.process_image(
                image=image,
                pixel_processor=pixel_processor,
                inversion_parameters=inversion_parameters,
                mask=mask,
                **kwargs
            )
            results.append(result)
        
        total_elapsed = time.time() - total_start_time
        print(f"\nBatch processing completed in {total_elapsed:.2f} seconds")
        print(f"Average time per image: {total_elapsed / len(images):.2f} seconds")
        
        return results
