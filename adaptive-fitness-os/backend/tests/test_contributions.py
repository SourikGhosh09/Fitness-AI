import time
import pytest
from sqlalchemy import select,func,update
from fitness import db,learning,contributions
from fitness.collect import summary
from test_system import system,workout,payload

def body(**kw):
    return {'event_id':'guided_event_00000001','session_id':'real_session_0001','exercise_id':'test:0','occurred_at':1700000000.,'sets':[{'reps':8,'load_kg':20}],**kw}

def full(**kw):
    return body(context={'experience':1,'sleep_hours':7,'energy':3,'soreness':1,'stress':1},history_mode='first_time',sets=[{'reps':8,'load_kg':20,'rpe':7,'pain':False,'planned_reps':8,'planned_load_kg':20,'target_rpe':7}],**kw)

def prepare(system):
    c,d,h=system;workout(system)
    s=c.put('/api/v1/learning/consent',headers=h,json={'enabled':True}).json()
    return c,d,h,s['account_id']

def test_partial_answers_saved_without_fabrication(system):
    c,d,h,u=prepare(system)
    r=c.post('/api/v1/contributions',headers=h,json=body());assert r.status_code==201,r.text
    assert r.json()['report']['potential_training_sets']==0
    assert 'original_prescription_unknown' in r.json()['report']['sets'][0]['reasons']
    with d.connect() as con:
        saved=con.execute(select(db.contributions.c.data)).scalar_one()
        assert saved['context']['sleep_hours'] is None
        assert saved['sets'][0]['rpe'] is None and saved['sets'][0]['pain'] is None
        assert not learning.eligible(con)
        assert summary(con)['contributors']==1
    assert c.get('/api/v1/learning/status',headers=h).json()['pending_contributions']==1

def test_review_translates_only_complete_records(system):
    c,d,h,u=prepare(system);r=c.post('/api/v1/contributions',headers=h,json=full()).json()
    assert r['report']['potential_training_sets']==1
    with d.begin() as con:
        assert not learning.eligible(con)
        result=contributions.review(con,r['id'],'Test reviewer','Checked original workout record')
        assert result['added']==1
        assert contributions.review(con,r['id'],'Reviewer','Same source')['duplicate']
        example=learning.eligible(con)[0]
        assert example['features']['load_kg']==20 and example['actual_rpe']==7
        assert example['features']['history_sessions']==0
        assert example['exercise_id']=='test:0'
    c.put('/api/v1/learning/consent',headers=h,json={'enabled':False})
    with d.connect() as con:
        assert con.execute(select(func.count()).select_from(db.contributions)).scalar_one()==0
        assert not learning.eligible(con)

@pytest.mark.parametrize('change,reason',[({'pain':True},'pain_reported_or_unknown'),({'pain':None},'pain_reported_or_unknown'),({'rpe':None},'effort_not_recorded'),({'skipped':True},'set_skipped'),({'reps':6},'actual_differs_from_prescription')])
def test_excluded_feedback_stays_out_of_neural_labels(system,change,reason):
    c,d,h,u=prepare(system);data=full();data['sets'][0].update(change)
    r=c.post('/api/v1/contributions',headers=h,json=data).json()
    assert reason in r['report']['sets'][0]['reasons']
    with d.begin() as con:
        assert contributions.review(con,r['id'],'Reviewer','Source')['added']==0
        assert not learning.eligible(con)

def test_idempotency_ownership_and_consent(system):
    c,d,h=system;workout(system)
    assert c.post('/api/v1/contributions',headers=h,json=body()).status_code==409
    c.put('/api/v1/learning/consent',headers=h,json={'enabled':True})
    a=c.post('/api/v1/contributions',headers=h,json=body()).json()
    b=c.post('/api/v1/contributions',headers=h,json=body()).json();assert b['duplicate'] and b['id']==a['id']
    assert c.post('/api/v1/contributions',headers=h,json=body(enjoyment=4)).status_code==409
    assert c.post('/api/v1/contributions',headers=h,json=body(event_id='another_event_00001')).status_code==409
    key=c.post('/api/v1/api-keys',headers=h,json={'name':'read only','scopes':['read']}).json()['key']
    assert c.post('/api/v1/contributions',headers={'Authorization':'Bearer '+key},json=body()).status_code==403
    other=c.post('/api/v1/auth/register',json={'email':'othercontributor@example.com','password':'another-long-password'}).json()['key']
    assert c.get('/api/v1/contributions',headers={'Authorization':'Bearer '+other}).json()==[]
    assert c.post('/api/v1/contributions',headers=h,json={**body(),'user_id':'someone_else'}).status_code==422
    assert c.post('/api/v1/contributions',headers=h,json=body(occurred_at=time.time()+9999)).status_code==422
    assert c.get('/api/v1/contributions?limit=1000',headers=h).status_code==422

def test_history_snapshot_ignores_later_records(system):
    c,d,h,u=prepare(system)
    old=c.post('/api/v1/contributions',headers=h,json=full()).json()
    with d.begin() as con:contributions.review(con,old['id'],'Reviewer','Source')
    later=full(event_id='guided_event_00000002',session_id='real_session_0002',occurred_at=1700100000.)
    later['history_mode']='recorded'
    r=c.post('/api/v1/contributions',headers=h,json=later).json()
    with d.begin() as con:
        contributions.review(con,r['id'],'Reviewer','Source')
        saved=con.execute(select(db.contributions.c.history_snapshot).where(db.contributions.c.id==r['id'])).scalar_one()
        assert saved=={'load':20,'rpe':7,'count':1}
    backfill=full(event_id='guided_event_00000003',session_id='real_session_0003',occurred_at=1600000000.)
    backfill['history_mode']='recorded'
    r=c.post('/api/v1/contributions',headers=h,json=backfill).json()
    assert 'previous_exercise_history_unknown' in r['report']['sets'][0]['reasons']

def test_unknown_metadata_cannot_be_used_by_review(system):
    c,d,h,u=prepare(system)
    with d.begin() as con:con.execute(update(db.exercise_metadata).values(status='needs_review'))
    r=c.post('/api/v1/contributions',headers=h,json=full()).json()
    with d.begin() as con:assert contributions.review(con,r['id'],'Reviewer','Source')['added']==0
    with d.begin() as con:
        con.execute(update(db.exercise_metadata).values(status='approved'))
        assert contributions.review(con,r['id'],'Reviewer','Metadata has now been reviewed')['added']==1
        assert contributions.review(con,r['id'],'Reviewer','Retry')['added']==0

def test_skipped_workout_has_no_fake_effort(system):
    c,d,h=system;w=workout(system)
    for i,item in enumerate(w['items']):
        for n in range(1,item['sets']+1):
            r=c.post('/api/v1/sets',headers=h,json=payload(w,exercise_id=item['exercise_id'],set_number=n,event_id=f'skip_guided_event_{i}_{n}',rpe=None,skipped=True,reps=0,load_kg=0))
            assert r.status_code==201,r.text
    assert c.post('/api/v1/workouts/'+w['id']+'/complete',headers=h).status_code==200
    history=c.get('/api/v1/progress',headers=h).json()['exercise_history']
    assert all(e['last_load'] is None and e['sessions'][0]['rpe'] is None for e in history.values())
