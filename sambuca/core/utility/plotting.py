def plot_siops(siop_files_or_patterns, siop_directory, output_file=None, title=None, x_label="Wavelength (nm)",
               y_label=None,
               figsize=(12, 8), colors=None, dark_mode=True, legend_loc='upper right', xlim=None, ylim=None,
               dpi=300, show=True):
    """
    Create a professional-looking plot of SIOP data with a similar style to the reference image.

    Parameters:
    -----------
    siop_files_or_patterns : list
        List of SIOP filenames or patterns to plot.
        Each item can be:
        - A tuple of (subdir, filename) e.g., ('absorption', 'water_absorption.csv')
        - A string pattern to search for, e.g., 'absorption/*.csv'
    siop_directory : str
        Root path to the directory containing the SIOP subdirectories
    output_file : str, optional
        Path to save the figure, if None, figure is not saved
    title : str, optional
        Figure title
    x_label : str, optional
        x-axis label
    y_label : str, optional
        y-axis label, if None, will be auto-detected from file type
    figsize : tuple, optional
        Figure size (width, height) in inches
    colors : list, optional
        List of colors for each SIOP, if None, predefined colors will be used
    dark_mode : bool, optional
        If True, use a dark background
    legend_loc : str, optional
        Legend location
    xlim : tuple, optional
        x-axis limits (min, max)
    ylim : tuple, optional
        y-axis limits (min, max)
    dpi : int, optional
        Resolution for saved figure
    show : bool, optional
        If True, display the figure

    Returns:
    --------
    matplotlib.figure.Figure
        The created figure
    """
    import os
    import glob
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator

    # Set up the figure and axis with the dark mode style
    if dark_mode:
        plt.style.use('dark_background')

    fig, ax = plt.subplots(figsize=figsize)

    # Define default colors if not provided
    if colors is None:
        colors = ['#ff6347', '#4bc0c0', '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452',
                  '#9a60b4']

    # For tracking files and labels
    file_paths = []
    labels = []

    # Process input file specifications
    for item in siop_files_or_patterns:
        if isinstance(item, tuple) and len(item) == 2:
            # This is a (subdir, filename) tuple
            subdir, filename = item
            file_path = os.path.join(siop_directory, subdir, filename)
            if os.path.exists(file_path):
                file_paths.append(file_path)
                # Create label from filename without extension
                base_name = os.path.splitext(filename)[0]
                labels.append(base_name.replace('_', ' ').title())
        else:
            # This is a pattern
            pattern = item if os.path.isabs(item) else os.path.join(siop_directory, item)
            matching_files = glob.glob(pattern)
            for file_path in matching_files:
                if os.path.isfile(file_path):
                    file_paths.append(file_path)
                    # Create label from filename without extension
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    labels.append(base_name.replace('_', ' ').title())

    # Determine the type of data to set y-axis label if not provided
    if y_label is None:
        if any('absorption' in path.lower() for path in file_paths):
            y_label = "Absorption (1/m)"
        elif any('backscatter' in path.lower() for path in file_paths):
            y_label = "Backscatter (1/m)"
        elif any('substrate' in path.lower() for path in file_paths):
            y_label = "Reflectance"
        else:
            y_label = "Value"

    # Plot each SIOP file
    for i, (file_path, label) in enumerate(zip(file_paths, labels)):
        # Get color for this line
        color = colors[i % len(colors)]

        try:
            # Read the CSV file
            df = pd.read_csv(file_path)

            # Get column names
            columns = df.columns.tolist()

            # First column is always wavelength
            wavelength_col = columns[0]

            # Second column is the value
            value_col = columns[1]

            # Plot the data
            ax.plot(df[wavelength_col], df[value_col], color=color, linewidth=2.0, label=label)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    # Set axis labels and title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    if title:
        ax.set_title(title, fontsize=14)

    # Set axis limits if provided
    if xlim:
        ax.set_xlim(xlim)
    else:
        # Default to 300-900 nm for wavelength
        ax.set_xlim(300, 900)

    if ylim:
        ax.set_ylim(ylim)
    else:
        # Auto-scale y-axis with a little padding
        y_min, y_max = ax.get_ylim()
        padding = (y_max - y_min) * 0.05
        ax.set_ylim(0, y_max + padding)  # Always start at 0

    # Add grid with lower opacity
    ax.grid(True, linestyle='-', alpha=0.3)

    # Set tick parameters
    ax.tick_params(axis='both', which='both', labelsize=10)

    # Configure major and minor tick locations
    ax.xaxis.set_major_locator(MultipleLocator(100))
    ax.xaxis.set_minor_locator(MultipleLocator(50))

    # Add legend
    if labels:
        ax.legend(fontsize=10, loc=legend_loc)

    # Tight layout
    plt.tight_layout()

    # Save the figure if output file is provided
    if output_file:
        plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
        print(f"Figure saved to {output_file}")

    # Show the figure
    if show:
        plt.show()

    return fig


