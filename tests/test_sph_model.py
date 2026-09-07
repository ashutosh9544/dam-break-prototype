"""
Unit tests for 2D Shallow Water SPH Hydrodynamic Solver
"""

import pytest
import numpy as np
from backend.core.dam_model import generate_breach_hydrograph
from backend.core.sph_model import SPHSimulationEngine, run_sph_simulation


@pytest.fixture
def synthetic_dem_and_hydrograph():
    # 50x50 synthetic DEM sloping from west (180m) to east (140m)
    rows, cols = 40, 50
    x = np.linspace(0, 1, cols)
    y = np.linspace(0, 1, rows)
    xx, yy = np.meshgrid(x, y)
    dem = (180.0 - 40.0 * xx + 5.0 * np.sin(yy * 3.14)).astype(np.float32)

    bounds = (83.80, 21.40, 84.05, 21.60)
    dam_coord = (83.871, 21.527)

    hydrograph = generate_breach_hydrograph(
        water_level=50.0,
        dam_height=60.0,
        breach_width=30.0,
        breach_time=30.0,
        total_duration_hours=2.0
    )
    return dem, bounds, dam_coord, hydrograph


def test_sph_simulation_execution(synthetic_dem_and_hydrograph):
    dem, bounds, dam_coord, hydrograph = synthetic_dem_and_hydrograph

    result = run_sph_simulation(
        dem_data=dem,
        bounds=bounds,
        dam_coord=dam_coord,
        hydrograph=hydrograph,
        manning_n=0.040
    )

    assert result["engine"] == "SPH"
    assert result["max_discharge"] > 0.0
    assert result["max_depth"] > 0.0
    assert result["arrival_time"] > 0.0
    assert isinstance(result["flood_extent"], list)
    assert len(result["flood_extent"]) > 0

    # Ensure no NaN in depth grid
    depth_grid = np.array(result["depth_grid"])
    assert not np.isnan(depth_grid).any()
    assert not np.isinf(depth_grid).any()
    assert np.all(depth_grid >= 0.0)


def test_sph_kernel_properties():
    """Verify kernel is non-negative and monotonically decreasing with distance."""
    dem = np.zeros((10, 10), dtype=np.float32)
    engine = SPHSimulationEngine(
        dem_data=dem,
        bounds=(83.8, 21.4, 84.0, 21.6),
        dam_coord=(83.87, 21.52),
        hydrograph={"time_minutes": [0, 10], "discharge_m3s": [0, 100], "peak_discharge": 100, "total_volume_mcm": 1.0}
    )

    w0, dw0 = engine._cubic_spline_kernel(0.0)
    w1, dw1 = engine._cubic_spline_kernel(engine.h_smooth * 0.5)
    w2, dw2 = engine._cubic_spline_kernel(engine.h_smooth * 1.5)
    w_far, _ = engine._cubic_spline_kernel(engine.h_smooth * 2.5)

    assert w0 > w1 > w2 > 0.0
    assert w_far == 0.0
    assert dw1 < 0.0  # negative gradient as r increases
