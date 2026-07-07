from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import targets, charts, config, workouts

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

@app.get("/")
def root():
    return {"message": "Welcome to Fitness OptiMax API. Visit /docs for Swagger UI."}
