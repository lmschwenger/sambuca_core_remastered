# SAMBUCA Utils - Workflows

This directory contains high-level workflow classes that combine SAMBUCA core functionality for common tasks.

## Workflows

### BathymetryWorkflow
The primary workflow for satellite-derived bathymetry processing.

**Features:**
- Automatic setup with sensible defaults for bathymetry retrieval
- Support for multiple sensors (Sentinel-2, Landsat-8)
- Parameter customization for different environments
- Image processing with optional water masking
- Single pixel analysis for validation
- RGB preview generation

**Example usage:**
```python
from sambuca_utils.workflows import BathymetryWorkflow

# Create workflow
workflow = BathymetryWorkflow('/path/to/siops', sensor='sentinel2')

# Customize parameters
workflow.customize_parameters(
    depth=(0, 20),
    fixed_chl=0.5,
    fixed_nap=0.001
)

# Process image
result = workflow.process_image(
    image_path='/path/to/satellite/image.tif',
    n_processes=4,
    progress_bar=True
)

# Save results
result.save_all_parameters('/path/to/output')
```

## Dependencies

The workflows module depends on:
- `sambuca.core.inversion` - for inversion parameters and processing
- `sambuca.core.results` - for result objects
- `sambuca.core.siop_manager` - for spectral library management
- `sambuca_utils.io` - for image loading and preprocessing

## Migration from sambuca.core.workflows

These workflows were moved from `sambuca.core.workflows` to improve modularity. 
To update existing code:

```python
# Old import
from sambuca.core.workflows import BathymetryWorkflow

# New import
from sambuca_utils.workflows import BathymetryWorkflow
```

## Testing

Tests for workflows are located in:
- `sambuca_utils/tests/unit/test_workflows.py` - Unit tests
- `sambuca_utils/tests/integration/test_bathymetry_workflow_integration.py` - Integration tests

Run tests with:
```bash
pytest sambuca_utils/tests/
```
