from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import targets, charts, config, workouts
import os

app = FastAPI(
    title="Fitness OptiMax API",
    description="Backend API to serve BigQuery SPC analytics and progressive overload targets.",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(targets.router, prefix="/api/targets", tags=["Targets"])
app.include_router(charts.router, prefix="/api/charts", tags=["Charts"])
app.include_router(config.router, prefix="/api/goals", tags=["Configuration"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["Workouts"])

@app.get("/api")
def root():
    return {"message": "Welcome to Fitness OptiMax API. Visit /docs for Swagger UI."}

# Mount static files if they exist
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Catch-all for SPA
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend build not found"}
