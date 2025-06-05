Examples & Tutorials
====================

This section provides comprehensive examples and tutorials demonstrating SAMBUCA Core's capabilities in real-world applications.

.. toctree::
   :maxdepth: 2

   basic_usage
   advanced_examples
   tutorials

Getting Started with Examples
-----------------------------

The examples are organized from basic to advanced, covering:

**Basic Usage**
   Simple forward modeling and inversion examples

**Advanced Examples**
   Real satellite data processing, validation studies, and custom applications

**Tutorials**
   Step-by-step guides for specific use cases

Quick Navigation
---------------

**I want to...**

🎯 **Learn the basics**
   → :doc:`basic_usage`

🛰️ **Process real satellite data**
   → :doc:`advanced_examples`

📚 **Follow detailed tutorials**
   → :doc:`tutorials`

Example Categories
------------------

Forward Modeling Examples
~~~~~~~~~~~~~~~~~~~~~~~~~

- Single spectrum simulation
- Parameter sensitivity studies
- Multi-sensor comparisons
- Custom SIOP development

Inversion Examples
~~~~~~~~~~~~~~~~~

- Single pixel analysis
- Image processing workflows
- Uncertainty quantification
- Validation against field data

Real Data Applications
~~~~~~~~~~~~~~~~~~~~~

- Sentinel-2 processing
- Landsat time series
- Coral reef mapping
- Coastal water quality monitoring

All examples include:

✅ **Complete working code**  
✅ **Sample data** (where possible)  
✅ **Expected outputs**  
✅ **Troubleshooting tips**  
✅ **Extension ideas**

Jupyter Notebooks
-----------------

Interactive Jupyter notebooks are available for most examples:

- ``examples/notebooks/01_basic_forward_model.ipynb``
- ``examples/notebooks/02_single_pixel_inversion.ipynb``
- ``examples/notebooks/03_image_processing.ipynb``
- ``examples/notebooks/04_validation_study.ipynb``

To run the notebooks:

.. code-block:: bash

   # Install Jupyter
   pip install jupyter ipywidgets

   # Start Jupyter server
   jupyter notebook examples/notebooks/

Data Requirements
----------------

Examples use a combination of:

- **Synthetic data** - Generated within the examples
- **Sample datasets** - Small representative files included
- **Public data** - Links to download real satellite data
- **Test data** - Validation datasets with known answers

Some examples require downloading additional data. Instructions are provided in each example.

Learning Path
-------------

**Beginner** (New to SAMBUCA)
   1. :doc:`basic_usage` - Start here for fundamental concepts
   2. Basic forward modeling examples
   3. Simple inversion examples

**Intermediate** (Familiar with basics)
   1. :doc:`advanced_examples` - Real data processing
   2. Validation and uncertainty analysis
   3. Custom sensor configurations

**Advanced** (Research/Development)
   1. :doc:`tutorials` - Detailed case studies
   2. Algorithm modifications
   3. Integration with other tools

Contributing Examples
--------------------

We welcome contributed examples! To add your example:

1. **Create a new example** following the template
2. **Include complete documentation** with explanations
3. **Test thoroughly** on different systems
4. **Submit a pull request** with your contribution

Example Template:

.. code-block:: python

   """
   Example Title: Brief description
   
   This example demonstrates [main concept].
   
   Requirements:
   - sambuca_core
   - additional packages if needed
   
   Data:
   - Source and download instructions
   
   Expected output:
   - Description of results
   """
   
   # Your example code here

Support and Discussion
---------------------

Need help with examples?

💬 **GitHub Discussions**: Community Q&A and examples sharing  
🐛 **GitHub Issues**: Report bugs in examples  
📧 **Contact**: Direct questions to the development team

Ready to start? Begin with :doc:`basic_usage` for fundamental examples, or jump to :doc:`advanced_examples` for real-world applications.
