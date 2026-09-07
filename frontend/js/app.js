/**
 * Dam Break Modelling & Flood Risk Simulation — Main Application Logic
 * Supports Quick Scenario Presets, In-Place Hydrodynamic Solvers (SPH & Delft3D),
 * Interactive GIS Inundation Visualization, Hydrograph Charting, and Multi-Scenario Comparisons.
 */

const API_BASE = '/api';

// Quick Scenario Presets Configuration (SIH Problem Statement 26161 - NTRO)
const PRESETS = {
  hirakud: {
    key: "hirakud",
    scenario_name: "Hirakud Dam — Monsoon Overtopping Breach",
    dam_name: "Hirakud Dam",
    river_name: "Mahanadi River Basin",
    water_level: 58.0,
    dam_height: 61.0,
    breach_width: 60.0,
    breach_time: 35.0,
    dam_latitude: 21.5270,
    dam_longitude: 83.8710,
    downstream_distance: 35.0,
    engine: "SPH"
  },
  tehri: {
    key: "tehri",
    scenario_name: "Tehri Dam — High-Head Piping Failure",
    dam_name: "Tehri Dam",
    river_name: "Bhagirathi River Basin",
    water_level: 240.0,
    dam_height: 260.5,
    breach_width: 85.0,
    breach_time: 45.0,
    dam_latitude: 30.3780,
    dam_longitude: 78.4800,
    downstream_distance: 50.0,
    engine: "SPH"
  },
  idukki: {
    key: "idukki",
    scenario_name: "Idukki Dam — Rapid Structural Failure",
    dam_name: "Idukki Dam",
    river_name: "Periyar River Basin",
    water_level: 155.0,
    dam_height: 168.9,
    breach_width: 45.0,
    breach_time: 30.0,
    dam_latitude: 9.8430,
    dam_longitude: 76.9750,
    downstream_distance: 30.0,
    engine: "Delft3D"
  },
  mullaperiyar: {
    key: "mullaperiyar",
    scenario_name: "Mullaperiyar Dam — Flash Inundation Wave",
    dam_name: "Mullaperiyar Dam",
    river_name: "Periyar River Basin",
    water_level: 48.0,
    dam_height: 53.6,
    breach_width: 35.0,
    breach_time: 25.0,
    dam_latitude: 9.5290,
    dam_longitude: 77.1430,
    downstream_distance: 25.0,
    engine: "SPH"
  },
  sardar_sarovar: {
    key: "sardar_sarovar",
    scenario_name: "Sardar Sarovar Dam — Spillway Surcharge Breach",
    dam_name: "Sardar Sarovar Dam",
    river_name: "Narmada River Basin",
    water_level: 135.0,
    dam_height: 163.0,
    breach_width: 75.0,
    breach_time: 50.0,
    dam_latitude: 21.8290,
    dam_longitude: 73.7480,
    downstream_distance: 45.0,
    engine: "Delft3D"
  }
};

let currentSimulationData = null;

document.addEventListener('DOMContentLoaded', () => {
  // Initialize map if present
  if (document.getElementById('map')) {
    initMap(21.5270, 83.8710);
  }

  // Setup form submission
  const simForm = document.getElementById('simulation-form');
  if (simForm) {
    simForm.addEventListener('submit', handleSimulationSubmit);
  }

  // Setup Quick Preset buttons
  document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const presetKey = chip.getAttribute('data-preset');
      applyPreset(presetKey, true); // true = auto run on click
    });
  });

  // Check URL parameters or load initial scenario
  const urlParams = new URLSearchParams(window.location.search);
  const requestedId = urlParams.get('id');

  loadInitialData(requestedId);
});

