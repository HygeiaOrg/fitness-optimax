from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# -----------------
# Target Endpoints
# -----------------
class TargetResponse(BaseModel):
    exercise_group: str
    training_goal: str
    last_session_date: date
    days_since_last_session: int
    staleness_alert: bool
    last_total_weight: float
    rolling_avg_5: float
    last_avg_reps_per_set: float
    rpe_avg_3: Optional[float]
    is_plateau: bool
    alert_type: str
    alert_message: str
    goal_aligned: bool
    target_total_weight: float
    target_sets: int
    target_reps: int
    target_weight_per_rep: float

# -----------------
# Chart Endpoints
# -----------------
class ControlLimits(BaseModel):
    cl: float
    ucl: float
    lcl: float

class SessionPoint(BaseModel):
    session_rank: int
    workout_date: date
    total_weight: float
    rolling_avg_3: Optional[float]
    rolling_avg_5: Optional[float]
    rolling_avg_7: Optional[float]
    is_out_of_control: bool
    # Golden cross / regression could be added here if needed for UI markers
    momentum_signal: str

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
