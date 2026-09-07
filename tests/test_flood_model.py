"""
Unit tests for the Unified Flood Simulation Orchestrator (backend/core/flood_model.py)
"""

import pytest
from backend.core.flood_model import run_flood_simulation


def test_unified_flood_simulation_sph():
    """Verify SPH simulation orchestration and contract compliance."""
    result = run_flood_simulation(
        water_level=55.0,
        dam_height=60.0,
        breach_width=40.0,
        breach_time=35.0,
        engine="SPH"
    )

    # Check Section 8 required fields
    assert result["engine"] == "SPH"
    assert "max_discharge" in result and result["max_discharge"] > 0
    assert "max_depth" in result and result["max_depth"] > 0
    assert "arrival_time" in result and result["arrival_time"] > 0
    assert "flood_extent" in result and isinstance(result["flood_extent"], list)
    assert "risk_summary" in result

    # Check risk summary
    risk = result["risk_summary"]
    assert risk["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert isinstance(risk["population_affected"], int)
    assert isinstance(risk["infrastructure_affected"], int)
    assert risk["population_affected"] >= 0

    # Hydrograph
    assert "hydrograph" in result
    assert len(result["hydrograph"]["time_minutes"]) > 10


def test_unified_flood_simulation_delft3d_fallback():
    """Verify Delft3D adapter dispatcher handles fallback cleanly without errors."""
    result = run_flood_simulation(
        water_level=50.0,
        dam_height=60.0,
        breach_width=30.0,
        breach_time=40.0,
        engine="Delft3D"
    )

    # Engine must be Delft3D (if installed) or Fallback Prototype (if not)
    assert result["engine"] in ["Delft3D", "Fallback Prototype"]
    assert result["max_discharge"] > 0
    assert result["max_depth"] > 0
    assert len(result["flood_extent"]) > 0
    assert result["risk_summary"]["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
