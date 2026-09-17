"""HMAC-authenticated, revision-aware Google Forms bridge. No model writes in HTTP."""
import hashlib,hmac,json,os,re,secrets,time
from typing import Literal
from pydantic import Field,ValidationError
from fastapi import HTTPException
from sqlalchemy import select,insert,update,delete
from sqlalchemy.exc import IntegrityError
from . import db,learning,contributions,security
from .contracts import Contract

class Enrollment(Contract):
    participant_code:str=Field(pattern=r'^[A-Za-z0-9_-]{32,100}$')

class SurveyEvent(Contract):
    response_id:str=Field(min_length=1,max_length=200)
    revision:int=Field(ge=1,le=100000000)
    operation:Literal['upsert','delete','withdraw']='upsert'
    participant_code:str|None=Field(default=None,pattern=r'^[A-Za-z0-9_-]{32,100}$')
    adult:bool=False
    consent:bool=False
    contribution:contributions.Contribution|None=None

def token_hash(token):return hashlib.sha256(token.encode()).hexdigest()

def authorize(c,path,raw,headers):
    secret=os.getenv('SURVEY_WEBHOOK_SECRET','');form_id=os.getenv('SURVEY_FORM_ID','')
    if len(secret)<32 or not form_id:raise HTTPException(503,'Survey bridge is not configured')
    stamp=headers.get('x-fitness-timestamp','');nonce=headers.get('x-fitness-nonce','');signature=headers.get('x-fitness-signature','')
    if not re.fullmatch(r'[0-9]{10}',stamp) or abs(time.time()-int(stamp))>300 or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',nonce):raise HTTPException(401,'Invalid survey signature')
    if headers.get('x-fitness-form')!=form_id:raise HTTPException(401,'Invalid survey form')
    message='\n'.join(['POST',path,form_id,stamp,nonce,hashlib.sha256(raw).hexdigest()])
    expected=hmac.new(secret.encode(),message.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature):raise HTTPException(401,'Invalid survey signature')
    c.execute(delete(db.survey_receipts).where(db.survey_receipts.c.expires_at<time.time()))
    if c.execute(select(db.survey_receipts.c.id).where(db.survey_receipts.c.id==nonce)).first():raise HTTPException(409,'Survey request already received; retry with a fresh nonce')
    c.execute(insert(db.survey_receipts).values(id=nonce,expires_at=time.time()+600))

def enroll(c,data):
    hashed=token_hash(data.participant_code)
    row=c.execute(select(db.survey_participants).where(db.survey_participants.c.token_hash==hashed)).mappings().first()
    if row:return {'status':'revoked' if row['revoked'] else 'ready','duplicate':True}
    user=db.uid()
    # A survey identity has no usable login password and contains no supplied email.
    c.execute(insert(db.users).values(id=user,email=user+'@survey.invalid',password_hash=security.passwords.hash(secrets.token_urlsafe(48))))
    c.execute(insert(db.survey_participants).values(user_id=user,token_hash=hashed,revoked=False))
    return {'status':'ready','duplicate':False}

def reset_derived(c,user):
    learning.invalidate_models(c,user,'Survey answers or exercise metadata changed; affected training examples must be rebuilt.')
    c.execute(delete(db.learning_examples).where(db.learning_examples.c.user_id==user))
    # Corrections may affect downstream history. Recompute it chronologically.
    c.execute(update(db.contributions).where(db.contributions.c.user_id==user).values(status='pending',history_snapshot=None,review={}))

