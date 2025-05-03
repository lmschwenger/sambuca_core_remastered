import os
import numpy as np
import pandas as pd


def create_siop_directory_structure():
    """Create a directory structure for SIOP files with example data."""

    # Create base directories
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'siops')
    os.makedirs(f"{base_dir}/absorption", exist_ok=True)
    os.makedirs(f"{base_dir}/backscatter", exist_ok=True)
    os.makedirs(f"{base_dir}/substrates", exist_ok=True)

    # Generate wavelength range (400-800nm in 1nm steps)
    wavelengths = np.arange(400, 801, 1)

    # 1. Create water absorption spectrum
    # Based on Pope and Fry (1997) data
    water_abs = np.zeros_like(wavelengths, dtype=float)

    # Approximate values (simplified model)
    for i, wl in enumerate(wavelengths):
        if wl < 500:
            water_abs[i] = 0.01 + 0.05 * np.exp(-(wl - 400) / 30)
        elif wl < 600:
            water_abs[i] = 0.015 + (wl - 500) * 0.0006
        elif wl < 700:
            water_abs[i] = 0.075 + (wl - 600) * 0.003
        else:
            water_abs[i] = 0.375 + (wl - 700) * 0.005

    pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs}).to_csv(
        f"{base_dir}/absorption/water_absorption.csv", index=False)

    # 2. Create phytoplankton absorption spectrum (specific absorption per mg/m³)
    # Simple model based on chlorophyll absorption peaks
    ph_abs = 0.02 * np.ones_like(wavelengths, dtype=float)

    # Add absorption peaks
    ph_abs += 0.02 * np.exp(-0.005 * (wavelengths - 440) ** 2)  # Blue peak
    ph_abs += 0.005 * np.exp(-0.005 * (wavelengths - 675) ** 2)  # Red peak

    pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs}).to_csv(
        f"{base_dir}/absorption/phytoplankton_absorption.csv", index=False)

    # 3. Create CDOM absorption spectrum (normalized at 440nm)
    # Exponential model
    cdom_abs = np.exp(-0.017 * (wavelengths - 440))

    pd.DataFrame({'Wavelength': wavelengths, 'Absorption': cdom_abs}).to_csv(
        f"{base_dir}/absorption/cdom_absorption.csv", index=False)

    # 4. Create NAP absorption spectrum (specific absorption per mg/L)
    # Exponential model
    nap_abs = 0.04 * np.exp(-0.01 * (wavelengths - 440))

    pd.DataFrame({'Wavelength': wavelengths, 'Absorption': nap_abs}).to_csv(
        f"{base_dir}/absorption/nap_absorption.csv", index=False)

    # 5. Create water backscatter spectrum
    # Power law model: bb_w = b_w/2 where b_w ~ lambda^-4.32
    water_bb = 0.0019 / 2 * (550 / wavelengths) ** 4.32

    pd.DataFrame({'Wavelength': wavelengths, 'Backscatter': water_bb}).to_csv(
        f"{base_dir}/backscatter/water_backscatter.csv", index=False)

    # 6. Create phytoplankton backscatter spectrum (specific backscatter per mg/m³)
    # Power law model
    ph_bb = 0.0015 * (550 / wavelengths) ** 0.9

    pd.DataFrame({'Wavelength': wavelengths, 'Backscatter': ph_bb}).to_csv(
        f"{base_dir}/backscatter/phytoplankton_backscatter.csv", index=False)

    # 7. Create NAP backscatter spectrum (specific backscatter per mg/L)
    # Power law model
    nap_bb = 0.022 * (550 / wavelengths) ** 0.9

    pd.DataFrame({'Wavelength': wavelengths, 'Backscatter': nap_bb}).to_csv(
        f"{base_dir}/backscatter/nap_backscatter.csv", index=False)

    # 8. Create substrate reflectance spectra

    # Sand substrate (bright, increasing with wavelength)
    sand_refl = 0.1 + 0.3 * (wavelengths - 400) / 400  # Linear increase from 0.1 to 0.4
    sand_refl = np.clip(sand_refl, 0, 1)  # Constrain to [0,1]

    pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl}).to_csv(
        f"{base_dir}/substrates/sand_substrate.csv", index=False)

    # Seagrass substrate (peak in green, low in blue/red)
    seagrass_refl = 0.05 * np.ones_like(wavelengths, dtype=float)
    seagrass_refl += 0.1 * np.exp(-0.001 * (wavelengths - 550) ** 2)  # Green peak
    seagrass_refl = np.clip(seagrass_refl, 0, 1)  # Constrain to [0,1]

    pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': seagrass_refl}).to_csv(
        f"{base_dir}/substrates/seagrass_substrate.csv", index=False)

    # Mud substrate (dark, slight increase with wavelength)
    mud_refl = 0.02 + 0.06 * (wavelengths - 400) / 400  # Linear increase from 0.02 to 0.08
    mud_refl = np.clip(mud_refl, 0, 1)  # Constrain to [0,1]

    pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': mud_refl}).to_csv(
        f"{base_dir}/substrates/mud_substrate.csv", index=False)

    print(f"Created SIOP directory structure with example files in {base_dir}/")


# Run the function to create the structure and files
if __name__ == "__main__":
    create_siop_directory_structure()