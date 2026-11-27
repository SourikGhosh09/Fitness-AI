import csv,json,time,zipfile
import numpy as np
import pytest
from sqlalchemy import insert,select,update,func
from fitness import db,learning,neural
from fitness.learning_contracts import TrainingRecord,Features
from fitness.ml import import_csv,review_imports,COLUMNS
from fitness.backup import backup,restore
from test_system import system,workout,payload

def features(**kw):
    return {'experience':1,'sleep_hours':7,'energy':3,'soreness':1,'stress':1,'reps':6,'load_kg':0,'target_rpe':7,'set_number':1,'previous_load_kg':0,'previous_rpe':7,'history_sessions':0,'pattern':'squat',**kw}

def record(**kw):
    return {'event_id':'import_event_0000001','session_id':'import_session_001','exercise_id':'test:0','occurred_at':1700000000.,'features':features(),'actual_rpe':6.,'actual_reps':6,'actual_load_kg':0.,'pain':False,'skipped':False,**kw}

def test_real_backprop_gradient_and_learning():
    rng=np.random.default_rng(12)
    weights=[rng.normal(0,.1,s) for s in neural.SHAPES]
    x=rng.normal(0,1,(7,neural.N_INPUT));y=rng.normal(0,.2,(7,1))
    gradients=neural.gradients(x,y,weights)
    for w,g in zip(weights,gradients):
        ix=tuple(0 for _ in w.shape);old=w[ix];eps=1e-6
        w[ix]=old+eps;a=np.mean((neural.forward(x,weights)[0]-y)**2)
        w[ix]=old-eps;b=np.mean((neural.forward(x,weights)[0]-y)**2);w[ix]=old
        assert g[ix]==pytest.approx((a-b)/(2*eps),rel=1e-4,abs=1e-6)
    rows=[]
    for n in range(180):
        f=features(reps=4+n%12,energy=1+n%5,load_kg=10+n%20)
        rows.append(record(features=f,actual_rpe=3+f['reps']*.2+f['energy']*.4,actual_reps=f['reps'],actual_load_kg=f['load_kg']))
    model=neural.fit(rows[:120],rows[120:150])
    error=np.mean([abs(neural.predict(model,r['features'],False)-r['actual_rpe']) for r in rows[150:]])
    assert error<.5
    assert model['epochs']>1
    assert neural.predict(model,features(load_kg=600)) is None
    model['weights'][0][0][0]=float('nan')
    with pytest.raises(ValueError):neural.predict(model,features())

def complete(c,h,w):
    for i,e in enumerate(w['items']):
        for n in range(1,e['sets']+1):
            p=payload(w,exercise_id=e['exercise_id'],set_number=n,event_id=f'learning_set_{i}_{n}_event',reps=e['reps'])
            assert c.post('/api/v1/sets',headers=h,json=p).status_code==201
    r=c.post('/api/v1/workouts/'+w['id']+'/complete',headers=h)
    assert r.status_code==200,r.text
    return r.json()

def test_opt_in_completed_collection_and_duplicates(system):
    c,d,h=system
    assert c.get('/api/v1/learning/status',headers=h).json()['consent'] is False
    c.put('/api/v1/learning/consent',headers=h,json={'enabled':True})
    w=workout(system)
    count=complete(c,h,w)['learning_examples_collected']
    assert count==sum(i['sets'] for i in w['items'])
    assert c.post('/api/v1/workouts/'+w['id']+'/complete',headers=h).json()['duplicate']
    s=c.get('/api/v1/learning/status',headers=h).json()
    assert s['eligible_examples']==count and s['mode']=='rules'
    assert c.put('/api/v1/learning/consent',headers=h,json={'enabled':False}).json()['eligible_examples']==0
    c.put('/api/v1/learning/consent',headers=h,json={'enabled':True})
    assert c.get('/api/v1/learning/status',headers=h).json()['eligible_examples']==0

def test_no_retroactive_collection(system):
    c,d,h=system;w=workout(system)
    c.put('/api/v1/learning/consent',headers=h,json={'enabled':True})
    assert complete(c,h,w)['learning_examples_collected']==0

