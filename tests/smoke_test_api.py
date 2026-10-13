"""Smoke tests for the API error handling, using a stubbed BigQuery client.

No credentials and no network needed:

    python tests/smoke_test_api.py

Exits non-zero if any check fails.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from google.api_core import exceptions as gexc

import api.routes.health as health_module
from api.dependencies import get_bq_client
from api.main import app


class FakeRow:
    """Mimics a BigQuery Row: .get() with default, attribute access, raises on unknown."""

    def __init__(self, data):
        self._data = data

    def get(self, name, default=None):
        return self._data.get(name, default)

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)


class FakeBQ:
    project_id = "test-project"
    dataset = "Optimmax"

    def __init__(self, rows=None, error=None):
        self._rows = rows or []
        self._error = error

    def query(self, sql, job_config=None):
        if self._error:
            raise self._error
        return iter(self._rows)

    def auth_info(self):
        return {"auth_mode": "fake", "service_account": "sa@test.iam.gserviceaccount.com"}


def use(bq):
    app.dependency_overrides[get_bq_client] = lambda: bq


client = TestClient(app, raise_server_exceptions=False)
failures = []


def check(name, condition, detail=""):
    print(("PASS  " if condition else "FAIL  ") + name + ("" if condition else f" -> {detail}"))
    if not condition:
        failures.append(name)


# --- 1. Fully populated row -------------------------------------------------
full = FakeRow(dict(
    exercise_group="Bench Press", training_goal="STRENGTH",
    last_session_date=datetime.date(2026, 9, 15), days_since_last_session=4,
    staleness_alert=False, last_total_weight=1200.0, rolling_avg_5=1150.0,
    last_avg_reps_per_set=5.0, rpe_avg_3=3.2, is_plateau=False,
    alert_type="SLIGHT_INCREASE", alert_message="Room for overload.",
    goal_aligned=True, target_total_weight=1178.75, target_sets=4.0,
    target_reps=8.0, target_weight_per_rep=147.3,
))
use(FakeBQ([full]))
r = client.get("/api/targets")
check("full row -> 200", r.status_code == 200, r.text)
check("float target_sets coerced to int", r.json()[0]["target_sets"] == 4, r.text)

# --- 2. NULL-heavy row (the old code 500'd on this) -------------------------
nulls = FakeRow(dict(
    exercise_group="Deadlift", training_goal=None, last_session_date=None,
    days_since_last_session=None, staleness_alert=None, last_total_weight=None,
    rolling_avg_5=None, last_avg_reps_per_set=None, rpe_avg_3=None,
    is_plateau=None, alert_type=None, alert_message=None, goal_aligned=None,
    target_total_weight=None, target_sets=None, target_reps=None,
    target_weight_per_rep=None,
))
use(FakeBQ([nulls]))
r = client.get("/api/targets")
check("all-NULL row -> 200", r.status_code == 200, r.text)
check("NULL is_plateau defaults to False", r.json()[0]["is_plateau"] is False, r.text)
check("NULL training_goal defaults", r.json()[0]["training_goal"] == "HYPERTROPHY", r.text)

# --- 3. Row missing columns entirely (view drifted) -------------------------
use(FakeBQ([FakeRow({"exercise_group": "Squat"})]))
r = client.get("/api/targets")
check("row missing columns -> 200", r.status_code == 200, r.text)

# --- 4. Drive-scope failure surfaces a real message --------------------------
from api.errors import DriveScopeError
use(FakeBQ(error=DriveScopeError("Permission denied while getting Drive credentials", hint="Grant token creator")))
r = client.get("/api/targets")
check("drive error -> 502", r.status_code == 502, r.text)
check("drive error has detail", "Drive credentials" in r.json().get("detail", ""), r.text)
check("drive error has hint", r.json().get("hint") == "Grant token creator", r.text)

# --- 5. Unexpected exception still explains itself ---------------------------
class Boom(FakeBQ):
    def query(self, sql, job_config=None):
        raise RuntimeError("kaboom")

use(Boom())
r = client.get("/api/targets")
check("unexpected error -> 500", r.status_code == 500, r.text)
check("unexpected error names the cause", "kaboom" in r.json().get("detail", ""), r.text)

# --- 6. Health + diagnostics -------------------------------------------------
r = client.get("/api/health")
check("health -> ok", r.status_code == 200 and r.json()["status"] == "ok", r.text)

class DiagBQ(FakeBQ):
    def query(self, sql, job_config=None):
        if "spc_charts" in sql:
            raise DriveScopeError("no drive", hint="share the sheet")
        return iter([FakeRow({"row_count": 42})])

health_module.BQClient = lambda: DiagBQ()
r = client.get("/api/diagnostics")
body = r.json()
check("diagnostics -> 200", r.status_code == 200, r.text)
check("diagnostics reports broken", body["status"] == "broken", r.text)
check("diagnostics names first failure", body["first_failure"]["layer"] == "spc_charts", str(body.get("first_failure")))
check("diagnostics counts healthy rows", body["layers"][0]["rows"] == 42, str(body["layers"][0]))

# --- 7. Chart route ----------------------------------------------------------
use(FakeBQ([FakeRow(dict(session_rank=1, workout_date=datetime.date(2026, 9, 1),
                         total_weight=None, rolling_avg_3=None, rolling_avg_5=None,
                         rolling_avg_7=None, cl=100.0, ucl=None, lcl=None,
                         is_out_of_control=None, momentum_signal=None))]))
r = client.get("/api/charts/Bench%20Press")
check("chart with NULLs -> 200", r.status_code == 200, r.text)

use(FakeBQ([]))
r = client.get("/api/charts/Nothing")
check("empty chart -> 404", r.status_code == 404, r.text)

# --- 8. Log workout ----------------------------------------------------------
use(FakeBQ([]))
r = client.post("/api/workouts", json=dict(athlete_name="John", exercise_group="Bench Press",
                                           sets=4, total_reps=32, total_weight=1200.0, rpe=4))
check("log workout -> 200", r.status_code == 200, r.text)

use(FakeBQ(error=gexc.BadRequest("Column mismatch")))
from api.errors import BigQueryQueryError
class FailingInsert(FakeBQ):
    def query(self, sql, job_config=None):
        raise BigQueryQueryError("BigQuery query failed: Column mismatch")
use(FailingInsert())
r = client.post("/api/workouts", json=dict(athlete_name="John", exercise_group="Bench Press",
                                           sets=4, total_reps=32, total_weight=1200.0, rpe=4))
check("failed insert -> 502 with reason", r.status_code == 502 and "Column mismatch" in r.json()["detail"], r.text)

# --- 9. One rep maxes --------------------------------------------------------
use(FakeBQ([FakeRow(dict(lift="Snatch", one_rm_kg=100.0, recorded_at=datetime.datetime(2026, 10, 1, 9, 0))),
            FakeRow(dict(lift="Back Squat", one_rm_kg=None, recorded_at=None))]))
r = client.get("/api/one-rep-maxes", params={"athlete_name": "John"})
check("list 1RMs -> 200", r.status_code == 200, r.text)
check("list 1RMs skips NULL rows", [m["lift"] for m in r.json()["one_rep_maxes"]] == ["Snatch"], r.text)

r = client.get("/api/one-rep-maxes")
check("list 1RMs without athlete -> 422", r.status_code == 422, r.text)

use(FakeBQ([]))
r = client.post("/api/one-rep-maxes", json=dict(athlete_name="John", lift="  Snatch ", one_rm_kg=102.5))
check("save 1RM -> 200", r.status_code == 200 and r.json()["lift"] == "Snatch" and r.json()["one_rm_kg"] == 102.5, r.text)

r = client.post("/api/one-rep-maxes", json=dict(athlete_name="John", lift="Snatch", one_rm_kg=0))
check("save 1RM of 0 -> 422", r.status_code == 422, r.text)
r = client.post("/api/one-rep-maxes", json=dict(athlete_name="John", lift="Snatch", one_rm_kg=1000))
check("save absurd 1RM -> 422", r.status_code == 422, r.text)

use(FailingInsert())
r = client.post("/api/one-rep-maxes", json=dict(athlete_name="John", lift="Snatch", one_rm_kg=100))
check("failed 1RM insert -> 502", r.status_code == 502, r.text)

print()
print("FAILURES:", failures if failures else "none")
sys.exit(1 if failures else 0)
