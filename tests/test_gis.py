"""
Unit tests for GIS Processor: DEM ingestion, Shapefile (.shp.zip), KML, and GeoJSON export.
"""

import os
import zipfile
import pytest
from backend.core.gis_processor import GISProcessor


@pytest.fixture
def sample_flood_features():
    return [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[83.87, 21.52], [83.88, 21.52], [83.88, 21.53], [83.87, 21.53], [83.87, 21.52]]
                ]
            },
            "properties": {
                "depth_m": 3.5,
                "arrival_time_min": 15.0,
                "zone": "Deep Inundation (> 3.0m)",
                "risk_level": "CRITICAL",
                "engine": "SPH"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[83.88, 21.51], [83.90, 21.51], [83.90, 21.52], [83.88, 21.52], [83.88, 21.51]]
                ]
            },
            "properties": {
                "depth_m": 1.8,
                "arrival_time_min": 25.0,
                "zone": "Medium Inundation (1.5m - 3.0m)",
                "risk_level": "HIGH",
                "engine": "SPH"
            }
        }
    ]


def test_dem_inspection_and_loading():
    """Verify DEM loading, CRS extraction, resolution, and bounds."""
    dem_path = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\data\terrain\hirakud_dem.tif"
    assert os.path.exists(dem_path), "Demo DEM file missing"

    meta = GISProcessor.inspect_and_load_dem(dem_path)
    assert meta["width"] > 0
    assert meta["height"] > 0
    assert meta["crs"] == "EPSG:4326"
    assert meta["bounds"][0] < meta["bounds"][2]  # west < east
    assert meta["bounds"][1] < meta["bounds"][3]  # south < north
    assert meta["elevation_array"].ndim == 2
    assert meta["min_elevation"] > 100.0  # reasonable terrain elevation


def test_geojson_export(sample_flood_features, tmp_path):
    proc = GISProcessor(outputs_dir=str(tmp_path))
    out_file = proc.export_geojson(sample_flood_features, "test_scen")

    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "FeatureCollection" in content
        assert "83.87" in content


def test_shapefile_export(sample_flood_features, tmp_path):
    proc = GISProcessor(outputs_dir=str(tmp_path))
    zip_path = proc.export_shapefile(sample_flood_features, "test_scen")

    assert os.path.exists(zip_path)
    assert zip_path.endswith(".zip")

    # Verify contents of zip file
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert any(n.endswith(".shp") for n in names)
        assert any(n.endswith(".shx") for n in names)
        assert any(n.endswith(".dbf") for n in names)
        assert any(n.endswith(".prj") for n in names)


def test_kml_export(sample_flood_features, tmp_path):
    proc = GISProcessor(outputs_dir=str(tmp_path))
    kml_path = proc.export_kml(sample_flood_features, "test_scen", "Test Flood Document")

    assert os.path.exists(kml_path)
    with open(kml_path, "r", encoding="utf-8") as f:
        kml_content = f.read()
        assert "<kml xmlns=" in kml_content
        assert "<Polygon>" in kml_content
        assert "<coordinates>" in kml_content
        assert "Test Flood Document" in kml_content