function applyPreset(presetKey, autoRun = false) {
  const preset = PRESETS[presetKey];
  if (!preset) return;

  // Highlight active preset chip
  document.querySelectorAll('.preset-chip').forEach(c => {
    if (c.getAttribute('data-preset') === presetKey) {
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });

  // Populate form fields
  if (document.getElementById('scenario_name')) document.getElementById('scenario_name').value = preset.scenario_name;
  if (document.getElementById('dam_name')) document.getElementById('dam_name').value = preset.dam_name;
  if (document.getElementById('river_name')) document.getElementById('river_name').value = preset.river_name;
  if (document.getElementById('water_level')) document.getElementById('water_level').value = preset.water_level;
  if (document.getElementById('dam_height')) document.getElementById('dam_height').value = preset.dam_height;
  if (document.getElementById('breach_width')) document.getElementById('breach_width').value = preset.breach_width;
  if (document.getElementById('breach_time')) document.getElementById('breach_time').value = preset.breach_time;
  if (document.getElementById('dam_latitude')) document.getElementById('dam_latitude').value = preset.dam_latitude;
  if (document.getElementById('dam_longitude')) document.getElementById('dam_longitude').value = preset.dam_longitude;
  if (document.getElementById('downstream_distance')) document.getElementById('downstream_distance').value = preset.downstream_distance;
  if (document.getElementById('engine-select')) document.getElementById('engine-select').value = preset.engine;

  // Update subtitle info
  const subInfo = document.getElementById('selected-basin-info');
  if (subInfo) {
    subInfo.textContent = `${preset.river_name} • ${preset.dam_name}`;
  }

  // Clear any inline errors
  document.querySelectorAll('.inline-error').forEach(el => el.style.display = 'none');
  const errBanner = document.getElementById('form-error-banner');
  if (errBanner) errBanner.style.display = 'none';

  if (autoRun) {
    executeSimulation();
  }
}

async function handleSimulationSubmit(e) {
  e.preventDefault();
  if (!validateForm()) return;
  await executeSimulation();
}

function validateForm() {
  let isValid = true;

  const fields = [
    { id: 'water_level', err: 'err-water_level', check: v => v > 0 },
    { id: 'dam_height', err: 'err-dam_height', check: v => v > 0 },
    { id: 'breach_width', err: 'err-breach_width', check: v => v > 0 },
    { id: 'breach_time', err: 'err-breach_time', check: v => v > 0 },
    { id: 'dam_latitude', err: 'err-dam_latitude', check: v => v >= -90 && v <= 90 },
    { id: 'dam_longitude', err: 'err-dam_longitude', check: v => v >= -180 && v <= 180 },
    { id: 'downstream_distance', err: 'err-downstream_distance', check: v => v > 0 }
  ];

  fields.forEach(f => {
    const el = document.getElementById(f.id);
    const err = document.getElementById(f.err);
    if (el && err) {
      const val = parseFloat(el.value);
      if (isNaN(val) || !f.check(val)) {
        err.style.display = 'block';
        isValid = false;
      } else {
        err.style.display = 'none';
      }
    }
  });

  const waterLevel = parseFloat(document.getElementById('water_level')?.value || 0);
  const damHeight = parseFloat(document.getElementById('dam_height')?.value || 0);
  if (waterLevel > damHeight) {
    const err = document.getElementById('err-water_level');
    if (err) {
      err.textContent = "Water level cannot exceed total dam height.";
      err.style.display = 'block';
      isValid = false;
    }
  }

  return isValid;
}

async function executeSimulation() {
  const overlay = document.getElementById('loading-overlay');
  const runBtn = document.getElementById('run-btn');
  const errorBanner = document.getElementById('form-error-banner');
  const errorText = document.getElementById('form-error-text');

  if (overlay) overlay.style.display = 'flex';
  if (runBtn) {
    runBtn.disabled = true;
    runBtn.textContent = 'Simulating Hydrodynamics...';
  }
  if (errorBanner) errorBanner.style.display = 'none';

  const payload = {
    water_level: parseFloat(document.getElementById('water_level').value),
    dam_height: parseFloat(document.getElementById('dam_height').value),
    breach_width: parseFloat(document.getElementById('breach_width').value),
    breach_time: parseFloat(document.getElementById('breach_time').value),
    dam_latitude: parseFloat(document.getElementById('dam_latitude')?.value || 21.5270),
    dam_longitude: parseFloat(document.getElementById('dam_longitude')?.value || 83.8710),
    downstream_distance: parseFloat(document.getElementById('downstream_distance')?.value || 25.0),
    engine: document.getElementById('engine-select')?.value || 'SPH',
    dam_name: document.getElementById('dam_name')?.value || "Hirakud Dam",
    river_name: document.getElementById('river_name')?.value || "Mahanadi River Basin",
    scenario_name: document.getElementById('scenario_name')?.value || "Hydrodynamic Simulation"
  };

  try {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Simulation computation failed');
    }

    const data = await res.json();
    currentSimulationData = data;
    localStorage.setItem('latest_simulation', JSON.stringify(data));

    // Update entire UI in-place
    updateDashboardUI(data);

    // Refresh multi-scenario comparison matrix
    await refreshScenarioComparison();

  } catch (error) {
    console.error("Simulation error:", error);
    if (errorBanner && errorText) {
      errorText.textContent = `Simulation Error: ${error.message}`;
      errorBanner.style.display = 'flex';
    } else {
      alert(`Simulation Error: ${error.message}`);
    }
  } finally {
    if (overlay) overlay.style.display = 'none';
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.textContent = 'Run Simulation';
    }
  }
}

