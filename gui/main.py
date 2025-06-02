#!/usr/bin/env python3
"""
Sambuca Core GUI Launcher

Main entry point for the Sambuca Core GUI application.
"""

import sys
import os
from pathlib import Path

# Add the sambuca_core_remastered directory to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from gui.app import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error importing GUI modules: {e}")
    print("Make sure you're running this from the sambuca_core_remastered directory")
    print("and that all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI: {e}")
    sys.exit(1)
