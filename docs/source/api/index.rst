API Reference
=============

This section provides comprehensive documentation for all SAMBUCA Core modules, classes, and functions.

Core Modules
------------

.. toctree::
   :maxdepth: 2

   core
   forward_model
   siop_manager
   inversion
   gui

Module Overview
---------------

:doc:`core`
   Main module containing the primary SAMBUCA functionality, exceptions, and utility functions.

:doc:`forward_model`
   Semi-analytical radiative transfer forward model implementation.

:doc:`siop_manager`
   Management of Spectral Inherent Optical Properties for different sensors.

:doc:`inversion`
   Inversion algorithms for estimating water properties from reflectance spectra.

:doc:`gui`
   Graphical user interface components for interactive analysis.

Quick Reference
---------------

Essential Classes and Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Core Functions:**

.. autosummary::
   sambuca.core.forward_model
   sambuca.core.SIOPManager
   sambuca.core.list_data_fetchers

**Results Classes:**

.. autosummary::
   sambuca.core.ForwardModelResults

**Exception Classes:**

.. autosummary::
   sambuca.core.SambucaException
   sambuca.core.UnsupportedDataFormatError
   sambuca.core.DataValidationError

Import Patterns
~~~~~~~~~~~~~~~

The recommended import patterns for SAMBUCA Core:

.. code-block:: python

   # Standard import
   import sambuca.core as sbc

   # Core functionality
   from sambuca.core import forward_model, SIOPManager, ForwardModelResults

   # Inversion functionality  
   from sambuca.core.inversion import InversionParameters, invert_spectrum, process_image

   # Exceptions
   from sambuca.core import SambucaException, DataValidationError

   # GUI (if installed)
   from sambuca.gui import launch_gui

Complete API Documentation
--------------------------

For complete details on each module, see the individual API documentation pages linked above.
