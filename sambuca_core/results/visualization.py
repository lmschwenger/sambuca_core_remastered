from pathlib import Path
from typing import Tuple

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

from sambuca_core.results.image_result import ImageInversionResult


class ResultVisualizer:
    """Visualization utilities for inversion results."""

    def __init__(self, result: 'ImageInversionResult'):
        self.result = result

        # Default colormaps for different parameters
        self.parameter_cmaps = {
            'depth': 'viridis',
            'chl': 'YlGn',
            'cdom': 'YlOrBr',
            'nap': 'OrRd',
            'error': 'Reds'
        }

    def create_summary_plot(self, figsize: Tuple[int, int] = (15, 10)) -> plt.Figure:
        """Create comprehensive summary visualization."""
        param_names = self.result.get_parameter_names()
        n_params = len(param_names)

        # Add error map if available
        if 'error' in self.result.results:
            param_names.append('error')
            n_params += 1

        # Calculate grid layout
        n_cols = min(3, n_params)
        n_rows = (n_params + n_cols - 1) // n_cols

        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(n_rows, n_cols, figure=fig)

        # Plot each parameter
        for i, param in enumerate(param_names):
            ax = fig.add_subplot(gs[i // n_cols, i % n_cols])
            self._plot_parameter_on_axis(ax, param)

        # Add overall title
        image_name = Path(self.result.image_path).name
        fig.suptitle(f'Inversion Results: {image_name}', fontsize=16, y=0.98)

        plt.tight_layout()
        return fig

    def plot_parameter(self,
                       param_name: str,
                       figsize: Tuple[int, int] = (10, 8),
                       colormap: str = 'auto',
                       show_colorbar: bool = True,
                       **kwargs) -> plt.Figure:
        """Plot individual parameter map."""
        fig, ax = plt.subplots(figsize=figsize)

        # Select colormap
        if colormap == 'auto':
            cmap = self.parameter_cmaps.get(param_name, 'plasma')
        else:
            cmap = colormap

        # Plot parameter
        data = self.result.results[param_name]
        masked_data = np.ma.masked_invalid(data)

        im = ax.imshow(masked_data, cmap=cmap, **kwargs)

        # Set title and labels
        title = self._get_parameter_title(param_name)
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')

        # Add colorbar
        if show_colorbar:
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(self._get_parameter_units(param_name))

        plt.tight_layout()
        return fig

    def _plot_parameter_on_axis(self, ax: plt.Axes, param_name: str):
        """Plot parameter on existing axis."""
        data = self.result.results[param_name]
        masked_data = np.ma.masked_invalid(data)

        # Select colormap
        cmap = self.parameter_cmaps.get(param_name, 'plasma')

        # Plot
        im = ax.imshow(masked_data, cmap=cmap)

        # Set title
        title = self._get_parameter_title(param_name)
        ax.set_title(title)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(self._get_parameter_units(param_name))

        ax.set_xlabel('Column')
        ax.set_ylabel('Row')

    def _get_parameter_title(self, param_name: str) -> str:
        """Get formatted title for parameter."""
        titles = {
            'depth': 'Water Depth',
            'chl': 'Chlorophyll Concentration',
            'cdom': 'CDOM Absorption',
            'nap': 'Non-Algal Particles',
            'error': 'Inversion Error (RMSE)'
        }
        return titles.get(param_name, param_name.replace('_', ' ').title())

    def _get_parameter_units(self, param_name: str) -> str:
        """Get units string for parameter."""
        units = {
            'depth': 'meters (m)',
            'chl': 'mg/m³',
            'cdom': '1/m',
            'nap': 'mg/L',
            'error': 'RMSE'
        }
        return units.get(param_name, '')