async function loadInitialData(scenarioId) {
  let simData = null;

  if (scenarioId) {
    try {
      const res = await fetch(`${API_BASE}/results/${scenarioId}`);
      if (res.ok) simData = await res.json();
    } catch (e) {
      console.warn("Could not load requested scenario:", e);
    }
  }

  if (!simData) {
    const stored = localStorage.getItem('latest_simulation');
    if (stored) {
      try { simData = JSON.parse(stored); } catch (e) {}
    }
  }

  if (simData) {
    currentSimulationData = simData;
    updateDashboardUI(simData);
  } else {
    // Run default Hirakud preset to populate initial state
    applyPreset('hirakud', true);
  }

  refreshScenarioComparison();
}

function updateDashboardUI(data) {
  if (!data) return;

  // Scenario Title & Location
  const titleEl = document.getElementById('scenario-title');
  if (titleEl) titleEl.textContent = data.scenario_name || 'Dam Break Simulation Results';

  const subtitleEl = document.getElementById('scenario-subtitle');
  if (subtitleEl) subtitleEl.textContent = `${data.dam_name || 'Hirakud Dam'} • ${data.river_name || 'Mahanadi River'}`;

  // Solver Engine Badge
  const engBadge = document.getElementById('engine-badge');
  if (engBadge) {
    const engineName = data.engine || 'SPH';
    engBadge.textContent = engineName;
    engBadge.className = 'badge';
    if (engineName === 'SPH') {
      engBadge.classList.add('badge-sph');
    } else if (engineName === 'Delft3D') {
      engBadge.classList.add('badge-delft3d');
    } else {
      engBadge.classList.add('badge-fallback');
      engBadge.textContent = 'Prototype Fallback';
    }
  }

  // Risk Level Badge
  const risk = data.risk_summary || {};
  const riskBadge = document.getElementById('risk-badge') || document.getElementById('res-risk-badge');
  const riskLvl = risk.risk_level || 'MODERATE';
  if (riskBadge) {
    riskBadge.textContent = riskLvl;
    riskBadge.className = `risk-level-badge risk-${riskLvl}`;
  }

  // KPIs
  const setElem = (id, html) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  };

  const dischargeFormatted = Math.round(data.max_discharge || 0).toLocaleString();
  setElem('kpi-discharge', `${dischargeFormatted} <span class="summary-unit">m³/s</span>`);
  setElem('res-discharge', `${dischargeFormatted} <span class="summary-unit">m³/s</span>`);

  const depthFormatted = (data.max_depth || 0).toFixed(2);
  setElem('kpi-depth', `${depthFormatted} <span class="summary-unit">m</span>`);
  setElem('res-depth', `${depthFormatted} <span class="summary-unit">m</span>`);

  const arrivalFormatted = (data.arrival_time || 0).toFixed(1);
  setElem('kpi-arrival', `${arrivalFormatted} <span class="summary-unit">min</span>`);
  setElem('res-arrival', `${arrivalFormatted} <span class="summary-unit">min</span>`);

  const meta = data.metadata || {};
  const areaSqkm = meta.inundated_area_sqkm || '--';
  setElem('kpi-area', `${areaSqkm} <span class="summary-unit">km²</span>`);

  const popFormatted = (risk.population_affected || 0).toLocaleString();
  setElem('kpi-population', popFormatted);
  setElem('res-population', popFormatted);

  const infraFormatted = (risk.infrastructure_affected || 0).toString();
  setElem('kpi-infrastructure', infraFormatted);
  setElem('res-infrastructure', infraFormatted);

  // Parameter Summary Table
  const p = data.input_parameters || {};
  setElem('param-water-level', `${p.water_level || '--'} m`);
  setElem('param-dam-height', `${p.dam_height || '--'} m`);
  setElem('param-breach-width', `${p.breach_width || '--'} m`);
  setElem('param-breach-time', `${p.breach_time || '--'} min`);
  setElem('param-dam-coords', `${(p.dam_latitude || 21.527).toFixed(4)}°N, ${(p.dam_longitude || 83.871).toFixed(4)}°E`);
  setElem('param-downstream', `${p.downstream_distance || 25.0} km`);
  setElem('param-engine', data.engine || 'SPH');

  // Update GIS Export Links
  const sId = data.scenario_id;
  if (sId) {
    const updateLink = (id, ext) => {
      const link = document.getElementById(id);
      if (link) link.href = `${API_BASE}/export/${sId}/${ext}`;
    };
    updateLink('download-shp', 'shp');
    updateLink('download-kml', 'kml');
    updateLink('download-geojson', 'geojson');
    updateLink('btn-export-shp', 'shp');
    updateLink('btn-export-kml', 'kml');
    updateLink('btn-export-geojson', 'geojson');
  }

  // Update Leaflet Map
  if (typeof renderFloodExtent === 'function') {
    const damLat = p.dam_latitude || 21.5270;
    const damLon = p.dam_longitude || 83.8710;
    const damName = data.dam_name || "Dam Location";
    if (typeof updateMapLocation === 'function') {
      updateMapLocation(damLat, damLon, damName);
    }
    renderFloodExtent(data.flood_extent || []);
  }

  // Render Hydrograph chart
  if (typeof renderHydrographChart === 'function' && data.hydrograph) {
    renderHydrographChart(data.hydrograph);
  }

  // Update Settlements Table
  updateSettlementsTable(risk.details ? risk.details.submerged_settlements : []);
}

