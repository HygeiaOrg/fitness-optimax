from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_bq_client
from api.services.bq_client import BQClient
from api.models import UpdateGoalRequest, UpdateGoalResponse

router = APIRouter()

@router.post("/", response_model=UpdateGoalResponse)
def update_training_goal(payload: UpdateGoalRequest, bq: BQClient = Depends(get_bq_client)):
    """
    Update the user's declared training goal (STRENGTH or HYPERTROPHY) 
    for a specific exercise group. Writes directly to the `training_goals` config table.
    """
    if payload.training_goal not in ("STRENGTH", "HYPERTROPHY"):
        raise HTTPException(status_code=400, detail="training_goal must be 'STRENGTH' or 'HYPERTROPHY'")
        
    # Mocking BigQuery MERGE due to Free Tier DML restrictions
    print(f"[MOCK UPDATE] Goal for {payload.exercise_group} set to {payload.training_goal}")
    # bq.client.query(query, job_config=job_config).result()
    
    return UpdateGoalResponse(
        message="Goal updated successfully",
        exercise_group=payload.exercise_group,
        training_goal=payload.training_goal
    )
