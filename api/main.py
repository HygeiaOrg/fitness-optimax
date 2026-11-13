import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.errors import register_exception_handlers
from api.routes import athletes, charts, consents, health, one_rep_maxes, targets, workouts

# Cloud Run captures stdout/stderr, so plain logging is all we need to get
# tracebacks into Logs Explorer.
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Fitness OptiMax API",
    description="Backend API to serve BigQuery SPC analytics and progressive overload targets.",
    version="1.1.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Register routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(targets.router, prefix="/api/targets", tags=["Targets"])
app.include_router(charts.router, prefix="/api/charts", tags=["Charts"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["Workouts"])
app.include_router(one_rep_maxes.router, prefix="/api/one-rep-maxes", tags=["One Rep Maxes"])
app.include_router(athletes.router, prefix="/api/athletes", tags=["Athletes"])
app.include_router(consents.router, prefix="/api/consents", tags=["Consents"])

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
        # An unknown /api/... path must 404 as JSON rather than silently
        # returning the SPA shell, which would look like a broken API.
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": f"No such API route: /{full_path}"})
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return JSONResponse(status_code=500, content={"detail": "Frontend build not found"})
