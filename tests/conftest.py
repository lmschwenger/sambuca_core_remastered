"""Test configuration for sambuca_core tests."""

import sys
import os
from pathlib import Path

# Add the project root to Python path so we can import sambuca modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import pytest and configure it
import pytest
import numpy as np

# Configure numpy error handling for tests
np.seterr(all='warn')

# Common test fixtures can be added here if needed
@pytest.fixture
def temp_directory():
    """Provide a temporary directory for tests."""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_wavelengths():
    """Standard wavelengths for testing."""
    return np.array([443, 490, 560, 665])

@pytest.fixture
def sample_reflectance():
    """Sample reflectance values for testing."""
    return np.array([0.05, 0.08, 0.06, 0.03])

@pytest.fixture
def basic_siops():
    """Basic SIOP values for testing."""
    return {
        'a_water': np.array([0.01, 0.02, 0.1, 0.5]),
        'a_ph_star': np.array([0.05, 0.03, 0.02, 0.01]),
        'substrate1': np.array([0.1, 0.2, 0.3, 0.4])
    }
