# Sambuca Core GUI

A minimal, modular graphical user interface for the Sambuca Core bathymetry processing library.

## Overview

The Sambuca Core GUI provides an intuitive interface for processing satellite imagery to create bathymetry maps. It supports both optimization-based and Look-Up Table (LUT) based processing methods.

## Features

- **Workflow Configuration**: Easy setup of input images, SIOP directories, and output locations
- **Parameter Tuning**: Adjust depth ranges, water column properties, and sensor settings
- **Processing Methods**: Choose between optimization and LUT-based processing
- **Results Visualization**: View depth maps, error maps, and statistical summaries
- **Modular Architecture**: Clean separation of views, controllers, and models

## Architecture

The GUI follows a Model-View-Controller (MVC) pattern with the following structure:

```
gui/
├── __init__.py              # Package initialization
├── app.py                   # Main application class
├── main.py                  # Entry point script
├── views/                   # GUI view components
│   ├── main_window.py       # Main application window
│   ├── workflow_panel.py    # Workflow configuration panel
│   ├── parameters_panel.py  # Parameter adjustment panel
│   └── results_panel.py     # Results display panel
├── controllers/             # Business logic controllers
│   └── workflow_controller.py # Workflow execution controller
├── models/                  # Data models
│   └── config_model.py      # Configuration management
└── components/              # Reusable UI components
    ├── progress_dialog.py   # Progress dialog component
    └── file_selector.py     # File selection component
```

## Installation & Usage

### Prerequisites

Ensure you have the following Python packages installed:
- `tkinter` (usually included with Python)
- `matplotlib`
- `numpy`
- `sambuca_core` (from the parent repository)

### Running the GUI

From the sambuca_core_remastered project root directory:

```bash
python run_gui.py
```

Or from within the gui directory:

```bash
python main.py
```

## Usage Guide

### 1. Workflow Configuration

1. **SIOP Directory**: Select the directory containing Specific Inherent Optical Properties (SIOP) files
2. **Input Image**: Choose the satellite image to process (TIFF format)
3. **Output Directory**: Select where to save the processing results
4. **Sensor**: Choose the satellite sensor (Sentinel-2, Landsat-8, etc.)
5. **Method**: Select processing method (optimization or LUT)

### 2. Parameter Configuration

Use the Parameters panel to adjust:
- **Depth Range**: Minimum and maximum expected depths
- **Water Column**: Chlorophyll, NAP, and CDOM concentrations
- **Substrate**: Substrate fraction parameters
- **Sensor Settings**: Wavelengths and band selections

### 3. Processing

1. Configure workflow and parameters
2. Click "Process Image" to start processing
3. Monitor progress through the progress bar
4. View results in the Results panel

### 4. Results

The Results panel provides:
- **Summary Tab**: Statistical summary of processing results
- **Visualization Tab**: Interactive plots of depth maps, error maps, and histograms

## Code Style

The GUI follows the established naming conventions:
- **Files**: `snake_case.py` containing one class per file
- **Classes**: `PascalCase` matching the filename pattern
- **Methods**: `snake_case` with leading underscores for private methods
- **Variables**: `snake_case` for consistency

## Extending the GUI

The modular architecture makes it easy to extend functionality:

1. **New Views**: Add new panel classes in `views/` following the existing pattern
2. **New Controllers**: Create specialized controllers in `controllers/` for new workflows
3. **New Components**: Add reusable UI components in `components/`
4. **Configuration**: Extend `ConfigModel` to handle new settings

## Example Integration

The GUI integrates seamlessly with your existing sambuca_core workflows. It essentially provides a graphical interface for operations like:

```python
# Your existing workflow code
workflow = BathymetryWorkflow(str(siop_dir), sensor='sentinel2')
workflow.customize_parameters(depth=(0, 25), fixed_chl=0.5, ...)
result = workflow.process_image(image_path, n_processes=4)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the correct directory and all dependencies are installed
2. **Path Issues**: Use absolute paths or ensure relative paths are correct
3. **Memory Issues**: Reduce the number of processes for large images
4. **Display Issues**: Ensure your system supports tkinter and matplotlib backends

### Error Reporting

Errors are displayed in message boxes and logged to the console. Check the terminal output for detailed error messages.

## Future Enhancements

Potential areas for expansion:
- Batch processing capabilities
- Advanced visualization options
- Configuration file import/export
- Plugin architecture for custom processing methods
- Integration with additional data sources

## Contributing

When adding new features:
1. Follow the existing naming conventions
2. Maintain the MVC architecture
3. Add appropriate error handling
4. Update this README as needed
