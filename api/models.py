from pydantic import BaseModel
from typing import Optional, List
from datetime import date

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
    training_goal: str = "HYPERTROPHY"
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
    goal_aligned: bool = True
    target_total_weight: Optional[float] = None
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    target_weight_per_rep: Optional[float] = None

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
# Config Endpoints
# -----------------
class UpdateGoalRequest(BaseModel):
    exercise_group: str
    training_goal: str  # Must be 'STRENGTH' or 'HYPERTROPHY'

class UpdateGoalResponse(BaseModel):
    message: str
    exercise_group: str
    training_goal: str

# -----------------
# Workout Endpoints
# -----------------
class LogWorkoutRequest(BaseModel):
    athlete_name: str
    exercise_group: str
    sets: int
    total_reps: int
    total_weight: float
    rpe: int

class LogWorkoutResponse(BaseModel):
    message: str
    workout_id: Optional[str] = None
