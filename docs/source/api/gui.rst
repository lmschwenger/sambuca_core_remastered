GUI Module
==========

.. automodule:: sambuca_core.gui
   :members:
   :undoc-members:
   :show-inheritance:

The GUI module provides a graphical user interface for interactive SAMBUCA analysis and visualization.

Overview
--------

The SAMBUCA GUI offers an intuitive interface for:

- **Interactive forward modeling** with real-time parameter adjustment
- **Single pixel inversion** with result visualization
- **SIOP library management** and spectral visualization
- **Batch processing** configuration and monitoring
- **Result analysis** and export capabilities

Main Components
--------------

Application Entry Point
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: sambuca_core.gui.main

Main entry point for launching the GUI application.

Core GUI Classes
~~~~~~~~~~~~~~~

.. autoclass:: sambuca_core.gui.MainWindow
   :members:
   :undoc-members:
   :show-inheritance:

The main application window containing all GUI components.

.. autoclass:: sambuca_core.gui.ForwardModelPanel
   :members:
   :undoc-members:
   :show-inheritance:

Panel for interactive forward model experimentation.

.. autoclass:: sambuca_core.gui.InversionPanel
   :members:
   :undoc-members:
   :show-inheritance:

Panel for single pixel and batch inversion operations.

.. autoclass:: sambuca_core.gui.SIOPPanel
   :members:
   :undoc-members:
   :show-inheritance:

Panel for SIOP library management and visualization.

Launching the GUI
----------------

Command Line
~~~~~~~~~~~

.. code-block:: bash

   # Launch GUI directly
   sambuca-gui

   # Or using Python module
   python -m sambuca_core.gui

   # Or from Python script
   python run_gui.py

From Python
~~~~~~~~~~

.. code-block:: python

   from sambuca_core.gui import main
   
   # Launch GUI
   main()

   # Or with specific configuration
   main(config_file='my_config.json')

GUI Features
-----------

Forward Model Tab
~~~~~~~~~~~~~~~~

**Interactive Parameters**
   - Sliders for real-time parameter adjustment
   - Numeric input fields for precise values
   - Parameter bounds configuration

**Real-time Visualization**
   - Spectral reflectance plots
   - Absorption and backscatter components
   - Substrate contribution visualization

**Sensor Configuration**
   - Dropdown for common sensors (Sentinel-2, Landsat, MODIS)
   - Custom wavelength configuration
   - SIOP library selection

.. code-block:: python

   # Programmatic access to forward model panel
   from sambuca_core.gui import ForwardModelPanel
   
   panel = ForwardModelPanel()
   panel.set_parameters(chl=2.0, cdom=0.5, nap=1.5, depth=8.0)
   panel.update_display()

Inversion Tab
~~~~~~~~~~~~

**Single Pixel Analysis**
   - Paste or load observed reflectance values
   - Interactive parameter bound setting
   - Real-time optimization progress
   - Spectral fit visualization

**Batch Processing**
   - Image file selection and preview
   - Processing parameter configuration
   - Progress monitoring and cancel options
   - Result visualization and export

**Quality Control**
   - Automatic quality metrics calculation
   - Error map visualization
   - Statistical summaries

.. code-block:: python

   # Programmatic inversion control
   from sambuca_core.gui import InversionPanel
   
   panel = InversionPanel()
   panel.load_observed_spectrum([0.012, 0.015, 0.008, 0.006])
   panel.set_parameter_bounds(depth=(0, 20), chl=(0.1, 10))
   result = panel.run_inversion()

SIOP Management Tab
~~~~~~~~~~~~~~~~~~

**Library Browser**
   - Tree view of available SIOP libraries
   - Spectral plot preview
   - Library metadata display

**Sensor Registration**
   - Add new sensor configurations
   - Wavelength input and validation
   - Interpolation quality assessment

**Library Import/Export**
   - Load external SIOP files
   - Export interpolated libraries
   - Format conversion utilities

.. code-block:: python

   # SIOP panel operations
   from sambuca_core.gui import SIOPPanel
   
   panel = SIOPPanel()
   panel.load_siop_directory("path/to/siops")
   panel.register_sensor("Custom", [400, 500, 600, 700])
   panel.export_sensor_siops("Custom", "output_file.csv")

Configuration and Preferences
----------------------------

Settings Management
~~~~~~~~~~~~~~~~~~

The GUI maintains user preferences and settings:

**Application Settings**
   - Default directories for data and output
   - Processing preferences (cores, chunk size)
   - Visualization options (color schemes, plot styles)

**Parameter Defaults**
   - Default parameter bounds for different regions
   - Preferred optimization algorithms
   - Quality control thresholds

.. code-block:: python

   # Access settings programmatically
   from sambuca_core.gui import Settings
   
   settings = Settings()
   settings.set('default_data_dir', '/path/to/data')
   settings.set('default_cores', 4)
   settings.save()

Project Management
~~~~~~~~~~~~~~~~~

**Save/Load Projects**
   - Complete analysis state preservation
   - Parameter configuration export
   - Result archiving

**Recent Files**
   - Quick access to recent data files
   - Project history management