# Function to find and categorize SIOPs in a hierarchical directory structure
def find_siops(siop_directory):
    """
    Find and categorize SIOP files in a directory structure with subdirectories.

    Parameters:
    -----------
    siop_directory : str
        Root path to the directory containing SIOP subdirectories

    Returns:
    --------
    dict
        Dictionary of categorized SIOPs by directory
    """
    import os

    categories = {}

    # Check if the directory exists
    if not os.path.isdir(siop_directory):
        print(f"Directory not found: {siop_directory}")
        return categories

    # Scan for subdirectories
    subdirs = [d for d in os.listdir(siop_directory)
               if os.path.isdir(os.path.join(siop_directory, d))]

    # If no subdirectories found, look for CSV files directly
    if not subdirs:
        csv_files = [f for f in os.listdir(siop_directory)
                     if f.lower().endswith('.csv') and os.path.isfile(os.path.join(siop_directory, f))]
        if csv_files:
            categories[''] = csv_files
    else:
        # Look for CSV files in each subdirectory
        for subdir in subdirs:
            subdir_path = os.path.join(siop_directory, subdir)
            csv_files = [f for f in os.listdir(subdir_path)
                         if f.lower().endswith('.csv') and os.path.isfile(os.path.join(subdir_path, f))]
            if csv_files:
                categories[subdir] = csv_files

    return categories


# Example function to plot all SIOP categories
def plot_all_siop_categories(siop_directory, output_dir=None, show=True):
    """
    Plot all SIOP categories found in the given directory structure.

    Parameters:
    -----------
    siop_directory : str
        Root path to the directory containing SIOP subdirectories
    output_dir : str, optional
        Directory to save figures, if None, figures are not saved
    show : bool, optional
        If True, display the figures
    """
    import os

    # Find all SIOPs
    siop_categories = find_siops(siop_directory)

    if not siop_categories:
        print(f"No SIOP files found in {siop_directory}")
        return

    print(
        f"Found {sum(len(files) for files in siop_categories.values())} SIOP files in {len(siop_categories)} categories")

    # Plot each category
    for category, files in siop_categories.items():
        # Skip empty categories
        if not files:
            continue

        # Generate title and output filename
        category_name = category.capitalize() if category else "SIOPs"
        title = f"{category_name} Spectra"

        # Generate output path if output_dir is provided
        output_file = None
        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_file = os.path.join(output_dir, f"{category_name.lower()}_siops.png")

        # Generate file specifications as tuples (subdir, filename)
        file_specs = [(category, file) for file in files]

        # Determine appropriate y-axis label
        if 'absorption' in category.lower():
            y_label = "Absorption (1/m)"
        elif 'backscatter' in category.lower():
            y_label = "Backscatter (1/m)"
        elif 'substrate' in category.lower():
            y_label = "Reflectance"
        else:
            y_label = "Value"

        # Plot this category
        plot_siops(file_specs, siop_directory,
                   output_file=output_file,
                   title=title,
                   y_label=y_label,
                   show=show)


