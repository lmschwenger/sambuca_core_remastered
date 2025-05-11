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
