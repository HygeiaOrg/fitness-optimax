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
from api.models import CURRENT_NOTICE_VERSION


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
    exercise_group="Upper Body, Chest",
    last_session_date=datetime.date(2026, 9, 15), days_since_last_session=4,
    staleness_alert=False, last_total_weight=1200.0, rolling_avg_5=1150.0,
    last_avg_reps_per_set=5.0, rpe_avg_3=3.2, is_plateau=False,
    alert_type="SLIGHT_INCREASE", alert_message="Room for overload.",
    target_total_weight=1178.75, target_sets=4.0,
    target_reps=8.0, target_weight_per_rep=147.3,
    last_avg_weight_per_rep=60.0, estimated_1rm=70.0, best_estimated_1rm=72.5,
))
use(FakeBQ([full]))
r = client.get("/api/targets")
check("full row -> 200", r.status_code == 200, r.text)
check("float target_sets coerced to int", r.json()[0]["target_sets"] == 4, r.text)
check("estimated 1RM passed through", r.json()[0]["best_estimated_1rm"] == 72.5, r.text)
check("no training goal in response", "training_goal" not in r.json()[0], r.text)

# --- 2. NULL-heavy row (the old code 500'd on this) -------------------------
nulls = FakeRow(dict(
    exercise_group="Snatch", last_session_date=None,
    days_since_last_session=None, staleness_alert=None, last_total_weight=None,
    rolling_avg_5=None, last_avg_reps_per_set=None, rpe_avg_3=None,
    is_plateau=None, alert_type=None, alert_message=None,
    target_total_weight=None, target_sets=None, target_reps=None,
    target_weight_per_rep=None, estimated_1rm=None, best_estimated_1rm=None,
))
use(FakeBQ([nulls]))
r = client.get("/api/targets")
check("all-NULL row -> 200", r.status_code == 200, r.text)
check("NULL is_plateau defaults to False", r.json()[0]["is_plateau"] is False, r.text)
check("NULL estimated 1RM stays null", r.json()[0]["estimated_1rm"] is None, r.text)

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
r = client.post("/api/workouts", json=dict(athlete_name="John", exercise_group="Snatch",
                                           sets=5, total_reps=10, total_weight=700.0, rpe=8))
check("RPE 8 on the 0-10 scale -> 200", r.status_code == 200, r.text)
r = client.post("/api/workouts", json=dict(athlete_name="John", exercise_group="Snatch",
                                           sets=5, total_reps=10, total_weight=700.0, rpe=11))
check("RPE outside the 0-10 scale -> 422", r.status_code == 422, r.text)
r = client.get("/api/goals")
check("training goals endpoint removed", r.status_code in (404, 405), r.text)

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

# --- 10. Athlete registration (issue #18) ------------------------------------
valid_athlete = dict(
    name="Jane Lifter", email="jane@example.com",
    sex_category="female", age_category="26_35", weight_category="69kg",
)

use(FakeBQ([]))
r = client.post("/api/athletes", json=valid_athlete)
check("register athlete -> 201", r.status_code == 201, r.text)
check("register athlete returns an athlete_id", bool(r.json().get("athlete_id")), r.text)

r = client.post("/api/athletes", json=dict(valid_athlete, sex_category="male"))
check("weight class for the wrong sex -> 422", r.status_code == 422, r.text)

r = client.post("/api/athletes", json=dict(valid_athlete, age_category="under_18"))
check("under-18 registration blocked -> 403", r.status_code == 403, r.text)
check("under-18 block names a contact path", "contact the club" in r.json()["detail"], r.text)

r = client.post("/api/athletes", json=dict(valid_athlete, email="not-an-email"))
check("invalid email -> 422", r.status_code == 422, r.text)

r = client.get("/api/athletes/weight-classes")
check("weight classes -> 200", r.status_code == 200, r.text)
check("weight classes lists male & female", set(r.json().keys()) == {"male", "female"}, r.text)

use(FakeBQ([FakeRow(dict(
    athlete_id="abc123", name="Jane Lifter", email="jane@example.com",
    sex_category="female", age_category="26_35", weight_category="69kg",
    created_at=datetime.datetime(2026, 11, 13, 12, 0),
))]))
r = client.get("/api/athletes/abc123")
check("get athlete -> 200", r.status_code == 200, r.text)
check("get athlete returns weight_category", r.json()["weight_category"] == "69kg", r.text)

use(FakeBQ([]))
r = client.get("/api/athletes/unknown-id")
check("get unknown athlete -> 404", r.status_code == 404, r.text)

r = client.delete("/api/athletes/unknown-id")
check("delete unknown athlete -> 404", r.status_code == 404, r.text)

use(FakeBQ([FakeRow(dict(athlete_id="abc123", name="Jane Lifter"))]))
r = client.delete("/api/athletes/abc123")
check("delete athlete -> 204", r.status_code == 204, r.text)

# --- 11. Consents (issue #16) -------------------------------------------------
use(FakeBQ([]))
r = client.get("/api/consents", params={"athlete_id": "ghost"})
check("consent status for unknown athlete -> 404", r.status_code == 404, r.text)

r = client.post("/api/consents", json=dict(athlete_id="ghost", consent_type="data_storage", granted=True))
check("record consent for unknown athlete -> 404", r.status_code == 404, r.text)

use(FakeBQ([FakeRow(dict(athlete_id="abc123"))]))
r = client.post("/api/consents", json=dict(athlete_id="abc123", consent_type="data_storage", granted=True))
check("record consent -> 201", r.status_code == 201, r.text)
check("record consent echoes current notice_version",
      r.json()["notice_version"] == CURRENT_NOTICE_VERSION, r.text)

use(FakeBQ([FakeRow(dict(
    consent_type="data_storage", granted=True, notice_version=CURRENT_NOTICE_VERSION,
    timestamp=datetime.datetime(2026, 11, 13, 12, 0),
))]))
r = client.get("/api/consents", params={"athlete_id": "abc123"})
check("consent status -> 200", r.status_code == 200, r.text)
by_type = {c["consent_type"]: c for c in r.json()["consents"]}
check("data_storage granted & current",
      by_type["data_storage"]["granted"] is True and by_type["data_storage"]["current"] is True, r.text)
check("share_logs defaults to never-recorded", by_type["share_logs"]["granted"] is None, r.text)

use(FakeBQ([FakeRow(dict(
    consent_type="data_storage", granted=True, notice_version="2025-01-01",
    timestamp=datetime.datetime(2025, 1, 1, 9, 0),
))]))
r = client.get("/api/consents", params={"athlete_id": "abc123"})
stale = {c["consent_type"]: c for c in r.json()["consents"]}["data_storage"]
check("consent on an old notice_version is not current", stale["current"] is False, r.text)

print()
print("FAILURES:", failures if failures else "none")
sys.exit(1 if failures else 0)
