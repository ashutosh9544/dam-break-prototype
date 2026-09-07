"""
Unit tests for Dam Break Breach Hydraulic Model (Froehlich / MacDonald formulations)
Tests physical sanity, monotonicity, and contract adherence.
"""

import pytest
from backend.core.dam_model import (
    calculate_peak_discharge,
    generate_breach_hydrograph,
    validate_dam_inputs
)


def test_input_validation_errors():
    """Verify that physically impossible or negative inputs raise descriptive ValueErrors."""
    with pytest.raises(ValueError, match="Water level must be positive"):
        validate_dam_inputs(water_level=-10.0, dam_height=50.0, breach_width=20.0, breach_time=30.0)

    with pytest.raises(ValueError, match="Dam height must be positive"):
        validate_dam_inputs(water_level=20.0, dam_height=0.0, breach_width=20.0, breach_time=30.0)

    with pytest.raises(ValueError, match="exceeds maximum allowable overtopping"):
        validate_dam_inputs(water_level=120.0, dam_height=50.0, breach_width=20.0, breach_time=30.0)

    with pytest.raises(ValueError, match="Breach width must be positive"):
        validate_dam_inputs(water_level=40.0, dam_height=50.0, breach_width=-5.0, breach_time=30.0)

    with pytest.raises(ValueError, match="Breach time must be positive"):
        validate_dam_inputs(water_level=40.0, dam_height=50.0, breach_width=20.0, breach_time=0.0)


def test_monotonicity_water_level():
    """Sanity Check 1: Higher stored water level must produce greater peak discharge."""
    q_low = calculate_peak_discharge(water_level=20.0, dam_height=60.0, breach_width=30.0, breach_time=45.0)
    q_high = calculate_peak_discharge(water_level=55.0, dam_height=60.0, breach_width=30.0, breach_time=45.0)
    assert q_high > q_low, f"Expected higher discharge for greater head: {q_high} vs {q_low}"


def test_monotonicity_breach_width():
    """Sanity Check 2: Larger breach width must produce greater peak discharge."""
    q_narrow = calculate_peak_discharge(water_level=45.0, dam_height=60.0, breach_width=15.0, breach_time=45.0)
    q_wide = calculate_peak_discharge(water_level=45.0, dam_height=60.0, breach_width=60.0, breach_time=45.0)
    assert q_wide > q_narrow, f"Expected higher discharge for wider breach: {q_wide} vs {q_narrow}"


def test_attenuation_breach_time():
    """Sanity Check 3: Longer breach formation time must attenuate peak discharge."""
    q_fast = calculate_peak_discharge(water_level=50.0, dam_height=60.0, breach_width=40.0, breach_time=15.0)
    q_slow = calculate_peak_discharge(water_level=50.0, dam_height=60.0, breach_width=40.0, breach_time=90.0)
    assert q_fast > q_slow, f"Expected fast breach to have higher peak than slow breach: {q_fast} vs {q_slow}"


def test_hydrograph_structure_and_conservation():
    """Verify that the generated hydrograph has positive values, matches peak, and has non-zero volume."""
    res = generate_breach_hydrograph(
        water_level=48.0,
        dam_height=55.0,
        breach_width=35.0,
        breach_time=30.0,
        total_duration_hours=4.0
    )

    assert "peak_discharge" in res
    assert "time_minutes" in res
    assert "discharge_m3s" in res
    assert "total_volume_mcm" in res
    assert res["peak_discharge"] > 100.0
    assert res["total_volume_mcm"] > 0.0

    # No negative flows
    assert all(q >= 0.0 for q in res["discharge_m3s"]), "Detected negative discharge in hydrograph"
    # Max in hydrograph should equal or closely match peak
    assert max(res["discharge_m3s"]) == pytest.approx(res["peak_discharge"], rel=0.05)
