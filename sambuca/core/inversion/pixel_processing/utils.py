"""Utility functions for pixel processing."""

from typing import Dict, Any, Optional
import time

import numpy as np
from numpy.typing import NDArray


def setup_nedr_kwargs(inversion_parameters, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Setup NEDR-related kwargs if NEDR is available.
    
    Args:
        inversion_parameters: Parameters for the inversion process.
        kwargs: Existing keyword arguments.
        
    Returns:
        Updated kwargs with NEDR information if available.
    """
    updated_kwargs = kwargs.copy()
    if hasattr(inversion_parameters, 'nedr') and inversion_parameters.nedr is not None:
        updated_kwargs['nedr'] = inversion_parameters.nedr
    return updated_kwargs


def create_nan_parameters_dict(param_names: list) -> Dict[str, float]:
    """Create a dictionary of parameter names with NaN values.
    
    Args:
        param_names: List of parameter names.
        
    Returns:
        Dictionary mapping parameter names to NaN values.
    """
    return {name: float('nan') for name in param_names}


def validate_processing_args(**kwargs) -> Dict[str, Any]:
    """Validate and normalize processing arguments.
    
    Args:
        **kwargs: Processing arguments to validate.
        
    Returns:
        Validated and normalized arguments.
        
    Raises:
        ValueError: If arguments are invalid.
    """
    validated = kwargs.copy()
    
    # Validate n_starts
    if 'n_starts' in validated:
        n_starts = validated['n_starts']
        if not isinstance(n_starts, int) or n_starts < 1:
            raise ValueError(f"n_starts must be a positive integer, got {n_starts}")
    
    # Validate chunk_size
    if 'chunk_size' in validated:
        chunk_size = validated['chunk_size']
        if not isinstance(chunk_size, int) or chunk_size < 1:
            raise ValueError(f"chunk_size must be a positive integer, got {chunk_size}")
    
    # Validate n_processes
    if 'n_processes' in validated:
        n_processes = validated['n_processes']
        if n_processes is not None and (not isinstance(n_processes, int) or n_processes < 1):
            raise ValueError(f"n_processes must be a positive integer or None, got {n_processes}")
    
    return validated


class ProcessingTimer:
    """Simple timer for tracking processing performance."""
    
    def __init__(self):
        """Initialize timer."""
        self.start_time = None
        self.end_time = None
        self.split_times = []
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
        self.split_times = []
    
    def split(self, label: str = None) -> float:
        """Record a split time.
        
        Args:
            label: Optional label for this split.
            
        Returns:
            Time elapsed since start.
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        self.split_times.append((label or f"split_{len(self.split_times)}", elapsed))
        return elapsed
    
    def stop(self) -> float:
        """Stop timing and return total elapsed time.
        
        Returns:
            Total elapsed time in seconds.
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        self.end_time = time.time()
        return self.end_time - self.start_time
    
    def get_elapsed(self) -> float:
        """Get elapsed time (without stopping timer).
        
        Returns:
            Time elapsed since start.
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        return time.time() - self.start_time
    
    def get_splits(self) -> list:
        """Get all recorded split times.
        
        Returns:
            List of (label, elapsed_time) tuples.
        """
        return self.split_times.copy()


class ProcessingStatistics:
    """Collects and reports processing statistics."""
    
    def __init__(self):
        """Initialize statistics collector."""
        self.reset()
    
    def reset(self):
        """Reset all statistics."""
        self.total_pixels = 0
        self.valid_pixels = 0
        self.converged_pixels = 0
        self.strategy_counts = {}
        self.error_types = {}
        self.processing_times = []
    
    def add_result(self, result: Dict[str, Any], processing_time: float = None):
        """Add a processing result to statistics.
        
        Args:
            result: Processing result dictionary.
            processing_time: Optional processing time for this pixel.
        """
        self.total_pixels += 1
        
        if result.get('status') != 'invalid_pixel':
            self.valid_pixels += 1
        
        if result.get('convergence', False):
            self.converged_pixels += 1
        
        # Track strategy usage
        strategy = result.get('strategy_used', 'unknown')
        self.strategy_counts[strategy] = self.strategy_counts.get(strategy, 0) + 1
        
        # Track error types
        status = result.get('status', 'unknown')
        self.error_types[status] = self.error_types.get(status, 0) + 1
        
        # Track processing times
        if processing_time is not None:
            self.processing_times.append(processing_time)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics.
        
        Returns:
            Dictionary with summary statistics.
        """
        summary = {
            'total_pixels': self.total_pixels,
            'valid_pixels': self.valid_pixels,
            'converged_pixels': self.converged_pixels,
            'validity_rate': self.valid_pixels / max(1, self.total_pixels),
            'convergence_rate': self.converged_pixels / max(1, self.valid_pixels),
            'strategy_counts': self.strategy_counts.copy(),
            'error_types': self.error_types.copy()
        }
        
        if self.processing_times:
            summary['timing'] = {
                'mean_time': np.mean(self.processing_times),
                'median_time': np.median(self.processing_times),
                'min_time': np.min(self.processing_times),
                'max_time': np.max(self.processing_times),
                'total_time': np.sum(self.processing_times)
            }
        
        return summary
    
    def print_summary(self):
        """Print formatted summary statistics."""
        summary = self.get_summary()
        
        print("Processing Statistics:")
        print(f"  Total pixels: {summary['total_pixels']}")
        print(f"  Valid pixels: {summary['valid_pixels']} ({summary['validity_rate']:.1%})")
        print(f"  Converged pixels: {summary['converged_pixels']} ({summary['convergence_rate']:.1%})")
        
        if summary['strategy_counts']:
            print("  Strategy usage:")
            for strategy, count in summary['strategy_counts'].items():
                rate = count / max(1, summary['total_pixels'])
                print(f"    {strategy}: {count} ({rate:.1%})")
        
        if 'timing' in summary:
            timing = summary['timing']
            print(f"  Processing timing:")
            print(f"    Mean: {timing['mean_time']:.3f}s")
            print(f"    Median: {timing['median_time']:.3f}s")
            print(f"    Range: {timing['min_time']:.3f}s - {timing['max_time']:.3f}s")
            print(f"    Total: {timing['total_time']:.1f}s")


def create_processing_report(output: Dict[str, NDArray], 
                           processing_time: float,
                           n_pixels: int,
                           strategies_used: Optional[list] = None) -> Dict[str, Any]:
    """Create a comprehensive processing report.
    
    Args:
        output: Processing output arrays.
        processing_time: Total processing time.
        n_pixels: Number of pixels processed.
        strategies_used: Optional list of strategies that were used.
        
    Returns:
        Dictionary with comprehensive processing report.
    """
    report = {
        'processing_time': processing_time,
        'total_pixels': n_pixels,
        'pixels_per_second': n_pixels / max(processing_time, 0.001)
    }
    
    # Convergence statistics
    if 'convergence' in output:
        converged = np.sum(output['convergence'])
        report['converged_pixels'] = int(converged)
        report['convergence_rate'] = float(converged / n_pixels)
    
    # Parameter statistics
    for param_name in output:
        if param_name in ['error', 'convergence', 'status', 'modeled_spectra']:
            continue
        
        param_values = output[param_name]
        valid_mask = ~np.isnan(param_values)
        valid_values = param_values[valid_mask]
        
        if len(valid_values) > 0:
            report[f'{param_name}_stats'] = {
                'valid_pixels': int(np.sum(valid_mask)),
                'mean': float(np.mean(valid_values)),
                'median': float(np.median(valid_values)),
                'std': float(np.std(valid_values)),
                'min': float(np.min(valid_values)),
                'max': float(np.max(valid_values))
            }
    
    # Error statistics
    if 'error' in output:
        error_values = output['error']
        valid_errors = error_values[~np.isnan(error_values)]
        if len(valid_errors) > 0:
            report['error_stats'] = {
                'mean_error': float(np.mean(valid_errors)),
                'median_error': float(np.median(valid_errors)),
                'min_error': float(np.min(valid_errors)),
                'max_error': float(np.max(valid_errors))
            }
    
    # Strategy usage (if available)
    if strategies_used:
        report['strategies_used'] = strategies_used
    
    return report
