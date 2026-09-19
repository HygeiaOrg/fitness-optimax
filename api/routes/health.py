"""Health and diagnostics endpoints.

`/api/diagnostics` walks the BigQuery pipeline one layer at a time and reports
the first layer that fails, with the real BigQuery message. Opening that URL in
a browser is the fastest way to turn an opaque dashboard 500 into a named cause.
"""

import logging

from fastapi import APIRouter

from api.errors import OptiMaxError
from api.services.bq_client import BQClient

router = APIRouter()
logger = logging.getLogger("optimax.health")

# Ordered as the pipeline builds: the first failure is the root cause,
# everything downstream of it fails for the same reason.
PIPELINE_LAYERS = [
    ("source_google_sheet", "Fitness OptiMax", "External Google Sheet (needs Drive access)"),
    ("native_workouts", "native_workouts", "Workouts logged from the app"),
    ("stg_workouts", "stg_workouts", "Layer 1 - cleaned/merged workouts"),
    ("workout_metrics", "workout_metrics", "Layer 2 - per-session metrics"),
    ("spc_rolling_averages", "spc_rolling_averages", "Layer 3 - rolling averages"),
    ("spc_charts", "spc_charts", "Layer 4 - SPC control limits"),
    ("training_goals", "training_goals", "Config - declared training goals"),
    ("exercise_taxonomy", "exercise_taxonomy", "Config - exercise taxonomy"),
    ("rpe_calibration", "rpe_calibration", "Layer 6 - RPE calibration"),
    ("plateau_detection", "plateau_detection", "Layer 7 - plateau detection"),
    ("workout_targets", "workout_targets", "Layer 8 - what the dashboard reads"),
]


@router.get("/health")
def health():
    """Cheap liveness probe — never touches BigQuery."""
    return {"status": "ok"}


@router.get("/diagnostics")
def diagnostics():
    """Probe every layer of the pipeline and report the first broken one."""
    report: dict = {"status": "ok", "auth": None, "layers": [], "first_failure": None}

    try:
        bq = BQClient()
    except OptiMaxError as exc:
        report["status"] = "auth_failed"
        report["first_failure"] = {
            "layer": "authentication",
            "error": exc.message,
            "hint": exc.hint,
        }
        return report

    report["auth"] = bq.auth_info()

    for key, table, description in PIPELINE_LAYERS:
        entry = {"layer": key, "description": description}
        try:
            # Table names come from the constant above, never from user input.
            results = bq.query(
                f"SELECT COUNT(*) AS row_count FROM `{bq.project_id}.{bq.dataset}.{table}`"
            )
            entry["ok"] = True
            entry["rows"] = next(iter(results)).row_count
        except OptiMaxError as exc:
            entry["ok"] = False
            entry["error"] = exc.message
            if exc.hint:
                entry["hint"] = exc.hint
            logger.warning("Diagnostics: layer %s failed: %s", key, exc.message)
        except Exception as exc:  # noqa: BLE001 - diagnostics must never itself 500
            entry["ok"] = False
            entry["error"] = f"{type(exc).__name__}: {exc}"

        report["layers"].append(entry)
        if not entry["ok"] and report["first_failure"] is None:
            report["status"] = "broken"
            report["first_failure"] = entry

    return report
