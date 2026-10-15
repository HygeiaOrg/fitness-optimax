from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# -----------------
# Target Endpoints
# -----------------
class TargetResponse(BaseModel):
    """One dashboard card.

    Every field except the exercise group is optional: the underlying BigQuery
    views LEFT JOIN several layers together, so a brand-new exercise group (or a
    single malformed row in the source sheet) can legitimately produce NULLs.
    Those must not take the whole dashboard down with a 500.
    """

    exercise_group: str
    last_session_date: Optional[date] = None
    days_since_last_session: Optional[int] = None
    staleness_alert: bool = False
    last_total_weight: Optional[float] = None
    rolling_avg_5: Optional[float] = None
    last_avg_reps_per_set: Optional[float] = None
    rpe_avg_3: Optional[float] = None
    is_plateau: bool = False
    alert_type: str = "MAINTAIN"
    alert_message: str = ""
    target_total_weight: Optional[float] = None
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    target_weight_per_rep: Optional[float] = None
    last_avg_weight_per_rep: Optional[float] = None
    # Epley estimates from logged sessions (latest, and best on record).
    estimated_1rm: Optional[float] = None
    best_estimated_1rm: Optional[float] = None

# -----------------
# Chart Endpoints
# -----------------
class ControlLimits(BaseModel):
    cl: Optional[float] = None
    ucl: Optional[float] = None
    lcl: Optional[float] = None

class SessionPoint(BaseModel):
    session_rank: int
    workout_date: Optional[date] = None
    total_weight: Optional[float] = None
    rolling_avg_3: Optional[float] = None
    rolling_avg_5: Optional[float] = None
    rolling_avg_7: Optional[float] = None
    is_out_of_control: bool = False
    # Golden cross / regression could be added here if needed for UI markers
    momentum_signal: str = "MIXED"

class ChartResponse(BaseModel):
    exercise_group: str
    control_limits: ControlLimits
    sessions: List[SessionPoint]

# -----------------
# Workout Endpoints
# -----------------
class LogWorkoutRequest(BaseModel):
    athlete_name: str
    exercise_group: str
    sets: int
    total_reps: int
    total_weight: float
    # RPE on the 0-10 scale (10 = maximal, nothing left; 9 = one rep left).
    rpe: int = Field(ge=0, le=10)

class LogWorkoutResponse(BaseModel):
    message: str
    workout_id: Optional[str] = None

# -----------------
# One Rep Max Endpoints
# -----------------
class OneRepMax(BaseModel):
    lift: str
    one_rm_kg: float
    recorded_at: Optional[datetime] = None

class OneRepMaxListResponse(BaseModel):
    athlete_name: str
    one_rep_maxes: List[OneRepMax]

class SaveOneRepMaxRequest(BaseModel):
    athlete_name: str = Field(min_length=1)
    lift: str = Field(min_length=1)
    # World-record territory is ~300 kg; 500 leaves room and still catches typos.
    one_rm_kg: float = Field(gt=0, le=500)
