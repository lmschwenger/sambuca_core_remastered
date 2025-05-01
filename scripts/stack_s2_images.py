import os
import rasterio
from rasterio.merge import merge
import numpy as np
from pathlib import Path


def stack_sentinel2_bands(input_folder, output_file=None):
    """
    Stack Sentinel-2 bands found in the input folder into a single multi-band GeoTIFF.
    Bands will be ordered according to the standard Sentinel-2 band ordering.

    Parameters:
    -----------
    input_folder : str
        Path to the folder containing Sentinel-2 band GeoTIFFs
    output_file : str, optional
        Path for the output stacked GeoTIFF. If None, will be named 'stacked_bands.tif'
        in the input folder.

    Returns:
    --------
    str : Path to the saved output file
    """
    # Define Sentinel-2 band order (all possible bands)
    s2_band_order = [
        'b01', 'b02', 'b03', 'b04', 'b05', 'b06', 'b07', 'b08',
        'b8a', 'b09', 'b10', 'b11', 'b12'
    ]

    # If no output file specified, create one in the input folder
    if output_file is None:
        output_file = os.path.join(input_folder, 'stacked_bands.tif')

    # Find all tif files in the folder
    tif_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.tif', '.tiff'))]

    # Extract band names and create a dictionary mapping band names to file paths
    band_files = {}
    for file in tif_files:
        # Extract the band name (assuming format like "something_b01.tif" or "b01.tif")
        for band in s2_band_order:
            if band in file.lower():
                band_files[band] = os.path.join(input_folder, file)
                break

    if not band_files:
        raise ValueError(f"No Sentinel-2 band files found in {input_folder}")

    print(f"Found the following bands: {', '.join(band_files.keys())}")

    # Sort the bands according to Sentinel-2 ordering
    available_bands = sorted(band_files.keys(),
                             key=lambda x: s2_band_order.index(x) if x in s2_band_order else 999)

    # Open the first band to get metadata
    with rasterio.open(band_files[available_bands[0]]) as src:
        meta = src.meta
        height = src.height
        width = src.width

    # Update metadata for the output file
    meta.update({
        'count': len(available_bands),
        'driver': 'GTiff',
        'compress': 'lzw'
    })

    # Create the output file and write the bands
    with rasterio.open(output_file, 'w', **meta) as dst:
        for idx, band_name in enumerate(available_bands):
            with rasterio.open(band_files[band_name]) as src:
                # Read the band data
                band_data = src.read(1)

                # Write to the output file (band index is 1-based)
                dst.write(band_data, idx + 1)

                # Copy the band metadata
                dst.set_band_description(idx + 1, band_name)

    print(f"Successfully stacked {len(available_bands)} bands into {output_file}")
    print(f"Band order in stacked file: {', '.join(available_bands)}")

    return output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Stack Sentinel-2 band GeoTIFFs into a multi-band file')
    parser.add_argument('input_folder', help='Folder containing Sentinel-2 band GeoTIFFs')
    parser.add_argument('--output', '-o', help='Output file path (optional)')

    args = parser.parse_args()

    stack_sentinel2_bands(args.input_folder, args.output)