import logging
from typing import List

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from api import rows
from api.dependencies import get_bq_client
from api.models import TargetResponse
from api.services.bq_client import BQClient

router = APIRouter()
logger = logging.getLogger("optimax.targets")


@router.get("", response_model=List[TargetResponse])
def get_workout_targets(bq: BQClient = Depends(get_bq_client)):
    """
    Fetch the most recent, actionable progressive overload targets for every exercise group.
    Sourced from Layer 5 (`workout_targets` BigQuery view).
    """
    query = f"""
    SELECT *
    FROM `{bq.project_id}.{bq.dataset}.workout_targets`
    ORDER BY last_session_date DESC
    """

    results = bq.query(query)

    targets: List[TargetResponse] = []
    skipped = 0
    for row in results:
        try:
            targets.append(TargetResponse(
                exercise_group=rows.as_str(row, "exercise_group"),
                training_goal=rows.as_str(row, "training_goal", "HYPERTROPHY"),
                last_session_date=rows.as_date(row, "last_session_date"),
                days_since_last_session=rows.as_int(row, "days_since_last_session"),
                staleness_alert=rows.as_bool(row, "staleness_alert"),
                last_total_weight=rows.as_float(row, "last_total_weight"),
                rolling_avg_5=rows.as_float(row, "rolling_avg_5"),
                last_avg_reps_per_set=rows.as_float(row, "last_avg_reps_per_set"),
                rpe_avg_3=rows.as_float(row, "rpe_avg_3"),
                is_plateau=rows.as_bool(row, "is_plateau"),
                alert_type=rows.as_str(row, "alert_type", "MAINTAIN"),
                alert_message=rows.as_str(row, "alert_message"),
                goal_aligned=rows.as_bool(row, "goal_aligned", True),
                target_total_weight=rows.as_float(row, "target_total_weight"),
                target_sets=rows.as_int(row, "target_sets"),
                target_reps=rows.as_int(row, "target_reps"),
                target_weight_per_rep=rows.as_float(row, "target_weight_per_rep"),
            ))
        except ValidationError as exc:
            # One unusable row should never blank the whole dashboard.
            skipped += 1
            logger.warning("Skipping unreadable target row: %s", exc)

    if skipped:
        logger.warning("Returned %d targets, skipped %d unreadable rows", len(targets), skipped)

    return targets
