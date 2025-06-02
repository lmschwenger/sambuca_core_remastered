"""
Configuration Model

Model for handling GUI configuration and settings.
"""

import json
from pathlib import Path
from typing import Dict, Any


class ConfigModel:
    """Model for managing GUI configuration."""
    
    def __init__(self, config_file: str = "sambuca_gui_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        
        # Load existing config if available
        if self.config_file.exists():
            self.load_config()
            
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            'window': {
                'width': 1000,
                'height': 700,
                'title': 'Sambuca Core - Bathymetry Processing GUI'
            },
            'paths': {
                'last_siop_dir': '',
                'last_image_dir': '',
                'last_output_dir': ''
            },
            'processing': {
                'default_sensor': 'sentinel2',
                'default_method': 'optimization',
                'default_processes': 4
            },
            'parameters': {
                'depth_min': 0.0,
                'depth_max': 25.0,
                'fixed_chl': 0.5,
                'fixed_nap': 0.001,
                'fixed_cdom': 0.0025,
                'fixed_substrate_fraction': 1.0,
                'wavelengths': [492.4, 559.8, 664.6, 704.1],
                'bands': [2, 3, 4, 5]
            },
            'ui': {
                'theme': 'clam',
                'show_progress': True,
                'auto_save_results': True
            }
        }
        
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                
            # Merge with default config to handle missing keys
            self._merge_configs(self.config, loaded_config)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config file: {e}")
            
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
            
    def _merge_configs(self, default: Dict, loaded: Dict):
        """Recursively merge loaded config with default config."""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_configs(default[key], value)
                else:
                    default[key] = value
                    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'window.width')."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
        
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
            
        # Set the final value
        config_ref[keys[-1]] = value
        
    def update_last_paths(self, siop_dir: str = None, image_dir: str = None, 
                         output_dir: str = None):
        """Update the last used directory paths."""
        if siop_dir:
            self.set('paths.last_siop_dir', str(Path(siop_dir).parent))
        if image_dir:
            self.set('paths.last_image_dir', str(Path(image_dir).parent))
        if output_dir:
            self.set('paths.last_output_dir', output_dir)
            
    def get_processing_defaults(self) -> Dict[str, Any]:
        """Get default processing parameters."""
        return {
            'sensor': self.get('processing.default_sensor'),
            'method': self.get('processing.default_method'),
            'n_processes': self.get('processing.default_processes'),
            'parameters': self.config['parameters'].copy()
        }
