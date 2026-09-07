"""
Results and GIS Export API Router
Endpoints:
- GET /api/results/{scenario_id}: Fetches complete result dictionary for a simulation run.
- GET /api/export/{scenario_id}/{format}: Downloads GIS assets (.shp.zip, .kml, .geojson).
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from backend.core.scenario_manager import ScenarioManager

router = APIRouter(prefix="/api", tags=["results"])

scenario_mgr = ScenarioManager()
outputs_base = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\outputs"


@router.get("/results/{scenario_id}")
def get_scenario_result(scenario_id: str):
    """Retrieve full simulation results by scenario ID."""
    data = scenario_mgr.get_scenario(scenario_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Scenario with ID '{scenario_id}' not found.")
    return data


@router.get("/export/{scenario_id}/{format}")
def export_scenario_gis(scenario_id: str, format: str):
    """
    Download GIS export file for a scenario.
    Format options: 'geojson', 'kml', 'shp'
    """
    fmt = format.lower().strip()
    if fmt == "geojson":
        file_p = os.path.join(outputs_base, "geojson", f"flood_extent_{scenario_id}.geojson")
        media_type = "application/geo+json"
        filename = f"flood_extent_{scenario_id}.geojson"
    elif fmt == "kml":
        file_p = os.path.join(outputs_base, "kml", f"flood_extent_{scenario_id}.kml")
        media_type = "application/vnd.google-earth.kml+xml"
        filename = f"flood_extent_{scenario_id}.kml"
    elif fmt in ["shp", "zip", "shapefile"]:
        file_p = os.path.join(outputs_base, "shp", f"flood_extent_{scenario_id}.zip")
        media_type = "application/zip"
        filename = f"flood_extent_{scenario_id}.zip"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Use 'geojson', 'kml', or 'shp'.")

    if not os.path.exists(file_p):
        raise HTTPException(status_code=404, detail=f"Export file not found for scenario '{scenario_id}' in format '{format}'.")

    return FileResponse(
        path=file_p,
        media_type=media_type,
        filename=filename
    )
