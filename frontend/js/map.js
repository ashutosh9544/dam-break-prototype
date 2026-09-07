/**
 * Technical Flood Map Module (Leaflet.js)
 * Visualizes Dam breach locations, downstream river valley extents,
 * settlements, critical infrastructure, and depth-classified inundation polygons.
 */

let leafletMap = null;
let floodLayerGroup = null;
let markersLayerGroup = null;

function initMap(initialLat = 21.5270, initialLon = 83.8710) {
  const mapElement = document.getElementById('map');
  if (!mapElement) return;

  if (leafletMap) {
    leafletMap.remove();
    leafletMap = null;
  }

  // Base Leaflet setup with standard clean controls
  leafletMap = L.map('map', {
    zoomControl: true,
    attributionControl: true
  }).setView([initialLat, initialLon], 11);

  // Clean OpenStreetMap basemap
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '© OpenStreetMap contributors | Hydrodynamic Inundation Model'
  }).addTo(leafletMap);

  floodLayerGroup = L.layerGroup().addTo(leafletMap);
  markersLayerGroup = L.layerGroup().addTo(leafletMap);

  // Add initial reference point markers
  addReferenceMarkers(initialLat, initialLon, "Hirakud Dam");
}

function updateMapLocation(damLat, damLon, damName) {
  if (!leafletMap) {
    initMap(damLat, damLon);
    return;
  }
  leafletMap.setView([damLat, damLon], 11);
  addReferenceMarkers(damLat, damLon, damName);
}

function addReferenceMarkers(damLat = 21.5270, damLon = 83.8710, damName = "Dam Location") {
  if (!markersLayerGroup) return;
  markersLayerGroup.clearLayers();

  // 1. Dam Breach Source Marker
  const damIcon = L.divIcon({
    className: 'leaflet-dam-marker',
    html: `<div style="background:#1e3a8a; color:#ffffff; border:1.5px solid #ffffff; width:26px; height:26px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:700; border-radius:3px; box-shadow:0 1px 4px rgba(0,0,0,0.35);">DAM</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13]
  });

  L.marker([damLat, damLon], { icon: damIcon })
    .bindPopup(`<b>${damName} (Breach Point)</b><br>Lat: ${damLat.toFixed(4)}°N, Lon: ${damLon.toFixed(4)}°E`)
    .addTo(markersLayerGroup);

  // 2. Downstream Settlements (contextual to Hirakud / Mahanadi region by default)
  if (Math.abs(damLat - 21.527) < 0.5) {
    const settlements = [
      { name: "Burla", lat: 21.503, lon: 83.875, pop: "46,000", dist: "3.2 km" },
      { name: "Sambalpur Town", lat: 21.466, lon: 83.978, pop: "184,000", dist: "14.5 km" },
      { name: "Dhankauda", lat: 21.485, lon: 83.955, pop: "15,200", dist: "11.8 km" },
      { name: "Chiplima", lat: 21.412, lon: 83.918, pop: "7,800", dist: "16.0 km" }
    ];

    settlements.forEach(s => {
      L.circleMarker([s.lat, s.lon], {
        radius: 6,
        fillColor: "#dc2626",
        color: "#ffffff",
        weight: 1.5,
        fillOpacity: 0.9
      }).bindPopup(`<b>${s.name}</b><br>Downstream Reach: ${s.dist}<br>Population: ${s.pop}`).addTo(markersLayerGroup);
    });

    const infra = [
      { name: "NH-53 Mahanadi Bridge", lat: 21.472, lon: 83.968, type: "Highway Transport Corridor" },
      { name: "Sambalpur Railway Bridge", lat: 21.465, lon: 83.962, type: "Rail Infrastructure" },
      { name: "Chiplima Hydro Station", lat: 21.415, lon: 83.921, type: "Power Substation" },
      { name: "Burla Hospital", lat: 21.501, lon: 83.878, type: "Critical Medical Facility" }
    ];

    infra.forEach(item => {
      L.circleMarker([item.lat, item.lon], {
        radius: 5,
        fillColor: "#c2410c",
        color: "#ffffff",
        weight: 1.5,
        fillOpacity: 0.9
      }).bindPopup(`<b>${item.name}</b><br>Type: ${item.type}`).addTo(markersLayerGroup);
    });
  }
}

function renderFloodExtent(floodFeatures) {
  if (!leafletMap || !floodLayerGroup) return;

  floodLayerGroup.clearLayers();

  if (!floodFeatures || floodFeatures.length === 0) return;

  const geoJsonLayer = L.geoJSON(floodFeatures, {
    style: function(feature) {
      const p = feature.properties || {};
      const depth = p.depth_m || 1.0;
      
      // Technical color ramp based on water depth
      let fillColor = "#60a5fa"; // Shallow: 0.2m - 1.5m
      let fillOpacity = 0.50;

      if (depth >= 3.0) {
        fillColor = "#1e3a8a"; // Deep: > 3.0m
        fillOpacity = 0.70;
      } else if (depth >= 1.5) {
        fillColor = "#2563eb"; // Medium: 1.5m - 3.0m
        fillOpacity = 0.60;
      }

      return {
        fillColor: fillColor,
        weight: 0.8,
        opacity: 0.85,
        color: "#ffffff",
        fillOpacity: fillOpacity
      };
    },
    onEachFeature: function(feature, layer) {
      const p = feature.properties || {};
      layer.bindPopup(`
        <div style="font-size:12px; line-height:1.45; font-family:inherit;">
          <b style="color:#1e3a8a;">Hydrodynamic Inundation Cell</b><br/>
          <b>Depth:</b> ${p.depth_m} m<br/>
          <b>Arrival Time:</b> ${p.arrival_time_min} min<br/>
          <b>Velocity:</b> ${p.velocity_ms || 3.2} m/s<br/>
          <b>Hazard Level:</b> <span style="font-weight:700; color:${p.depth_m >= 3.0 ? '#b91c1c' : (p.depth_m >= 1.5 ? '#c2410c' : '#2563eb')}">${p.risk_level || 'MODERATE'}</span>
        </div>
      `);
    }
  });

  floodLayerGroup.addLayer(geoJsonLayer);

  // Fit map viewport to flood extent
  try {
    const bounds = geoJsonLayer.getBounds();
    if (bounds.isValid()) {
      leafletMap.fitBounds(bounds, { padding: [30, 30] });
    }
  } catch (e) {
    console.warn("Could not fit map bounds:", e);
  }
}
