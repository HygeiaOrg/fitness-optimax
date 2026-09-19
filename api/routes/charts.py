from fastapi import APIRouter, Depends, HTTPException
from google.cloud import bigquery

from api import rows
from api.dependencies import get_bq_client
from api.models import ChartResponse, ControlLimits, SessionPoint
from api.services.bq_client import BQClient

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
    FROM `{bq.project_id}.{bq.dataset}.spc_charts`
    WHERE LOWER(exercise_group) = LOWER(@exercise_group)
    ORDER BY session_rank ASC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("exercise_group", "STRING", exercise_group)
        ]
    )

    results = bq.query(query, job_config=job_config)

    sessions = []
    cl, ucl, lcl = 0.0, 0.0, 0.0

    # We'll just grab the control limits from the last row since they are static per group
    # (unless phase-based limits are introduced later)
    for row in results:
        cl = rows.as_float(row, "cl", cl)
        ucl = rows.as_float(row, "ucl", ucl)
        lcl = rows.as_float(row, "lcl", lcl)
        sessions.append(SessionPoint(
            session_rank=rows.as_int(row, "session_rank", 0),
            workout_date=rows.as_date(row, "workout_date"),
            total_weight=rows.as_float(row, "total_weight"),
            rolling_avg_3=rows.as_float(row, "rolling_avg_3"),
            rolling_avg_5=rows.as_float(row, "rolling_avg_5"),
            rolling_avg_7=rows.as_float(row, "rolling_avg_7"),
            is_out_of_control=rows.as_bool(row, "is_out_of_control"),
            momentum_signal=rows.as_str(row, "momentum_signal", "MIXED"),
        ))

    if not sessions:
        raise HTTPException(status_code=404, detail=f"No data found for exercise group: {exercise_group}")

    return ChartResponse(
        exercise_group=exercise_group,
        control_limits=ControlLimits(cl=cl, ucl=ucl, lcl=lcl),
        sessions=sessions,
    )
