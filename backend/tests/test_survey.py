import copy,hashlib,hmac,json,time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,insert,func,update
from fitness import db,learning,survey,survey_worker
from fitness.api import create_app
from test_system import system,workout

@pytest.fixture
def bridge(system,monkeypatch):
    monkeypatch.setenv('SURVEY_FORM_ID','test-form-id');monkeypatch.setenv('SURVEY_WEBHOOK_SECRET','a-test-secret-with-at-least-thirty-two-chars')
    workout(system)
    return system

def signed(c,path,payload,nonce=None,stamp=None,secret='a-test-secret-with-at-least-thirty-two-chars'):
    raw=json.dumps(payload,separators=(',',':')).encode();stamp=str(int(time.time()) if stamp is None else stamp);nonce=nonce or db.uid()
    text='\n'.join(['POST',path,'test-form-id',stamp,nonce,hashlib.sha256(raw).hexdigest()])
    headers={'X-Fitness-Form':'test-form-id','X-Fitness-Timestamp':stamp,'X-Fitness-Nonce':nonce,'X-Fitness-Signature':hmac.new(secret.encode(),text.encode(),hashlib.sha256).hexdigest(),'Content-Type':'application/json'}
    return c.post(path,content=raw,headers=headers)

def enroll(c,code='a'*64):
    r=signed(c,'/api/v1/survey/enroll',{'participant_code':code});assert r.status_code==200,r.text
    return code

def event(code='a'*64,revision=1,response='response-one',session='survey_session_01',when=None,**extra):
    return {'response_id':response,'revision':revision,'operation':'upsert','participant_code':code,'adult':True,'consent':True,
        'contribution':{'event_id':'irrelevant_source_event_id','session_id':session,'exercise_id':'test:0','occurred_at':when or time.time()-3600,
            'context':{'experience':1,'sleep_hours':7,'energy':4,'soreness':1,'stress':1},'history_mode':'first_time',
            'sets':[{'reps':6,'load_kg':10,'rpe':7,'pain':False,'planned_reps':6,'planned_load_kg':10,'target_rpe':7}]},**extra}

def ingest(c,payload):
    r=signed(c,'/api/v1/survey/events',payload);assert r.status_code==200,r.text
    return r.json()

def survey_user(d,code='a'*64):
    with d.connect() as c:return c.execute(select(db.survey_participants.c.user_id).where(db.survey_participants.c.token_hash==survey.token_hash(code))).scalar_one()

def fake_model(d,user):
    with d.begin() as c:
        ident=db.uid();g=learning.grant(c,user)
        c.execute(insert(db.learning_models).values(id=ident,status='passed',artifact={'test':'NOT REAL WEIGHTS'},report={},dataset_hash=db.uid(),review={}))
        c.execute(insert(db.learning_members).values(user_id=user,model_id=ident,grant_token=g['grant_token']))
        c.execute(insert(db.learning_deployment).values(id='global',model_id=ident,mode='shadow'))
    return ident

def test_signature_replay_and_disabled(bridge,monkeypatch):
    c,d,h=bridge
    assert c.post('/api/v1/survey/enroll',json={'participant_code':'a'*64}).status_code==401
    assert signed(c,'/api/v1/survey/status',{},secret='wrong').status_code==401
    assert signed(c,'/api/v1/survey/status',{},stamp=int(time.time())-600).status_code==401
    n=db.uid();assert signed(c,'/api/v1/survey/status',{},nonce=n).status_code==200
    assert signed(c,'/api/v1/survey/status',{},nonce=n).status_code==409
    monkeypatch.delenv('SURVEY_WEBHOOK_SECRET')
    assert signed(c,'/api/v1/survey/status',{}).status_code==503

def test_enroll_is_idempotent_and_not_opt_in(bridge):
    c,d,h=bridge;enroll(c);enroll(c)
    with d.connect() as con:
        assert con.execute(select(func.count()).select_from(db.survey_participants)).scalar_one()==1
        assert not learning.grant(con,survey_user(d))
        assert con.execute(select(db.survey_participants.c.token_hash)).scalar_one()!='a'*64

def test_ingest_duplicate_versions_and_worker(bridge):
    c,d,h=bridge;enroll(c);e=event();assert ingest(c,e)['status']=='active';assert ingest(c,e)['status']=='duplicate'
    with d.connect() as con:assert con.execute(select(func.count()).select_from(db.contributions)).scalar_one()==1
    result=survey_worker.cycle(d);assert result['validated_submissions']==1 and result['status']=='waiting_for_data'
    with d.connect() as con:assert len(learning.eligible(con))==1
    assert survey_worker.cycle(d)['validated_submissions']==0
    changed=copy.deepcopy(e);changed['contribution']['sets'][0]['rpe']=8
    assert signed(c,'/api/v1/survey/events',changed).status_code==409
    changed['revision']=2;assert ingest(c,changed)['status']=='active'
    assert ingest(c,e)['status']=='stale'
    survey_worker.cycle(d)
    with d.connect() as con:assert [x['actual_rpe'] for x in learning.eligible(con)]==[8]

def test_edit_retires_models_and_rebuilds_history(bridge):
    c,d,h=bridge;enroll(c);one=event(when=time.time()-20000);ingest(c,one);survey_worker.cycle(d)
    two=event(response='two',session='survey_session_02',when=time.time()-10000);two['contribution']['history_mode']='recorded';ingest(c,two);survey_worker.cycle(d)
    user=survey_user(d);ident=fake_model(d,user)
    revised=copy.deepcopy(one);revised['revision']=2;revised['contribution']['sets'][0]['rpe']=5;ingest(c,revised)
    with d.connect() as con:
        assert con.execute(select(db.learning_models.c.artifact).where(db.learning_models.c.id==ident)).scalar_one()=={}
        assert not learning.eligible(con)
    survey_worker.cycle(d)
    with d.connect() as con:
        later=[r for r in learning.eligible(con) if r['session_id']=='survey_session_02'][0]
        assert later['features']['previous_rpe']==5

