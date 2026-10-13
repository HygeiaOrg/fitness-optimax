"""Athletes' one-rep maxes, used by Log Workout to turn a % of 1RM into kg."""
from fastapi import APIRouter, Depends, Query
from google.cloud import bigquery

from api.dependencies import get_bq_client
from api.models import OneRepMax, OneRepMaxListResponse, SaveOneRepMaxRequest
from api.services.bq_client import BQClient

router = APIRouter()


@router.get("", response_model=OneRepMaxListResponse)
def list_one_rep_maxes(athlete_name: str = Query(..., min_length=1), bq: BQClient = Depends(get_bq_client)):
    """Current (most recently recorded) 1RM per lift for one athlete."""
    query = f"""
      SELECT lift, one_rm_kg, recorded_at
      FROM `{bq.project_id}.{bq.dataset}.one_rep_maxes`
      WHERE athlete_name = @athlete_name
      QUALIFY ROW_NUMBER() OVER (PARTITION BY lift ORDER BY recorded_at DESC) = 1
      ORDER BY lift
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("athlete_name", "STRING", athlete_name.strip())]
    )
    rows = bq.query(query, job_config=job_config)
    return OneRepMaxListResponse(
        athlete_name=athlete_name.strip(),
        one_rep_maxes=[
            OneRepMax(lift=r.get("lift"), one_rm_kg=r.get("one_rm_kg"), recorded_at=r.get("recorded_at"))
            for r in rows
            if r.get("lift") and r.get("one_rm_kg") is not None
        ],
    )


@router.post("", response_model=OneRepMax)
def save_one_rep_max(payload: SaveOneRepMaxRequest, bq: BQClient = Depends(get_bq_client)):
    """Record a new 1RM. History is kept; the newest row becomes current."""
    lift = " ".join(payload.lift.split())
    query = f"""
      INSERT INTO `{bq.project_id}.{bq.dataset}.one_rep_maxes` (athlete_name, lift, one_rm_kg, recorded_at)
      VALUES (@athlete_name, @lift, @one_rm_kg, CURRENT_TIMESTAMP())
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("athlete_name", "STRING", payload.athlete_name.strip()),
            bigquery.ScalarQueryParameter("lift", "STRING", lift),
            bigquery.ScalarQueryParameter("one_rm_kg", "FLOAT64", payload.one_rm_kg),
        ]
    )
    bq.query(query, job_config=job_config)
    return OneRepMax(lift=lift, one_rm_kg=payload.one_rm_kg)
