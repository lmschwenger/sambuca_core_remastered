"""Basic tests for the forward model functionality."""

import numpy as np
import pytest

import sambuca_core as sbc


def test_forward_model_basic():
    """Test the forward model with simple inputs."""
    # Set up test data
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.01, 0.1, num_bands)
    a_ph_star = np.linspace(0.05, 0.5, num_bands)
    substrate1 = np.linspace(0.1, 0.5, num_bands)

    # Run forward model
    results = sbc.forward_model(
        chl=1.5,
        cdom=0.5,
        nap=2.0,
        depth=5.0,
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands
    )

    # Basic validation that the results object has the expected attributes
    assert hasattr(results, 'rrs')
    assert hasattr(results, 'rrsdp')
    assert hasattr(results, 'r_0_minus')
    assert hasattr(results, 'rdp_0_minus')
    assert hasattr(results, 'a')
    assert hasattr(results, 'bb')

    # Validate shapes
    assert len(results.rrs) == num_bands
    assert len(results.rrsdp) == num_bands
    assert len(results.a) == num_bands
    assert len(results.bb) == num_bands

    # Validate relationships
    assert np.allclose(results.r_0_minus, results.rrs * np.pi)
    assert np.allclose(results.rdp_0_minus, results.rrsdp * np.pi)

    # Validate total absorption
    expected_a_ph = 1.5 * a_ph_star  # chl * a_ph_star
    expected_a = a_water + expected_a_ph + results.a_cdom + results.a_nap
    assert np.allclose(results.a, expected_a)

    # Test substrate without substrate2
    assert np.allclose(results.r_substratum, substrate1)


def test_forward_model_with_two_substrates():
    """Test the forward model with two substrates."""
    # Set up test data
    num_bands = 10
    wavelengths = np.linspace(400, 800, num_bands)
    a_water = np.linspace(0.01, 0.1, num_bands)
    a_ph_star = np.linspace(0.05, 0.5, num_bands)
    substrate1 = np.linspace(0.1, 0.5, num_bands)
    substrate2 = np.linspace(0.2, 0.6, num_bands)
    substrate_fraction = 0.7

    # Run forward model
    results = sbc.forward_model(
        chl=1.5,
        cdom=0.5,
        nap=2.0,
        depth=5.0,
        substrate1=substrate1,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        num_bands=num_bands,
        substrate2=substrate2,
        substrate_fraction=substrate_fraction
    )

    # Calculate expected combined substrate
    expected_substrate = substrate_fraction * substrate1 + (1.0 - substrate_fraction) * substrate2

    # Validate combined substrate
    assert np.allclose(results.r_substratum, expected_substrate)