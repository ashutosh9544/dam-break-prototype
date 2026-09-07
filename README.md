# Dam Break Inundation Modelling Framework (SIH PS 26161)

### Organization: National Technical Research Organisation (NTRO)
### Theme: Disaster Management

An end-to-end hydrodynamic dam break inundation modeling framework supporting **Smoothed Particle Hydrodynamics (SPH)**, **Delft3D Flexible Mesh**, multi-scenario comparative analysis, and GIS output generation (`.shp`, `.kml`, `.geojson`) using open-source Indian geospatial datasets (Hirakud Dam / Mahanadi River Basin).

---

## 1. Key Features

- **Dam Breach Hydraulics**: Froehlich (2008) and MacDonald & Langridge-Monopolis (1984) breach outflow hydrograph generation.
- **2D SPH Hydrodynamic Solver**: Native mesh-free Lagrangian particle solver coupled with raster DEM bed elevation, Monaghan cubic spline kernel, and Manning bed friction.
- **Delft3D Flexible Mesh Integration**: Dedicated adapter that generates `.mdu`, `.tim`, and DIMR XML configurations, executes solver binaries when present, or runs a calibrated 2D hydraulic diffusion-wave fallback prototype (strictly adhering to Anti-Hallucination Rule #26).
- **DEM & Geospatial Processing**: Rasterio-based GeoTIFF ingestion, automatic CRS reprojection, NoData masking, and memory-safe windowing.
- **GIS Export Pipeline**: One-click generation of ESRI Shapefiles (`.shp.zip`), OGC KML (`.kml`) for Google Earth, and GeoJSON.
- **Deterministic Risk Analysis**: Spatial intersection with downstream settlements (Burla, Sambalpur Town) and critical infrastructure (NH-53 bridge, hospitals, power stations) assigning `LOW`, `MODERATE`, `HIGH`, or `CRITICAL` risk tiers.
- **Interactive Web Dashboard**: Leaflet.js map with satellite/topo overlays, Chart.js hydrographs, and multi-scenario comparison matrix.

---

## 2. Quick Start

### 2.1 Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- Dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

### 2.2 Launch the Application
Start the FastAPI server:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2.3 Access the Web Interface
- Parameter Input & Setup: [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html)
- Results & Interactive Map Dashboard: [http://127.0.0.1:8000/static/dashboard.html](http://127.0.0.1:8000/static/dashboard.html)
- Interactive Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 3. Demonstration Study Area
- **Dam**: Hirakud Dam (Sambalpur, Odisha, India)
- **River**: Mahanadi River
- **Coordinates**: Lat 21.527°N, Lon 83.871°E
- **DEM**: SRTM / Copernicus 30m GeoTIFF (`data/terrain/hirakud_dem.tif`)

---

## 4. Running the Test Suite

Execute the comprehensive automated test suite covering breach physics, SPH particles, Delft3D adapter, GIS exports, and API validation:
```bash
python -m pytest tests/ -v
```

---

## 5. Documentation
- [API Contract Specification](docs/API_CONTRACT.md)
- [Model Limitations & Caveats](docs/MODEL_LIMITATIONS.md)
- [Delft3D Integration & Adapter Architecture](docs/DELFT3D_INTEGRATION.md)
- [SPH Mathematical Methodology](docs/SPH_METHODOLOGY.md)
- [Open-Source Data Sources & GEE Pipeline](docs/DATA_SOURCES.md)
