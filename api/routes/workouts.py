from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_bq_client
from api.services.bq_client import BQClient
from api.models import LogWorkoutRequest, LogWorkoutResponse
from google.cloud import bigquery

router = APIRouter()

@router.post("/", response_model=LogWorkoutResponse)
def log_workout(payload: LogWorkoutRequest, bq: BQClient = Depends(get_bq_client)):
    """
    Log a new workout session into the native_workouts BigQuery table.
    """
    query = """
      INSERT INTO `gen-lang-client-0937519537.Optimmax.native_workouts` 
      (workout_timestamp, workout_date, athlete_name, exercise_group, sets, total_reps, total_weight, rpe)
      VALUES (CURRENT_TIMESTAMP(), CURRENT_DATE(), @athlete_name, @exercise_group, @sets, @total_reps, @total_weight, @rpe)
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("athlete_name", "STRING", payload.athlete_name),
            bigquery.ScalarQueryParameter("exercise_group", "STRING", payload.exercise_group),
            bigquery.ScalarQueryParameter("sets", "INT64", payload.sets),
            bigquery.ScalarQueryParameter("total_reps", "INT64", payload.total_reps),
            bigquery.ScalarQueryParameter("total_weight", "FLOAT64", payload.total_weight),
            bigquery.ScalarQueryParameter("rpe", "INT64", payload.rpe)
        ]
    )
    
    try:
        bq.client.query(query, job_config=job_config).result()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert workout: {str(e)}")
        
    return LogWorkoutResponse(
        message="Workout logged successfully",
        workout_id="native-" + payload.exercise_group.lower().replace(" ", "-")
    )
