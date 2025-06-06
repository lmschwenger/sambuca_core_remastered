Core Module (sambuca.core)
===========================

.. automodule:: sambuca.core
   :members:
   :undoc-members:
   :show-inheritance:

The core module provides the main entry point and essential functionality for SAMBUCA Core.

Main Functions
--------------

.. autofunction:: sambuca.core.forward_model

.. autofunction:: sambuca.core.list_data_fetchers

Core Classes
------------

.. autoclass:: sambuca.core.SIOPManager
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: sambuca.core.ForwardModelResults
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. autoexception:: sambuca.core.SambucaException
   :members:
   :show-inheritance:

.. autoexception:: sambuca.core.UnsupportedDataFormatError
   :members:
   :show-inheritance:

.. autoexception:: sambuca.core.DataValidationError
   :members:
   :show-inheritance:

.. autoexception:: sambuca.core.DataFetchError
   :members:
   :show-inheritance:

.. autoexception:: sambuca.core.MissingDependencyError
   :members:
   :show-inheritance:

Utility Functions
-----------------

.. autofunction:: sambuca.core.strictly_decreasing

.. autofunction:: sambuca.core.strictly_increasing

Type Definitions
----------------

The module defines several type aliases for documentation and type hints:

.. py:data:: Spectra
   :type: Tuple[List[float], List[float]]

   Type alias for spectral data: (wavelengths, values)

.. py:data:: SpectraDict
   :type: Dict[str, Spectra]

   Type alias for dictionary of spectral data

Constants
---------

.. autodata:: sambuca.core.__version__
   :annotation: = "0.1.0"

   Current version of SAMBUCA Core

.. autodata:: sambuca_core.__author__
   :annotation: = "Lasse M. Schwenger"

   Package author

Module Details
--------------

The sambuca_core module serves as the main entry point for the SAMBUCA modeling system. It provides:

1. **Forward modeling capabilities** through the :func:`forward_model` function
2. **SIOP management** via the :class:`SIOPManager` class  
3. **Exception handling** with custom exception classes
4. **Utility functions** for data validation and processing
5. **Optional data fetchers** for satellite data integration

Usage Examples
--------------

Basic Forward Model
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sambuca_core as sbc
   
   # Basic forward model usage
   results = sbc.forward_model(
       chl=1.5, cdom=0.5, nap=2.0, depth=5.0,
       substrate1=[0.3, 0.3, 0.25, 0.2],
       wavelengths=[492.4, 559.8, 664.6, 704.1],
       a_water=[0.007, 0.015, 0.325, 0.619],
       a_ph_star=[0.055, 0.023, 0.014, 0.010],
       num_bands=4
   )
   
   print(f"Modeled reflectance: {results.rrs}")

SIOP Manager Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Initialize SIOP manager
   siop_manager = sbc.SIOPManager("data/")
   
   # Register sensor
   siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])
   
   # Get interpolated SIOPs
   siops = siop_manager.get_standard_siops("Sentinel-2")

Exception Handling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   try:
       results = sbc.forward_model(...)
   except sbc.DataValidationError as e:
       print(f"Invalid input data: {e}")
   except sbc.SambucaException as e:
       print(f"SAMBUCA error: {e}")

Data Fetcher Information
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Check available data fetchers
   fetchers = sbc.list_data_fetchers()
   for name, info in fetchers.items():
       status = "✓" if info.get('available', False) else "✗"
       print(f"{status} {info.get('name', name)}")

See Also
--------

- :doc:`forward_model` for detailed forward model documentation
- :doc:`siop_manager` for SIOP management details
- :doc:`inversion` for inversion algorithms
- :doc:`../user_guide/getting_started` for usage tutorials
