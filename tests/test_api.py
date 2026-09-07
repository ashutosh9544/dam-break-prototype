"""
Integration and API endpoint tests for FastAPI backend
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "engines" in data
    assert data["engines"]["sph"]["available"] is True


def test_api_datasets():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "dams" in data
    assert len(data["dams"]) > 0
    assert data["dams"][0]["dam_name"] == "Hirakud Dam"


def test_simulate_success():
    payload = {
        "water_level": 50.0,
        "dam_height": 61.0,
        "breach_width": 40.0,
        "breach_time": 45.0,
        "engine": "SPH",
        "scenario_name": "API Test SPH"
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Section 8 Contract checks
    assert data["engine"] == "SPH"
    assert "max_discharge" in data
    assert "max_depth" in data
    assert "arrival_time" in data
    assert "flood_extent" in data
    assert "risk_summary" in data
    assert data["risk_summary"]["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert "scenario_id" in data
    assert "export_urls" in data


def test_simulate_validation_failure():
    # Negative water level
    payload = {
        "water_level": -10.0,
        "dam_height": 60.0,
        "breach_width": 20.0,
        "breach_time": 30.0
    }
    response = client.post("/api/simulate", json=payload)
    # Pydantic gt=0 returns 422 Unprocessable Entity
    assert response.status_code == 422


def test_scenarios_and_compare():
    # Run two simulations to have data to compare
    p1 = {
        "water_level": 40.0,
        "dam_height": 60.0,
        "breach_width": 25.0,
        "breach_time": 40.0,
        "engine": "SPH",
        "scenario_name": "Test Scen 1"
    }
    r1 = client.post("/api/simulate", json=p1).json()
    id1 = r1["scenario_id"]

    p2 = {
        "water_level": 55.0,
        "dam_height": 60.0,
        "breach_width": 60.0,
        "breach_time": 30.0,
        "engine": "SPH",
        "scenario_name": "Test Scen 2"
    }
    r2 = client.post("/api/simulate", json=p2).json()
    id2 = r2["scenario_id"]

    # List scenarios
    list_res = client.get("/api/scenarios")
    assert list_res.status_code == 200
    scenarios = list_res.json()
    assert len(scenarios) >= 2

    # Compare scenarios
    comp_res = client.post("/api/scenarios/compare", json={"scenario_ids": [id1, id2]})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "deltas" in comp_data
    assert "discharge_delta_m3s" in comp_data["deltas"]
    assert comp_data["num_scenarios"] == 2


def test_gis_export_endpoints():
    # Create scenario
    p = {
        "water_level": 48.0,
        "dam_height": 60.0,
        "breach_width": 30.0,
        "breach_time": 40.0,
        "engine": "SPH"
    }
    r = client.post("/api/simulate", json=p).json()
    sid = r["scenario_id"]

    # Test GeoJSON download
    r_geo = client.get(f"/api/export/{sid}/geojson")
    assert r_geo.status_code == 200
    assert "application/geo+json" in r_geo.headers["content-type"]

    # Test KML download
    r_kml = client.get(f"/api/export/{sid}/kml")
    assert r_kml.status_code == 200

    # Test SHP zip download
    r_shp = client.get(f"/api/export/{sid}/shp")
    assert r_shp.status_code == 200
    assert "application/zip" in r_shp.headers["content-type"]