def test_import_consent_isolation_validation_review(system,tmp_path):
    c,d,h=system;workout(system);r=record()
    assert c.post('/api/v1/learning/examples',headers=h,json={'records':[r]}).status_code==409
    c.put('/api/v1/learning/consent',headers=h,json={'enabled':True})
    result=c.post('/api/v1/learning/examples',headers=h,json={'records':[r]})
    assert result.status_code==201 and result.json()['added']==1
    assert c.post('/api/v1/learning/examples',headers=h,json={'records':[r]}).json()['duplicates']==1
    assert c.post('/api/v1/learning/examples',headers=h,json={'records':[{**r,'actual_rpe':9}]}).status_code==409
    for bad in ({'actual_rpe':float('inf')},{'actual_reps':7},{'pain':True},{'occurred_at':time.time()+10000}):
        with pytest.raises(ValueError):TrainingRecord.model_validate({**r,**bad})
    # Whole batch rolls back when one exercise is unknown.
    batch=[{**r,'event_id':'import_event_0000002'},{**r,'event_id':'import_event_0000003','exercise_id':'unknown'}]
    assert c.post('/api/v1/learning/examples',headers=h,json={'records':batch}).status_code==409
    s=c.get('/api/v1/learning/status',headers=h).json();assert s['pending_review']==1
    with d.connect() as con:assert not learning.eligible(con)
    assert review_imports(d,s['account_id'],'test reviewer','source record verified')['approved']==1
    with d.connect() as con:assert len(learning.eligible(con))==1
    key=c.post('/api/v1/api-keys',headers=h,json={'name':'read','scopes':['read']}).json()['key'];kh={'Authorization':'Bearer '+key}
    assert c.put('/api/v1/learning/consent',headers=kh,json={'enabled':False}).status_code==403
    assert c.post('/api/v1/learning/examples',headers=kh,json={'records':[r]}).status_code==403
    t=c.post('/api/v1/auth/register',json={'email':'other@example.com','password':'another-long-password'}).json()['key']
    assert c.get('/api/v1/learning/status',headers={'Authorization':'Bearer '+t}).json()['eligible_examples']==0

def seed_learning(database):
    with database.begin() as c:
        c.execute(insert(db.exercises).values(id='test:0',name='Synthetic only',source='TEST',source_commit='test',source_hash='test',data={}))
        for user in range(24):
            uid=f'synthetic-user-{user:02}'
            c.execute(insert(db.users).values(id=uid,email=f'{uid}@invalid.test',password_hash='TEST'))
            learning.set_consent(c,uid,True)
            for session in range(10):
                for s in range(1,4):
                    f=features(experience=user%6,reps=4+(session+user)%12,energy=1+(session*2+user)%5,set_number=s,load_kg=10+(user+session)%20,previous_load_kg=10+(user+session)%20,history_sessions=session,previous_rpe=6)
                    r=record(event_id=f'synthetic_event_{user}_{session}_{s}',session_id=f'synthetic_session_{user}_{session}',occurred_at=1700000000.+session*86400+user*10+s,features=f,actual_reps=f['reps'],actual_load_kg=f['load_kg'],actual_rpe=3+.2*f['reps']+.4*f['energy']+.1*s)
                    learning.add_record(c,uid,r,'app','approved')

def test_train_deploy_withdraw_and_backup(tmp_path):
    path=tmp_path/'training.db';d=db.make_engine('sqlite:///'+str(path));db.metadata.create_all(d);seed_learning(d)
    result=learning.train(d)
    assert result['status']=='passed',result
    assert result['metrics']['test']['mae']<.5
    assert result['metrics']['future_sessions']['mae']<.5
    assert learning.train(d)['status']=='unchanged_data'
    with d.begin() as c:
        m=c.execute(select(db.learning_models).where(db.learning_models.c.id==result['model_id'])).mappings().one()
        parts=m['report']['split_sample_ids'];all_ids=[i for part in parts.values() for i in part]
        assert len(all_ids)==len(set(all_ids))==720
        learning.deploy(c,m['id'],'shadow','TEST ONLY','Synthetic integration test, never clinical evidence')
        assert learning.active(c)['mode']=='shadow'
        weights=m['artifact']['weights']
    archive=tmp_path/'backup.zip';backup(str(d.url),archive)
    restored=tmp_path/'restored.db';restore(archive,restored)
    restored_db=db.make_engine('sqlite:///'+str(restored))
    with restored_db.connect() as c:
        assert learning.active(c) is None
        assert c.execute(select(db.learning_models.c.artifact)).scalar_one()['weights']==weights
        assert not learning.eligible(c)
        assert c.execute(select(db.learning_models.c.status)).scalar_one()=='quarantined'
    with pytest.raises(ValueError):restore(archive,restored)
    with d.begin() as c:
        learning.set_consent(c,'synthetic-user-00',False)
        assert learning.active(c) is None
        assert c.execute(select(db.learning_models.c.artifact)).scalar_one()=={}
        with pytest.raises(ValueError):learning.deploy(c,m['id'],'live','TEST','cannot revive retired weights')
    d.dispose();restored_db.dispose()

