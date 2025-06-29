# SAMBUCA Utils

Utility package for SAMBUCA (Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment).

## Overview

This package provides utility functions and modules for the SAMBUCA ecosystem. Currently, this is an empty package that serves as a foundation for future utility implementations.

## Installation

Install from source:

```bash
# Navigate to package directory
cd sambuca_utils

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

## Usage

```python
import sambuca_utils

# Package is currently empty but ready for extension
print(sambuca_utils.__version__)
```

## Development

To contribute to this package:

```bash
# Install with development dependencies
pip install -e .[dev]

# Run tests (when available)
pytest

# Format code
black sambuca_utils/
isort sambuca_utils/

# Type checking
mypy sambuca_utils/
```

## Requirements

- Python >= 3.8
- numpy >= 1.20.0

## License

MIT License - see the main project repository for details.

## Related Packages

This package is part of the SAMBUCA ecosystem:
- [sambuca-core](https://github.com/lmschwenger/sambuca_core_remastered) - Main SAMBUCA package

## Contributing

This package follows standard Python development practices. Please refer to the main repository for contribution guidelines.
