"""
Unit tests for Delft3D Flexible Mesh Adapter and Fallback Prototype
Verifies input generation, fallback execution, and strict Anti-Hallucination compliance.
"""

import os
import pytest
import numpy as np
from backend.core.dam_model import generate_breach_hydrograph
from backend.core.delft3d_model import (
    is_delft3d_available,
    prepare_delft3d_inputs,
    run_delft3d_simulation
)


def test_delft3d_detection_and_anti_hallucination():
    """
    Verify that if Delft3D is not installed on PATH, the adapter:
    1. Accurately reports it as not available.
    2. Runs the fallback prototype.
    3. STRICTLY sets engine = 'Fallback Prototype' and NEVER 'Delft3D'.
    """
    is_avail, exe_path = is_delft3d_available()

    dem = np.full((30, 30), 160.0, dtype=np.float32)
    bounds = (83.80, 21.40, 84.05, 21.60)
    dam_coord = (83.871, 21.527)
    hydrograph = generate_breach_hydrograph(
        water_level=45.0,
        dam_height=55.0,
        breach_width=30.0,
        breach_time=30.0
    )

    result = run_delft3d_simulation(
        dem_data=dem,
        bounds=bounds,
        dam_coord=dam_coord,
        hydrograph=hydrograph
    )

    if not is_avail:
        # Crucial Anti-Hallucination requirement
        assert result["engine"] == "Fallback Prototype", (
            f"Expected 'Fallback Prototype' when Delft3D is uninstalled, but got {result['engine']}"
        )
        assert result["metadata"]["delft3d_available"] is False
        assert "INTEGRATION READY BUT NOT INSTALLED" in result["metadata"]["delft3d_status"]
    else:
        assert result["engine"] in ["Delft3D", "Fallback Prototype"]


def test_delft3d_input_file_generation(tmp_path):
    """Verify that MDU, DIMR config, and boundary files are correctly generated."""
    work_dir = str(tmp_path / "delft3d_test")
    hydrograph = generate_breach_hydrograph(
        water_level=50.0,
        dam_height=60.0,
        breach_width=40.0,
        breach_time=30.0
    )

    files = prepare_delft3d_inputs(
        work_dir=work_dir,
        model_name="test_model",
        dam_coord=(83.871, 21.527),
        hydrograph=hydrograph,
        bounds=(83.80, 21.40, 84.05, 21.60)
    )

    assert os.path.exists(files["mdu"])
    assert os.path.exists(files["dimr"])
    assert os.path.exists(files["tim"])
    assert os.path.exists(files["ext"])

    # Inspect MDU content
    with open(files["mdu"], "r") as f:
        content = f.read()
        assert "fileType = modelDefinition" in content
        assert "program = D-Flow FM" in content

    # Inspect boundary hydrograph
    with open(files["tim"], "r") as f:
        lines = f.readlines()
        assert len(lines) > 5
        assert "# Time(minutes)" in lines[0]
