"""
Bathymetry Processing Example

"""
import os

from sambuca.core.sensors import S2
from sambuca.core.workflows import BathymetryWorkflow
from sambuca_utils.visualization import ResultVisualizer
from pathlib import Path


def main():
    # Define paths
    siop_dir = Path("../data/siops")
    image_path = Path("../data/input//example_groensund.tif")
    mask_path = Path("../data/input/examples/S2_L2A_20180508_B01-B05_ndwi_clipped2.tif")
    output_dir = Path("../data/output/example_groensund")

    # Create workflow - this handles all the setup automatically!
    workflow = BathymetryWorkflow(str(siop_dir), sensor='sentinel2')

    # Optional: customize parameters
    workflow.customize_parameters(
        depth=(0, 25),
        fixed_chl=0.5,
        fixed_nap=0.001,
        fixed_cdom=0.0025,
        fixed_substrate_fraction=1,
    )

    workflow.wavelengths = [S2.B02.wavelength, S2.B03.wavelength, S2.B04.wavelength, S2.B05.wavelength]
    workflow.bands = [2, 3, 4, 5]

    # Process entire image - one line!
    result = workflow.process_image(
        image_path=str(image_path),
        mask_path=None, # str(mask_path) if mask_path.exists() else
        n_processes=4,
        progress_bar=True
    )

    # Analysis and visualization - also one line each!
    result.print_summary()
    os.makedirs(output_dir, exist_ok=True)
    
    # Create visualizer and plot summary
    viz = ResultVisualizer(result)
    summary_fig = viz.create_summary_plot(figsize=(15, 10))
    summary_fig.savefig(str(output_dir / "summary.png"), dpi=300, bbox_inches='tight')
    
    result.save_all_parameters(str(output_dir), formats=['tiff', 'png'])

    print(f"\nResults saved to: {output_dir}")


if __name__ == "__main__":
    main()