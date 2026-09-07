# Model Limitations & Scientific Assumptions

This document outlines the scientific caveats, prototype-level simplifications, and engineering constraints of the V1 Dam Break Inundation Modelling Prototype developed for SIH Problem Statement 26161 (NTRO).

---

## 1. Prototype-Level Nature

> [!WARNING]
> This software is a **proof-of-concept research prototype (V1)** developed for architectural demonstration, GIS workflow verification, and multi-engine comparative evaluation. It is **not an operational national flood forecasting system** and must not be used for real-time life safety evacuations without calibration against physical hydraulic benchmarks.

---

## 2. Hydraulic Breach Modeling Assumptions

- **Breach Geometry**: The breach is represented as an expanding trapezoidal or rectangular opening governed by empirical broad-crested weir hydraulics and Froehlich (2008) / MacDonald & Langridge-Monopolis (1984) regression envelopes.
- **Geotechnical Erosion Mechanics**: Complex geotechnical erosion physics (piping cavity progression, headcut migration, soil pore-water pressure dissipation, embankment slope stability sliding) are abstracted into an empirical time-expansion curve.
- **Tailwater Submergence**: Full tailwater submergence effects on the weir discharge coefficient are approximated rather than dynamically coupled to reservoir draw-down.

---

## 3. DEM & Terrain Representation Caveats

- **Spatial Resolution**: The demonstration raster uses a 30m grid resampled from SRTM / Copernicus digital elevation datasets. Narrow drainage culverts, micro-topography, elevated road embankments, and levees smaller than 30m are smoothed out.
- **Digital Surface Bias**: Raw radar DEMs include vegetation canopies and structural heights (DSM vs DTM artifacts), which can slightly bias surface water flow directions in dense urban or forested reaches.
- **Bathymetry Absence**: Satellite-derived DEMs do not penetrate water surfaces; submerged riverbed bathymetry is approximated using synthetic channel deepening rather than multibeam sonar sounding.

---

## 4. SPH (Smoothed Particle Hydrodynamics) Simplifications

- **2D Depth-Averaged Formulation**: The SPH engine implements the 2D Shallow Water Equations (SWE) in Lagrangian coordinates. Vertical accelerations, non-hydrostatic pressures, and 3D overturning breaker waves are not resolved.
- **Particle Count Optimization**: For real-time browser demonstration, the prototype discretizes the flood wave into hundreds of Lagrangian fluid particles. Industrial-scale SPH solvers (such as DualSPHysics) use tens of millions of particles running on high-performance GPU clusters.
- **Turbulence & Roughness**: Turbulence is treated via an artificial Monaghan shear viscosity, and bottom friction is modeled via a depth-averaged Manning formulation.

---

## 5. Delft3D Adapter & Integration Constraints

- **Execution Environment**: When Delft3D Flexible Mesh (`dflowfm`) is not installed on the host operating system, the system activates a **calibrated 2D hydraulic diffusion-wave fallback prototype**.
- **Anti-Hallucination Compliance**: In accordance with SIH PS 26161 requirements, fallback outputs are **never labeled as Delft3D simulation output**. They are strictly designated as `"Fallback Prototype"`.
- **Mesh Generation**: The adapter generates valid `.mdu`, `.tim`, and DIMR XML files; running full 3D Delft3D meshes requires a local Delft3D license and installation.

---

## 6. Socio-Economic Risk Analysis Constraints

- **Population Exposure**: Affected population counts are calculated by intersecting flood extent polygons with municipal settlement centroids and buffer polygons. Spatial population distribution inside buildings is uniform rather than diurnal (daytime vs nighttime census).
- **Damage Function**: Building destruction and economic loss curves are deterministic heuristics based on water depth thresholds rather than structural finite-element impact modeling.

---

## 7. Model Validation & Accuracy Claims

- In accordance with NTRO evaluation guidelines, **no unsubstantiated scientific accuracy percentages** (e.g., "99.8% accurate") are claimed.
- Accuracy validation requires formal calibration against historical flood marks (e.g., historical 1982 or 2008 Mahanadi flood levels recorded at Sambalpur CWC gauge stations).
