# Smoothed Particle Hydrodynamics (SPH) Methodology

This document details the mathematical formulation, kernel equations, numerical discretization, and post-processing algorithms implemented in the **2D Shallow Water SPH Engine** (`backend/core/sph_model.py`) for SIH Problem Statement 26161 (NTRO).

---

## 1. Overview of SPH in Flood Modeling

Smoothed Particle Hydrodynamics (SPH) is a mesh-free Lagrangian particle method. Unlike Eulerian grid solvers that struggle with wet/dry moving boundaries and steep shock fronts (such as dam-break flood waves), SPH represents water as discrete moving fluid particles that carry mass, momentum, and water depth.

---

## 2. Mathematical Formulation

### 2.1 State Variables
Each fluid particle $i$ possesses:
- Position vector: $\mathbf{r}_i = (x_i, y_i)$
- Velocity vector: $\mathbf{u}_i = (u_i, v_i)$
- Water depth: $h_i$
- Fluid mass: $m_i$
- Bed elevation: $z_{b,i} = z_b(x_i, y_i)$ (interpolated from DEM)
- Fluid density: $\rho = 1000\text{ kg/m}^3$

### 2.2 Smoothing Kernel Function
We utilize the Monaghan 2D Cubic Spline kernel $W(r, h_{smooth})$ defined over non-dimensional distance $q = \frac{r}{h_{smooth}}$:

$$W(r, h) = \frac{10}{7\pi h^2} \begin{cases} 
1 - \frac{3}{2}q^2 + \frac{3}{4}q^3 & 0 \le q < 1 \\
\frac{1}{4}(2 - q)^3 & 1 \le q < 2 \\
0 & q \ge 2 
\end{cases}$$

The kernel gradient is given by:
$$\nabla_i W_{ij} = \frac{\mathbf{r}_i - \mathbf{r}_j}{r_{ij}} \frac{\partial W}{\partial r}$$

The smoothing length $h_{smooth}$ is scaled adaptively based on the domain dimensions to maintain approximately 20–40 neighboring particles in the support domain.

### 2.3 2D Shallow Water SPH Equations

#### Continuity (Depth Evolution):
$$\frac{D h_i}{Dt} = \sum_j \frac{m_j}{\rho} (\mathbf{u}_i - \mathbf{u}_j) \cdot \nabla_i W_{ij}$$

#### Momentum Conservation:
$$\frac{D \mathbf{u}_i}{Dt} = -g \nabla (h_i + z_{b,i}) - \mathbf{F}_{friction} + \mathbf{F}_{visc}$$

Where:
1. **Hydrostatic Pressure & Bed Slope Force**:
   $$-g \left[ \sum_j m_j \left( \frac{h_i}{2\rho_i} + \frac{h_j}{2\rho_j} \right) \nabla_i W_{ij} + \nabla z_{b,i} \right]$$
   The bed gradient $\nabla z_{b,i} = (\frac{\partial z_b}{\partial x}, \frac{\partial z_b}{\partial y})$ directly drives particles down the DEM river valley.

2. **Manning Roughness Friction Resistance**:
   $$\mathbf{F}_{friction} = g \frac{n_{manning}^2 |\mathbf{u}_i|}{h_i^{4/3}} \mathbf{u}_i$$
   Where $n_{manning} \approx 0.035 - 0.055\text{ s/m}^{1/3}$.

3. **Artificial Viscosity (Monaghan, 1992)**:
   Stabilizes shock fronts and suppresses numerical oscillations:
   $$\Pi_{ij} = \begin{cases} \frac{-\alpha c \mu_{ij} + \beta \mu_{ij}^2}{\bar{\rho}_{ij}} & \mathbf{u}_{ij} \cdot \mathbf{r}_{ij} < 0 \\ 0 & \text{otherwise} \end{cases}$$

---

## 3. Topography Coupling with DEM

- The underlying GeoTIFF DEM raster is sampled using continuous bilinear interpolation:
  $$z_b(x, y) = (1-u)(1-v)z_{00} + u(1-v)z_{10} + (1-u)vz_{01} + uv z_{11}$$
- Bed slope components $\frac{\partial z_b}{\partial x}$ and $\frac{\partial z_b}{\partial y}$ are computed via central differences on the DEM grid cells.
- Particles automatically follow river thalwegs and flow around flanking topography barriers.

---

## 4. Time Stepping & Numerical Stability

Time integration follows the **Velocity-Verlet / Predictor-Corrector** scheme. The time step $\Delta t$ is constrained by the Courant-Friedrichs-Lewy (CFL) stability criterion:

$$\Delta t \le C_{CFL} \frac{h_{smooth}}{\sqrt{g h_{max}} + |\mathbf{u}|_{max}}$$

With $C_{CFL} \approx 0.25$.

---

## 5. Eulerian Grid Extraction & Polygonization

To provide GIS-compatible results (GeoJSON, ESRI Shapefile, KML):
1. An Eulerian monitoring grid $(N_x \times N_y)$ is maintained over the downstream study domain.
2. At each time interval, particle depths $h_i$ are mapped to the grid cells.
3. The peak water depth $H_{max}(x, y) = \max_t h(x, y, t)$ is recorded.
4. The flood arrival time $T_{arrival}(x, y)$ is recorded when cell depth first crosses the inundation threshold ($h > 0.15\text{ m}$).
5. Contiguous wetted cells are vectorized into polygon features classified into shallow ($0.2 - 1.5\text{ m}$), medium ($1.5 - 3.0\text{ m}$), and deep ($> 3.0\text{ m}$) hazard tiers.