def receive(c,event):
    key=token_hash(os.environ['SURVEY_FORM_ID']+':'+event.response_id)
    previous=c.execute(select(db.survey_responses).where(db.survey_responses.c.response_key==key)).mappings().first()
    if event.operation=='delete':
        if not previous:return {'status':'absent'}
        user=previous['user_id']
    else:
        if not event.participant_code:raise ValueError('Open your private participant link')
        participant=c.execute(select(db.survey_participants).where(db.survey_participants.c.token_hash==token_hash(event.participant_code))).mappings().first()
        if not participant:raise ValueError('Participant link is not enrolled')
        user=participant['user_id']
        if previous and previous['user_id']!=user:raise ValueError('A response cannot change participant')
    c.execute(select(db.users.c.id).where(db.users.c.id==user).with_for_update())
    previous=c.execute(select(db.survey_responses).where(db.survey_responses.c.response_key==key).with_for_update()).mappings().first()
    hashed=learning.digest(event.model_dump())
    if previous:
        if event.revision<previous['revision']:return {'status':'stale'}
        if event.revision==previous['revision']:
            if hashed!=previous['payload_hash']:raise ValueError('Revision has different content')
            return {'status':'duplicate'}
    if event.operation!='delete':
        participant=c.execute(select(db.survey_participants).where(db.survey_participants.c.user_id==user)).mappings().one()
        if participant['revoked']:return {'status':'withdrawn'}
    # Explicit withdrawal, or changing consent/adult eligibility to false, erases
    # backend training records and invalidates every influenced model immediately.
    withdrawn=event.operation=='withdraw' or (event.operation=='upsert' and (not event.consent or not event.adult))
    contribution_id=None;status='deleted'
    if withdrawn:
        learning.set_consent(c,user,False)
        c.execute(update(db.survey_participants).where(db.survey_participants.c.user_id==user).values(revoked=True))
        c.execute(update(db.survey_responses).where(db.survey_responses.c.user_id==user).values(status='withdrawn'))
        status='withdrawn'
    else:
        if event.operation=='upsert':
            if event.contribution is None:raise ValueError('Workout answers are missing')
            if event.contribution.occurred_at>time.time()+300:raise ValueError('Future workout time')
        if previous:
            reset_derived(c,user)
            if previous['contribution_id']:c.execute(delete(db.contributions).where(db.contributions.c.id==previous['contribution_id']))
        if event.operation=='upsert':
            # Survey consent is a distinct recorded action, not inferred from a visit.
            learning.set_consent(c,user,True)
            payload=event.contribution.model_copy(update={'event_id':'survey_'+key[:40]})
            result=contributions.submit(c,user,payload);contribution_id=result['id'];status='active'
            # Ordinary new outcomes do not invalidate a model trained on earlier
            # data. Backdated outcomes can alter downstream history and must.
            later=c.execute(select(db.contributions.c.id).where(db.contributions.c.user_id==user,db.contributions.c.occurred_at>payload.occurred_at)).first()
            if later and not previous:reset_derived(c,user)
    values={'user_id':user,'response_key':key,'revision':event.revision,'payload_hash':hashed,'contribution_id':contribution_id,'status':status}
    if previous:c.execute(update(db.survey_responses).where(db.survey_responses.c.id==previous['id']).values(**values))
    else:c.execute(insert(db.survey_responses).values(**values))
    return {'status':status,'training':'queued_for_validation' if status=='active' else 'affected_models_retired'}

def catalog(c):
    # Catalog choices are references, never an automatically prescribed workout.
    return [{'id':r['id'],'name':r['name']} for r in c.execute(select(db.exercises.c.id,db.exercises.c.name).order_by(db.exercises.c.name)).mappings()]

async def endpoint(request,database,action):
    raw=b''
    async for chunk in request.stream():
        raw+=chunk
        if len(raw)>65536:raise HTTPException(413,'Survey payload too large')
    try:
        with database.begin() as c:
            authorize(c,request.url.path,raw,request.headers)
            data=json.loads(raw)
            if action=='enroll':return enroll(c,Enrollment.model_validate(data))
            if action=='catalog':return {'exercises':catalog(c)}
            if action=='status':
                latest=c.execute(select(db.learning_models.c.id,db.learning_models.c.status).order_by(db.learning_models.c.created_at.desc())).mappings().first()
                return {'latest_candidate':dict(latest) if latest else None,'eligible_sets':len(learning.eligible(c)),'mode':(learning.active(c) or {}).get('mode','rules')}
            return receive(c,SurveyEvent.model_validate(data))
    except ValidationError:raise HTTPException(422,'Survey answers did not match the form schema; check required fields and numeric ranges')
    except (ValueError,TypeError,IntegrityError):raise HTTPException(409,'Survey update could not be applied; check participant link, response revision and workout answers')
