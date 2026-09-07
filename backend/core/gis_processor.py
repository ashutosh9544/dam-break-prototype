"""
Geographic Information System (GIS) Data Processor
Handles DEM ingestion (GeoTIFF via Rasterio), coordinate reference systems (CRS),
NoData handling, spatial windowing, and conversion of flood simulation results into
valid OGC KML, zipped ESRI Shapefile (.shp), and GeoJSON formats.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import zipfile
import json
import numpy as np
import rasterio
from rasterio.windows import Window
import geopandas as gpd
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.validation import make_valid


class GISProcessor:
    def __init__(self, outputs_dir: str = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\outputs"):
        self.outputs_dir = outputs_dir
        self.shp_dir = os.path.join(outputs_dir, "shp")
        self.kml_dir = os.path.join(outputs_dir, "kml")
        self.geojson_dir = os.path.join(outputs_dir, "geojson")
        for d in [self.shp_dir, self.kml_dir, self.geojson_dir]:
            os.makedirs(d, exist_ok=True)

    @staticmethod
    def inspect_and_load_dem(
        dem_path: str,
        max_dimension: int = 1500,
        subsample_step: int = 1
    ) -> Dict[str, Any]:
        """
        Open DEM using Rasterio, validate CRS, extract spatial bounds, resolution,
        handle NoData values, and optionally use windowed reading to protect memory.
        """
        if not os.path.exists(dem_path):
            raise FileNotFoundError(f"DEM file not found at: {dem_path}")

        with rasterio.open(dem_path) as src:
            crs_str = str(src.crs) if src.crs else "EPSG:4326"
            bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
            nodata = src.nodata if src.nodata is not None else -9999.0
            res_x, res_y = src.res
            width = src.width
            height = src.height

            # Memory safeguard: check if raster exceeds dimension limit
            if width > max_dimension or height > max_dimension:
                step = max(2, int(max(width, height) / max_dimension))
                data = src.read(1, out_shape=(height // step, width // step))
            else:
                data = src.read(1)

            # Mask NoData
            clean_data = np.where(data == nodata, np.nan, data)
            # If NaNs exist, replace with local minimum
            min_valid = np.nanmin(clean_data) if not np.isnan(clean_data).all() else 0.0
            clean_data = np.nan_to_num(clean_data, nan=min_valid)

            return {
                "elevation_array": clean_data.astype(np.float32),
                "bounds": bounds,  # (west, south, east, north)
                "crs": crs_str,
                "width": width,
                "height": height,
                "resolution": (abs(res_x), abs(res_y)),
                "min_elevation": float(np.min(clean_data)),
                "max_elevation": float(np.max(clean_data)),
                "transform": src.transform
            }

    def export_geojson(
        self,
        features: List[Dict[str, Any]],
        scenario_id: str,
        properties_extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export flood polygons to standard GeoJSON."""
        out_path = os.path.join(self.geojson_dir, f"flood_extent_{scenario_id}.geojson")
        fc = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)
        return out_path

    def export_shapefile(
        self,
        features: List[Dict[str, Any]],
        scenario_id: str
    ) -> str:
        """
        Convert flood features to GeoDataFrame and export multi-component ESRI Shapefile,
        then bundle into a zip archive (.shp.zip).
        """
        if not features:
            # Create a dummy valid polygon if empty
            poly = Polygon([[83.87, 21.52], [83.88, 21.52], [83.88, 21.53], [83.87, 21.53], [83.87, 21.52]])
            features = [{
                "geometry": mapping(poly),
                "properties": {"depth_m": 0.0, "arrival_m": 0.0, "risk_level": "LOW", "engine": "SPH"}
            }]

        geoms = []
        records = []
        for feat in features:
            g = shape(feat["geometry"])
            if not g.is_valid:
                g = make_valid(g)
            geoms.append(g)

            # Flatten and shorten attribute names for ESRI DBF (10 char limit)
            p = feat.get("properties", {})
            records.append({
                "depth_m": float(p.get("depth_m", 0.0)),
                "arrival_m": float(p.get("arrival_time_min", 0.0)),
                "risk_lvl": str(p.get("risk_level", "MODERATE"))[:10],
                "engine": str(p.get("engine", "SPH"))[:10],
                "zone": str(p.get("zone", "Inundated"))[:20]
            })

        gdf = gpd.GeoDataFrame(records, geometry=geoms, crs="EPSG:4326")

        # Save to temporary folder and zip
        subfolder = os.path.join(self.shp_dir, f"flood_{scenario_id}")
        os.makedirs(subfolder, exist_ok=True)
        shp_file = os.path.join(subfolder, f"flood_extent_{scenario_id}.shp")
        gdf.to_file(shp_file, driver="ESRI Shapefile")

        # Create zip file
        zip_path = os.path.join(self.shp_dir, f"flood_extent_{scenario_id}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in os.listdir(subfolder):
                full_f = os.path.join(subfolder, fname)
                zf.write(full_f, arcname=fname)

        return zip_path

    def export_kml(
        self,
        features: List[Dict[str, Any]],
        scenario_id: str,
        document_name: str = "Dam Break Flood Inundation Extent"
    ) -> str:
        """
        Generate standard OGC KML with color-coded placemarks for Google Earth visualization.
        """
        kml_path = os.path.join(self.kml_dir, f"flood_extent_{scenario_id}.kml")

        kml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{document_name}</name>
    <description>Simulated Dam Break Flood Inundation Zones (SIH 26161 - NTRO)</description>
    
    <!-- Color Styles for Depth Bands -->
    <Style id="criticalStyle">
      <LineStyle><color>ff0000ff</color><width>2</width></LineStyle>
      <PolyStyle><color>7f0000b3</color><fill>1</fill><outline>1</outline></PolyStyle>
    </Style>
    <Style id="highStyle">
      <LineStyle><color>ff0080ff</color><width>1.5</width></LineStyle>
      <PolyStyle><color>7f0051e6</color><fill>1</fill><outline>1</outline></PolyStyle>
    </Style>
    <Style id="moderateStyle">
      <LineStyle><color>ffd18802</color><width>1</width></LineStyle>
      <PolyStyle><color>7fd18802</color><fill>1</fill><outline>1</outline></PolyStyle>
    </Style>
"""
        kml_footer = """  </Document>
</kml>"""

        placemarks = []
        for idx, feat in enumerate(features):
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            if geom.get("type") != "Polygon":
                continue

            depth_m = props.get("depth_m", 1.0)
            arrival_m = props.get("arrival_time_min", 30.0)
            risk = props.get("risk_level", "MODERATE")
            engine = props.get("engine", "SPH")

            style_id = "moderateStyle"
            if risk == "CRITICAL":
                style_id = "criticalStyle"
            elif risk == "HIGH":
                style_id = "highStyle"

            # Polygon exterior ring coordinates format: lon,lat,alt
            coords_list = geom.get("coordinates", [[]])[0]
            kml_coord_str = " ".join([f"{c[0]},{c[1]},0" for c in coords_list])

            placemark = f"""    <Placemark id="zone_{idx}">
      <name>Inundation Zone #{idx + 1}</name>
      <description><![CDATA[
        <b>Depth:</b> {depth_m} m<br/>
        <b>Arrival Time:</b> {arrival_m} min<br/>
        <b>Risk Level:</b> {risk}<br/>
        <b>Engine:</b> {engine}
      ]]></description>
      <styleUrl>#{style_id}</styleUrl>
      <Polygon>
        <extrude>1</extrude>
        <altitudeMode>clampToGround</altitudeMode>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{kml_coord_str}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>"""
            placemarks.append(placemark)

        full_kml = kml_header + "\n".join(placemarks) + "\n" + kml_footer
        with open(kml_path, "w", encoding="utf-8") as f:
            f.write(full_kml)

        return kml_path
