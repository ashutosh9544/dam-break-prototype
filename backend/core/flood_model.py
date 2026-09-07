"""
Unified Flood Hydrodynamic Simulation Orchestrator
Connects dam breach outflow modeling with hydrodynamic simulation engines (SPH, Delft3D, Fallback Prototype)
and downstream disaster risk assessment.
"""

from typing import Dict, Any, List, Optional
import os
from backend.core.dam_model import generate_breach_hydrograph, validate_dam_inputs
from backend.core.sph_model import run_sph_simulation
from backend.core.delft3d_model import run_delft3d_simulation, is_delft3d_available
from backend.core.gis_processor import GISProcessor
from backend.core.risk_model import analyze_flood_risk


def run_flood_simulation(
    water_level: float,
    dam_height: float,
    breach_width: float,
    breach_time: float,
    engine: str = "SPH",
    dem_path: Optional[str] = None,
    dam_coord: Optional[tuple] = None,
    downstream_distance: float = 25.0,
    reservoir_volume_mcm: float = 0.0,
    settlements_file: Optional[str] = None,
    infrastructure_file: Optional[str] = None,
    manning_n: float = 0.045
) -> Dict[str, Any]:
    """
    Unified entry point for hydrodynamic flood simulation.
    
    Parameters:
        water_level: Water head above breach invert (m)
        dam_height: Total dam structure height (m)
        breach_width: Average breach width (m)
        breach_time: Formation time (minutes)
        engine: 'SPH' or 'Delft3D'
    
    Returns:
        Dict strictly conforming to Section 8 & Section 11 API contract.
    """
    validate_dam_inputs(water_level, dam_height, breach_width, breach_time)

    # Resolve default paths
    default_base = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\data"
    if dem_path is None:
        dem_path = os.path.join(default_base, "terrain", "hirakud_dem.tif")
    if dam_coord is None:
        dam_coord = (83.871, 21.527)  # Hirakud Dam coordinates (Lon, Lat)

    # 1. Calculate breach outflow hydrograph
    hydrograph = generate_breach_hydrograph(
        water_level=water_level,
        dam_height=dam_height,
        breach_width=breach_width,
        breach_time=breach_time,
        reservoir_volume_mcm=reservoir_volume_mcm
    )

    # 2. Ingest DEM terrain
    dem_meta = GISProcessor.inspect_and_load_dem(dem_path)
    dem_array = dem_meta["elevation_array"]
    bounds = dem_meta["bounds"]

    # 3. Dispatch to selected hydrodynamic engine
    engine_upper = engine.strip().upper()
    if engine_upper == "SPH":
        raw_result = run_sph_simulation(
            dem_data=dem_array,
            bounds=bounds,
            dam_coord=dam_coord,
            hydrograph=hydrograph,
            manning_n=manning_n
        )
    elif engine_upper in ["DELFT3D", "DELFT-3D", "DELFT"]:
        raw_result = run_delft3d_simulation(
            dem_data=dem_array,
            bounds=bounds,
            dam_coord=dam_coord,
            hydrograph=hydrograph,
            manning_n=manning_n
        )
    else:
        # Default to SPH
        raw_result = run_sph_simulation(
            dem_data=dem_array,
            bounds=bounds,
            dam_coord=dam_coord,
            hydrograph=hydrograph,
            manning_n=manning_n
        )

    # 4. Perform deterministic disaster risk intersection
    risk_summary = analyze_flood_risk(
        flood_extent_features=raw_result["flood_extent"],
        settlements_file=settlements_file,
        infrastructure_file=infrastructure_file,
        max_depth=raw_result["max_depth"],
        min_arrival_time=raw_result["arrival_time"]
    )

    # 5. Assemble unified result structure conforming to Section 8 contract
    combined_result = {
        "engine": raw_result["engine"],
        "max_discharge": raw_result["max_discharge"],
        "max_depth": raw_result["max_depth"],
        "arrival_time": raw_result["arrival_time"],
        "flood_extent": raw_result["flood_extent"],
        "risk_summary": risk_summary,
        "depth_grid": raw_result.get("depth_grid", []),
        "hydrograph": {
            "time_minutes": hydrograph["time_minutes"],
            "discharge_m3s": hydrograph["discharge_m3s"],
            "total_volume_mcm": hydrograph["total_volume_mcm"]
        },
        "metadata": {
            **raw_result.get("metadata", {}),
            "dam_inputs": {
                "water_level": water_level,
                "dam_height": dam_height,
                "breach_width": breach_width,
                "breach_time": breach_time,
                "dam_latitude": dam_coord[1] if dam_coord else 21.527,
                "dam_longitude": dam_coord[0] if dam_coord else 83.871,
                "downstream_distance": downstream_distance
            },
            "dem_info": {
                "crs": dem_meta["crs"],
                "resolution": dem_meta["resolution"],
                "bounds": bounds
            }
        }
    }

    return combined_result
