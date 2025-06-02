"""
Workflow Controller

Handles workflow execution and coordinates between GUI and sambuca_core.
"""

import os
import threading
from pathlib import Path
from typing import Dict, Callable, Any

from sambuca_core.workflows import BathymetryWorkflow
from sambuca_core.inversion import LookUpTable, process_image
from sambuca_core.results import ImageInversionResult


# Sensor definitions - centralized for easy access
SENSOR_DEFINITIONS = {
    'sentinel2': {
        'name': 'Sentinel-2',
        'bands': {
            'B1': 443.9,   # Coastal aerosol
            'B2': 496.6,   # Blue
            'B3': 560.0,   # Green
            'B4': 664.5,   # Red
            'B5': 703.9,   # Red edge 1
            'B6': 740.2,   # Red edge 2
            'B7': 782.5,   # Red edge 3
            'B8': 835.1,   # NIR
            'B8A': 864.8,  # NIR narrow
            'B9': 945.0,   # Water vapour
            'B10': 1373.5, # SWIR cirrus
            'B11': 1613.7, # SWIR 1
            'B12': 2202.4  # SWIR 2
        }
    },
    'landsat8': {
        'name': 'Landsat-8',
        'bands': {
            'B1': 443,     # Coastal
            'B2': 482,     # Blue
            'B3': 562,     # Green
            'B4': 655,     # Red
            'B5': 865,     # NIR
            'B6': 1610,    # SWIR 1
            'B7': 2200,    # SWIR 2
            'B8': 590,     # Panchromatic
            'B9': 1375     # Cirrus
        }
    }
}


def get_sensor_wavelengths(selected_bands, sensor_name):
    """Get wavelengths for selected bands from sensor definition."""
    if sensor_name not in SENSOR_DEFINITIONS:
        raise ValueError(f"Unknown sensor: {sensor_name}")
        
    sensor_def = SENSOR_DEFINITIONS[sensor_name]
    wavelengths = []
    
    for band in selected_bands:
        if band in sensor_def['bands']:
            wavelengths.append(sensor_def['bands'][band])
        else:
            raise ValueError(f"Band {band} not available for sensor {sensor_name}")
            
    return wavelengths


class WorkflowController:
    """Controller for managing bathymetry workflows."""
    
    def __init__(self):
        self.workflow = None
        self.current_parameters = {}
        self.lut = None
        self._callbacks = {}
        
        # Initialize default parameters
        self._initialize_default_parameters()
        
    def _initialize_default_parameters(self):
        """Initialize default processing parameters."""
        self.current_parameters = {
            'depth_range': (0.0, 25.0),
            'fixed_chl': 0.5,
            'fixed_nap': 0.001,
            'fixed_cdom': 0.0025,
            'fixed_substrate_fraction': 1.0,
            'selected_bands': ['B2', 'B3', 'B4', 'B5'],
            'band_indices': [1, 2, 3, 4]
        }
        
    def subscribe(self, event: str, callback: Callable):
        """Subscribe to controller events."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
        
    def _notify(self, event: str, data: Any = None):
        """Notify subscribers of an event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in callback for event {event}: {e}")
                    
    def update_parameters(self, parameters: Dict):
        """Update processing parameters."""
        self.current_parameters.update(parameters)
        
    def process_image(self, params: Dict, progress_callback: Callable = None, 
                     completion_callback: Callable = None):
        """Process an image using the specified parameters."""
        
        def run_processing():
            try:
                # Initialize workflow
                self.workflow = BathymetryWorkflow(
                    params['siop_dir'], 
                    sensor=params['sensor']
                )
                
                # Apply custom parameters
                self.workflow.customize_parameters(
                    depth=self.current_parameters['depth_range'],
                    fixed_chl=self.current_parameters['fixed_chl'],
                    fixed_nap=self.current_parameters['fixed_nap'],
                    fixed_cdom=self.current_parameters['fixed_cdom'],
                    fixed_substrate_fraction=self.current_parameters['fixed_substrate_fraction']
                )
                
                # Get wavelengths from sensor definition and set bands
                try:
                    wavelengths = get_sensor_wavelengths(
                        self.current_parameters['selected_bands'], 
                        params['sensor']
                    )
                    self.workflow.wavelengths = wavelengths
                    self.workflow.bands = self.current_parameters['band_indices']
                except Exception as e:
                    raise ValueError(f"Error configuring bands: {e}")
                
                # Update progress
                if progress_callback:
                    progress_callback(20)
                
                # Choose processing method
                if params['method'] == 'lut':
                    result = self._process_with_lut(params, progress_callback)
                else:
                    result = self._process_with_optimization(params, progress_callback)
                
                # Update progress
                if progress_callback:
                    progress_callback(90)
                
                # Save results
                output_dir = Path(params['output_dir'])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                result.save_all_parameters(str(output_dir), formats=['tiff'])
                result.plot_summary(save_path=str(output_dir / "summary.png"))
                
                # Update progress
                if progress_callback:
                    progress_callback(100)
                
                # Notify completion
                if completion_callback:
                    completion_callback(True, f"Processing completed successfully. Results saved to {output_dir}")
                
                # Notify result update
                self._notify('result_updated', result)
                
            except Exception as e:
                if completion_callback:
                    completion_callback(False, f"Processing failed: {str(e)}")
                    
        # Run processing in separate thread
        processing_thread = threading.Thread(target=run_processing, daemon=True)
        processing_thread.start()
        
    def _process_with_optimization(self, params: Dict, progress_callback: Callable = None):
        """Process image using optimization method."""
        if progress_callback:
            progress_callback(30)
            
        result = self.workflow.process_image(
            image_path=params['image_path'],
            n_processes=params['n_processes'],
            progress_bar=False  # We handle progress through callback
        )
        
        if progress_callback:
            progress_callback(80)
            
        return result
        
    def _process_with_lut(self, params: Dict, progress_callback: Callable = None):
        """Process image using LUT method."""
        if progress_callback:
            progress_callback(30)
            
        # Build LUT if not exists
        if self.lut is None:
            self.lut = LookUpTable(self.workflow.inversion_params)
            
            if progress_callback:
                progress_callback(40)
                
            self.lut.build_table(
                grid_size=200,
                progress_bar=False,
                use_kdtree=True
            )
            
        if progress_callback:
            progress_callback(60)
            
        # Load image
        image_data = self.workflow.image_loader.load(
            params['image_path'], 
            bands=self.current_parameters['band_indices']
        )
        
        if progress_callback:
            progress_callback(70)
            
        # Process with LUT
        results = process_image(
            image_data.data,
            self.workflow.inversion_params,
            lut=self.lut,
            n_processes=params['n_processes'],
            progress_bar=False,
            refinement=False
        )
        
        # Create result object
        result = ImageInversionResult(
            results=results,
            image_metadata=image_data.metadata,
            workflow_config=self.workflow.get_config(),
            image_path=params['image_path']
        )
        
        return result
        
    def get_workflow_config(self):
        """Get current workflow configuration."""
        if self.workflow:
            return self.workflow.get_config()
        return {}
        
    def clear_lut(self):
        """Clear the current LUT to force rebuilding."""
        self.lut = None
