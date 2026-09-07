# API Contract: Dam Break Inundation Modelling

This document specifies the exact JSON schemas and endpoints implemented in the V1 prototype for Smart India Hackathon (SIH 26161 - NTRO).

---

## 1. Endpoints Overview

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/simulate` | Executes hydrodynamic dam break simulation, risk analysis, and GIS exports. |
| `GET` | `/api/results/{scenario_id}` | Retrieves complete result object for a simulation scenario. |
| `GET` | `/api/scenarios` | Lists summaries of all recorded simulation scenarios. |
| `POST` | `/api/scenarios/compare` | Compares two or more simulation runs and returns deltas. |
| `GET` | `/api/export/{scenario_id}/{format}` | Downloads GIS assets (`shp`, `kml`, `geojson`). |
| `GET` | `/api/datasets` | Lists available Indian river/dam datasets and engine statuses. |
| `GET` | `/api/health` | Service health and solver engine availability check. |

---

## 2. Base Input Contract (`POST /api/simulate`)

Preserves the required fields with strict validation:

```json
{
  "water_level": 58.0,
  "dam_height": 61.0,
  "breach_width": 45.0,
  "breach_time": 40.0,
  "engine": "SPH",
  "dam_name": "Hirakud Dam",
  "river_name": "Mahanadi River",
  "scenario_name": "Monsoon Overtopping Scenario",
  "reservoir_volume_mcm": 5896.0
}
```

### Field Definitions:
- `water_level` (float, required): Height of water column above breach invert (meters). Must be $> 0$.
- `dam_height` (float, required): Total height of dam structure (meters).
- `breach_width` (float, required): Average final breach width (meters).
- `breach_time` (float, required): Breach formation time (minutes).
- `engine` (string, optional): Simulation engine: `"SPH"` or `"Delft3D"`. Defaults to `"SPH"`.
- `dam_name` (string, optional): Name of dam. Defaults to `"Hirakud Dam"`.
- `river_name` (string, optional): Name of river. Defaults to `"Mahanadi River"`.
- `scenario_name` (string, optional): User-defined label for scenario comparisons.

---

## 3. Simulation Response Contract

Conforms strictly to Section 8 & Section 11 specifications:

```json
{
  "engine": "SPH",
  "max_discharge": 14250.0,
  "max_depth": 7.8,
  "arrival_time": 16.4,
  "flood_extent": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[83.87, 21.52], [83.88, 21.52], [83.88, 21.53], [83.87, 21.53], [83.87, 21.52]]]
      },
      "properties": {
        "depth_m": 4.2,
        "arrival_time_min": 18.0,
        "zone": "Deep Inundation (> 3.0m)",
        "risk_level": "CRITICAL",
        "fill_color": "#b30000",
        "engine": "SPH"
      }
    }
  ],
  "risk_summary": {
    "risk_level": "CRITICAL",
    "population_affected": 24800,
    "infrastructure_affected": 4,
    "details": {
      "submerged_settlements": [
        {
          "name": "Burla",
          "total_population": 46000,
          "affected_population": 23000,
          "water_depth_m": 4.2,
          "arrival_time_min": 16.4,
          "severity_zone": "Deep Inundation (> 3.0m)"
        }
      ],
      "submerged_infrastructure": [
        {
          "name": "VSS Institute of Medical Sciences (Burla)",
          "type": "Healthcare / Hospital",
          "criticality": "CRITICAL",
          "water_depth_m": 3.8,
          "arrival_time_min": 17.2
        }
      ]
    }
  },
  "depth_grid": [[...]],
  "hydrograph": {
    "time_minutes": [0.0, 5.0, 10.0, ...],
    "discharge_m3s": [0.0, 1200.0, 8500.0, ...],
    "total_volume_mcm": 142.5
  },
  "scenario_id": "a1b2c3d4",
  "export_urls": {
    "geojson": "/api/export/a1b2c3d4/geojson",
    "kml": "/api/export/a1b2c3d4/kml",
    "shp": "/api/export/a1b2c3d4/shp"
  },
  "metadata": {
    "method": "2D Shallow Water SPH (Monaghan formulation)",
    "particles_simulated": 850,
    "inundated_area_sqkm": 38.4
  }
}
```

### Risk Summary Levels:
- `CRITICAL`
- `HIGH`
- `MODERATE`
- `LOW`

### Engine Values:
- `"SPH"`: When SPH engine was executed.
- `"Delft3D"`: When Delft3D Flexible Mesh binary was executed.
- `"Fallback Prototype"`: When Delft3D binaries were not present on the host system.
