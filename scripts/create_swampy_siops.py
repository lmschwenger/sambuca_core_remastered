import csv
import math
import numpy as np
import os

# Make sure the output directories exist
siops_root = os.path.join(os.path.dirname(__file__), "..", "data", "swampy_siops")
os.makedirs(os.path.join(siops_root, "absorption"), exist_ok=True)
os.makedirs(os.path.join(siops_root, "backscatter"), exist_ok=True)
os.makedirs(os.path.join(siops_root, "substrates"), exist_ok=True)

# Define the wavelength range used in the SIOP files (400-800 nm with 1 nm interval)
wavelengths = range(400, 801)

# Extract representative parameter values from the SIOPMatrix data
# Using a row with complete data (from the MD04 dataset, row 200403)
params = {
    'A_CDOM_SLOPE': 0.0171004,  # CDOM absorption slope
    'A_CDOM_440NM': 0.1100509,  # CDOM absorption reference value at 440 nm
    'A_NAP_STAR_440NM': 0.0266682,  # NAP specific absorption at 440 nm
    'A_NAP_SLOPE': 0.0116964,  # NAP absorption slope
    'A_PHY_STAR_440NM': 0.0673131,  # Phytoplankton specific absorption at 440 nm
    'A_PHY_STAR_676NM': 0.026025,  # Phytoplankton specific absorption at 676 nm
    'BB_NAP_STAR_555NM': 0.0074657,  # NAP specific backscatter at 555 nm
    'BB_NAP_SLOPE': 1.173946,  # NAP backscatter slope
    'BB_B_RATIO': 0.0224,  # Backscatter to scatter ratio
    'B_NAP_STAR_555NM': 0.3308684  # NAP specific scatter at 555 nm
}


def create_cdom_absorption():
    """Generate CDOM absorption spectrum based on exponential model."""
    data = [["Wavelength", "Absorption"]]
    for wl in wavelengths:
        # a(λ) = a(λref) * exp(-S * (λ - λref))
        absorption = params['A_CDOM_440NM'] * math.exp(-params['A_CDOM_SLOPE'] * (wl - 440))
        data.append([wl, absorption])
    return data


def create_nap_absorption():
    """Generate NAP absorption spectrum based on exponential model."""
    data = [["Wavelength", "Absorption"]]
    for wl in wavelengths:
        # a*(λ) = a*(λref) * exp(-S * (λ - λref))
        absorption = params['A_NAP_STAR_440NM'] * math.exp(-params['A_NAP_SLOPE'] * (wl - 440))
        data.append([wl, absorption])
    return data


def create_phytoplankton_absorption():
    """Generate phytoplankton absorption spectrum based on the two-peak model."""
    data = [["Wavelength", "Absorption"]]
    for wl in wavelengths:
        # Simplified two-peak Gaussian model
        peak440 = params['A_PHY_STAR_440NM'] * math.exp(-0.5 * ((wl - 440) / 25) ** 2)
        peak676 = params['A_PHY_STAR_676NM'] * math.exp(-0.5 * ((wl - 676) / 20) ** 2)

        # Combine the two peaks and ensure a minimum baseline
        absorption = peak440 + peak676
        absorption = max(absorption, 0.002)  # Minimum baseline

        data.append([wl, absorption])
    return data


def create_nap_backscatter():
    """Generate NAP backscatter spectrum based on power law model."""
    data = [["Wavelength", "Backscatter"]]
    for wl in wavelengths:
        # bb*(λ) = bb*(λref) * (λref/λ)^slope
        backscatter = params['BB_NAP_STAR_555NM'] * ((555 / wl) ** params['BB_NAP_SLOPE'])
        data.append([wl, backscatter])
    return data


def create_phytoplankton_backscatter():
    """Generate phytoplankton backscatter spectrum."""
    data = [["Wavelength", "Backscatter"]]
    for wl in wavelengths:
        # Approximate phytoplankton scattering (simplified relationship)
        phyto_scattering = params['B_NAP_STAR_555NM'] * 0.2 * ((550 / wl) ** 0.3)

        # Apply bb:b ratio to get backscattering
        backscatter = phyto_scattering * params['BB_B_RATIO']

        data.append([wl, backscatter])
    return data


def create_water_absorption():
    """Retain the existing water absorption data as it's a physical constant."""
    # This uses the Pope & Fry (1997) and Smith & Baker (1981) data
    data = [["Wavelength", "Absorption"]]

    # Read existing water absorption file and keep the data
    with open(os.path.join(siops_root, 'absorption', 'water_absorption.csv'), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            wl = int(row[0])
            absorption = float(row[1])
            data.append([wl, absorption])

    return data


def create_water_backscatter():
    """Generate water backscatter based on standard model."""
    data = [["Wavelength", "Backscatter"]]
    for wl in wavelengths:
        # Pure water backscattering (Morel 1974)
        backscatter = 0.0038 * (550 / wl) ** 4.32
        data.append([wl, backscatter])
    return data


def write_siop_file(data, filename):
    """Write the data to a CSV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    print(f"Created {filename}")


def create_substrate_file(source_content, output_filename):
    """Convert substrate data from the original format to the required CSV format."""
    lines = source_content.strip().split('\n')

    # Skip the header line and process the data
    wavelengths = []
    reflectance = []

    for line in lines[1:]:  # Skip header line
        parts = line.strip().split()
        if len(parts) == 2:
            wl = int(float(parts[0]))
            ref = float(parts[1])

            # Only include wavelengths in our target range (400-800)
            if 400 <= wl <= 800:
                wavelengths.append(wl)
                reflectance.append(ref)

    # Create CSV data
    data = [["Wavelength", "Reflectance"]]
    for wl, ref in zip(wavelengths, reflectance):
        data.append([wl, ref])

    write_siop_file(data, output_filename)


# Create all the updated SIOP files in the correct directories
write_siop_file(create_cdom_absorption(), os.path.join(siops_root, 'absorption/cdom_absorption.csv'))
write_siop_file(create_nap_absorption(), os.path.join(siops_root, 'absorption/nap_absorption.csv'))
write_siop_file(create_phytoplankton_absorption(), os.path.join(siops_root, 'absorption/phytoplankton_absorption.csv'))
write_siop_file(create_water_absorption(), os.path.join(siops_root, 'absorption/water_absorption.csv'))
write_siop_file(create_nap_backscatter(), os.path.join(siops_root, 'backscatter/nap_backscatter.csv'))
write_siop_file(create_phytoplankton_backscatter(), os.path.join(siops_root, 'backscatter/phytoplankton_backscatter.csv'))
write_siop_file(create_water_backscatter(), os.path.join(siops_root, 'backscatter/water_backscatter.csv'))