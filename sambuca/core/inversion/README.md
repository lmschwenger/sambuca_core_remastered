# Sambuca Core Inversion Module

The inversion module for Sambuca Core provides tools to derive water column properties from observed remote sensing reflectance. This module implements various approaches for inverting the Sambuca forward model, allowing you to determine parameters like water depth, chlorophyll concentration, CDOM, and substrate composition from spectral data.

## Overview

The inversion process works by finding the combination of input parameters that, when run through the forward model, produces the closest match to observed spectral data. This module provides multiple approaches to solve this inverse problem:

1. **Optimization-based Inversion**: Uses numerical optimization techniques to find the best-fitting parameters.
2. **Look-Up Table (LUT) Approach**: Pre-computes model results for many parameter combinations and finds the closest match.
3. **Hybrid Approaches**: Combines LUT and optimization for efficient and accurate inversion.

## Module Components

- `parameters.py`: Definition of inversion parameters, bounds, and conversion utilities
- `objective_functions.py`: Error metrics between observed and modeled spectra
- `optimization.py`: Optimization-based inversion using scipy
- `lut.py`: Look-up table generation and searching
- `pixel_processor.py`: Tools for processing entire images

## Usage Examples

### Basic Optimization-based Inversion

```python
from sambuca_core import forward_model
from sambuca_core.inversion import InversionParameters, invert_spectrum

# Define inversion parameters (which to invert for, which to keep fixed)
params = InversionParameters(
    # Parameters to invert for (with bounds)
    chl=(0.1, 10.0),           # Chlorophyll concentration
    cdom=(0.01, 2.0),          # CDOM concentration
    depth=(0.1, 25.0),         # Water depth
    
    # Fixed model parameters
    wavelengths=wavelengths,    # Spectrum wavelengths
    a_water=a_water,           # Water absorption coefficient
    a_ph_star=a_ph_star,       # Specific phytoplankton absorption
    substrate1=substrate1       # Bottom substrate reflectance
)

# Run inversion
result = invert_spectrum(observed_rrs, params)

# Access results
print("Inverted parameters:")
print(f"  Chlorophyll: {result.parameters['chl']} mg/m³")
print(f"  CDOM: {result.parameters['cdom']} 1/m")
print(f"  Depth: {result.parameters['depth']} m")
print(f"  Error: {result.objective_value}")

# Plot observed vs. modeled spectra
plt.figure()
plt.plot(wavelengths, observed_rrs, 'o', label='Observed')
plt.plot(wavelengths, result.modeled_spectra, '-', label='Modeled')
plt.legend()
plt.show()
```

### Look-Up Table Approach

```python
from sambuca_core.inversion import LookUpTable

# Create and build LUT
lut = LookUpTable(params)
lut.build_table(grid_size=[10, 10, 20])  # Specify grid density per parameter

# Save for later use
lut.save("sambuca_lut.pkl")

# Load existing LUT
lut = LookUpTable.load("sambuca_lut.pkl")

# Invert using LUT with refinement
result = lut.invert(observed_rrs, refine=True)

print("LUT-based inversion results:")
print(f"  Chlorophyll: {result['parameters']['chl']} mg/m³")
print(f"  CDOM: {result['parameters']['cdom']} 1/m")
print(f"  Depth: {result['parameters']['depth']} m")
```

### Processing an Image

```python
from sambuca_core.inversion import process_image

# Process an image (all pixels)
results = process_image(
    hyperspectral_image,    # Shape (height, width, bands)
    params,                 # InversionParameters object
    lut=lut,                # Optional LUT for faster processing
    n_processes=4           # Number of parallel processes
)

# Access parameter maps
depth_map = results['depth']         # Shape (height, width)
chlorophyll_map = results['chl']     # Shape (height, width)
error_map = results['error']         # Shape (height, width)

# Visualize results
plt.figure()
plt.imshow(depth_map, cmap='viridis')
plt.colorbar(label='Depth (m)')
plt.title('Bathymetry Map')
plt.show()
```

## Best Practices

1. **Parameter Bounds**: Set realistic bounds for parameters based on your study area.
2. **Multiple Starting Points**: Use `multi_start_inversion()` to avoid local minima.
3. **LUT Resolution**: For LUTs, balance grid density with memory usage and computation time.
4. **Refinement**: Use LUT with refinement (`refine=True`) for better accuracy.
5. **Parallelization**: For large images, use multiple processes and/or batch processing.

## Advanced Usage

For advanced usage, you can:

- Create custom objective functions
- Implement uncertainty estimation
- Add constraints to the optimization process
- Incorporate spatial context in the inversion

See the examples directory for more detailed examples.