function updateSettlementsTable(settlements) {
  const table = document.getElementById('settlements-table');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  if (!tbody) return;

  if (!settlements || settlements.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No downstream settlements inundated under this breach magnitude.</td></tr>`;
    return;
  }

  tbody.innerHTML = settlements.map(s => `
    <tr>
      <td><b>${s.name}</b></td>
      <td>${s.distance_km || '--'} km</td>
      <td><span style="color: #2563eb; font-weight: 600;">${s.water_depth_m} m</span></td>
      <td>${s.arrival_time_min} min</td>
      <td><span style="color: #dc2626; font-weight: 600;">${(s.affected_population || 0).toLocaleString()}</span> / ${(s.total_population || 0).toLocaleString()}</td>
    </tr>
  `).join('');
}

async function refreshScenarioComparison() {
  const table = document.getElementById('comparison-table');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  const narrative = document.getElementById('comparison-narrative');
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/scenarios`);
    if (!res.ok) return;

    const list = await res.json();
    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No simulation scenarios recorded yet. Run a simulation above to start multi-scenario comparisons.</td></tr>`;
      if (narrative) narrative.textContent = "";
      return;
    }

    tbody.innerHTML = list.map(sc => `
      <tr>
        <td><b>${sc.scenario_name}</b></td>
        <td><span class="badge ${sc.engine === 'SPH' ? 'badge-sph' : (sc.engine === 'Delft3D' ? 'badge-delft3d' : 'badge-fallback')}">${sc.engine}</span></td>
        <td>${Math.round(sc.max_discharge || 0).toLocaleString()} m³/s</td>
        <td>${(sc.max_depth || 0).toFixed(2)} m</td>
        <td>${(sc.arrival_time || 0).toFixed(1)} min</td>
        <td>${sc.inundated_area_sqkm || '--'} km²</td>
        <td><span style="color: #dc2626; font-weight: 600;">${(sc.population_affected || 0).toLocaleString()}</span></td>
        <td><span class="badge badge-${(sc.risk_level || 'moderate').toLowerCase()}">${sc.risk_level || 'MODERATE'}</span></td>
      </tr>
    `).join('');

    // If 2 or more scenarios exist, generate comparative narrative
    if (list.length >= 2) {
      const id1 = list[list.length - 2].scenario_id;
      const id2 = list[list.length - 1].scenario_id;
      try {
        const compRes = await fetch(`${API_BASE}/scenarios/compare`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario_ids: [id1, id2] })
        });
        if (compRes.ok) {
          const compData = await compRes.json();
          if (narrative) {
            narrative.innerHTML = `<strong>Hydrodynamic Variance Analysis:</strong> ${compData.summary_text || ''}`;
          }
        }
      } catch (e) {
        console.warn("Scenario comparison error:", e);
      }
    }

  } catch (e) {
    console.error("Failed to refresh scenario comparison:", e);
  }
}
