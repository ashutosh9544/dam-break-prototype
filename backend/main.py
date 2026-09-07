"""
FastAPI Main Application Entry Point
Dam Break Inundation Modelling Hydrodynamic Platform (SIH Problem Statement 26161 - NTRO)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from backend.api.simulation import router as simulation_router
from backend.api.results import router as results_router
from backend.core.delft3d_model import is_delft3d_available

app = FastAPI(
    title="Dam Break Inundation Modelling API",
    description="Hydrodynamic Dam Break Simulation Platform utilizing SPH and Delft3D (SIH 26161 - NTRO)",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(simulation_router)
app.include_router(results_router)


@app.get("/api/health", tags=["system"])
def health_check():
    """System health check and engine capability verification."""
    delft3d_installed, d3d_path = is_delft3d_available()
    return {
        "status": "healthy",
        "service": "Dam Break Hydrodynamic Modelling Engine",
        "engines": {
            "sph": {
                "available": True,
                "type": "Native 2D Shallow Water SPH",
                "status": "OPERATIONAL"
            },
            "delft3d": {
                "available": delft3d_installed,
                "executable_path": d3d_path,
                "status": "AVAILABLE" if delft3d_installed else "INTEGRATION READY BUT NOT INSTALLED",
                "fallback_mode": "Calibrated 2D Hydraulic Diffusion-Wave Prototype"
            }
        },
        "version": "1.0.0"
    }


# Mount frontend static directory if exists
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def root():
        return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
