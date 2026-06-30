from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_bq_client
from api.services.bq_client import BQClient
from api.models import ChartResponse, ControlLimits, SessionPoint

router = APIRouter()

@router.get("/{exercise_group}", response_model=ChartResponse)
def get_spc_chart(exercise_group: str, bq: BQClient = Depends(get_bq_client)):
    """
    Fetch the time-series data for a specific exercise group to plot I-MR charts.
    Sourced from Layer 4 (`spc_charts`).
    """
    # Use parameterized query to prevent SQL injection
    query = f"""
    SELECT 
        session_rank,
        workout_date,
        total_weight,
        rolling_avg_3,
        rolling_avg_5,
        rolling_avg_7,
        cl, ucl, lcl,
        is_out_of_control,
        momentum_signal
    FROM `gen-lang-client-0937519537.Optimmax.spc_charts`
    WHERE LOWER(exercise_group) = LOWER(@exercise_group)
    ORDER BY session_rank ASC
    """
    
    job_config = bq.client.query_modules.QueryJobConfig(
        query_parameters=[
            bq.client.query_modules.ScalarQueryParameter("exercise_group", "STRING", exercise_group)
        ]
    )
    
    results = bq.client.query(query, job_config=job_config).result()
    
    sessions = []
    cl, ucl, lcl = 0.0, 0.0, 0.0
    
    # We'll just grab the control limits from the last row since they are static per group
    # (unless phase-based limits are introduced later)
    for row in results:
        cl, ucl, lcl = row.cl, row.ucl, row.lcl
        sessions.append(SessionPoint(
            session_rank=row.session_rank,
            workout_date=row.workout_date,
            total_weight=row.total_weight,
            rolling_avg_3=row.rolling_avg_3,
            rolling_avg_5=row.rolling_avg_5,
            rolling_avg_7=row.rolling_avg_7,
            is_out_of_control=row.is_out_of_control,
            momentum_signal=row.momentum_signal
        ))
        
    if not sessions:
        raise HTTPException(status_code=404, detail=f"No data found for exercise group: {exercise_group}")
        
    return ChartResponse(
        exercise_group=exercise_group,
        control_limits=ControlLimits(cl=cl, ucl=ucl, lcl=lcl),
        sessions=sessions
    )
