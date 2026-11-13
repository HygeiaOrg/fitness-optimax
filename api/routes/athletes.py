"""Athlete registration (issue #18)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from google.cloud import bigquery

from api import rows
from api.dependencies import get_bq_client
from api.models import (
    AgeCategory,
    AthleteResponse,
    RegisterAthleteRequest,
    SexCategory,
    WEIGHT_CLASSES,
    WeightClassesResponse,
)
from api.services.bq_client import BQClient

router = APIRouter()


@router.get("/weight-classes", response_model=WeightClassesResponse)
def list_weight_classes():
    """The valid weight_category values per sex_category, for the registration form."""
    return WeightClassesResponse(
        male=WEIGHT_CLASSES[SexCategory.male],
        female=WEIGHT_CLASSES[SexCategory.female],
    )


@router.post("", response_model=AthleteResponse, status_code=201)
def register_athlete(payload: RegisterAthleteRequest, bq: BQClient = Depends(get_bq_client)):
    """Register a new athlete.

    Juniors are excluded from the pilot (issue #18): no parental-consent flow
    exists yet, so under-18 sign-ups are rejected here rather than left for
    the frontend alone to enforce.
    """
    if payload.age_category == AgeCategory.under_18:
        raise HTTPException(
            status_code=403,
            detail="Junior sign-up (under 18) needs a parent/guardian — please contact the club directly.",
        )

    athlete_id = str(uuid.uuid4())
    query = f"""
      INSERT INTO `{bq.project_id}.{bq.dataset}.athletes`
      (athlete_id, name, email, sex_category, age_category, weight_category, created_at)
      VALUES (@athlete_id, @name, @email, @sex_category, @age_category, @weight_category, CURRENT_TIMESTAMP())
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("athlete_id", "STRING", athlete_id),
            bigquery.ScalarQueryParameter("name", "STRING", payload.name),
            bigquery.ScalarQueryParameter("email", "STRING", payload.email),
            bigquery.ScalarQueryParameter("sex_category", "STRING", payload.sex_category.value),
            bigquery.ScalarQueryParameter("age_category", "STRING", payload.age_category.value),
            bigquery.ScalarQueryParameter("weight_category", "STRING", payload.weight_category),
        ]
    )
    bq.query(query, job_config=job_config)

    return AthleteResponse(
        athlete_id=athlete_id,
        name=payload.name,
        email=payload.email,
        sex_category=payload.sex_category,
        age_category=payload.age_category,
        weight_category=payload.weight_category,
    )


def _fetch_athlete_row(bq: BQClient, athlete_id: str):
    query = f"""
      SELECT athlete_id, name, email, sex_category, age_category, weight_category, created_at
      FROM `{bq.project_id}.{bq.dataset}.athletes`
      WHERE athlete_id = @athlete_id
      LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("athlete_id", "STRING", athlete_id)]
    )
    return list(bq.query(query, job_config=job_config))


@router.get("/{athlete_id}", response_model=AthleteResponse)
def get_athlete(athlete_id: str, bq: BQClient = Depends(get_bq_client)):
    found = _fetch_athlete_row(bq, athlete_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"No athlete found with id {athlete_id}")
    row = found[0]
    return AthleteResponse(
        athlete_id=rows.as_str(row, "athlete_id"),
        name=rows.as_str(row, "name"),
        email=rows.as_str(row, "email"),
        sex_category=rows.as_str(row, "sex_category"),
        age_category=rows.as_str(row, "age_category"),
        weight_category=rows.as_str(row, "weight_category"),
        created_at=rows.get(row, "created_at"),
    )


@router.delete("/{athlete_id}", status_code=204)
def delete_athlete(athlete_id: str, bq: BQClient = Depends(get_bq_client)):
    """Withdraw required consent entirely: erase this athlete's profile and
    consent history.

    Does NOT touch native_workouts/one_rep_maxes — those are still keyed by
    free-text athlete_name, not athlete_id, so there is no reliable link to
    delete by yet (that needs #18's identity-mechanism decision first).
    """
    if not _fetch_athlete_row(bq, athlete_id):
        raise HTTPException(status_code=404, detail=f"No athlete found with id {athlete_id}")

    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("athlete_id", "STRING", athlete_id)]
    )
    bq.query(
        f"DELETE FROM `{bq.project_id}.{bq.dataset}.consents` WHERE athlete_id = @athlete_id",
        job_config=job_config,
    )
    bq.query(
        f"DELETE FROM `{bq.project_id}.{bq.dataset}.athletes` WHERE athlete_id = @athlete_id",
        job_config=job_config,
    )
