"""Athlete consent decisions (issue #16)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud import bigquery

from api import rows
from api.dependencies import get_bq_client
from api.models import (
    CURRENT_NOTICE_VERSION,
    ConsentRecord,
    ConsentStatus,
    ConsentStatusResponse,
    ConsentType,
    RecordConsentRequest,
)
from api.services.bq_client import BQClient

router = APIRouter()


def _athlete_exists(bq: BQClient, athlete_id: str) -> bool:
    query = f"""
      SELECT athlete_id FROM `{bq.project_id}.{bq.dataset}.athletes`
      WHERE athlete_id = @athlete_id
      LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("athlete_id", "STRING", athlete_id)]
    )
    return bool(list(bq.query(query, job_config=job_config)))


@router.get("", response_model=ConsentStatusResponse)
def get_consent_status(athlete_id: str = Query(..., min_length=1), bq: BQClient = Depends(get_bq_client)):
    """Current (most recently recorded) decision per consent type.

    `current` is False whenever the latest decision was made under an older
    notice_version than CURRENT_NOTICE_VERSION — that's what re-prompts an
    athlete after the notice changes.
    """
    if not _athlete_exists(bq, athlete_id):
        raise HTTPException(status_code=404, detail=f"No athlete found with id {athlete_id}")

    query = f"""
      SELECT consent_type, granted, notice_version, timestamp
      FROM `{bq.project_id}.{bq.dataset}.consents`
      WHERE athlete_id = @athlete_id
      QUALIFY ROW_NUMBER() OVER (PARTITION BY consent_type ORDER BY timestamp DESC) = 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("athlete_id", "STRING", athlete_id)]
    )
    latest = {rows.as_str(r, "consent_type"): r for r in bq.query(query, job_config=job_config)}

    consents = []
    for consent_type in ConsentType:
        row = latest.get(consent_type.value)
        if row is None:
            consents.append(ConsentStatus(consent_type=consent_type))
            continue
        notice_version = rows.as_str(row, "notice_version")
        consents.append(ConsentStatus(
            consent_type=consent_type,
            granted=rows.as_bool(row, "granted"),
            notice_version=notice_version,
            timestamp=rows.get(row, "timestamp"),
            current=notice_version == CURRENT_NOTICE_VERSION,
        ))

    return ConsentStatusResponse(
        athlete_id=athlete_id,
        notice_version=CURRENT_NOTICE_VERSION,
        consents=consents,
    )


@router.post("", response_model=ConsentRecord, status_code=201)
def record_consent(payload: RecordConsentRequest, bq: BQClient = Depends(get_bq_client)):
    """Append one consent decision. History is kept; the newest row per
    (athlete_id, consent_type) is current — same pattern as one_rep_maxes."""
    if not _athlete_exists(bq, payload.athlete_id):
        raise HTTPException(status_code=404, detail=f"No athlete found with id {payload.athlete_id}")

    query = f"""
      INSERT INTO `{bq.project_id}.{bq.dataset}.consents`
      (athlete_id, consent_type, granted, notice_version, timestamp)
      VALUES (@athlete_id, @consent_type, @granted, @notice_version, CURRENT_TIMESTAMP())
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("athlete_id", "STRING", payload.athlete_id),
            bigquery.ScalarQueryParameter("consent_type", "STRING", payload.consent_type.value),
            bigquery.ScalarQueryParameter("granted", "BOOL", payload.granted),
            bigquery.ScalarQueryParameter("notice_version", "STRING", payload.notice_version),
        ]
    )
    bq.query(query, job_config=job_config)

    return ConsentRecord(
        athlete_id=payload.athlete_id,
        consent_type=payload.consent_type,
        granted=payload.granted,
        notice_version=payload.notice_version,
    )
