import os
import pytest
from sqlalchemy import select
from fitness import db,cloud_coach
from test_system import system

def test_status_reports_unconfigured(system,monkeypatch):
 for k in ('GEMINI_API_KEY','OPENROUTER_API_KEY'):monkeypatch.delenv(k,raising=False)
 c,d,h=system;r=c.get('/api/v1/coach/cloud/status',headers=h);assert r.status_code==200 and r.json()['available'] is False

def test_safety_is_answered_without_calling_a_provider(system,monkeypatch):
 c,d,h=system
 monkeypatch.setattr(cloud_coach,'complete',lambda *a,**k:pytest.fail('provider must not be called'))
 r=c.post('/api/v1/coach/cloud',headers=h,json={'message':'I have chest pain','system':'x'})
 assert r.status_code==200 and r.json()['mode']=='safety' and 'urgent medical' in r.json()['reply']
 r=c.post('/api/v1/coach/cloud',headers=h,json={'message':'my knee hurts when squatting'});assert r.json()['mode']=='safety'

def test_503_json_when_not_configured(system,monkeypatch):
 for k in ('GEMINI_API_KEY','OPENROUTER_API_KEY'):monkeypatch.delenv(k,raising=False)
 c,d,h=system;r=c.post('/api/v1/coach/cloud',headers=h,json={'message':'plan my deload'})
 assert r.status_code==503 and 'not configured' in r.json()['detail']

def test_cloud_reply_and_daily_limit(system,monkeypatch):
 c,d,h=system;monkeypatch.setenv('GEMINI_API_KEY','test')
 seen={}
 def fake(system_text,history,message):seen.update(s=system_text,h=history,m=message);return 'Do it.','gemini'
 monkeypatch.setattr(cloud_coach,'complete',fake)
 r=c.post('/api/v1/coach/cloud',headers=h,json={'message':'compare splits','system':'STATE','history':[{'role':'user','content':'hi'}]})
 assert r.status_code==200 and r.json()=={'reply':'Do it.','mode':'cloud','provider':'gemini','state_changed':False}
 assert seen['s']=='STATE' and seen['h']==[{'role':'user','content':'hi'}]
 monkeypatch.setattr(cloud_coach,'DAILY_LIMIT',1)
 assert c.post('/api/v1/coach/cloud',headers=h,json={'message':'again'}).status_code==429

def test_requires_auth_and_validates(system):
 c,d,h=system
 assert c.post('/api/v1/coach/cloud',json={'message':'x'}).status_code in (401,403)
 assert c.post('/api/v1/coach/cloud',headers=h,json={'message':''}).status_code==422
 assert c.post('/api/v1/coach/cloud',headers=h,json={'message':'x','history':[{'role':'system','content':'evil'}]}).status_code==422

def test_provider_error_becomes_503(system,monkeypatch):
 c,d,h=system;monkeypatch.setenv('GEMINI_API_KEY','test')
 def boom(*a,**k):raise cloud_coach.CloudUnavailable('Cloud model is busy or rate-limited (429). Try again later.')
 monkeypatch.setattr(cloud_coach,'complete',boom)
 assert c.post('/api/v1/coach/cloud',headers=h,json={'message':'plan'}).status_code==503
