from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

GOALS = {'strength','hypertrophy','fat_loss','muscular_endurance','cardio','mobility','flexibility','power','athleticism','general_health','sport','recomposition'}
class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
class Profile(Contract):
    display_name: str = Field(min_length=1,max_length=80)
    adult: bool
    experience: int = Field(default=0,ge=0,le=6)
    goals: dict[str,int]
    equipment: list[str] = Field(default_factory=lambda:['body weight'],max_length=50)
    minutes: int = Field(default=40,ge=15,le=120)
    days: list[int] = Field(default_factory=lambda:[0,2,4],min_length=1,max_length=7)
    blocked_patterns: list[str] = Field(default_factory=list,max_length=30)
    restrictions: list[str] = Field(default_factory=list,max_length=30)
    disliked: list[str] = Field(default_factory=list,max_length=100)
    age: int | None = Field(default=None,ge=18,le=100)
    sex: Literal['male','female','intersex','prefer_not_to_say'] | None = None
    height_cm: float | None = Field(default=None,ge=100,le=250)
    body_fat_percent: float | None = Field(default=None,ge=2,le=70)
    sport: str | None = Field(default=None,max_length=100)
    occupation_activity: Literal['sedentary','light','moderate','high'] | None = None
    training_history: str | None = Field(default=None,max_length=2000)
    injuries: list[str] = Field(default_factory=list,max_length=30)
    movement_limitations: list[str] = Field(default_factory=list,max_length=30)
    liked: list[str] = Field(default_factory=list,max_length=100)
    dietary_preferences: list[str] = Field(default_factory=list,max_length=30)
    food_allergies: list[str] = Field(default_factory=list,max_length=30)
    locale: Literal['en','bn'] = 'en'
    timezone: str = Field(default='UTC',max_length=80)
    assessment_mode: Literal['quick','guided','data_assisted'] = 'quick'
    nutrition: bool = False
    gamification: bool = True
    weight_kg: float | None = Field(default=None,ge=30,le=350)
    @model_validator(mode='after')
    def validate_goals(self):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try: ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError): raise ValueError('Invalid IANA timezone')
        if not self.adult: raise ValueError('This release supports adults only.')
        if not self.goals or set(self.goals)-GOALS or sum(self.goals.values())!=100 or any(v<0 or v>100 for v in self.goals.values()):
            raise ValueError('Choose supported goals with priorities totaling 100%.')
        if len(set(self.days))!=len(self.days) or any(d<0 or d>6 for d in self.days): raise ValueError('Training days must be unique weekday numbers 0–6.')
        return self
class Readiness(Contract):
    sleep_hours: float = Field(ge=0,le=24)
    energy: int = Field(ge=1,le=5)
    soreness: int = Field(ge=0,le=5)
    stress: int = Field(ge=0,le=5)
    pain: bool = False
    red_flag: bool = False
class Credentials(Contract):
    email: str = Field(min_length=5,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=12,max_length=128)
class KeyRequest(Contract):
    name: str = Field(min_length=1,max_length=80)
    scopes: list[Literal['read','train','coach']] = Field(min_length=1,max_length=3)
    expires_days: int = Field(default=30,ge=1,le=365)
class SetLog(Contract):
    event_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{16,80}$')
    workout_id: str
    exercise_id: str
    set_number: int = Field(ge=1,le=20)
    reps: int = Field(ge=0,le=200)
    load_kg: float = Field(ge=0,le=600)
    rpe: float = Field(ge=1,le=10)
    pain: bool = False
    skipped: bool = False
class CoachRequest(Contract):
    message: str = Field(min_length=1,max_length=2000)
class Substitute(Contract):
    exercise_id: str
    reason: Literal['occupied','dislike','equipment','uncomfortable','travel']
class NutritionInput(Contract):
    maintenance_estimate: int = Field(ge=1200,le=6000)
    adjustment: int = Field(default=0,ge=-300,le=300)
    weight_kg: float = Field(ge=40,le=250)
    meals: int = Field(default=4,ge=1,le=8)
    allergies: list[str] = Field(default_factory=list,max_length=30)