def plot_inversion_results(results, wavelengths=None, output_dir=None, prefix='inversion_result', 
                          figsize=(12, 10), dpi=300, show=True, sample_pixel=None, observed_spectra=None):
    """
    Create comprehensive plots of inversion results.

    Parameters:
    -----------
    results : dict
        Dictionary of inversion results from process_image
    wavelengths : list or array, optional
        Wavelengths used in the inversion
    output_dir : str, optional
        Directory to save figures, if None, figures are not saved
    prefix : str, optional
        Prefix for output filenames
    figsize : tuple, optional
        Figure size (width, height) in inches
    dpi : int, optional
        Resolution for saved figures
    show : bool, optional
        If True, display the figures
    sample_pixel : tuple, optional
        (y, x) coordinates of a sample pixel to plot spectra for
    observed_spectra : ndarray, optional
        Original image data, needed if sample_pixel is provided

    Returns:
    --------
    dict
        Dictionary of created figures
    """
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.gridspec as gridspec

    # Create output directory if needed
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Store all created figures
    figures = {}

    # Get parameter names (excluding metadata)
    param_names = [key for key in results.keys() 
                  if key not in ['error', 'convergence', 'status']]

    # Create a figure with subplots for all parameters and error
    n_params = len(param_names) + 1  # +1 for error
    n_cols = min(3, n_params)
    n_rows = (n_params + n_cols - 1) // n_cols

    # Create figure for parameter maps
    fig_maps = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig_maps)

    # Plot each parameter
    for i, param in enumerate(param_names):
        ax = fig_maps.add_subplot(gs[i // n_cols, i % n_cols])

        # Get data and mask invalid values
        data = results[param]
        masked_data = np.ma.masked_invalid(data)

        # Choose appropriate colormap
        if param.lower() == 'depth':
            cmap = 'viridis'
            title = 'Depth (m)'
        elif param.lower() == 'chl':
            cmap = 'YlGn'
            title = 'Chlorophyll (mg/m³)'
        elif param.lower() == 'cdom':
            cmap = 'YlOrBr'
            title = 'CDOM (1/m)'
        elif param.lower() == 'nap':
            cmap = 'OrRd'
            title = 'NAP (g/m³)'
        else:
            cmap = 'plasma'
            title = param

        # Plot the parameter map
        im = ax.imshow(masked_data, cmap=cmap)
        ax.set_title(title)
        plt.colorbar(im, ax=ax)

    # Plot error map
    error_idx = len(param_names)
    ax = fig_maps.add_subplot(gs[error_idx // n_cols, error_idx % n_cols])

    # Get error data and mask invalid values
    error_data = results['error']
    masked_error = np.ma.masked_invalid(error_data)

    # Plot the error map with a different colormap
    im = ax.imshow(masked_error, cmap='Reds')
    ax.set_title('Error (RMSE)')
    plt.colorbar(im, ax=ax)

    # Adjust layout
    plt.tight_layout()

    # Save figure if output directory is provided
    if output_dir:
        maps_filename = os.path.join(output_dir, f"{prefix}_parameter_maps.png")
        plt.savefig(maps_filename, dpi=dpi, bbox_inches='tight')
        print(f"Parameter maps saved to {maps_filename}")

    figures['parameter_maps'] = fig_maps

    # Create convergence map
    if 'convergence' in results:
        fig_conv = plt.figure(figsize=(10, 8))
        ax = fig_conv.add_subplot(111)

        # Create a custom colormap for boolean values
        colors = [(0.8, 0.2, 0.2), (0.2, 0.8, 0.2)]  # Red to Green
        cmap_name = 'convergence'
        cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=2)

        # Plot convergence map
        im = ax.imshow(results['convergence'], cmap=cm)
        ax.set_title('Convergence Status')

        # Create custom colorbar with labels
        cbar = plt.colorbar(im, ax=ax, ticks=[0.25, 0.75])
        cbar.ax.set_yticklabels(['Failed', 'Converged'])

        plt.tight_layout()

        # Save figure if output directory is provided
        if output_dir:
            conv_filename = os.path.join(output_dir, f"{prefix}_convergence_map.png")
            plt.savefig(conv_filename, dpi=dpi, bbox_inches='tight')
            print(f"Convergence map saved to {conv_filename}")

        figures['convergence_map'] = fig_conv

    # Plot spectra for a sample pixel if provided
    if sample_pixel and wavelengths is not None and observed_spectra is not None:
        y, x = sample_pixel

        # Check if the sample pixel is valid
        if (0 <= y < results[param_names[0]].shape[0] and 
            0 <= x < results[param_names[0]].shape[1] and
            not np.isnan(results[param_names[0]][y, x])):

            fig_spectra = plt.figure(figsize=(10, 6))
            ax = fig_spectra.add_subplot(111)

            # Get observed spectrum for this pixel
            observed = observed_spectra[y, x, :]

            # Plot observed spectrum
            ax.plot(wavelengths, observed, 'o-', color='blue', label='Observed')

            # If modeled_spectra is in the results, plot it
            if 'modeled_spectra' in results:
                modeled = results['modeled_spectra'][y, x, :]
                ax.plot(wavelengths, modeled, 's--', color='red', label='Modeled')

            ax.set_xlabel('Wavelength (nm)')
            ax.set_ylabel('Remote Sensing Reflectance')
            ax.set_title(f'Spectra at Pixel ({y}, {x})')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Add parameter values as text
#            param_text = "\n".join([f"{param}: {results[param][y, x]:.4f}" for param in param_names])
            error_text = f"Error: {results['error'][y, x]:.4f}"
 #           ax.text(0.02, 0.02, param_text + "\n" + error_text,
    #               transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.7))

            plt.tight_layout()

            # Save figure if output directory is provided
            if output_dir:
                spectra_filename = os.path.join(output_dir, f"{prefix}_sample_spectra.png")
                plt.savefig(spectra_filename, dpi=dpi, bbox_inches='tight')
                print(f"Sample spectra saved to {spectra_filename}")

            figures['sample_spectra'] = fig_spectra

    # Show figures if requested
    if show:
        plt.show()

    return figures