def test_new_outcome_preserves_prior_models(bridge):
    c,d,h=bridge;enroll(c);ingest(c,event(when=time.time()-20000));survey_worker.cycle(d);ident=fake_model(d,survey_user(d))
    e=event(response='two',session='survey_session_02',when=time.time()-10000);e['contribution']['history_mode']='recorded';ingest(c,e)
    with d.connect() as con:assert con.execute(select(db.learning_models.c.status).where(db.learning_models.c.id==ident)).scalar_one()=='passed'

def test_delete_and_withdraw_cannot_resurrect(bridge):
    c,d,h=bridge;enroll(c);e=event();ingest(c,e);survey_worker.cycle(d)
    assert ingest(c,{'response_id':'response-one','revision':2,'operation':'delete'})['status']=='deleted'
    assert ingest(c,e)['status']=='stale'
    with d.connect() as con:assert not learning.eligible(con)
    e['revision']=3;ingest(c,e);survey_worker.cycle(d);ident=fake_model(d,survey_user(d))
    assert ingest(c,{'response_id':'withdrawal','revision':1,'operation':'withdraw','participant_code':'a'*64})['status']=='withdrawn'
    e['revision']=4;assert ingest(c,e)['status']=='withdrawn'
    with d.connect() as con:
        assert con.execute(select(func.count()).select_from(db.contributions)).scalar_one()==0
        assert con.execute(select(db.learning_models.c.artifact).where(db.learning_models.c.id==ident)).scalar_one()=={}
        assert not learning.grant(con,survey_user(d))['enabled']

@pytest.mark.parametrize('field,value',[('pain',True),('rpe',None),('planned_reps',None)])
def test_incomplete_or_pain_data_not_trained(bridge,field,value):
    c,d,h=bridge;enroll(c);e=event();e['contribution']['sets'][0][field]=value;ingest(c,e);survey_worker.cycle(d)
    with d.connect() as con:assert not learning.eligible(con)

def test_unreviewed_metadata_not_auto_approved(bridge):
    c,d,h=bridge;enroll(c)
    with d.begin() as con:con.execute(update(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id=='test:0').values(status='needs_review'))
    ingest(c,event());survey_worker.cycle(d)
    with d.connect() as con:
        assert not learning.eligible(con)
        assert con.execute(select(db.exercise_metadata.c.status).where(db.exercise_metadata.c.exercise_id=='test:0')).scalar_one()=='needs_review'

def test_other_participant_cannot_take_response(bridge):
    c,d,h=bridge;enroll(c);enroll(c,'b'*64);e=event();ingest(c,e);e['revision']=2;e['participant_code']='b'*64
    assert signed(c,'/api/v1/survey/events',e).status_code==409

def test_consent_edit_retires_and_clears(bridge):
    c,d,h=bridge;enroll(c);e=event();ingest(c,e);e['revision']=2;e['consent']=False;ingest(c,e)
    with d.connect() as con:assert not con.execute(select(db.contributions)).first()

def test_worker_rechecks_catalog_review_changes(bridge):
    c,d,h=bridge;enroll(c)
    with d.begin() as con:con.execute(update(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id=='test:0').values(status='needs_review'))
    ingest(c,event());survey_worker.cycle(d)
    with d.begin() as con:
        assert not learning.eligible(con)
        con.execute(update(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id=='test:0').values(status='approved'))
    survey_worker.cycle(d)
    with d.begin() as con:
        assert len(learning.eligible(con))==1
        con.execute(update(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id=='test:0').values(status='needs_review'))
    survey_worker.cycle(d)
    with d.connect() as con:assert not learning.eligible(con)

def test_survey_to_real_trained_weights_end_to_end(bridge):
    c,d,h=bridge;enroll(c);now=time.time()
    for i in range(10):
        e=event(response='training-'+str(i),session='survey_training_'+str(i),when=now-(11-i)*86400)
        e['contribution']['history_mode']='first_time' if i==0 else 'recorded'
        e['contribution']['sets']=[copy.deepcopy(e['contribution']['sets'][0]) for _ in range(3)]
        ingest(c,e)
    result=survey_worker.cycle(d)
    assert result['status']=='experimental' and result['rows']==30
    with d.connect() as con:
        artifact=con.execute(select(db.learning_models.c.artifact).where(db.learning_models.c.id==result['model_id'])).scalar_one()
        assert len(artifact['weights'])==6
        assert not learning.active(con)
    assert survey_worker.cycle(d)['status']=='unchanged_data'

@pytest.mark.parametrize('mode,promoted',[('live',False),('shadow',True)])
def test_automatic_promotion_is_shadow_only(bridge,monkeypatch,mode,promoted):
    c,d,h=bridge;calls=[]
    monkeypatch.setattr(learning,'train',lambda database:{'status':'passed','model_id':'candidate'})
    monkeypatch.setattr(learning,'active',lambda connection:{'id':'prior','mode':mode})
    monkeypatch.setattr(learning,'deploy',lambda connection,ident,choice,reviewer,evidence:calls.append((ident,choice)))
    survey_worker.cycle(d)
    assert calls==([('candidate','shadow')] if promoted else [])
