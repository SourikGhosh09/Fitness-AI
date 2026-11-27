"""Free-form workout logbook: dated, per-set journal with timers metadata.

The logbook is a personal journal. It never feeds the adaptive engine, the immutable
performance_logs history, XP or learning examples, so it cannot weaken safety gating.
"""
from datetime import date as _date, timedelta
from typing import Literal
from pydantic import Field, model_validator
from .contracts import Contract

def parse_day(value):
    try:
        parsed=_date.fromisoformat(value)
    except (TypeError,ValueError):
        raise ValueError('date must be an ISO date in YYYY-MM-DD format')
    if parsed.isoformat()!=value:raise ValueError('date must be an ISO date in YYYY-MM-DD format')
    return parsed

class LogSet(Contract):
    kind: Literal['reps','seconds'] = 'reps'
    weight_kg: float | None = Field(default=None,ge=0,le=1000)
    reps: int | None = Field(default=None,ge=0,le=3600)
    rir: int | None = Field(default=None,ge=0,le=10)
    done: bool = False
    completed_at: float | None = Field(default=None,ge=0)
    rest_seconds: int | None = Field(default=None,ge=0,le=3600)
class LogExercise(Contract):
    exercise_id: str | None = Field(default=None,max_length=80)
    name: str = Field(min_length=1,max_length=120)
    target: str = Field(default='',max_length=200)
    baseline: str = Field(default='',max_length=200)
    notes: str = Field(default='',max_length=500)
    rest_seconds: int = Field(default=90,ge=0,le=900)
    sets: list[LogSet] = Field(default_factory=list,max_length=30)
class LogCheck(Contract):
    text: str = Field(min_length=1,max_length=200)
    done: bool = False
class LogCardio(Contract):
    activity: str = Field(default='',max_length=120)
    target: str = Field(default='',max_length=200)
    minutes: float | None = Field(default=None,ge=0,le=1440)
class LogSession(Contract):
    version: int = Field(default=0,ge=0)
    title: str = Field(default='Workout',min_length=1,max_length=120)
    status: Literal['planned','in_progress','completed'] = 'planned'
    started_at: float | None = Field(default=None,ge=0)
    ended_at: float | None = Field(default=None,ge=0)
    paused_seconds: int = Field(default=0,ge=0,le=86400)
    body_weight_kg: float | None = Field(default=None,ge=20,le=500)
    sleep_hours: float | None = Field(default=None,ge=0,le=24)
    energy: int | None = Field(default=None,ge=0,le=10)
    soreness_pre: int | None = Field(default=None,ge=0,le=10)
    pain_pre: int | None = Field(default=None,ge=0,le=10)
    soreness_post: int | None = Field(default=None,ge=0,le=10)
    pain_post: int | None = Field(default=None,ge=0,le=10)
    difficulty: str = Field(default='',max_length=200)
    technique: str = Field(default='',max_length=200)
    notes: str = Field(default='',max_length=4000)
    exercises: list[LogExercise] = Field(default_factory=list,max_length=40)
    warmup: list[LogCheck] = Field(default_factory=list,max_length=30)
    stretch: list[LogCheck] = Field(default_factory=list,max_length=30)
    cooldown: list[LogCheck] = Field(default_factory=list,max_length=30)
    cardio: LogCardio = Field(default_factory=LogCardio)
    @model_validator(mode='after')
    def coherent(self):
        if self.started_at is not None and self.ended_at is not None and self.ended_at<self.started_at:
            raise ValueError('ended_at cannot be before started_at')
        if self.status=='completed' and self.started_at is None and self.ended_at is not None:
            raise ValueError('ended_at requires started_at')
        return self

def data_of(session):
    return session.model_dump(exclude={'version'})

def summarize(row):
    d=row['data'];sets=[s for e in d.get('exercises',[]) for s in e.get('sets',[])]
    done=[s for s in sets if s.get('done')]
    volume=sum((s.get('weight_kg') or 0)*(s.get('reps') or 0) for s in done if s.get('kind','reps')=='reps')
    return {'date':row['day'],'title':d.get('title'),'status':d.get('status'),'version':row['version'],'exercise_count':len(d.get('exercises',[])),'sets_total':len(sets),'sets_done':len(done),'volume_kg':round(volume,2)}

def week_bounds(day):
    d=parse_day(day);start=d-timedelta(days=d.weekday())
    return start.isoformat(),(start+timedelta(days=6)).isoformat()
