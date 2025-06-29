#!/usr/bin/env python3
"""Setup script for SAMBUCA Utils.

Professional packaging configuration for sambuca_utils package.
"""

from pathlib import Path
from setuptools import setup, find_packages
import re


def get_version():
    """Extract version from package __init__.py file."""
    init_file = Path(__file__).parent / "sambuca_utils" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")
    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.MULTILINE)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string in __init__.py")


def get_long_description():
    """Read long description from README file."""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return __doc__


# Package metadata
NAME = "sambuca-utils"
DESCRIPTION = "Utility package for SAMBUCA with data fetching and visualization capabilities"
URL = "https://github.com/lmschwenger/sambuca_core_remastered"
AUTHOR = "Lasse M. Schwenger"
AUTHOR_EMAIL = "lasse.m.schwenger@gmail.com"
LICENSE = "MIT"

# Minimal requirements for base package
INSTALL_REQUIRES = [
    "numpy>=1.20.0",
    "matplotlib>=3.5.0",
    "copernicusmarine>=1.0.0",
    "xarray>=0.20.0",
    "rasterio>=1.2.0",
    "geopandas>=0.12.0",
    "shapely>=1.8.0",
    "pandas>=1.3.0",
    "scipy>=1.7.0",
]

# Optional dependencies
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=6.0.0",
        "pytest-cov>=2.12.0",
        "black>=22.0.0",
        "flake8>=4.0.0",
        "mypy>=0.910",
        "isort>=5.10.0",
    ],
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0",
    ],
}

# Classifiers for PyPI
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: GIS",
    "Topic :: Scientific/Engineering :: Image Processing",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities",
]

# Keywords for package discovery
KEYWORDS = [
    "sambuca",
    "remote sensing", 
    "bathymetry",
    "ocean optics",
    "data fetching",
    "satellite data",
    "sentinel-3",
    "visualization",
    "plotting",
    "matplotlib",
    "utilities",
    "scientific computing",
]

# Project URLs
PROJECT_URLS = {
    "Homepage": URL,
    "Bug Reports": f"{URL}/issues",
    "Source": URL,
    "Documentation": f"{URL}#readme",
}


if __name__ == "__main__":
    setup(
        name=NAME,
        version=get_version(),
        description=DESCRIPTION,
        long_description=get_long_description(),
        long_description_content_type="text/markdown",
        url=URL,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS,
        project_urls=PROJECT_URLS,
        packages=find_packages(exclude=["tests", "tests.*"]),
        python_requires=">=3.8",
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        include_package_data=True,
        zip_safe=False,
    )
