#!/usr/bin/env python3
"""
Sambuca Core GUI Launcher Script

Simple launcher to start the Sambuca Core GUI from the project root.
"""

import sys
from pathlib import Path


def main():
    """Launch the Sambuca Core GUI."""
    # Get the project root directory
    project_root = Path(__file__).parent

    # Add project root to Python path
    sys.path.insert(0, str(project_root))

    try:
        # Import and run the GUI
        from sambuca.gui.app import SambucaGuiApp

        print("Starting Sambuca Core GUI...")
        app = SambucaGuiApp()
        app.run()

    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("\nPlease ensure:")
        print("1. You're in the sambuca_core_remastered directory")
        print("2. All dependencies are installed (tkinter, matplotlib, numpy)")
        print("3. The sambuca_core module is available")
        return 1

    except Exception as e:
        print(f"Error starting GUI: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
