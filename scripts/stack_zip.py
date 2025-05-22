import os
import shutil
import zipfile

import numpy as np
import rasterio


def stack_bands_from_zip(zip_path, output_dir, bands_to_stack, output_file=None):
    """
    Extracts a ZIP file containing band TIFFs, stacks the specified bands,
    and removes the extracted files.

    Args:
        zip_path (str): Path to the ZIP file containing band TIFFs.
        output_dir (str): Temporary directory for extracting the ZIP contents.
        bands_to_stack (list): List of band names to stack (e.g., ["B01", "B02", "B03"]).
        output_file (str): Optional path to save the stacked bands as a GeoTIFF.

    Returns:
        numpy.ndarray: Stacked array of shape (bands, height, width).
    """
    # Step 1: Extract the ZIP file
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    print(f"Extracted files to {output_dir}")

    # Step 2: Stack the specified bands
    band_arrays = []
    reference_file = None

    for band in bands_to_stack:
        # Locate the file matching the band name
        band_file = next((f for f in os.listdir(output_dir) if band in f), None)
        if not band_file:
            raise FileNotFoundError(f"Band {band} not found in {output_dir}")

        # Open the band file with rasterio and read it as an array
        band_path = os.path.join(output_dir, band_file)
        with rasterio.open(band_path) as src:
            band_array = src.read(1)
            band_arrays.append(band_array)

            # Store the first file as reference for metadata
            if reference_file is None:
                reference_file = band_path

    # Stack the bands into a single array
    stacked_array = np.stack(band_arrays, axis=0)  # Shape: (bands, height, width)
    print(f"Stacked bands shape: {stacked_array.shape}")

    # Step 3: Optionally save the stacked array as a GeoTIFF
    if output_file:
        with rasterio.open(reference_file) as src:
            profile = src.profile.copy()
            profile.update(count=len(bands_to_stack), dtype=rasterio.float32)

            with rasterio.open(output_file, 'w', **profile) as dst:
                dst.write(stacked_array.astype(rasterio.float32))
        print(f"Saved stacked bands to {output_file}")

    # Step 4: Clean up extracted files
    shutil.rmtree(output_dir)
    print(f"Removed temporary files from {output_dir}")

    return stacked_array

def main():
    zip_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raws', 'Browser_images.zip')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raws', 'temp')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'images',
                              os.path.basename(zip_path).replace(".zip", ".tif"))
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    stack_bands_from_zip(zip_path=zip_path, output_dir=output_dir, output_file=output_file,
                                    bands_to_stack=["B01", "B02", "B03", "B04", "B05"])

if __name__ == '__main__':
    main()