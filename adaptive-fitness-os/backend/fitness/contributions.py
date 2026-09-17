"""Human-friendly collection. Missing observations stay missing; review gates training."""
import time
from typing import Literal
from pydantic import Field,model_validator
from sqlalchemy import select,insert,update
from . import db,learning
from .contracts import Contract
from .learning_contracts import TrainingRecord,PATTERNS

class Context(Contract):
    experience:int|None=Field(default=None,ge=0,le=6)
    sleep_hours:float|None=Field(default=None,ge=0,le=24)
    energy:int|None=Field(default=None,ge=1,le=5)
    soreness:int|None=Field(default=None,ge=0,le=5)
    stress:int|None=Field(default=None,ge=0,le=5)

class Observation(Contract):
    reps:int=Field(ge=0,le=200)
    load_kg:float=Field(ge=0,le=600)
    rpe:float|None=Field(default=None,ge=1,le=10)
    pain:bool|None=None
    skipped:bool=False
    planned_reps:int|None=Field(default=None,ge=1,le=50)
    planned_load_kg:float|None=Field(default=None,ge=0,le=600)
    target_rpe:float|None=Field(default=None,ge=1,le=10)

class Contribution(Contract):
    event_id:str=Field(pattern=r'^[a-zA-Z0-9_-]{16,80}$')
    session_id:str=Field(pattern=r'^[a-zA-Z0-9_-]{8,80}$')
    exercise_id:str=Field(min_length=1,max_length=80)
    occurred_at:float=Field(gt=0)
    context:Context=Field(default_factory=Context)
    history_mode:Literal['unknown','first_time','recorded']='unknown'
    sets:list[Observation]=Field(min_length=1,max_length=20)
    enjoyment:int|None=Field(default=None,ge=1,le=5)
    duration_minutes:int|None=Field(default=None,ge=1,le=300)
    @model_validator(mode='after')
    def not_future(self):
        if self.occurred_at>time.time()+300:raise ValueError('Workout time cannot be in the future')
        return self

def previous(c,user,data):
    if data.history_mode=='unknown':return None
    # Use only already reviewed, earlier contributions; never today's or future outcomes.
    rows=c.execute(select(db.contributions).where(db.contributions.c.user_id==user,db.contributions.c.exercise_id==data.exercise_id,db.contributions.c.session_id!=data.session_id,db.contributions.c.occurred_at<data.occurred_at,db.contributions.c.status=='reviewed').order_by(db.contributions.c.occurred_at)).mappings()
    sessions=[]
    for r in rows:
        sets=[s for s in r['data']['sets'] if not s['skipped'] and s['pain'] is False and s['rpe'] is not None]
        if sets:sessions.append({'load':sets[-1]['load_kg'],'rpe':sum(s['rpe'] for s in sets)/len(sets)})
    if data.history_mode=='first_time':return {'count':0,'load':0,'rpe':None} if not sessions else None
    return {**sessions[-1],'count':min(len(sessions),1000)} if sessions else None

def assess(c,user,data,source_id,history=None):
    metadata=c.execute(select(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id==data.exercise_id)).mappings().first()
    pattern=metadata['data'].get('pattern') if metadata else None
    reasons=[];records=[]
    context=data.context.model_dump()
    if any(v is None for v in context.values()):reasons.append('missing_pre_workout_context')
    if not metadata or metadata['status']!='approved' or pattern not in PATTERNS or not metadata['data'].get('safety_reviewed'):reasons.append('exercise_metadata_needs_review')
    if history is None:reasons.append('previous_exercise_history_unknown')
    for i,s in enumerate(data.sets,1):
        why=list(reasons)
        if s.pain is not False:why.append('pain_reported_or_unknown')
        if s.skipped:why.append('set_skipped')
        if s.rpe is None:why.append('effort_not_recorded')
        if any(v is None for v in (s.planned_reps,s.planned_load_kg,s.target_rpe)):why.append('original_prescription_unknown')
        elif s.reps!=s.planned_reps or abs(s.load_kg-s.planned_load_kg)>.01:why.append('actual_differs_from_prescription')
        if not why:
            records.append(TrainingRecord(event_id=f'guided_{source_id}_{i}',session_id=data.session_id,exercise_id=data.exercise_id,occurred_at=data.occurred_at,
                features={**context,'pattern':pattern,'reps':s.planned_reps,'load_kg':s.planned_load_kg,'target_rpe':s.target_rpe,'set_number':i,
                    'previous_load_kg':history['load'],'previous_rpe':history['rpe'] if history['rpe'] is not None else s.target_rpe,'history_sessions':history['count']},
                actual_reps=s.reps,actual_load_kg=s.load_kg,actual_rpe=s.rpe))
        reasons_for_set={'set':i,'ready_for_review':not why,'reasons':list(dict.fromkeys(why))}
        yield reasons_for_set,records[-1] if not why else None

