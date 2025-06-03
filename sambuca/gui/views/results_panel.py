"""
Results Panel View

Panel for displaying processing results and visualizations.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np


class ResultsPanel:
    """Panel for displaying processing results."""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.current_result = None
        
        self._setup_ui()
        self._setup_bindings()
        
    def _setup_ui(self):
        """Set up the results panel UI."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Results", padding="10")
        
        # Create notebook for different result views
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Summary tab
        self._create_summary_tab()
        
        # Visualization tab
        self._create_visualization_tab()
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
    def _create_summary_tab(self):
        """Create the summary results tab."""
        summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(summary_frame, text="Summary")
        
        # Text widget for summary display
        text_frame = ttk.Frame(summary_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.summary_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                   font=('Courier', 10))
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.summary_text.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        
    def _create_visualization_tab(self):
        """Create the visualization tab."""
        viz_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(viz_frame, text="Visualization")
        
        # Control panel for visualization options
        control_frame = ttk.Frame(viz_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Plot type selection
        ttk.Label(control_frame, text="Plot Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.plot_type_var = tk.StringVar(value="depth")
        plot_combo = ttk.Combobox(control_frame, textvariable=self.plot_type_var,
                                 values=["depth", "error", "summary"], state="readonly")
        plot_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Update plot button
        ttk.Button(control_frame, text="Update Plot", 
                  command=self._update_plot).grid(row=0, column=2)
        
        # Matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Navigation toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        
        # Configure grid weights
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)
        
    def _setup_bindings(self):
        """Set up event bindings."""
        # Subscribe to controller events
        self.controller.subscribe('result_updated', self.update_results)
        
    def update_results(self, result):
        """Update the results display with new processing results."""
        self.current_result = result
        
        # Update summary
        self._update_summary()
        
        # Update visualization
        self._update_plot()
        
    def _update_summary(self):
        """Update the summary text display."""
        if not self.current_result:
            return
            
        # Enable text widget for editing
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        try:
            # Get summary information
            summary_text = self._generate_summary_text()
            self.summary_text.insert(1.0, summary_text)
        except Exception as e:
            self.summary_text.insert(1.0, f"Error generating summary: {e}")
        finally:
            # Disable text widget
            self.summary_text.config(state=tk.DISABLED)
            
    def _generate_summary_text(self):
        """Generate summary text from current results."""
        if not self.current_result:
            return "No results available."
            
        lines = []
        lines.append("SAMBUCA PROCESSING RESULTS")
        lines.append("=" * 50)
        lines.append("")
        
        # Basic information
        if hasattr(self.current_result, 'image_path'):
            lines.append(f"Input Image: {self.current_result.image_path}")
        
        if hasattr(self.current_result, 'workflow_config'):
            config = self.current_result.workflow_config
            lines.append(f"Sensor: {config.get('sensor', 'Unknown')}")
            lines.append(f"Processing Method: {config.get('method', 'Unknown')}")
        
        lines.append("")
        lines.append("RESULTS SUMMARY")
        lines.append("-" * 20)
        
        # Check if we have depth results
        if hasattr(self.current_result, 'results') and 'depth' in self.current_result.results:
            depth_data = self.current_result.results['depth']
            valid_depths = depth_data[~np.isnan(depth_data)]
            
            if len(valid_depths) > 0:
                lines.append(f"Valid pixels: {len(valid_depths):,}")
                lines.append(f"Total pixels: {depth_data.size:,}")
                lines.append(f"Coverage: {len(valid_depths)/depth_data.size*100:.1f}%")
                lines.append("")
                lines.append(f"Depth Statistics:")
                lines.append(f"  Minimum: {valid_depths.min():.2f} m")
                lines.append(f"  Maximum: {valid_depths.max():.2f} m")
                lines.append(f"  Mean: {valid_depths.mean():.2f} m")
                lines.append(f"  Median: {np.median(valid_depths):.2f} m")
                lines.append(f"  Std Dev: {valid_depths.std():.2f} m")
            else:
                lines.append("No valid depth measurements found.")
        else:
            lines.append("Depth data not available.")
            
        # Add error statistics if available
        if hasattr(self.current_result, 'results') and 'error' in self.current_result.results:
            error_data = self.current_result.results['error']
            valid_errors = error_data[~np.isnan(error_data)]
            
            if len(valid_errors) > 0:
                lines.append("")
                lines.append(f"Error Statistics:")
                lines.append(f"  Mean Error: {valid_errors.mean():.4f}")
                lines.append(f"  Min Error: {valid_errors.min():.4f}")
                lines.append(f"  Max Error: {valid_errors.max():.4f}")
        
        return "\n".join(lines)
        
    def _update_plot(self):
        """Update the visualization plot."""
        if not self.current_result:
            return
            
        # Clear previous plot
        self.fig.clear()
        
        try:
            plot_type = self.plot_type_var.get()
            
            if plot_type == "depth":
                self._plot_depth_map()
            elif plot_type == "error":
                self._plot_error_map()
            elif plot_type == "summary":
                self._plot_summary()
                
        except Exception as e:
            # Show error in plot
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Error creating plot:\n{e}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Plot Error")
            
        # Refresh canvas
        self.canvas.draw()
        
    def _plot_depth_map(self):
        """Plot the depth map."""
        if not hasattr(self.current_result, 'results') or 'depth' not in self.current_result.results:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No depth data available", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Depth Map")
            return
            
        depth_data = self.current_result.results['depth']
        
        ax = self.fig.add_subplot(111)
        
        # Create masked array to handle NaN values
        masked_depth = np.ma.masked_invalid(depth_data)
        
        if masked_depth.count() > 0:
            im = ax.imshow(masked_depth, cmap='viridis_r', origin='upper')
            self.fig.colorbar(im, ax=ax, label='Depth (m)')
            ax.set_title('Bathymetry Map')
        else:
            ax.text(0.5, 0.5, "No valid depth data", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Depth Map - No Data")
            
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')
        
    def _plot_error_map(self):
        """Plot the error map."""
        if not hasattr(self.current_result, 'results') or 'error' not in self.current_result.results:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No error data available", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Error Map")
            return
            
        error_data = self.current_result.results['error']
        
        ax = self.fig.add_subplot(111)
        
        # Create masked array to handle NaN values
        masked_error = np.ma.masked_invalid(error_data)
        
        if masked_error.count() > 0:
            im = ax.imshow(masked_error, cmap='hot', origin='upper')
            self.fig.colorbar(im, ax=ax, label='Error')
            ax.set_title('Inversion Error Map')
        else:
            ax.text(0.5, 0.5, "No valid error data", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Error Map - No Data")
            
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')
        
    def _plot_summary(self):
        """Plot a summary figure with multiple subplots."""
        if not self.current_result or not hasattr(self.current_result, 'results'):
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No results available", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Summary Plot")
            return
            
        results = self.current_result.results
        
        # Determine available data
        has_depth = 'depth' in results
        has_error = 'error' in results
        
        if has_depth and has_error:
            # Two subplots
            ax1 = self.fig.add_subplot(121)
            ax2 = self.fig.add_subplot(122)
            
            # Depth histogram
            depth_data = results['depth']
            valid_depths = depth_data[~np.isnan(depth_data)]
            if len(valid_depths) > 0:
                ax1.hist(valid_depths, bins=50, alpha=0.7, color='blue')
                ax1.set_xlabel('Depth (m)')
                ax1.set_ylabel('Frequency')
                ax1.set_title('Depth Distribution')
                ax1.grid(True, alpha=0.3)
            
            # Error histogram
            error_data = results['error']
            valid_errors = error_data[~np.isnan(error_data)]
            if len(valid_errors) > 0:
                ax2.hist(valid_errors, bins=50, alpha=0.7, color='red')
                ax2.set_xlabel('Error')
                ax2.set_ylabel('Frequency')
                ax2.set_title('Error Distribution')
                ax2.grid(True, alpha=0.3)
                
        elif has_depth:
            # Single depth plot
            ax = self.fig.add_subplot(111)
            depth_data = results['depth']
            valid_depths = depth_data[~np.isnan(depth_data)]
            if len(valid_depths) > 0:
                ax.hist(valid_depths, bins=50, alpha=0.7, color='blue')
                ax.set_xlabel('Depth (m)')
                ax.set_ylabel('Frequency')
                ax.set_title('Depth Distribution')
                ax.grid(True, alpha=0.3)
        else:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data available for summary plot", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Summary Plot - No Data")
            
        self.fig.tight_layout()
        
    def clear_results(self):
        """Clear the current results display."""
        self.current_result = None
        
        # Clear summary
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, "No results available.")
        self.summary_text.config(state=tk.DISABLED)
        
        # Clear plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "No results to display", 
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title("Results")
        self.canvas.draw()
