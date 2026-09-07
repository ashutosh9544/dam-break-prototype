# Open-Source Data Sources & GEE Integration Workflow

This document catalogs open-source geospatial datasets, hydrological archives, satellite imagery portals, and the Google Earth Engine (GEE) integration pathway for SIH Problem Statement 26161 (NTRO).

---

## 1. Digital Elevation Models (DEM)

| Dataset | Provider | Resolution | Coverage | Access Link |
|---|---|---|---|---|
| **Copernicus DEM (GLO-30)** | ESA / Copernicus | 30 meters | Global / India | [Copernicus Space Component Data Access](https://spacedata.copernicus.eu/) |
| **SRTM (Shuttle Radar Topography Mission)** | NASA / USGS | 30 meters (1 arc-second) | $60^\circ\text{N} - 56^\circ\text{S}$ | [EarthExplorer (USGS)](https://earthexplorer.usgs.gov/) |
| **CartoDEM (Bhuvan)** | ISRO / NRSC | 30 meters | Pan-India | [ISRO Bhuvan Portal](https://bhuvan-app1.nrsc.gov.in/) |

*Note: For the demonstration study reach along the Mahanadi River at Hirakud Dam, a 30m GeoTIFF raster in EPSG:4326 is packaged in `data/terrain/hirakud_dem.tif`.*

---

## 2. Satellite Earth Observation & Remote Sensing

| Satellite Constellation | Sensor Type | Resolution | Revisit | Use Case | Access Portal |
|---|---|---|---|---|---|
| **Copernicus Sentinel-1** | C-band Synthetic Aperture Radar (SAR) | 10 meters (IW mode) | 6–12 days | All-weather, cloud-penetrating flood water extent mapping | [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) |
| **Copernicus Sentinel-2** | Multi-Spectral Instrument (MSI) | 10–20 meters | 5 days | Optical post-flood inundation, turbidity, spectral indices (MNDWI) | [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) |
| **Landsat 8 / 9** | OLI / TIRS | 30 meters | 8–16 days | Multi-decadal historical flood extent analysis | [USGS EarthExplorer](https://earthexplorer.usgs.gov/) |

---

## 3. Hydrological & Dam Records

| Resource | Agency | Description | Link |
|---|---|---|---|
| **India-WRIS** | Ministry of Jal Shakti / NWIC | Water Resources Information System of India (river discharge, reservoir levels, stage data) | [indiawris.gov.in](https://indiawris.gov.in/) |
| **National Register of Large Dams (NRLD)** | Central Water Commission (CWC) | Physical specifications, storage capacities, crest levels of 5,745 Indian dams | [cwc.gov.in](https://cwc.gov.in/) |
| **CWC Flood Forecasting Bulletins** | Central Water Commission | Real-time monsoon river stages and flood warning bulletins | [ffs.india-water.gov.in](https://ffs.india-water.gov.in/) |

---

## 4. Downstream Vulnerability & Infrastructure Data

| Layer | Source | Format | Purpose |
|---|---|---|---|
| **Settlement Centroids & Pop** | Census of India / HDX (Humanitarian Data Exchange) | GeoJSON / SHP | Estimating population at risk in downstream floodplains |
| **Road & Railway Bridges** | OpenStreetMap (OSM) via Geofabrik | GeoJSON / SHP | Identifying cut-off transportation lifelines (e.g. NH-53 bridge) |
| **Critical Facilities** | OpenStreetMap / State Disaster Management Authorities | GeoJSON / SHP | Evaluating hospitals, power stations, and schools in hazard zones |

---

## 5. Google Earth Engine (GEE) Near-Real-Time Flood Analysis Workflow

For automated near-real-time satellite monitoring, the platform supports the standard GEE Otsu SAR thresholding pipeline:

```javascript
// GEE Earth Engine JavaScript Reference Workflow
// Filter Sentinel-1 SAR GRD collections
var studyArea = ee.Geometry.Rectangle([83.80, 21.40, 84.05, 21.60]);

var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(studyArea)
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.eq('instrumentMode', 'IW'));

// Filter pre-flood baseline and during-flood event images
var preFlood = s1.filterDate('2026-07-01', '2026-07-25').select('VV').median();
var postFlood = s1.filterDate('2026-08-01', '2026-08-15').select('VV').min();

// Log-ratio backscatter thresholding for smooth water detection
var diff = postFlood.subtract(preFlood);
var floodWater = diff.lt(-3.0).and(postFlood.lt(-14.0));

// Mask out permanent water bodies using JRC Global Surface Water
var jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater');
var permanentWater = jrc.select('occurrence').gt(80);
var inundationOnly = floodWater.updateMask(permanentWater.not());

Map.centerObject(studyArea, 11);
Map.addLayer(inundationOnly, {palette: ['#0000FF']}, 'Satellite Flood Inundation');
```
