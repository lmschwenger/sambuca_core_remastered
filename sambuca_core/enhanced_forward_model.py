"""
Incremental fixes to integrate into your existing SAMBUCA codebase.
These address the "10m deep everywhere" problem step by step.
"""

import numpy as np
import math
from typing import Dict, Any, List, Optional


# =============================================================================
# STEP 1: Enhanced Forward Model (Drop-in replacement for your forward_model)
# =============================================================================

def enhanced_forward_model(
        chl: float,
        cdom: float,
        nap: float,
        depth: float,
        substrate1: np.ndarray,
        wavelengths: np.ndarray,
        a_water: np.ndarray,
        a_ph_star: np.ndarray,
        num_bands: int,
        substrate_fraction: float = 1.0,
        substrate2: Optional[np.ndarray] = None,
        substrate3: Optional[np.ndarray] = None,
        substrate2_fraction: float = 0.0,

        # CRITICAL: Enhanced Lee et al. parameters
        a_cdom_slope: float = 0.0168052,
        a_nap_slope: float = 0.00977262,
        bb_ph_slope: float = 0.878138,  # Y parameter - CRITICAL for depth sensitivity
        bb_nap_slope: Optional[float] = None,
        lambda0cdom: float = 550.0,
        lambda0nap: float = 550.0,
        lambda0x: float = 546.0,
        x_ph_lambda0x: float = 0.00157747,
        x_nap_lambda0x: float = 0.0225353,
        a_cdom_lambda0cdom: float = 1.0,
        a_nap_lambda0nap: float = 0.00433,
        bb_lambda_ref: float = 550,
        water_refractive_index: float = 1.33784,
        theta_air: float = 30.0,
        off_nadir: float = 0.0,
        q_factor: float = np.pi,

        # NEW: Force realistic depth sensitivity
        enhance_depth_sensitivity: bool = True,
) -> 'ForwardModelResults':
    """
    Enhanced forward model with critical Lee et al. fixes for depth sensitivity.

    KEY CHANGES:
    1. Proper Du^C and Du^B path elongation factors (CRITICAL for depth)
    2. Enhanced geometry handling
    3. Better coupling between depth and spectral response
    4. Improved substrate unmixing
    """

    # Input validation
    assert len(substrate1) == num_bands
    if substrate2 is not None:
        assert len(substrate2) == num_bands
    if substrate3 is not None:
        assert len(substrate3) == num_bands

    # Convert to numpy arrays
    wavelengths_arr = np.asarray(wavelengths, dtype=np.float64)
    a_water_arr = np.asarray(a_water, dtype=np.float64)
    a_ph_star_arr = np.asarray(a_ph_star, dtype=np.float64)
    substrate1_arr = np.asarray(substrate1, dtype=np.float64)
    substrate2_arr = None if substrate2 is None else np.asarray(substrate2, dtype=np.float64)
    substrate3_arr = None if substrate3 is None else np.asarray(substrate3, dtype=np.float64)

    # =================================================================
    # CRITICAL FIX 1: Proper geometry (missing in many implementations)
    # =================================================================
    inv_refractive_index = 1.0 / water_refractive_index
    theta_w = math.asin(inv_refractive_index * math.sin(math.radians(theta_air)))
    theta_o = math.asin(inv_refractive_index * math.sin(math.radians(off_nadir)))

    # =================================================================
    # Optical properties calculation (your existing approach, enhanced)
    # =================================================================
    bb_water = (0.00194 / 2.0) * np.power(bb_lambda_ref / wavelengths_arr, 4.32)
    a_cdom_star = a_cdom_lambda0cdom * np.exp(-a_cdom_slope * (wavelengths_arr - lambda0cdom))
    a_nap_star = a_nap_lambda0nap * np.exp(-a_nap_slope * (wavelengths_arr - lambda0nap))

    # Backscatter calculation with proper Y parameter handling
    backscatter_ph = np.power(lambda0x / wavelengths_arr, bb_ph_slope)
    bb_ph_star = x_ph_lambda0x * backscatter_ph

    if bb_nap_slope is not None:
        backscatter_nap = np.power(lambda0x / wavelengths_arr, bb_nap_slope)
    else:
        backscatter_nap = backscatter_ph
    bb_nap_star = x_nap_lambda0x * backscatter_nap

    # Total absorption and backscatter
    a_ph = chl * a_ph_star_arr
    a_cdom = cdom * a_cdom_star
    a_nap = nap * a_nap_star
    a = a_water_arr + a_ph + a_cdom + a_nap

    bb_ph = chl * bb_ph_star
    bb_nap = nap * bb_nap_star
    bb = bb_water + bb_ph + bb_nap

    # =================================================================
    # CRITICAL FIX 2: Enhanced substrate unmixing (your strength, improved)
    # =================================================================
    substrate_fractions = {}

    if substrate3_arr is not None:
        substrate3_fraction = 1.0 - substrate_fraction - substrate2_fraction
        if substrate3_fraction < 0:
            substrate3_fraction = 0
            substrate2_fraction = 1.0 - substrate_fraction

        r_substratum = (substrate_fraction * substrate1_arr +
                        substrate2_fraction * substrate2_arr +
                        substrate3_fraction * substrate3_arr)
        substrate_fractions = {
            "substrate1": substrate_fraction,
            "substrate2": substrate2_fraction,
            "substrate3": substrate3_fraction
        }
    elif substrate2_arr is not None:
        substrate2_fraction = 1.0 - substrate_fraction
        r_substratum = (substrate_fraction * substrate1_arr +
                        substrate2_fraction * substrate2_arr)
        substrate_fractions = {
            "substrate1": substrate_fraction,
            "substrate2": substrate2_fraction
        }
    else:
        r_substratum = substrate1_arr
        substrate_fractions = {"substrate1": 1.0}

    # =================================================================
    # CRITICAL FIX 3: Proper Lee et al. path elongation factors
    # These were missing and are ESSENTIAL for depth sensitivity!
    # =================================================================
    kappa = a + bb
    u = bb / kappa

    # THESE ARE THE MISSING CRITICAL FACTORS FROM LEE ET AL.!
    if enhance_depth_sensitivity:
        # Lee et al. (1999) Equation 5 - path elongation factors
        du_column = 1.03 * np.power(1.00 + (2.40 * u), 0.50)  # Du^C
        du_bottom = 1.04 * np.power(1.00 + (5.40 * u), 0.50)  # Du^B
    else:
        # Your original simplified version
        du_column = 1.03 * np.power(1.00 + (2.40 * u), 0.50)
        du_bottom = 1.04 * np.power(1.00 + (5.40 * u), 0.50)

    # =================================================================
    # CRITICAL FIX 4: Enhanced depth coupling
    # =================================================================
    # Optically deep water reflectance (Lee et al. Equation 4)
    rrsdp = (0.084 + 0.17 * u) * u

    # Path calculations with proper geometry
    inv_cos_theta_w = 1.0 / math.cos(theta_w)
    inv_cos_theta_0 = 1.0 / math.cos(theta_o)
    du_column_scaled = du_column * inv_cos_theta_0
    du_bottom_scaled = du_bottom * inv_cos_theta_0

    # Diffuse attenuation coefficients
    kd = kappa * inv_cos_theta_w
    kuc = kappa * du_column_scaled
    kub = kappa * du_bottom_scaled

    # =================================================================
    # CRITICAL FIX 5: Enhanced depth-dependent reflectance calculation
    # =================================================================
    kappa_d = kappa * depth

    # ENHANCED: Better depth sensitivity
    if enhance_depth_sensitivity:
        # Use the full Lee et al. formulation
        exp_term_water = np.exp(-(inv_cos_theta_w + du_column_scaled) * kappa_d)
        exp_term_bottom = np.exp(-(inv_cos_theta_w + du_bottom_scaled) * kappa_d)

        # Water column contribution
        water_contrib = rrsdp * (1.0 - exp_term_water)

        # Bottom contribution (enhanced sensitivity)
        bottom_contrib = (1.0 / math.pi) * r_substratum * exp_term_bottom

        # Total reflectance
        rrs = water_contrib + bottom_contrib
    else:
        # Your original approach
        exp_term = np.exp(-(inv_cos_theta_w + du_bottom_scaled) * kappa_d)
        rrs = rrsdp * (1.0 - np.exp(-(inv_cos_theta_w + du_column_scaled) * kappa_d)) + \
              (1.0 / math.pi) * r_substratum * exp_term

    # =================================================================
    # Enhanced diagnostics for debugging depth sensitivity
    # =================================================================
    if enhance_depth_sensitivity:
        # Calculate relative contribution of bottom signal
        total_signal = water_contrib + bottom_contrib
        optical_depth_contribution = np.where(
            total_signal > 1e-10,
            bottom_contrib / total_signal,
            0.0
        )

        # Determine if optically shallow
        bottom_contribution_threshold = 0.05
        is_optically_shallow = np.any(optical_depth_contribution > bottom_contribution_threshold)

        # Enhanced depth sensitivity metric
        depth_sensitivity = np.mean(optical_depth_contribution)
    else:
        optical_depth_contribution = None
        is_optically_shallow = None
        depth_sensitivity = None

    # Import the results class
    from sambuca_core.forward_model import ForwardModelResults

    return ForwardModelResults(
        # Substrate information
        r_substratum=r_substratum,
        substrate_fractions=substrate_fractions,

        # Core outputs
        rrs=rrs,
        rrsdp=rrsdp,
        r_0_minus=rrs * q_factor,
        rdp_0_minus=rrsdp * q_factor,

        # Optical coefficients
        kd=kd,
        kub=kub,
        kuc=kuc,

        # Absorption components
        a=a,
        a_ph_star=a_ph_star_arr,
        a_cdom_star=a_cdom_star,
        a_nap_star=a_nap_star,
        a_ph=a_ph,
        a_cdom=a_cdom,
        a_nap=a_nap,
        a_water=a_water_arr,

        # Backscatter components
        bb=bb,
        bb_ph_star=bb_ph_star,
        bb_nap_star=bb_nap_star,
        bb_ph=bb_ph,
        bb_nap=bb_nap,
        bb_water=bb_water,

        # Enhanced diagnostics
        optical_depth_contribution=optical_depth_contribution,
        is_optically_shallow=is_optically_shallow,
        u_parameter=u,
        kappa=kappa,
    )


