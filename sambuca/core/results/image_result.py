from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from pathlib import Path
import rasterio
from rasterio.enums import Resampling
from skimage.draw import line


class ImageInversionResult:
    """Container for image inversion results with built-in analysis and visualization."""

    def __init__(self,
                 results: Dict[str, np.ndarray],
                 image_metadata: Dict[str, Any],
                 workflow_config: Dict[str, Any],
                 image_path: str):
        """
        Initialize result container.

        Args:
            results: Dictionary of parameter arrays from process_image
            image_metadata: Original image metadata from rasterio
            workflow_config: Configuration used for processing
            image_path: Path to original image file
        """
        self.results = results
        self.image_metadata = image_metadata
        self.workflow_config = workflow_config
        self.image_path = image_path
        self._stats_cache = None

    def get_parameter_names(self) -> List[str]:
        """Get list of retrieved parameter names."""
        return [key for key in self.results.keys()
                if key not in ['error', 'convergence', 'status', 'modeled_spectra']]

    def get_parameter_map(self, param_name: str) -> np.ndarray:
        """Get parameter map as numpy array."""
        if param_name not in self.results:
            available = ', '.join(self.results.keys())
            raise ValueError(f"Parameter '{param_name}' not found. Available: {available}")
        return self.results[param_name]

    def get_statistics(self, force_recalculate: bool = False) -> Dict[str, Dict[str, float]]:
        """
        Get comprehensive statistics for all parameters.

        Args:
            force_recalculate: Recalculate even if cached

        Returns:
            Nested dictionary with statistics for each parameter
        """
        if self._stats_cache is not None and not force_recalculate:
            return self._stats_cache

        stats = {}

        for param_name in self.get_parameter_names():
            data = self.results[param_name]
            valid_data = data[~np.isnan(data)]

            if len(valid_data) > 0:
                stats[param_name] = {
                    'valid_pixels': len(valid_data),
                    'total_pixels': np.size(data),
                    'valid_percentage': len(valid_data) / np.size(data) * 100,
                    'min': float(np.min(valid_data)),
                    'max': float(np.max(valid_data)),
                    'mean': float(np.mean(valid_data)),
                    'median': float(np.median(valid_data)),
                    'std': float(np.std(valid_data)),
                    'p25': float(np.percentile(valid_data, 25)),
                    'p75': float(np.percentile(valid_data, 75))
                }
            else:
                stats[param_name] = {
                    'valid_pixels': 0,
                    'total_pixels': np.size(data),
                    'valid_percentage': 0.0
                }

        # Add error statistics
        if 'error' in self.results:
            error_data = self.results['error']
            valid_errors = error_data[~np.isnan(error_data)]
            if len(valid_errors) > 0:
                stats['error'] = {
                    'min': float(np.min(valid_errors)),
                    'max': float(np.max(valid_errors)),
                    'mean': float(np.mean(valid_errors)),
                    'median': float(np.median(valid_errors))
                }

        # Add convergence statistics
        if 'convergence' in self.results:
            convergence = self.results['convergence']
            converged_pixels = np.sum(convergence)
            total_pixels = np.size(convergence)
            stats['convergence'] = {
                'converged_pixels': int(converged_pixels),
                'total_pixels': int(total_pixels),
                'convergence_rate': float(converged_pixels / total_pixels * 100)
            }

        self._stats_cache = stats
        return stats

    def print_summary(self):
        """Print a summary of inversion results."""
        print("=" * 60)
        print("INVERSION RESULTS SUMMARY")
        print("=" * 60)

        stats = self.get_statistics()

        for param_name in self.get_parameter_names():
            if param_name in stats:
                s = stats[param_name]
                print(f"\n{param_name.upper()}:")
                print(f"  Valid pixels: {s['valid_pixels']} of {s['total_pixels']} "
                      f"({s['valid_percentage']:.1f}%)")

                if s['valid_pixels'] > 0:
                    print(f"  Range: {s['min']:.3f} - {s['max']:.3f}")
                    print(f"  Mean ± Std: {s['mean']:.3f} ± {s['std']:.3f}")
                    print(f"  Median [Q1-Q3]: {s['median']:.3f} [{s['p25']:.3f}-{s['p75']:.3f}]")

        if 'error' in stats:
            e = stats['error']
            print(f"\nERROR STATISTICS:")
            print(f"  RMSE range: {e['min']:.6f} - {e['max']:.6f}")
            print(f"  Mean RMSE: {e['mean']:.6f}")

        if 'convergence' in stats:
            c = stats['convergence']
            print(f"\nCONVERGENCE:")
            print(f"  Success rate: {c['convergence_rate']:.1f}% "
                  f"({c['converged_pixels']} of {c['total_pixels']})")

        print("=" * 60)

    def plot_summary(self,
                     figsize: Tuple[int, int] = (15, 10),
                     save_path: Optional[str] = None,
                     dpi: int = 300) -> 'matplotlib.figure.Figure':
        """
        Create comprehensive summary plot.

        Args:
            figsize: Figure size (width, height)
            save_path: Optional path to save figure
            dpi: Resolution for saved figure

        Returns:
            matplotlib Figure object
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        from .visualization import ResultVisualizer

        visualizer = ResultVisualizer(self)
        fig = visualizer.create_summary_plot(figsize=figsize)

        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            print(f"Summary plot saved to: {save_path}")

        return fig

    def plot_parameter(self,
                       param_name: str,
                       figsize: Tuple[int, int] = (10, 8),
                       colormap: str = 'auto',
                       **kwargs) -> 'matplotlib.figure.Figure':
        """
        Plot individual parameter map.

        Args:
            param_name: Name of parameter to plot
            figsize: Figure size
            colormap: Colormap name or 'auto' for automatic selection
            **kwargs: Additional arguments for imshow

        Returns:
            matplotlib Figure object
        """
        import matplotlib.pyplot as plt
        from .visualization import ResultVisualizer

        visualizer = ResultVisualizer(self)
        return visualizer.plot_parameter(param_name, figsize=figsize,
                                         colormap=colormap, **kwargs)

    def save_depth_map(self, output_path: str, format: str = 'tiff'):
        """
        Save depth map as GeoTIFF.

        Args:
            output_path: Output file path
            format: Output format ('tiff' or 'png')
        """
        if 'depth' not in self.results:
            raise ValueError("No depth data available to save")

        output_path = Path(output_path)

        if format.lower() == 'tiff':
            self._save_as_geotiff(output_path, 'depth')
        elif format.lower() == 'png':
            self._save_as_png(output_path, 'depth')
        else:
            raise ValueError(f"Unsupported format: {format}")

        print(f"Depth map saved to: {output_path}")

    def save_all_parameters(self,
                            output_dir: str,
                            formats: List[str] = ['tiff'],
                            prefix: str = 'sambuca') -> Dict[str, str]:
        """
        Save all parameter maps to files.

        Args:
            output_dir: Output directory
            formats: List of formats to save ('tiff', 'png')
            prefix: Filename prefix

        Returns:
            Dictionary mapping parameter names to saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        for param_name in self.get_parameter_names():
            for fmt in formats:
                if fmt.lower() == 'tiff':
                    filename = f"{prefix}_{param_name}.tif"
                    filepath = output_dir / filename
                    self._save_as_geotiff(filepath, param_name)
                elif fmt.lower() == 'png':
                    filename = f"{prefix}_{param_name}.png"
                    filepath = output_dir / filename
                    self._save_as_png(filepath, param_name)

                saved_files[f"{param_name}_{fmt}"] = str(filepath)

        print(f"Saved {len(saved_files)} files to: {output_dir}")
        return saved_files

    def _save_as_geotiff(self, output_path: Path, param_name: str):
        """Save parameter as GeoTIFF with spatial reference."""
        data = self.results[param_name].astype(np.float32)

        # Update metadata for single band output
        meta = self.image_metadata.copy()
        meta.update({
            'count': 1,
            'dtype': 'float32',
            'nodata': np.nan,
            'compress': 'lzw'
        })

        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(data, 1)
            dst.set_band_description(1, param_name)

    def _save_as_png(self, output_path: Path, param_name: str):
        """Save parameter as PNG with colorbar."""
        import matplotlib.pyplot as plt
        from .visualization import ResultVisualizer

        visualizer = ResultVisualizer(self)
        fig = visualizer.plot_parameter(param_name, show_colorbar=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

    def extract_transect(self,
                         start_coords: Tuple[int, int],
                         end_coords: Tuple[int, int],
                         param_name: str = 'depth') -> Dict[str, np.ndarray]:
        """
        Extract values along a transect line.

        Args:
            start_coords: (row, col) start coordinates
            end_coords: (row, col) end coordinates
            param_name: Parameter to extract

        Returns:
            Dictionary with distance and parameter values
        """

        y0, x0 = start_coords
        y1, x1 = end_coords

        # Get line coordinates
        rr, cc = line(y0, x0, y1, x1)

        # Extract values
        data = self.results[param_name]
        values = data[rr, cc]

        # Calculate distances
        distances = np.sqrt((rr - y0) ** 2 + (cc - x0) ** 2)

        return {
            'distance': distances,
            'values': values,
            'coordinates': list(zip(rr, cc))
        }