.. code-block:: python

   # Project operations
   from sambuca_core.gui import Project
   
   project = Project()
   project.load_parameters('analysis_config.json')
   project.add_result('depth_map.tif')
   project.save('my_analysis.sambuca')

Visualization Components
-----------------------

Interactive Plots
~~~~~~~~~~~~~~~~

**Spectral Plots**
   - Real-time updating spectral curves
   - Component decomposition views
   - Zoom and pan capabilities
   - Export to common formats

**Parameter Maps**
   - False-color parameter visualizations
   - Adjustable color scales
   - Overlay capabilities
   - Zoom and profile tools

**Quality Plots**
   - Error distribution histograms
   - Scatter plots for validation
   - Statistical summary displays

.. code-block:: python

   # Custom plot configuration
   from sambuca_core.gui.plots import SpectralPlot
   
   plot = SpectralPlot()
   plot.set_wavelengths([492, 560, 665, 704])
   plot.add_spectrum('observed', [0.012, 0.015, 0.008, 0.006])
   plot.add_spectrum('modeled', [0.011, 0.016, 0.007, 0.005])
   plot.update_display()

Export Capabilities
~~~~~~~~~~~~~~~~~~

**Image Export**
   - High-resolution plot export
   - Multiple format support (PNG, PDF, SVG)
   - Custom size and DPI settings

**Data Export**
   - Parameter maps as GeoTIFF
   - Results as CSV tables
   - Configuration files for reproducibility

Customization and Extensions
---------------------------

Plugin Architecture
~~~~~~~~~~~~~~~~~~

The GUI supports plugins for extended functionality:

.. code-block:: python

   # Example plugin structure
   from sambuca_core.gui.plugin import Plugin
   
   class CustomAnalysisPlugin(Plugin):
       def __init__(self):
           super().__init__()
           self.name = "Custom Analysis"
           self.version = "1.0"
       
       def create_panel(self):
           # Return custom GUI panel
           pass
       
       def process_data(self, data):
           # Custom processing logic
           pass

Custom Widgets
~~~~~~~~~~~~~

Create custom widgets for specialized functionality:

.. code-block:: python

   from sambuca_core.gui.widgets import ParameterWidget
   
   class CustomParameterWidget(ParameterWidget):
       def __init__(self, parent=None):
           super().__init__(parent)
           self.setup_ui()
       
       def setup_ui(self):
           # Custom widget layout
           pass

Scripting Interface
~~~~~~~~~~~~~~~~~~

Automate GUI operations through scripting:

.. code-block:: python

   from sambuca_core.gui import AutomationScript
   
   script = AutomationScript()
   script.load_data('sentinel2_image.tif')
   script.set_parameters(depth=(0, 20), chl=(0.1, 10))
   script.run_processing()
   script.export_results('output_directory')

Troubleshooting
--------------

Common GUI Issues
~~~~~~~~~~~~~~~~

**Issue**: GUI doesn't start

**Solutions**:
- Check tkinter installation
- Verify matplotlib backend
- Update to latest Python version

**Issue**: Slow performance

**Solutions**:
- Reduce plot update frequency
- Limit displayed data points
- Close unused tabs/panels

**Issue**: Memory errors with large images

**Solutions**:
- Enable memory-efficient processing
- Reduce chunk sizes
- Use 64-bit Python

Debug Mode
~~~~~~~~~

Enable debugging for troubleshooting:

.. code-block:: bash

   # Launch with debug output
   sambuca-gui --debug

   # Enable verbose logging
   sambuca-gui --verbose

.. code-block:: python

   # Programmatic debugging
   from sambuca_core.gui import main
   
   main(debug=True, log_level='DEBUG')

Keyboard Shortcuts
------------------

Common shortcuts for efficient operation:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+O``
     - Open file
   * - ``Ctrl+S``
     - Save project
   * - ``Ctrl+R``
     - Run processing
   * - ``Ctrl+E``
     - Export results
   * - ``F5``
     - Refresh displays
   * - ``Ctrl+Z``
     - Undo last action
   * - ``Ctrl+Q``
     - Quit application

System Requirements
------------------

**Minimum Requirements**
   - Python 3.8+
   - 4GB RAM
   - 1GB free disk space
   - Graphics support for matplotlib

**Recommended**
   - Python 3.9+
   - 8GB+ RAM
   - Multi-core processor
   - High-resolution display

**Operating Systems**
   - Windows 10/11
   - macOS 10.14+
   - Linux (Ubuntu 18.04+, CentOS 7+)

Installation Notes
-----------------

GUI-specific installation requirements:

.. code-block:: bash

   # Install with GUI support
   pip install "sambuca-core[gui]"

   # On Linux, may need additional packages
   sudo apt-get install python3-tk

   # On macOS with Homebrew
   brew install python-tk

   # Verify GUI installation
   python -c "import tkinter; print('GUI support available')"

See Also
--------

- :doc:`../user_guide/getting_started` for GUI usage tutorials
- :doc:`../installation` for GUI installation instructions
- :doc:`core` for underlying functionality
- :doc:`../examples/basic_usage` for GUI workflow examples

**Note**: The GUI module is optional and requires additional dependencies. Install with ``pip install "sambuca-core[gui]"`` to enable GUI functionality.
