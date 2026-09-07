import os
import json
import numpy as np
import rasterio
from rasterio.transform import from_bounds

base_dir = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\data"

# 1. Dam specification
dam_info = {
    "dam_name": "Hirakud Dam",
    "river_name": "Mahanadi River",
    "state": "Odisha, India",
    "latitude": 21.527,
    "longitude": 83.871,
    "dam_type": "Composite (Earthen + Concrete)",
    "dam_height_m": 60.96,
    "crest_length_m": 4800.0,
    "full_reservoir_level_m": 192.02,
    "dead_storage_level_m": 179.83,
    "gross_storage_capacity_mcm": 5896.0,
    "effective_storage_mcm": 4821.0,
    "catchment_area_sqkm": 83400.0,
    "design_flood_discharge_m3s": 42450.0,
    "default_simulation_inputs": {
        "water_level": 58.0,
        "dam_height": 61.0,
        "breach_width": 45.0,
        "breach_time": 45.0
    }
}
with open(os.path.join(base_dir, "dam", "hirakud_dam.json"), "w") as f:
    json.dump(dam_info, f, indent=2)

# 2. Hydrology specifications
hydrology_info = {
    "river": "Mahanadi River",
    "basin": "Mahanadi Basin",
    "gauge_station": "Sambalpur (CWC Station 021-M)",
    "baseflow_m3s": 450.0,
    "manning_roughness_channel": 0.035,
    "manning_roughness_floodplain": 0.055,
    "average_river_slope": 0.00045,
    "average_channel_width_m": 350.0,
    "monsoon_high_flow_m3s": 12500.0
}
with open(os.path.join(base_dir, "hydrology", "mahanadi_hydrology.json"), "w") as f:
    json.dump(hydrology_info, f, indent=2)

# 3. GeoTIFF DEM creation
# Study area bounds: Longitude 83.80 to 84.05 E, Latitude 21.40 to 21.60 N
# (~25 km west-east, ~22 km south-north)
width = 250
height = 220
west, east = 83.80, 84.05
south, north = 21.40, 21.60

transform = from_bounds(west, south, east, north, width, height)

# Create realistic river valley topography:
# River flows from Dam (83.871, 21.527) southeasterly toward (83.98, 21.45)
lons = np.linspace(west, east, width)
lats = np.linspace(north, south, height)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Valley elevation model: base elevation drops from 180m near reservoir to 142m downstream
t_flow = (lon_grid - west) / (east - west)
# River path centerline:
river_lat = 21.54 - 0.09 * t_flow + 0.015 * np.sin(4 * np.pi * t_flow)
dist_to_river = np.abs(lat_grid - river_lat) * 111000.0  # meters

# Elevation: channel is 142m-155m, banks rise gently to 170m-210m in flanking hills
base_elevation = 165.0 - 15.0 * t_flow
channel_depth = 18.0 * np.exp(- (dist_to_river / 400.0)**2)
hills = 35.0 * (np.sin(3 * np.pi * (lon_grid - west)/(east - west))**2 + np.cos(2 * np.pi * (lat_grid - south)/(north - south))**2)

dem_elevation = base_elevation - channel_depth + hills * (dist_to_river / 3000.0).clip(0, 1)
# Reservoir area above dam (west of 83.871 and north of 21.52)
res_mask = (lon_grid < 83.871) & (lat_grid > 21.52)
dem_elevation[res_mask] = 188.0

dem_data = dem_elevation.astype(np.float32)

dem_path = os.path.join(base_dir, "terrain", "hirakud_dem.tif")
with rasterio.open(
    dem_path,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype=rasterio.float32,
    crs="EPSG:4326",
    transform=transform,
    nodata=-9999.0
) as dst:
    dst.write(dem_data, 1)

# 4. Population / Settlements GeoJSON
settlements = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Burla", "category": "Township", "population": 46000, "distance_km": 3.2, "elevation_m": 168},
            "geometry": {"type": "Point", "coordinates": [83.875, 21.503]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Sambalpur City", "category": "Municipal Corporation", "population": 184000, "distance_km": 14.5, "elevation_m": 150},
            "geometry": {"type": "Point", "coordinates": [83.978, 21.466]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Dhankauda", "category": "Suburban Settlement", "population": 15200, "distance_km": 11.8, "elevation_m": 154},
            "geometry": {"type": "Point", "coordinates": [83.955, 21.485]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Chiplima", "category": "Power Village", "population": 7800, "distance_km": 16.0, "elevation_m": 144},
            "geometry": {"type": "Point", "coordinates": [83.918, 21.412]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Hirakud Town", "category": "Industrial Town", "population": 31000, "distance_km": 2.5, "elevation_m": 172},
            "geometry": {"type": "Point", "coordinates": [83.882, 21.535]}
        }
    ]
}
with open(os.path.join(base_dir, "population", "downstream_settlements.geojson"), "w") as f:
    json.dump(settlements, f, indent=2)

# 5. Infrastructure GeoJSON
infrastructure = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "National Highway 53 Bridge", "type": "Transportation (Bridge)", "criticality": "CRITICAL"},
            "geometry": {"type": "LineString", "coordinates": [[83.960, 21.480], [83.975, 21.465]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Sambalpur Railway Bridge", "type": "Transportation (Rail)", "criticality": "HIGH"},
            "geometry": {"type": "LineString", "coordinates": [[83.955, 21.472], [83.970, 21.458]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Chiplima Hydroelectric Power Station", "type": "Energy Grid", "criticality": "CRITICAL"},
            "geometry": {"type": "Point", "coordinates": [83.921, 21.415]}
        },
        {
            "type": "Feature",
            "properties": {"name": "VSS Institute of Medical Sciences (Burla)", "type": "Healthcare / Hospital", "criticality": "CRITICAL"},
            "geometry": {"type": "Point", "coordinates": [83.878, 21.501]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Sambalpur District Administrative Center", "type": "Government", "criticality": "MODERATE"},
            "geometry": {"type": "Point", "coordinates": [83.980, 21.470]}
        }
    ]
}
with open(os.path.join(base_dir, "infrastructure", "critical_infrastructure.geojson"), "w") as f:
    json.dump(infrastructure, f, indent=2)

# 6. Satellite metadata & GEE workflow
satellite_info = {
    "optical_source": "Copernicus Sentinel-2 MSI (Level-2A)",
    "radar_source": "Copernicus Sentinel-1 SAR GRD (C-band IW)",
    "study_area": {
        "name": "Mahanadi River Basin - Hirakud Downstream",
        "bbox": [83.80, 21.40, 84.05, 21.60],
        "crs": "EPSG:4326"
    },
    "near_real_time_gee_workflow": {
        "collection_sentinel1": "COPERNICUS/S1_GRD",
        "polarization": ["VV", "VH"],
        "instrument_mode": "IW",
        "orbit_pass": "DESCENDING",
        "flood_detection_method": "Otsu thresholding on log-ratio SAR backscatter (VV)",
        "gee_script_reference": "scripts/gee_flood_detection.js"
    }
}
with open(os.path.join(base_dir, "satellite", "satellite_metadata.json"), "w") as f:
    json.dump(satellite_info, f, indent=2)

print("Demo dataset generated successfully!")
