"""
Simulation API Router
Endpoints:
- POST /api/simulate: Orchestrates dam-break simulation, GIS exports, and scenario recording.
- GET /api/scenarios: Lists all saved simulation scenarios.
- POST /api/scenarios/compare: Side-by-side scenario comparison.
- GET /api/datasets: Lists available Indian rivers, dams, DEMs, and satellite datasets.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import os
import json

from backend.core.flood_model import run_flood_simulation
from backend.core.gis_processor import GISProcessor
from backend.core.scenario_manager import ScenarioManager
from backend.core.delft3d_model import is_delft3d_available

router = APIRouter(prefix="/api", tags=["simulation"])

scenario_mgr = ScenarioManager()
gis_proc = GISProcessor()


class SimulationRequest(BaseModel):
    # Preserved base contract fields (Section 8)
    water_level: float = Field(..., description="Water depth/head above breach invert (m)", gt=0)
    dam_height: float = Field(..., description="Dam structure height (m)", gt=0)
    breach_width: float = Field(..., description="Breach width (m)", gt=0)
    breach_time: float = Field(..., description="Breach formation time (minutes)", gt=0)

    # Location / context fields (Section 20)
    dam_latitude: Optional[float] = Field(21.527, description="Dam Latitude (degrees N)", ge=-90.0, le=90.0)
    dam_longitude: Optional[float] = Field(83.871, description="Dam Longitude (degrees E)", ge=-180.0, le=180.0)
    downstream_distance: Optional[float] = Field(25.0, description="Downstream reach distance (km)", gt=0)

    # Optional fields
    engine: Optional[str] = Field("SPH", description="Hydrodynamic engine: 'SPH' or 'Delft3D'")
    dam_name: Optional[str] = Field("Hirakud Dam", description="Dam name")
    river_name: Optional[str] = Field("Mahanadi River", description="River name")
    scenario_name: Optional[str] = Field(None, description="Descriptive name for this scenario")
    reservoir_volume_mcm: Optional[float] = Field(0.0, description="Gross reservoir volume (MCM)")


class CompareRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_length=1, description="List of scenario IDs to compare")


@router.post("/simulate")
def simulate(req: SimulationRequest) -> Dict[str, Any]:
    """
    Execute dam break inundation simulation.
    Supports SPH and Delft3D (with automatic fallback prototype detection).
    """
    try:
        # Run simulation
        result = run_flood_simulation(
            water_level=req.water_level,
            dam_height=req.dam_height,
            breach_width=req.breach_width,
            breach_time=req.breach_time,
            engine=req.engine or "SPH",
            dam_coord=(req.dam_longitude or 83.871, req.dam_latitude or 21.527),
            downstream_distance=req.downstream_distance or 25.0,
            reservoir_volume_mcm=req.reservoir_volume_mcm or 0.0
        )

        scenario_name = req.scenario_name or f"{req.dam_name} ({result['engine']})"
        result["scenario_name"] = scenario_name
        result["dam_name"] = req.dam_name
        result["river_name"] = req.river_name

        # Save scenario to store
        scenario_id = scenario_mgr.save_scenario(result)
        result["scenario_id"] = scenario_id

        # Pre-generate GIS exports
        try:
            gis_proc.export_geojson(result["flood_extent"], scenario_id)
            gis_proc.export_kml(result["flood_extent"], scenario_id, document_name=scenario_name)
            gis_proc.export_shapefile(result["flood_extent"], scenario_id)
        except Exception as e:
            # Non-blocking export warning
            result["metadata"]["gis_export_warning"] = str(e)

        result["export_urls"] = {
            "geojson": f"/api/export/{scenario_id}/geojson",
            "kml": f"/api/export/{scenario_id}/kml",
            "shp": f"/api/export/{scenario_id}/shp"
        }

        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(ex)}")


@router.get("/scenarios")
def list_scenarios() -> List[Dict[str, Any]]:
    """Retrieve summary of all stored simulation scenarios."""
    return scenario_mgr.list_scenarios()


@router.post("/scenarios/compare")
def compare_scenarios(req: CompareRequest) -> Dict[str, Any]:
    """Compare multiple scenario simulation results."""
    try:
        return scenario_mgr.compare_scenarios(req.scenario_ids)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/datasets")
def get_datasets() -> Dict[str, Any]:
    """Retrieve available study area datasets, DEMs, and hydrological profiles."""
    base_data = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\data"
    dams = []
    dam_file = os.path.join(base_data, "dam", "hirakud_dam.json")
    if os.path.exists(dam_file):
        with open(dam_file, "r") as f:
            dams.append(json.load(f))

    hydrology = []
    hydro_file = os.path.join(base_data, "hydrology", "mahanadi_hydrology.json")
    if os.path.exists(hydro_file):
        with open(hydro_file, "r") as f:
            hydrology.append(json.load(f))

    satellite = {}
    sat_file = os.path.join(base_data, "satellite", "satellite_metadata.json")
    if os.path.exists(sat_file):
        with open(sat_file, "r") as f:
            satellite = json.load(f)

    delft3d_installed, _ = is_delft3d_available()

    return {
        "dams": dams,
        "hydrology": hydrology,
        "satellite": satellite,
        "supported_engines": [
            {
                "id": "SPH",
                "name": "Smooth Particle Hydrodynamics (SPH)",
                "status": "AVAILABLE",
                "description": "2D Shallow Water Lagrangian SPH Solver (Monaghan formulation)"
            },
            {
                "id": "Delft3D",
                "name": "Delft3D Flexible Mesh",
                "status": "AVAILABLE" if delft3d_installed else "INTEGRATION READY BUT NOT INSTALLED (Fallback Prototype Active)",
                "description": "Delft3D hydrodynamic solver with calibrated 2D hydraulic diffusion-wave fallback"
            }
        ]
    }
