# Delft3D Flexible Mesh Integration Guide

This document describes the architectural interface, file formats, execution workflow, and fallback mechanisms for integrating **Delft3D Flexible Mesh (Delft3D-FM / D-Flow FM)** into the Dam Break Inundation Modelling Framework (SIH 26161 - NTRO).

---

## 1. Architectural Role

Delft3D is an internationally recognized hydrodynamic modeling suite developed by Deltares. In our framework, Delft3D functions as an external simulation engine orchestrated through an adapter module (`backend/core/delft3d_model.py`).

```
Dam-Break Hydrograph Q(t) + DEM Bathymetry
                 │
                 ▼
     [Delft3D Adapter Module]
                 │
  ┌──────────────┴──────────────┐
  │ Binary Found?               │
  ▼                             ▼
[YES]                         [NO]
Run dflowfm.exe             Run Calibrated 2D Hydraulic
Parse NetCDF outputs        Diffusion-Wave Fallback
Output Engine: "Delft3D"    Output Engine: "Fallback Prototype"
  │                             │
  └──────────────┬──────────────┘
                 ▼
   Common Inundation Format (GeoJSON, SHP, KML)
```

---

## 2. Installation & Prerequisites

To execute actual Delft3D simulations:

1. Download and install the **Delft3D Flexible Mesh Suite** (Open Source version available from Deltares / OSS community).
2. Ensure the following binaries are accessible on the system `PATH`:
   - `dflowfm` or `dflowfm.exe` (D-Flow FM 1D/2D/3D numerical solver)
   - `dimr` or `dimr.exe` (Deltares Integrated Model Runner orchestrator)
3. Windows Default Locations checked automatically:
   - `C:\Program Files\Deltares\Delft3D Flexible Mesh Suite\bin`
   - `C:\Deltares\Delft3D\bin`

---

## 3. Input File Specifications

The adapter automatically generates the required Delft3D configuration files in `outputs/delft3d/`:

### 3.1 Master Definition File (`{model_name}.mdu`)
Defines simulation time control, numerical parameters (CFL max $= 0.7$, advection scheme), physical constants ($g = 9.81\text{ m/s}^2$, Manning roughness $n = 0.035$), and pointers to geometry and boundary files.

### 3.2 Time Series Boundary Condition (`breach_inflow.tim`)
Discretizes the dam breach outflow hydrograph calculated by `dam_model.py`:
```text
# Time(minutes)   Discharge(m3/s)
      0.00           0.000
      5.00        1245.320
     15.00        8930.500
     30.00       14250.000
    ...
```

### 3.3 External Forcing Specification (`external_forcings.ext`)
Maps the inflow hydrograph to the dam location node (`DamBreachNode`).

### 3.4 DIMR Configuration (`dimr_config.xml`)
Coordinates the solver execution pipeline:
```xml
<dimrConfig xmlns="http://schemas.deltares.nl/dimr">
  <component name="DFlowFM">
    <library>dflowfm</library>
    <inputFile>hirakud_mahanadi_flood.mdu</inputFile>
  </component>
  <control>
    <parallel><start name="DFlowFM" /></parallel>
  </control>
</dimrConfig>
```

---

## 4. Execution & Parsing

When binaries are available, the adapter executes:
```bash
dflowfm --autostartstop hirakud_mahanadi_flood.mdu
```
The solver outputs CF-compliant NetCDF files:
- `*_map.nc`: 2D spatial distribution of water depth ($s1$), water level ($s0$), flow velocities ($ucx, ucy$), and shear stress at designated time intervals.
- `*_his.nc`: Station time histories at downstream gauge points.

The adapter extracts maximum water depths, calculates threshold arrival times ($h > 0.15\text{ m}$), and vectorizes inundation zones into the common flood polygon format.

---

## 5. Fallback Prototype Mode & Anti-Hallucination Compliance

> [!IMPORTANT]
> **Anti-Hallucination Rule (#26)**:
> If Delft3D binaries are not installed on the host machine:
> 1. The adapter **NEVER** claims Delft3D ran.
> 2. The result field `engine` is set strictly to `"Fallback Prototype"`.
> 3. The metadata dictionary includes:
>    ```json
>    "delft3d_available": false,
>    "delft3d_status": "INTEGRATION READY BUT NOT INSTALLED",
>    "method": "Calibrated 2D Hydraulic Diffusion-Wave Fallback"
>    ```
> 4. The user interface displays a distinct amber badge notifying the user that fallback prototype mode is active while input configuration files are generated and ready for an installed solver.
