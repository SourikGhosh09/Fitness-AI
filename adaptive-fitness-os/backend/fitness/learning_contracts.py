"""Small, explicit feature schema; no names, emails, medical text or chat content."""
import time
from typing import Literal
from pydantic import Field, model_validator
from .contracts import Contract

PATTERNS=('squat','hinge','lunge','horizontal_push','horizontal_pull','vertical_push','vertical_pull','carry','rotation','anti_rotation','locomotion','core')
class LearningConsent(Contract):
    enabled: bool

class Features(Contract):
    experience: int=Field(ge=0,le=6)
    sleep_hours: float=Field(ge=0,le=24)
    energy: int=Field(ge=1,le=5)
    soreness: int=Field(ge=0,le=5)
    stress: int=Field(ge=0,le=5)
    reps: int=Field(ge=1,le=50)
    load_kg: float=Field(ge=0,le=600)
    target_rpe: float=Field(ge=1,le=10)
    set_number: int=Field(ge=1,le=20)
    previous_load_kg: float=Field(ge=0,le=600)
    previous_rpe: float=Field(ge=1,le=10)
    history_sessions: int=Field(ge=0,le=1000)
    pattern: Literal['squat','hinge','lunge','horizontal_push','horizontal_pull','vertical_push','vertical_pull','carry','rotation','anti_rotation','locomotion','core']

class TrainingRecord(Contract):
    event_id: str=Field(pattern=r'^[a-zA-Z0-9_-]{16,80}$')
    session_id: str=Field(pattern=r'^[a-zA-Z0-9_-]{8,80}$')
    exercise_id: str=Field(min_length=1,max_length=80)
    occurred_at: float=Field(gt=0)
    features: Features
    actual_rpe: float=Field(ge=1,le=10)
    # Importer accepts only matched, completed, pain-free prescriptions.
    actual_reps: int=Field(ge=1,le=50)
    actual_load_kg: float=Field(ge=0,le=600)
    pain: Literal[False]=False
    skipped: Literal[False]=False
    @model_validator(mode='after')
    def matched(self):
        if self.occurred_at>time.time()+300:raise ValueError('Future outcome timestamps are not accepted')
        if self.actual_reps!=self.features.reps or abs(self.actual_load_kg-self.features.load_kg)>0.01:
            raise ValueError('RPE training requires actual reps/load to match the recorded prescription')
        return self

class TrainingBatch(Contract):
    records: list[TrainingRecord]=Field(min_length=1,max_length=500)
