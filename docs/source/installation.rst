Installation Guide
==================

This guide covers various methods for installing SAMBUCA Core Remastered, from basic usage to development setup.

Requirements
------------

System Requirements
~~~~~~~~~~~~~~~~~~~

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum, 8GB+ recommended for large image processing
- **Storage**: 500MB free space for installation and data

Core Dependencies
~~~~~~~~~~~~~~~~~

SAMBUCA Core requires the following Python packages:

.. code-block:: text

   numpy>=1.20.0         # Scientific computing
   scipy>=1.7.0          # Optimization and signal processing
   pandas>=1.3.0         # Data manipulation
   matplotlib>=3.5.0     # Plotting and visualization

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

Additional packages for enhanced functionality:

.. code-block:: text

   # Geospatial data handling
   rasterio>=1.2.0       # Satellite image I/O
   gdal                  # Geospatial data abstraction library

   # Performance and UI
   tqdm>=4.60.0          # Progress bars
   numba>=0.56.0         # Fast numerical computations
   scikit-optimize>=0.9.0 # Advanced optimization methods

   # Development tools
   pytest>=6.0.0         # Testing framework
   black>=21.0.0         # Code formatting
   sphinx>=4.0.0         # Documentation generation

Installation Methods
--------------------

Method 1: Direct from GitHub (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install directly from the GitHub repository for the latest version:

**Basic Installation:**

.. code-block:: bash

   pip install git+https://github.com/lmschwenger/sambuca_core_remastered.git

**With GUI Support:**

.. code-block:: bash

   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[gui]"

**Complete Installation (All Features):**

.. code-block:: bash

   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

Method 2: Clone and Install from Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more control or development purposes:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/lmschwenger/sambuca_core_remastered.git
   cd sambuca_core_remastered

   # Basic installation
   pip install -e .

   # Or with specific feature sets
   pip install -e .[gui]         # GUI support
   pip install -e .[raster]      # Raster processing
   pip install -e .[complete]    # All features

Installation Options
--------------------

SAMBUCA Core provides several installation options to suit different needs:

Core Installation
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .

Includes only the essential dependencies for forward modeling and basic inversion.

GUI Installation
~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .[gui]

Adds GUI dependencies for the graphical interface:

- Enhanced matplotlib support
- Tkinter integration (usually included with Python)

Raster Processing
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .[raster]

Adds geospatial data handling capabilities:

- rasterio for satellite image I/O
- GDAL for geospatial operations

Complete Installation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .[complete]

Includes all optional dependencies for full functionality:

- GUI support
- Raster processing
- Performance optimizations
- Jupyter notebook support

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .[dev]

Includes development tools:

- Testing frameworks (pytest)
- Code formatting (black, flake8)
- Type checking (mypy)
- Documentation tools (sphinx)

Platform-Specific Instructions
------------------------------

Windows
~~~~~~~

1. **Install Python 3.8+** from `python.org <https://python.org/downloads/>`_
2. **Open Command Prompt or PowerShell**
3. **Install SAMBUCA Core**:

   .. code-block:: batch

      pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

4. **For GUI support**, ensure tkinter is available (usually included with Python on Windows)

**Note for GDAL**: If you need raster processing capabilities, consider using conda:

.. code-block:: batch

   conda install -c conda-forge gdal rasterio
   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git"

macOS
~~~~~

1. **Install Python 3.8+** (recommended via Homebrew):

   .. code-block:: bash

      brew install python

2. **Install SAMBUCA Core**:

   .. code-block:: bash

      pip3 install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

3. **For GUI support**, ensure tkinter is available:

   .. code-block:: bash

      # If using Homebrew Python, tkinter should be included
      # If issues occur, install python-tk
      brew install python-tk

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~~~~

1. **Install Python and pip**:

   .. code-block:: bash

      sudo apt update
      sudo apt install python3 python3-pip python3-tk

2. **Install GDAL (optional, for raster processing)**:

   .. code-block:: bash

      sudo apt install gdal-bin libgdal-dev

3. **Install SAMBUCA Core**:

   .. code-block:: bash

      pip3 install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

Linux (CentOS/RHEL)
~~~~~~~~~~~~~~~~~~~

1. **Install Python and development tools**:

   .. code-block:: bash

      sudo yum install python3 python3-pip tkinter

2. **Install SAMBUCA Core**:

   .. code-block:: bash

      pip3 install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

Conda Installation (Alternative)
---------------------------------

For users who prefer conda package management:

.. code-block:: bash

   # Create a new environment
   conda create -n sambuca python=3.9
   conda activate sambuca

   # Install scientific computing stack
   conda install -c conda-forge numpy scipy pandas matplotlib rasterio gdal

   # Install SAMBUCA Core
   pip install git+https://github.com/lmschwenger/sambuca_core_remastered.git

Verifying Installation
----------------------

After installation, verify that SAMBUCA Core is working correctly:

**Basic Test:**

.. code-block:: bash

   python -c "import sambuca.core as sbc; print(f'SAMBUCA Core v{sbc.__version__} installed successfully')"

**Run Built-in Tests:**

.. code-block:: bash

   python -m sambuca.core

**Launch GUI (if installed with GUI support):**

.. code-block:: bash

   sambuca-gui

**Test Forward Model:**

.. code-block:: python

   import sambuca.core as sbc
   import numpy as np

   # Create test data
   wavelengths = [492.4, 559.8, 664.6, 704.1]  # Sentinel-2 bands
   a_water = [0.007, 0.015, 0.325, 0.619]
   a_ph_star = [0.055, 0.023, 0.014, 0.010]
   substrate = [0.3, 0.3, 0.25, 0.2]

   # Run forward model
   results = sbc.forward_model(
       chl=1.5, cdom=0.5, nap=2.0, depth=5.0,
       substrate1=substrate, wavelengths=wavelengths,
       a_water=a_water, a_ph_star=a_ph_star,
       num_bands=len(wavelengths)
   )

   print(f"Forward model successful! RRS: {results.rrs}")

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**ImportError: No module named 'tkinter'**

Solution for Linux:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install python3-tk

   # CentOS/RHEL
   sudo yum install tkinter

**GDAL installation issues**

GDAL can be challenging to install. Try using conda:

.. code-block:: bash

   conda install -c conda-forge gdal rasterio

**Permission errors on Linux/macOS**

Use user installation:

.. code-block:: bash

   pip install --user "git+https://github.com/lmschwenger/sambuca_core_remastered.git"

**Version conflicts**

Create a virtual environment:

.. code-block:: bash

   python -m venv sambuca_env
   source sambuca_env/bin/activate  # On Windows: sambuca_env\\Scripts\\activate
   pip install "git+https://github.com/lmschwenger/sambuca_core_remastered.git[complete]"

Getting Help
~~~~~~~~~~~~

If you encounter installation issues:

1. **Check the error message** for specific missing dependencies
2. **Update pip**: ``pip install --upgrade pip``
3. **Try a fresh virtual environment**
4. **Consult the GitHub issues**: `SAMBUCA Issues <https://github.com/lmschwenger/sambuca_core_remastered/issues>`_
5. **Ask for help**: `GitHub Discussions <https://github.com/lmschwenger/sambuca_core_remastered/discussions>`_

Next Steps
----------

After successful installation:

1. **Read the** :doc:`quickstart` **guide** for a rapid introduction
2. **Explore the** :doc:`user_guide/getting_started` **for detailed tutorials**
3. **Check out the** :doc:`examples/index` **for practical applications**
4. **Launch the GUI** with ``sambuca-gui`` for interactive exploration

Development Setup
-----------------

For contributors and developers:

.. code-block:: bash

   # Clone repository
   git clone https://github.com/lmschwenger/sambuca_core_remastered.git
   cd sambuca_core_remastered

   # Create development environment
   python -m venv dev_env
   source dev_env/bin/activate  # On Windows: dev_env\\Scripts\\activate

   # Install with development dependencies
   pip install -e .[dev]

   # Run tests
   pytest tests/

   # Check code style
   black sambuca/
   flake8 sambuca/

   # Build documentation
   cd docs_readthedocs
   make html
