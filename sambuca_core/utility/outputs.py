import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import rasterio
from rasterio.plot import show
import seaborn as sns
import pandas as pd


def visualize_sambuca_results(results_dict, output_dir, image_name='sambuca_results'):
    """
    Visualize multiple SAMBUCA output parameters with enhanced visualizations.

    Parameters:
    -----------
    results_dict : dict
        Dictionary containing parameter arrays from SAMBUCA inversion
    output_dir : str
        Directory to save output images
    image_name : str
        Base name for output images
    """
    os.makedirs(output_dir, exist_ok=True)

    # Create a multi-panel figure for main parameters
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Depth map with improved colormap
    ax = axes[0, 0]
    im = ax.imshow(results_dict['depth'], cmap='viridis_r',
                   vmin=0, vmax=np.nanpercentile(results_dict['depth'], 98))
    ax.set_title('Bathymetry (m)', fontsize=14)
    plt.colorbar(im, ax=ax, shrink=0.7)

    # Chlorophyll map
    if 'chl' in results_dict:
        ax = axes[0, 1]
        # Using log scale for chlorophyll which often has log-normal distribution
        im = ax.imshow(results_dict['chl'], cmap='YlGn',
                       norm=LogNorm(vmin=0.1, vmax=np.nanpercentile(results_dict['chl'], 98)))
        ax.set_title('Chlorophyll-a (mg/m³)', fontsize=14)
        plt.colorbar(im, ax=ax, shrink=0.7)

    # CDOM map
    if 'cdom' in results_dict:
        ax = axes[1, 0]
        im = ax.imshow(results_dict['cdom'], cmap='YlOrBr',
                       vmin=0, vmax=np.nanpercentile(results_dict['cdom'], 98))
        ax.set_title('CDOM Absorption (m⁻¹)', fontsize=14)
        plt.colorbar(im, ax=ax, shrink=0.7)

    # NAP map or error map if NAP not available
    if 'nap' in results_dict:
        ax = axes[1, 1]
        im = ax.imshow(results_dict['nap'], cmap='OrRd',
                       vmin=0, vmax=np.nanpercentile(results_dict['nap'], 98))
        ax.set_title('Non-Algal Particles (mg/L)', fontsize=14)
        plt.colorbar(im, ax=ax, shrink=0.7)
    elif 'error' in results_dict:
        ax = axes[1, 1]
        im = ax.imshow(results_dict['error'], cmap='plasma',
                       vmin=0, vmax=np.nanpercentile(results_dict['error'], 98))
        ax.set_title('Inversion Error (RMSE)', fontsize=14)
        plt.colorbar(im, ax=ax, shrink=0.7)

    # Add text information
    valid_pixels = {param: np.nansum(results_dict[param]) for param in results_dict
                    if isinstance(results_dict[param], np.ndarray) and results_dict[param].ndim == 2}

    info_text = "Valid pixels:\n"
    for param, count in valid_pixels.items():
        percent = count / results_dict[param].size * 100
        info_text += f"{param}: {count} ({percent:.1f}%)\n"

    fig.text(0.02, 0.02, info_text, fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{image_name}_main_parameters.png"), dpi=300)

    # Create histograms of valid depths and errors
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Depth histogram
    valid_depths = results_dict['depth'][~np.isnan(results_dict['depth'])]
    sns.histplot(valid_depths.flatten(), bins=30, kde=True, ax=axes[0])
    axes[0].set_title('Depth Distribution', fontsize=14)
    axes[0].set_xlabel('Depth (m)')
    axes[0].set_ylabel('Frequency')

    # Add depth statistics as text
    depth_stats = (
        f"Mean: {np.mean(valid_depths):.2f} m\n"
        f"Median: {np.median(valid_depths):.2f} m\n"
        f"Min: {np.min(valid_depths):.2f} m\n"
        f"Max: {np.max(valid_depths):.2f} m\n"
        f"Std Dev: {np.std(valid_depths):.2f} m"
    )
    axes[0].text(0.05, 0.95, depth_stats, transform=axes[0].transAxes,
                 va='top', ha='left', bbox=dict(facecolor='white', alpha=0.7))

    # Error histogram if available
    if 'error' in results_dict:
        valid_errors = results_dict['error'][~np.isnan(results_dict['error'])]
        sns.histplot(valid_errors.flatten(), bins=30, kde=True, ax=axes[1])
        axes[1].set_title('Error Distribution', fontsize=14)
        axes[1].set_xlabel('RMSE')
        axes[1].set_ylabel('Frequency')

        # Add error statistics as text
        error_stats = (
            f"Mean: {np.mean(valid_errors):.4f}\n"
            f"Median: {np.median(valid_errors):.4f}\n"
            f"Min: {np.min(valid_errors):.4f}\n"
            f"Max: {np.max(valid_errors):.4f}\n"
            f"Std Dev: {np.std(valid_errors):.4f}"
        )
        axes[1].text(0.05, 0.95, error_stats, transform=axes[1].transAxes,
                     va='top', ha='left', bbox=dict(facecolor='white', alpha=0.7))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{image_name}_distributions.png"), dpi=300)

    # Create scatter plots for parameter relationships (if available)
    if all(k in results_dict for k in ['depth', 'chl', 'cdom']):
        # Create a DataFrame for easier plotting
        valid_mask = (~np.isnan(results_dict['depth']) &
                      ~np.isnan(results_dict['chl']) &
                      ~np.isnan(results_dict['cdom']))

        if np.sum(valid_mask) > 0:  # Check we have valid data
            data = {
                'Depth': results_dict['depth'][valid_mask].flatten(),
                'Chlorophyll': results_dict['chl'][valid_mask].flatten(),
                'CDOM': results_dict['cdom'][valid_mask].flatten()
            }

            if 'nap' in results_dict:
                data['NAP'] = results_dict['nap'][valid_mask].flatten()

            df = pd.DataFrame(data)

            # Sample if too many points (for performance)
            if len(df) > 10000:
                df = df.sample(10000, random_state=42)

            # Create pairplot
            g = sns.pairplot(df, diag_kind='kde', corner=True)
            g.fig.suptitle('Parameter Relationships', y=1.02, fontsize=16)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{image_name}_parameter_relationships.png"), dpi=300)

    print(f"Visualizations saved to {output_dir}")
