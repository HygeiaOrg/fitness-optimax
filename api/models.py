import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
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

# -----------------
# Athlete Endpoints (issue #18)
# -----------------
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class SexCategory(str, Enum):
    male = "male"
    female = "female"

class AgeCategory(str, Enum):
    under_18 = "under_18"
    age_18_25 = "18_25"
    age_26_35 = "26_35"
    masters_35_plus = "masters_35_plus"

# IWF-style weight classes, keyed by sex_category. The two lists share no
# values, but a field is still asked for because the lists themselves differ.
WEIGHT_CLASSES: dict[SexCategory, list[str]] = {
    SexCategory.male: ["65kg", "75kg", "85kg", "95kg", "110kg", "+110kg"],
    SexCategory.female: ["53kg", "61kg", "69kg", "77kg", "86kg", "+86kg"],
}

class RegisterAthleteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str
    sex_category: SexCategory
    age_category: AgeCategory
    weight_category: str

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("must be a valid email address")
        return v

    @model_validator(mode="after")
    def weight_category_matches_sex(self):
        allowed = WEIGHT_CLASSES[self.sex_category]
        if self.weight_category not in allowed:
            raise ValueError(
                f"weight_category must be one of {allowed} for sex_category={self.sex_category.value}"
            )
        return self

class AthleteResponse(BaseModel):
    athlete_id: str
    name: str
    email: str
    sex_category: SexCategory
    age_category: AgeCategory
    weight_category: str
    created_at: Optional[datetime] = None

class WeightClassesResponse(BaseModel):
    male: List[str]
    female: List[str]

# -----------------
# Consent Endpoints (issue #16)
# -----------------

# Bump this to re-prompt every athlete, even ones who already consented.
CURRENT_NOTICE_VERSION = "2026-11-13"

class ConsentType(str, Enum):
    data_storage = "data_storage"
    share_logs = "share_logs"

class RecordConsentRequest(BaseModel):
    athlete_id: str = Field(min_length=1)
    consent_type: ConsentType
    granted: bool
    # Defaults to the current notice; callers shouldn't normally override this.
    notice_version: str = Field(default=CURRENT_NOTICE_VERSION, min_length=1)

class ConsentRecord(BaseModel):
    athlete_id: str
    consent_type: ConsentType
    granted: bool
    notice_version: str
    timestamp: Optional[datetime] = None

class ConsentStatus(BaseModel):
    consent_type: ConsentType
    granted: Optional[bool] = None
    notice_version: Optional[str] = None
    timestamp: Optional[datetime] = None
    # True only if granted under CURRENT_NOTICE_VERSION — a bump makes this
    # False again until the athlete re-consents, which is what re-prompts them.
    current: bool = False

class ConsentStatusResponse(BaseModel):
    athlete_id: str
    notice_version: str
    consents: List[ConsentStatus]