def report(c,user,data,source_id,history):
    pairs=list(assess(c,user,data,source_id,history))
    return {'sets_recorded':len(data.sets),'potential_training_sets':sum(record is not None for _,record in pairs),'sets':[r for r,_ in pairs],
            'message':'Saved as reported. Complete matching sets can enter training after operator review; missing answers were not guessed.'},[r for _,r in pairs if r]

def submit(c,user,data):
    c.execute(select(db.users.c.id).where(db.users.c.id==user).with_for_update())
    g=learning.grant(c,user)
    if not g or not g['enabled']:raise ValueError('Enable voluntary shared-learning participation before sending a contribution')
    hashed=learning.digest(data.model_dump())
    old=c.execute(select(db.contributions).where(db.contributions.c.user_id==user,db.contributions.c.event_id==data.event_id)).mappings().first()
    if old:
        if old['payload_hash']!=hashed:raise ValueError('Submission ID reused with changed answers')
        return {'id':old['id'],'duplicate':True,'report':old['report']}
    if c.execute(select(db.exercises.c.id).where(db.exercises.c.id==data.exercise_id)).scalar_one_or_none() is None:raise ValueError('Select an exercise from the library')
    if c.execute(select(db.contributions.c.id).where(db.contributions.c.user_id==user,db.contributions.c.session_id==data.session_id,db.contributions.c.exercise_id==data.exercise_id)).scalar_one_or_none():raise ValueError('This exercise is already saved in this workout')
    ident=db.uid();history=previous(c,user,data);summary,_=report(c,user,data,ident,history)
    c.execute(insert(db.contributions).values(id=ident,user_id=user,event_id=data.event_id,session_id=data.session_id,exercise_id=data.exercise_id,occurred_at=data.occurred_at,
        grant_token=g['grant_token'],payload_hash=hashed,status='pending',data=data.model_dump(),history_snapshot=history,report=summary,review={}))
    return {'id':ident,'duplicate':False,'report':summary}

def review(c,ident,reviewer,evidence):
    if not reviewer.strip() or not evidence.strip():raise ValueError('Reviewer and source evidence are required')
    row=c.execute(select(db.contributions).where(db.contributions.c.id==ident)).mappings().first()
    if not row:raise ValueError('Contribution not found')
    c.execute(select(db.users.c.id).where(db.users.c.id==row['user_id']).with_for_update())
    row=c.execute(select(db.contributions).where(db.contributions.c.id==ident).with_for_update()).mappings().first()
    if not row:raise ValueError('Contribution was withdrawn')
    g=learning.grant(c,row['user_id'])
    if not g or not g['enabled'] or g['grant_token']!=row['grant_token']:raise ValueError('Consent is no longer valid')
    data=Contribution.model_validate(row['data']);summary,records=report(c,row['user_id'],data,row['id'],row['history_snapshot'])
    added=sum(learning.add_record(c,row['user_id'],r,'guided','approved') for r in records)
    audit={'reviewer':reviewer,'evidence':evidence,'reviewed_at':time.time()}
    c.execute(update(db.contributions).where(db.contributions.c.id==ident).values(status='reviewed',report=summary,review=audit))
    for r in records:c.execute(update(db.learning_examples).where(db.learning_examples.c.user_id==row['user_id'],db.learning_examples.c.event_id==r.event_id).values(review=audit))
    return {'added':added,'duplicate':row['status']=='reviewed' and added==0,'report':summary}