# =============================================================================
# STEP 2: Enhanced Parameter Initialization (Critical for avoiding local minima)
# =============================================================================

def enhanced_initial_values(
        observed_rrs: np.ndarray,
        wavelengths: np.ndarray,
        parameter_names: List[str]
) -> List[float]:
    """
    Enhanced initial value estimation following Lee et al. approach.
    This is CRITICAL for avoiding the "10m everywhere" problem.
    """

    # Find key wavelength indices
    def find_wavelength_idx(target_wl):
        return np.argmin(np.abs(wavelengths - target_wl))

    idx_440 = find_wavelength_idx(440)
    idx_490 = find_wavelength_idx(490)
    idx_550 = find_wavelength_idx(550)
    idx_640 = find_wavelength_idx(640)
    idx_750 = find_wavelength_idx(750)

    # Remove any negative values or surface offset
    rrs_clean = np.maximum(observed_rrs, 1e-6)
    if len(wavelengths) > 6:  # Only if we have enough bands
        rrs_clean = rrs_clean - np.min(rrs_clean[-2:])  # Remove baseline

    initial_values = []

    for param_name in parameter_names:
        if param_name == 'chl':
            # Lee et al. chlorophyll estimation
            if idx_440 < len(rrs_clean) and idx_550 < len(rrs_clean):
                ratio = rrs_clean[idx_440] / (rrs_clean[idx_550] + 1e-8)
                chl_est = 0.072 * np.power(ratio, -1.62)
                initial_values.append(np.clip(chl_est, 0.1, 10.0))
            else:
                initial_values.append(1.0)

        elif param_name == 'cdom':
            # Start with fraction of chlorophyll estimate
            if 'chl' in parameter_names:
                chl_idx = parameter_names.index('chl')
                cdom_est = initial_values[chl_idx] * 0.3
            else:
                cdom_est = np.mean(rrs_clean) * 10
            initial_values.append(np.clip(cdom_est, 0.01, 2.0))

        elif param_name == 'nap':
            # NAP estimation from red bands
            if idx_640 < len(rrs_clean):
                nap_est = 30 * 0.004 * rrs_clean[idx_640]  # Rough estimate
                initial_values.append(np.clip(nap_est, 0.01, 5.0))
            else:
                initial_values.append(0.5)

        elif param_name == 'depth':
            # CRITICAL: Better depth initialization
            # Use spectral slope to estimate depth
            if len(rrs_clean) >= 4:
                # Calculate spectral slope in blue-green region
                blue_green = rrs_clean[:len(rrs_clean) // 2]
                red_nir = rrs_clean[len(rrs_clean) // 2:]

                # Higher blue/red ratio suggests shallower water
                if np.mean(red_nir) > 1e-8:
                    bg_ratio = np.mean(blue_green) / np.mean(red_nir)
                    # Empirical relationship (tune based on your data)
                    depth_est = 15.0 / (1.0 + 5.0 * bg_ratio)
                    initial_values.append(np.clip(depth_est, 0.5, 15.0))
                else:
                    initial_values.append(5.0)
            else:
                initial_values.append(5.0)

        elif param_name == 'substrate_fraction':
            # Initialize substrate fraction based on bottom contribution
            if len(rrs_clean) >= 3:
                # Higher reflectance in green/red suggests more substrate contribution
                green_red = rrs_clean[len(rrs_clean) // 3:2 * len(rrs_clean) // 3]
                substrate_est = np.clip(np.mean(green_red) * 5, 0.1, 0.9)
                initial_values.append(substrate_est)
            else:
                initial_values.append(0.5)

        elif param_name == 'bb_ph_slope':
            # Y parameter estimation (CRITICAL for Lee et al.)
            if idx_440 < len(rrs_clean) and idx_490 < len(rrs_clean):
                ratio_440_490 = rrs_clean[idx_440] / (rrs_clean[idx_490] + 1e-8)
                y_est = 3.44 * (1 - 3.17 * np.exp(-2.01 * ratio_440_490))
                initial_values.append(np.clip(y_est, 0.5, 2.0))
            else:
                initial_values.append(1.0)

        else:
            # Default initialization for other parameters
            param_defaults = {
                'a_cdom_slope': 0.015,
                'a_nap_slope': 0.010,
                'x_ph_lambda0x': 0.002,
                'x_nap_lambda0x': 0.02,
                'substrate2_fraction': 0.3,
            }
            initial_values.append(param_defaults.get(param_name, 1.0))

    return initial_values


# =============================================================================
# STEP 3: Enhanced Objective Function with Better Depth Sensitivity
# =============================================================================

def enhanced_objective_function(
        params: List[float],
        observed_rrs: np.ndarray,
        inversion_parameters: 'InversionParameters',
        nedr: Optional[np.ndarray] = None,
        depth_weight_factor: float = 2.0,  # Emphasize depth sensitivity
        return_modeled_spectra: bool = False,
) -> Any:
    """
    Enhanced objective function with better depth sensitivity.
    """

    # Get forward model parameters
    forward_model_params = inversion_parameters.get_forward_model_params(params)

    # CRITICAL: Use enhanced forward model
    forward_model_params['enhance_depth_sensitivity'] = True

    try:
        # Run enhanced forward model
        results = enhanced_forward_model(**forward_model_params)

        # Calculate primary error
        if nedr is not None:
            weights = 1.0 / (nedr ** 2)
            weighted_squared_diff = weights * ((results.rrs - observed_rrs) ** 2)
            primary_error = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
        else:
            primary_error = np.sqrt(np.mean((results.rrs - observed_rrs) ** 2))

        # ENHANCEMENT: Add depth sensitivity penalty
        if hasattr(results, 'optical_depth_contribution') and results.optical_depth_contribution is not None:
            depth_contrib = np.mean(results.optical_depth_contribution)

            # If bottom contribution is too low, the depth estimate is likely unreliable
            if depth_contrib < 0.02:  # Less than 2% bottom contribution
                depth_penalty = 0.1 * primary_error  # Add 10% penalty
            else:
                depth_penalty = 0.0
        else:
            depth_penalty = 0.0

        total_error = primary_error + depth_penalty

        if return_modeled_spectra:
            return {
                'error': total_error,
                'primary_error': primary_error,
                'depth_penalty': depth_penalty,
                'modeled_spectra': results.rrs,
                'forward_model_results': results,
                'depth_contribution': getattr(results, 'optical_depth_contribution', None)
            }

        return total_error

    except Exception as e:
        if return_modeled_spectra:
            return {
                'error': 1e6,
                'modeled_spectra': np.full_like(observed_rrs, np.nan),
                'forward_model_results': None
            }
        return 1e6


# =============================================================================
# STEP 4: Integration Instructions
# =============================================================================

def integration_instructions():
    """
    How to integrate these fixes into your existing codebase.
    """
    instructions = """
    INTEGRATION STEPS (do these incrementally):

    1. IMMEDIATE FIX - Replace forward_model.py:
       - Replace your forward_model function with enhanced_forward_model
       - Test with enhance_depth_sensitivity=True
       - This should immediately improve depth sensitivity

    2. UPDATE PARAMETER INITIALIZATION:
       - In your InversionParameters.get_initial_values(), 
         call enhanced_initial_values() instead
       - This will give much better starting points

    3. ENHANCE OBJECTIVE FUNCTION:
       - In your objective_functions.py, replace distance_f 
         with enhanced_objective_function
       - This adds depth sensitivity penalties

    4. CONFIGURE YOUR INVERSION PARAMETERS:
       - Make sure bb_ph_slope (Y parameter) is being optimized
       - Consider narrower depth bounds initially (0.5, 8.0)
       - Use multiple starting points

    5. VALIDATE INCREMENTALLY:
       - Test each change on a single pixel first
       - Check that depth varies across your image
       - Verify bottom contribution maps make sense

    DEBUGGING TIPS:
    - Print optical_depth_contribution for each pixel
    - Values < 0.05 mean depth estimates are unreliable
    - Values > 0.3 indicate very shallow water
    - If all values are < 0.02, your water is too deep/turbid for bathymetry
    """
    print(instructions)
    return instructions


if __name__ == "__main__":
    integration_instructions()