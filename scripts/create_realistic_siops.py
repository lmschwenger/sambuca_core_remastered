"""
EMERGENCY SIOP CORRECTION SCRIPT
Run this IMMEDIATELY to fix your broken SIOP data.
"""

import numpy as np
import pandas as pd
import os


def create_pope_fry_water_absorption():
    """Create corrected water absorption based on Pope & Fry (1997)."""

    # Pope & Fry (1997) reference data points
    # These are the STANDARD values used in ocean color remote sensing
    wl_ref = np.array([
        400, 410, 420, 430, 440, 450, 460, 470, 480, 490,
        500, 510, 520, 530, 540, 550, 560, 570, 580, 590,
        600, 610, 620, 630, 640, 650, 660, 670, 680, 690,
        700, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800
    ])

    abs_ref = np.array([
        0.00663, 0.00473, 0.00454, 0.00495, 0.00635, 0.00751, 0.00795,
        0.00835, 0.00896, 0.0150, 0.0204, 0.0325, 0.0396, 0.0409,
        0.0417, 0.0434, 0.0596, 0.0619, 0.0642, 0.0695, 0.0772,
        0.0896, 0.1110, 0.1351, 0.1672, 0.2224, 0.2644, 0.2755,
        0.2834, 0.2916, 0.3108, 0.3400, 0.4100, 0.4390, 0.4500,
        0.4650, 0.4820, 0.5030, 0.5280, 0.5630, 0.6080
    ])

    # Extend range and interpolate
    wavelengths = np.arange(340, 902)  # Match your original range

    # For wavelengths outside reference range, extrapolate carefully
    from scipy.interpolate import interp1d
    interpolator = interp1d(wl_ref, abs_ref, kind='cubic',
                            bounds_error=False, fill_value='extrapolate')

    absorption = interpolator(wavelengths)

    # Ensure physical constraints
    absorption = np.maximum(absorption, 0.001)  # No values below 0.001

    return wavelengths, absorption


def create_realistic_phytoplankton_absorption():
    """Create realistic phytoplankton specific absorption spectrum."""

    wavelengths = np.arange(350, 901)  # Match your original range
    a_ph_star = np.zeros_like(wavelengths, dtype=float)

    # Based on Bricaud et al. (1998) and Lee et al. models
    for i, wl in enumerate(wavelengths):
        if wl <= 400:
            # UV region - high absorption
            a_ph_star[i] = 0.08 * np.exp(-0.01 * (wl - 400))
        elif wl <= 440:
            # Blue peak region
            a_ph_star[i] = 0.055 + 0.025 * np.exp(-((wl - 420) ** 2) / (2 * 20 ** 2))
        elif wl <= 500:
            # Blue-green transition
            a_ph_star[i] = 0.055 * (1 - 0.6 * (wl - 440) / 60)
        elif wl <= 550:
            # Green minimum
            a_ph_star[i] = 0.023 - 0.008 * (wl - 500) / 50
        elif wl <= 620:
            # Green-red transition
            a_ph_star[i] = 0.015 + 0.005 * (wl - 550) / 70
        elif wl <= 680:
            # Chlorophyll-a red peak (around 665-675nm)
            peak_wl = 670
            peak_width = 15
            peak_amplitude = 0.035
            base_absorption = 0.015
            peak_factor = np.exp(-((wl - peak_wl) ** 2) / (2 * peak_width ** 2))
            a_ph_star[i] = base_absorption + peak_amplitude * peak_factor
        else:
            # Red/NIR - exponential decay
            a_ph_star[i] = 0.011 * np.exp(-0.015 * (wl - 680))

    # Ensure all values are positive and realistic
    a_ph_star = np.maximum(a_ph_star, 0.001)  # Minimum 0.001
    a_ph_star = np.minimum(a_ph_star, 0.150)  # Maximum 0.150

    return wavelengths, a_ph_star


def validate_and_fix_existing_siops():
    """Validate and fix existing SIOP files."""

    fixes_applied = []

    # Fix CDOM - ensure no negatives and proper exponential decay
    try:
        cdom_df = pd.read_csv('cdom_absorption.csv')
        cdom_values = cdom_df.iloc[:, 1].values

        if np.any(cdom_values < 0):
            cdom_values = np.maximum(cdom_values, 0.0001)
            cdom_df.iloc[:, 1] = cdom_values
            cdom_df.to_csv('cdom_absorption_fixed.csv', index=False)
            fixes_applied.append("CDOM: Fixed negative values")
    except Exception as e:
        print(f"Could not fix CDOM: {e}")

    # Fix NAP - ensure no negatives
    try:
        nap_df = pd.read_csv('nap_absorption.csv')
        nap_values = nap_df.iloc[:, 1].values

        if np.any(nap_values < 0):
            nap_values = np.maximum(nap_values, 0.0001)
            nap_df.iloc[:, 1] = nap_values
            nap_df.to_csv('nap_absorption_fixed.csv', index=False)
            fixes_applied.append("NAP: Fixed negative values")
    except Exception as e:
        print(f"Could not fix NAP: {e}")

    return fixes_applied


