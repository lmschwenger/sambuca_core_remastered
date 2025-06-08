#!/usr/bin/env python3
"""Setup script for SAMBUCA Core Remastered.

Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment
"""

from pathlib import Path

from setuptools import setup, find_packages

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment (SAMBUCA)"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
else:
    # Fallback requirements
    requirements = [
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "pandas>=1.3.0",
        "matplotlib>=3.5.0",
    ]

# GUI-specific requirements
gui_requirements = [
    "matplotlib>=3.5.0",
    "numpy>=1.20.0",
]

# Optional requirements for enhanced functionality
extras_require = {
    "gui": gui_requirements,
    "raster": [
        "rasterio>=1.2.0",
        "gdal",
    ],
    "optimization": [
        "scikit-optimize>=0.9.0",
        "numba>=0.56.0",
    ],
    "progress": [
        "tqdm>=4.60.0",
    ],
    "notebooks": [
        "jupyter>=1.0.0",
        "ipywidgets>=7.6.0",
        "notebook>=6.4.0",
    ],
    "build": [
        "pyinstaller>=5.0.0",
    ],
    "dev": [
        "pytest>=6.0.0",
        "pytest-cov>=2.12.0",
        "black>=21.0.0",
        "flake8>=3.9.0",
        "mypy>=0.910",
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=0.5.0",
    ],
    "complete": [
        "rasterio>=1.2.0",
        "tqdm>=4.60.0",
        "scikit-optimize>=0.9.0",
        "numba>=0.56.0",
        "jupyter>=1.0.0",
        "ipywidgets>=7.6.0",
    ]
}

setup(
    name="sambuca-core",
    version="0.1.0",
    author="Lasse M. Schwenger",
    author_email="lasse.m.schwenger@gmail.com",
    description="Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lmschwenger/sambuca_core_remastered",
    project_urls={
        "Bug Tracker": "https://github.com/lmschwenger/sambuca_core_remastered/issues",
        "Documentation": "https://github.com/lmschwenger/sambuca_core_remastered/docs",
        "Source Code": "https://github.com/lmschwenger/sambuca_core_remastered",
        "Original SAMBUCA": "https://github.com/csiro-aquatic-remote-sensing/sambuca_core",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "sambuca-gui=sambuca.gui.app:main",
            "sambuca-core=sambuca.core:main",
            "sambuca-build=quick_build:main",
        ],
    },
    include_package_data=True,
    package_data={
        "sambuca.core": ["data/**/*"],
        "sambuca.gui": ["assets/**/*", "icons/**/*"],
    },
    zip_safe=False,
    keywords=[
        "remote sensing",
        "bathymetry",
        "ocean optics",
        "radiative transfer",
        "satellite imagery",
        "water quality",
        "SAMBUCA",
        "physics-based modeling",
        "semi-analytical",
    ],
    platforms=["any"],
    license="MIT",
)
