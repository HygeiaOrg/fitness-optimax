from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_bq_client
from api.services.bq_client import BQClient
from api.models import UpdateGoalRequest, UpdateGoalResponse
from google.cloud import bigquery

router = APIRouter()

@router.post("/", response_model=UpdateGoalResponse)
def update_training_goal(payload: UpdateGoalRequest, bq: BQClient = Depends(get_bq_client)):
    """
    Update the user's declared training goal (STRENGTH or HYPERTROPHY) 
    for a specific exercise group. Writes directly to the `training_goals` config table.
    """
    if payload.training_goal not in ("STRENGTH", "HYPERTROPHY"):
        raise HTTPException(status_code=400, detail="training_goal must be 'STRENGTH' or 'HYPERTROPHY'")
        
    # We use MERGE to either update if it exists or insert if it doesn't
    query = """
    MERGE `gen-lang-client-0937519537.Optimmax.training_goals` T
    USING (SELECT @exercise_group AS exercise_group, @training_goal AS training_goal) S
    ON T.exercise_group = S.exercise_group
    WHEN MATCHED THEN
      UPDATE SET training_goal = S.training_goal, updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
      INSERT (exercise_group, training_goal, updated_at) 
      VALUES (S.exercise_group, S.training_goal, CURRENT_TIMESTAMP())
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("exercise_group", "STRING", payload.exercise_group),
            bigquery.ScalarQueryParameter("training_goal", "STRING", payload.training_goal)
        ]
    )
    
    bq.client.query(query, job_config=job_config).result()
    
    return UpdateGoalResponse(
        message="Goal updated successfully",
        exercise_group=payload.exercise_group,
        training_goal=payload.training_goal
    )
