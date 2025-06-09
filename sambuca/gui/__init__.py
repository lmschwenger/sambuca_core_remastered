"""
Sambuca Core GUI Package

A minimal, modular GUI for the sambuca_core_remastered repository.
"""

from .app import SambucaGuiApp
from .views import MainWindow

__version__ = "0.1.0"
__all__ = ['MainWindow', 'SambucaGuiApp']
