from fastapi import APIRouter, Depends
from typing import List
from api.dependencies import get_bq_client
from api.services.bq_client import BQClient
from api.models import TargetResponse
from google.cloud import bigquery

router = APIRouter()

@router.get("", response_model=List[TargetResponse])
def get_workout_targets(bq: BQClient = Depends(get_bq_client)):
    """
    Fetch the most recent, actionable progressive overload targets for every exercise group.
    Sourced from Layer 5 (`workout_targets` BigQuery view).
    """
    query = """
    SELECT *
    FROM `gen-lang-client-0937519537.Optimmax.workout_targets`
    ORDER BY last_session_date DESC
    """
    
    results = bq.query(query)
    
    # Map BigQuery rows to Pydantic models
    targets = []
    for row in results:
        targets.append(TargetResponse(
            exercise_group=row.exercise_group,
            training_goal=row.training_goal,
            last_session_date=row.last_session_date,
            days_since_last_session=row.days_since_last_session,
            staleness_alert=row.staleness_alert,
            last_total_weight=row.last_total_weight,
            rolling_avg_5=row.rolling_avg_5,
            last_avg_reps_per_set=row.last_avg_reps_per_set,
            rpe_avg_3=row.rpe_avg_3,
            is_plateau=row.is_plateau,
            alert_type=row.alert_type,
            alert_message=row.alert_message,
            goal_aligned=row.goal_aligned,
            target_total_weight=row.target_total_weight,
            target_sets=row.target_sets,
            target_reps=row.target_reps,
            target_weight_per_rep=row.target_weight_per_rep
        ))
    
    return targets
