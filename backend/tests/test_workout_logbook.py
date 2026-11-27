import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert,select
from fitness import db,logbook
from fitness.api import create_app
from test_system import system,workout  # noqa: F401

def sets(*rows,**kw):return [{'weight_kg':w,'reps':r,'rir':kw.get('rir'),'done':kw.get('done',True),'kind':kw.get('kind','reps')} for w,r in rows]
def body(version=0,**kw):
    data={'version':version,'title':'Push','status':'in_progress','started_at':1000.0,'exercises':[{'name':'Bench press','sets':sets((45,5),(45,5),(50,3),done=False)}]}
    data.update(kw);return data

def test_create_read_update_with_versioning(system):
    c,d,h=system
    assert c.get('/api/v1/logs/2026-10-26',headers=h).status_code==404
    r=c.put('/api/v1/logs/2026-10-26',headers=h,json=body());assert r.status_code==200,r.text
    assert r.json()['version']==1 and r.json()['date']=='2026-10-26'
    stale=c.put('/api/v1/logs/2026-10-26',headers=h,json=body(0));assert stale.status_code==409
    ok=c.put('/api/v1/logs/2026-10-26',headers=h,json=body(1,status='completed',ended_at=2800.0));assert ok.status_code==200 and ok.json()['version']==2
    got=c.get('/api/v1/logs/2026-10-26',headers=h).json();assert got['status']=='completed' and got['ended_at']==2800.0
    assert c.put('/api/v1/logs/2026-10-27',headers=h,json=body(3)).status_code==409

def test_validation_and_dates(system):
    c,d,h=system
    for bad in ['2026-13-01','26-10-2026','2026-1-5','tomorrow']:
        assert c.get('/api/v1/logs/'+bad,headers=h).status_code==422
    assert c.put('/api/v1/logs/2026-10-26',headers=h,json=body(ended_at=1.0)).status_code==422
    assert c.put('/api/v1/logs/2026-10-26',headers=h,json=body(unknown_field=1)).status_code==422
    assert c.put('/api/v1/logs/2026-10-26',headers=h,json={'exercises':[{'name':'X','sets':[{'reps':-1}]}]}).status_code==422
    assert c.put('/api/v1/logs/2026-10-26',headers=h,json={'exercises':[{'name':'X','exercise_id':'missing:1','sets':[]}]}).status_code==422

def test_week_range_summary_and_bounds(system):
    c,d,h=system
    c.put('/api/v1/logs/2026-10-26',headers=h,json=body(exercises=[{'name':'Bench','sets':sets((45,5),(45,5))+sets((50,3),done=False)}]))
    c.put('/api/v1/logs/2026-10-28',headers=h,json=body(title='Legs',exercises=[]))
    r=c.get('/api/v1/logs?start=2026-10-26&end=2026-11-01',headers=h).json()
    assert [x['date'] for x in r['logs']]==['2026-10-26','2026-10-28']
    first=r['logs'][0];assert first['sets_total']==3 and first['sets_done']==2 and first['volume_kg']==450
    assert c.get('/api/v1/logs?start=2026-10-26',headers=h).status_code==422
    assert c.get('/api/v1/logs?start=2026-11-01&end=2026-10-26',headers=h).status_code==422
    assert c.get('/api/v1/logs?start=2026-01-01&end=2026-12-31',headers=h).status_code==422
    assert c.get('/api/v1/logs',headers=h).status_code==200
    assert logbook.week_bounds('2026-10-28')==('2026-10-26','2026-11-01')

def test_previous_performance_and_timed_sets(system):
    c,d,h=system
    with d.begin() as con:
        con.execute(insert(db.exercises).values(id='test:plank',name='Plank',source='TEST ONLY',source_commit='test',source_hash='t',data={'equipment':'body weight','target':'core','secondary_muscles':[],'instruction_steps':{'en':['Hold']}}))
    ex=lambda s:[{'name':'Plank','exercise_id':'test:plank','sets':s}]
    c.put('/api/v1/logs/2026-10-26',headers=h,json=body(exercises=ex([{'kind':'seconds','weight_kg':7.5,'reps':30,'done':True}])))
    c.put('/api/v1/logs/2026-10-29',headers=h,json=body(exercises=ex([{'kind':'seconds','reps':None}])))
    got=c.get('/api/v1/logs/2026-10-29',headers=h).json()
    assert got['previous']['test:plank']=={'date':'2026-10-26','sets':[{'kind':'seconds','weight_kg':7.5,'reps':30}]}
    assert c.get('/api/v1/logs/2026-10-26',headers=h).json()['previous']=={}
    assert c.get('/api/v1/logs?start=2026-10-26&end=2026-10-31',headers=h).json()['logs'][0]['volume_kg']==0

def test_owner_isolation_and_scopes(system):
    c,d,h=system
    c.put('/api/v1/logs/2026-10-26',headers=h,json=body())
    other=c.post('/api/v1/auth/register',json={'email':'b@example.com','password':'another-secret-pass-42'}).json()['key']
    h2={'Authorization':'Bearer '+other}
    assert c.get('/api/v1/logs/2026-10-26',headers=h2).status_code==404
    assert c.delete('/api/v1/logs/2026-10-26',headers=h2).status_code==404
    assert c.get('/api/v1/logs/2026-10-26').status_code==401
    key=c.post('/api/v1/api-keys',headers=h,json={'name':'ro','scopes':['read']}).json()
    assert 'secret' in key or 'key' in key
    token=key.get('key') or key.get('secret');hr={'Authorization':'Bearer '+token}
    assert c.get('/api/v1/logs/2026-10-26',headers=hr).status_code==200
    assert c.put('/api/v1/logs/2026-10-27',headers=hr,json=body()).status_code==403
    assert c.delete('/api/v1/logs/2026-10-26',headers=hr).status_code==403

def test_delete_export_and_isolation_from_adaptive_history(system):
    c,d,h=system
    w=workout(system)
    c.put('/api/v1/logs/2026-10-26',headers=h,json=body())
    assert c.get('/api/v1/progress',headers=h).json()['exercise_history']=={}
    exported=c.get('/api/v1/account/export',headers=h).json();assert len(exported['workout_logs'])==1
    assert c.delete('/api/v1/logs/2026-10-26',headers=h).status_code==204
    assert c.get('/api/v1/logs/2026-10-26',headers=h).status_code==404
    with d.connect() as con:assert con.execute(select(db.logs)).first() is None
    assert w['id']

def test_from_plan_prefills_exercises(system):
    c,d,h=system
    w=workout(system)
    with d.connect() as con:day=con.execute(select(db.workouts.c.day)).scalar_one()
    r=c.post(f'/api/v1/logs/{day}/from-plan',headers=h);assert r.status_code==201,r.text
    log=r.json();assert len(log['exercises'])==len(w['items']);assert all(e['exercise_id'] and e['sets'] for e in log['exercises'])
    assert log['exercises'][0]['sets'][0]['done'] is False
    assert c.post(f'/api/v1/logs/{day}/from-plan',headers=h).status_code==409
    assert c.post('/api/v1/logs/2001-01-01/from-plan',headers=h).status_code==404
    r2=c.put(f'/api/v1/logs/{day}',headers=h,json={**{k:v for k,v in log.items() if k not in ('date','updated_at','previous')},'status':'in_progress','started_at':5.0});assert r2.status_code==200,r2.text