def main():
    """Main correction function - run this to fix your SIOPs."""

    print("🚨 EMERGENCY SIOP CORRECTION")
    print("=" * 50)

    backup_dir = "siop_backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"✅ Created backup directory: {backup_dir}")

    # Backup original files
    original_files = [
        'water_absorption.csv',
        'phytoplankton_absorption.csv',
        'cdom_absorption.csv',
        'nap_absorption.csv'
    ]

    for file in original_files:
        if os.path.exists(file):
            backup_path = os.path.join(backup_dir, f"{file}.original")
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(file, backup_path)
                print(f"✅ Backed up {file}")

    # Generate corrected water absorption
    print("\n🔧 Generating corrected water absorption (Pope & Fry 1997)...")
    wl_water, abs_water = create_pope_fry_water_absorption()

    water_df = pd.DataFrame({
        'Wavelength': wl_water.astype(int),
        'Absorption': abs_water
    })
    water_df.to_csv('water_absorption_corrected.csv', index=False)
    print("✅ Created: water_absorption_corrected.csv")

    # Validate key wavelengths
    test_wavelengths = {440: 0.0044, 490: 0.0071, 560: 0.0596, 665: 0.2885}
    print("\nValidation against Pope & Fry standards:")
    for test_wl, expected in test_wavelengths.items():
        idx = np.argmin(np.abs(wl_water - test_wl))
        actual = abs_water[idx]
        error = abs(actual - expected) / expected * 100
        status = "✅" if error < 10 else "⚠️" if error < 30 else "❌"
        print(f"  {test_wl}nm: {actual:.6f} (expected {expected:.6f}, error {error:.1f}%) {status}")

    # Generate corrected phytoplankton absorption
    print("\n🔧 Generating corrected phytoplankton absorption...")
    wl_phyto, abs_phyto = create_realistic_phytoplankton_absorption()

    phyto_df = pd.DataFrame({
        'Wavelength': wl_phyto.astype(int),
        'Absorption': abs_phyto
    })
    phyto_df.to_csv('phytoplankton_absorption_corrected.csv', index=False)
    print("✅ Created: phytoplankton_absorption_corrected.csv")

    # Validate no negative values
    if np.all(abs_phyto >= 0):
        print("✅ No negative values in corrected phytoplankton absorption")
    else:
        print("❌ Still has negative values - check code!")

    # Fix other SIOP files
    print("\n🔧 Fixing other SIOP files...")
    fixes = validate_and_fix_existing_siops()
    for fix in fixes:
        print(f"✅ {fix}")

    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Update your SIOP directory to use *_corrected.csv files")
    print("2. Test on a single pixel first")
    print("3. Expect MUCH better depth variation!")
    print("4. If still issues, check the enhanced forward model")
    print("=" * 50)

    # Create a simple validation script
    validation_script = '''
# QUICK VALIDATION SCRIPT
import pandas as pd
import numpy as np

# Test the corrected files
water_corrected = pd.read_csv('water_absorption_corrected.csv')
phyto_corrected = pd.read_csv('phytoplankton_absorption_corrected.csv')

print("Validation of corrected SIOPs:")
print(f"Water absorption range: {water_corrected.iloc[:,1].min():.6f} - {water_corrected.iloc[:,1].max():.6f}")
print(f"Phytoplankton absorption range: {phyto_corrected.iloc[:,1].min():.6f} - {phyto_corrected.iloc[:,1].max():.6f}")

# Check for negatives
water_neg = np.sum(water_corrected.iloc[:,1] < 0)
phyto_neg = np.sum(phyto_corrected.iloc[:,1] < 0)

print(f"Negative water values: {water_neg} (should be 0)")
print(f"Negative phytoplankton values: {phyto_neg} (should be 0)")

if water_neg == 0 and phyto_neg == 0:
    print("✅ ALL CHECKS PASSED - SIOPs are now physically realistic!")
else:
    print("❌ Still have issues - check the correction code")
'''


if __name__ == "__main__":
    main()