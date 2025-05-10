#!/usr/bin/env python
# scripts/plot_siop_libraries.py

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def load_csv_spectra(filepath):
    """Load a CSV spectral file and return wavelengths and values."""
    try:
        df = pd.read_csv(filepath)
        # Check if we have a two-column format
        if len(df.columns) == 2:
            return df.iloc[:, 0].values, df.iloc[:, 1].values
        else:
            print(f"Warning: Unexpected format in {filepath}")
            return None, None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None, None


def plot_siop_libraries(siop_dir='./data/siops'):
    """Plot all SIOP libraries from the given directory."""
    # Define SIOP categories and their expected paths
    categories = {
        'Absorption': os.path.join(siop_dir, 'absorption'),
        'Backscatter': os.path.join(siop_dir, 'backscatter'),
        'Substrates': os.path.join(siop_dir, 'substrates')
    }

    # Create a figure with subplots
    fig = plt.figure(figsize=(15, 18))
    gs = GridSpec(3, 1, figure=fig, height_ratios=[1, 1, 1])

    category_axes = {
        'Absorption': fig.add_subplot(gs[0]),
        'Backscatter': fig.add_subplot(gs[1]),
        'Substrates': fig.add_subplot(gs[2])
    }

    # Color mapping for consistent colors per type
    colors = {
        'water': 'blue',
        'phytoplankton': 'green',
        'cdom': 'brown',
        'nap': 'red',
        'sand': 'gold',
        'seagrass': 'darkgreen',
        'mud': 'saddlebrown'
    }

    legends = {}

    # Process each category
    for category, category_path in categories.items():
        if not os.path.exists(category_path):
            print(f"Directory not found: {category_path}")
            continue

        ax = category_axes[category]
        legends[category] = []

        # Process each CSV file in the category directory
        for filename in sorted(os.listdir(category_path)):
            if filename.endswith('.csv'):
                filepath = os.path.join(category_path, filename)

                # Load spectral data
                wavelengths, values = load_csv_spectra(filepath)

                if wavelengths is not None and values is not None:
                    # Determine color and label from filename
                    base_name = os.path.splitext(filename)[0]
                    type_name = base_name.split('_')[0]

                    color = colors.get(type_name, 'gray')
                    label = base_name.replace('_', ' ').title()

                    # Plot the data
                    line, = ax.plot(wavelengths, values, '-', color=color, linewidth=2, label=label)
                    legends[category].append(line)

        # Set axis labels and title
        ax.set_xlabel('Wavelength (nm)')
        if category == 'Absorption':
            ax.set_ylabel('Absorption Coefficient (m⁻¹)')
        elif category == 'Backscatter':
            ax.set_ylabel('Backscattering Coefficient (m⁻¹)')
        else:  # Substrates
            ax.set_ylabel('Reflectance')

        ax.set_title(f'{category} Spectra')
        ax.grid(True, linestyle='--', alpha=0.7)

        # Add legend
        if legends[category]:
            ax.legend(handles=legends[category], loc='upper right')

    plt.tight_layout()

    # Save the plot
    output_path = os.path.join('plots', 'siop_libraries.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")

    # Create individual plots per category for better detail
    for category, category_path in categories.items():
        if not os.path.exists(category_path):
            continue

        plt.figure(figsize=(10, 6))

        # Process each CSV file in the category directory
        for filename in sorted(os.listdir(category_path)):
            if filename.endswith('.csv'):
                filepath = os.path.join(category_path, filename)

                # Load spectral data
                wavelengths, values = load_csv_spectra(filepath)

                if wavelengths is not None and values is not None:
                    # Determine color and label from filename
                    base_name = os.path.splitext(filename)[0]
                    type_name = base_name.split('_')[0]

                    color = colors.get(type_name, 'gray')
                    label = base_name.replace('_', ' ').title()

                    # Plot the data
                    plt.plot(wavelengths, values, '-', color=color, linewidth=2, label=label)

        # Set axis labels and title
        plt.xlabel('Wavelength (nm)')
        if category == 'Absorption':
            plt.ylabel('Absorption Coefficient (m⁻¹)')
        elif category == 'Backscatter':
            plt.ylabel('Backscattering Coefficient (m⁻¹)')
        else:  # Substrates
            plt.ylabel('Reflectance')

        plt.title(f'{category} Spectra')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(loc='best')

        # Save individual plot
        output_path = os.path.join('plots', f'{category.lower()}_spectra.png')
        plt.savefig(output_path, dpi=300)
        print(f"{category} plot saved to {output_path}")

    # Also create a plot comparing water properties for better understanding of water column physics
    plt.figure(figsize=(12, 8))

    # Water absorption
    water_abs_path = os.path.join(siop_dir, 'absorption', 'water_absorption.csv')
    if os.path.exists(water_abs_path):
        wavelengths, values = load_csv_spectra(water_abs_path)
        plt.plot(wavelengths, values, 'b-', linewidth=2, label='Water Absorption')

    # Water backscatter
    water_bb_path = os.path.join(siop_dir, 'backscatter', 'water_backscatter.csv')
    if os.path.exists(water_bb_path):
        wavelengths, values = load_csv_spectra(water_bb_path)
        plt.plot(wavelengths, values, 'b--', linewidth=2, label='Water Backscatter')

    # Phytoplankton absorption
    phyto_abs_path = os.path.join(siop_dir, 'absorption', 'phytoplankton_absorption.csv')
    if os.path.exists(phyto_abs_path):
        wavelengths, values = load_csv_spectra(phyto_abs_path)
        plt.plot(wavelengths, values, 'g-', linewidth=2, label='Phytoplankton Absorption')

    # Set axis labels and title
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Coefficient (m⁻¹)')
    plt.title('Water Column Optical Properties')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    # Save water properties plot
    output_path = os.path.join('plots', 'water_column_properties.png')
    plt.savefig(output_path, dpi=300)
    print(f"Water column properties plot saved to {output_path}")

    # Create simulated reflectance plot using these properties
    create_forward_model_simulation(siop_dir)

    return True


def create_forward_model_simulation(siop_dir):
    """Create a simulation of reflectance using the forward model and loaded SIOPs."""
    import sambuca_core as sbc

    # Load water absorption
    water_abs_path = os.path.join(siop_dir, 'absorption', 'water_absorption.csv')
    if not os.path.exists(water_abs_path):
        print(f"Water absorption file not found: {water_abs_path}")
        return

    wavelengths, a_water = load_csv_spectra(water_abs_path)

    # Load phytoplankton absorption
    phyto_abs_path = os.path.join(siop_dir, 'absorption', 'phytoplankton_absorption.csv')
    if not os.path.exists(phyto_abs_path):
        print(f"Phytoplankton absorption file not found: {phyto_abs_path}")
        return

    _, a_ph_star = load_csv_spectra(phyto_abs_path)

    # Load sand substrate
    sand_path = os.path.join(siop_dir, 'substrates', 'sand_substrate.csv')
    if not os.path.exists(sand_path):
        print(f"Sand substrate file not found: {sand_path}")
        return

    _, substrate1 = load_csv_spectra(sand_path)

    # Load seagrass substrate if available
    seagrass_path = os.path.join(siop_dir, 'substrates', 'seagrass_substrate.csv')
    substrate2 = None
    if os.path.exists(seagrass_path):
        _, substrate2 = load_csv_spectra(seagrass_path)

    # Ensure all arrays are the same length by interpolating if needed
    if len({len(a_water), len(a_ph_star), len(substrate1)}) > 1:
        print("Warning: Arrays have different lengths. Interpolation needed.")
        # Implementation of interpolation would go here
        # For simplicity, just use the shortest length for now
        min_len = min(len(a_water), len(a_ph_star), len(substrate1))
        wavelengths = wavelengths[:min_len]
        a_water = a_water[:min_len]
        a_ph_star = a_ph_star[:min_len]
        substrate1 = substrate1[:min_len]
        if substrate2 is not None:
            substrate2 = substrate2[:min_len]

    num_bands = len(wavelengths)

    # Test with a grid of parameters
    depths = [0.5, 1.0, 2.0, 3.5, 5.0, 10.0]
    chls = [0.5, 1.0, 2.0, 5.0]

    # Create plots for varying depth and chlorophyll
    plt.figure(figsize=(12, 8))

    for depth in depths:
        result = sbc.forward_model(
            chl=1.0,  # Fixed chlorophyll
            cdom=0.005,
            nap=0,
            depth=depth,
            substrate1=substrate1,
            substrate2=substrate2,
            substrate_fraction=0.7 if substrate2 is not None else 1.0,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=num_bands
        )
        plt.plot(wavelengths, result.rrs, '-', linewidth=2, label=f'Depth = {depth}m')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Depth on Reflectance (Fixed Chl=1.0 mg/m³)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    output_path = os.path.join('plots', 'depth_effect.png')
    plt.savefig(output_path, dpi=300)
    print(f"Depth effect plot saved to {output_path}")

    # Plot for varying chlorophyll
    plt.figure(figsize=(12, 8))

    for chl in chls:
        result = sbc.forward_model(
            chl=chl,
            cdom=0.5,
            nap=1.0,
            depth=3.0,  # Fixed depth
            substrate1=substrate1,
            substrate2=substrate2,
            substrate_fraction=0.7 if substrate2 is not None else 1.0,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            num_bands=num_bands
        )
        plt.plot(wavelengths, result.rrs, '-', linewidth=2, label=f'Chl = {chl} mg/m³')

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Remote Sensing Reflectance')
    plt.title('Effect of Chlorophyll on Reflectance (Fixed Depth=3.0m)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    output_path = os.path.join('plots', 'chlorophyll_effect.png')
    plt.savefig(output_path, dpi=300)
    print(f"Chlorophyll effect plot saved to {output_path}")


if __name__ == "__main__":
    plot_siop_libraries(siop_dir=os.path.join('..', 'data', 'siops'))
    print("SIOP plotting complete!")