def test_small_data_cannot_activate(tmp_path):
    d=db.make_engine('sqlite:///'+str(tmp_path/'small.db'));db.metadata.create_all(d)
    assert learning.train(d)['status']=='waiting_for_data'
    with d.begin() as c:
        with pytest.raises(ValueError):learning.deploy(c,'unknown','live','TEST','TEST')

def test_csv_roundtrip_and_transaction(system,tmp_path):
    c,d,h=system;workout(system);s=c.put('/api/v1/learning/consent',headers=h,json={'enabled':True}).json()
    row=record();flat={**{k:v for k,v in row.items() if k!='features'},**row['features'],'pain':'false','skipped':'false'}
    p=tmp_path/'records.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS);writer.writeheader();writer.writerow(flat)
    assert import_csv(d,p,s['account_id'])['added']==1
    assert import_csv(d,p,s['account_id'])['duplicates']==1
    assert c.get('/api/v1/learning/status',headers=h).json()['pending_review']==1

def test_backup_detects_tampering(tmp_path):
    d=db.make_engine('sqlite:///'+str(tmp_path/'b.db'));db.metadata.create_all(d)
    original=tmp_path/'backup.zip';backup(str(d.url),original)
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(original) as src,zipfile.ZipFile(bad,'w') as dst:
        dst.writestr('manifest.json',src.read('manifest.json'));dst.writestr('fitness.sqlite',b'bad bytes')
    with pytest.raises(ValueError):restore(bad,tmp_path/'invalid.db')
    assert not (tmp_path/'invalid.db').exists()

def test_live_adjustment_is_bounded_and_safety_runs_first(system,monkeypatch):
    from fitness.contracts import Profile,Readiness
    from fitness.engine import SafetyStop
    c,d,h=system;w=workout(system)
    p=Profile(display_name='Test',adult=True,goals={'strength':100})
    r=Readiness(sleep_hours=7,energy=3,soreness=1,stress=1)
    monkeypatch.setattr(learning,'active',lambda con:{'id':'TEST ONLY','mode':'live','artifact':{'exercise_ids':['test:0']}})
    monkeypatch.setattr(neural,'predict',lambda *args:10.)
    catalog=[{'id':'test:0','data':{'equipment':'barbell'}}]
    past={'test:0':{'last_load':40,'sessions':[{'rpe':7}]*3}}
    plan={'items':[{**w['items'][0],'load_kg':40,'reasoning':{}}]}
    with d.begin() as con:
        learning.annotate_plan(con,'unused-test',plan,p,r,past,catalog)
        assert plan['items'][0]['load_kg']==38
        assert plan['items'][0]['learning_input']['load_kg']==38
        assert plan['items'][0]['reasoning']['neural']['original_load_kg']==40
        learning.annotate_plan(con,'unused-test',plan,p,r,past,catalog)
        assert plan['items'][0]['load_kg']==38
        with pytest.raises(SafetyStop):learning.annotate_plan(con,'unused-test',plan,p,r.model_copy(update={'pain':True}),past,catalog)
        for predicted,session_count in [(3.,3),(10.,1)]:
            monkeypatch.setattr(neural,'predict',lambda *args:predicted)
            plan={'items':[{**w['items'][0],'load_kg':40,'reasoning':{}}]}
            past['test:0']['sessions']=[{'rpe':7}]*session_count
            learning.annotate_plan(con,'unused-test',plan,p,r,past,catalog)
            assert plan['items'][0]['load_kg']==40

def test_withdrawal_during_training_discards_candidate(tmp_path,monkeypatch):
    d=db.make_engine('sqlite:///'+str(tmp_path/'race.db'));db.metadata.create_all(d);seed_learning(d)
    real_fit=neural.fit
    def withdrawing_fit(*args,**kwargs):
        result=real_fit(*args,**kwargs)
        with d.begin() as c:learning.set_consent(c,'synthetic-user-00',False)
        return result
    monkeypatch.setattr(neural,'fit',withdrawing_fit)
    with pytest.raises(ValueError,match='changed|withdrawn'):learning.train(d)
    with d.connect() as c:assert c.execute(select(func.count()).select_from(db.learning_models)).scalar_one()==0
