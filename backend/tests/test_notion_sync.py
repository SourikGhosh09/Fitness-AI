import copy, time, uuid
import pytest
from sqlalchemy import select, insert, func
from fitness import db, learning, contributions, notion_sync as ns
from fitness.notion_worker import cycle, NotionError, NotionClient
from test_system import system,workout

def row(code, **changes):
    values={'Participant ID':code,'Exercise':'Fixture 0','Exercise ID':'test:0','Session ID':'notion_session_0001','Set number':1,'Reps':8,'Load kg':20,'RPE':7,'Pain':'None reported','Skipped':False,'Planned reps':8,'Planned load kg':20,'Target RPE':7,'Experience':1,'Sleep hours':7,'Energy':3,'Soreness':1,'Stress':1,'History mode':'First time','Workout date':'2023-11-14T00:00:00Z','Learning consent':True,'Notion sharing consent':True,'Consent version':ns.CONSENT_VERSION,'Consent captured at':'2023-11-13T00:00:00Z','Record type':'Participant','Review':'Pending','Sync status':'Not connected'}
    values.update(changes);props={}
    for k,v in values.items():
        if k in ['Pain','History mode','Record type','Review','Sync status']:t='select';v={'name':v} if v else None
        elif k in ['Workout date','Consent captured at']:t='date';v={'start':v} if v else None
        elif isinstance(v,bool):t='checkbox'
        elif isinstance(v,(int,float)) or v is None:t='number'
        else:t='rich_text';v=[{'plain_text':v}]
        props[k]={'type':t,t:v}
    return {'object':'page','id':str(uuid.uuid4()),'properties':props,'archived':False}

class Fake:
    def __init__(self,pages):self.data=pages;self.purged=[];self.fail=False
    def pages(self):return copy.deepcopy(self.data)
    def purge(self,id):
        if self.fail:raise NotionError(429)
        self.purged.append(id)

def prepare(system):
    c,d,h=system;workout(system)
    u=c.put('/api/v1/learning/consent',headers=h,json={'enabled':True}).json()['account_id']
    r=c.put('/api/v1/integrations/notion/consent',headers=h,json={'enabled':True});assert r.status_code==200,r.text
    return c,d,h,u,r.json()['participant_code']

def count(d,t):
    with d.connect() as c:return c.execute(select(func.count()).select_from(t)).scalar_one()

def test_sync_dedup_edit_and_no_auto_training(system):
    c,d,h,u,code=prepare(system);f=Fake([row(code)])
    assert cycle(d,f)['imported']==1
    assert cycle(d,f)['unchanged']==1
    assert count(d,db.contributions)==1 and count(d,db.learning_examples)==0 and count(d,db.learning_models)==0
    with d.begin() as con:
        old=con.execute(select(db.contributions.c.id)).scalar_one();contributions.review(con,old,'TEST','Synthetic fixture only')
        assert len(learning.eligible(con))==1
    f.data[0]['properties']['RPE']['number']=8
    assert cycle(d,f)['imported']==1
    with d.connect() as con:
        assert not learning.eligible(con)
        current=con.execute(select(db.contributions)).mappings().one()
        assert current['status']=='pending' and current['data']['sets'][0]['rpe']==8
    assert c.get('/api/v1/integrations/notion',headers=h).json()['imported_workouts']==1

def test_multiple_sets_and_missing_values(system):
    c,d,h,u,code=prepare(system);p=row(code,RPE=None,Pain='Unknown');p2=row(code,**{'Set number':2,'RPE':None,'Pain':'Unknown'})
    cycle(d,Fake([p,p2]))
    with d.connect() as con:
        data=con.execute(select(db.contributions.c.data)).scalar_one()
        assert len(data['sets'])==2 and data['sets'][0]['rpe'] is None and data['sets'][0]['pain'] is None

@pytest.mark.parametrize('change',[{'Set number':2},{'Reps':-1},{'Reps':8.5},{'Load kg':float('nan')},{'Exercise ID':'made_up'},{'Record type':'Synthetic test'},{'Review':'Excluded'},{'Consent version':'old'},{'Consent captured at':None}])
def test_invalid_never_enters_training(system,change):
    c,d,h,u,code=prepare(system);result=cycle(d,Fake([row(code,**change)]))
    assert result['rejected']==1 and count(d,db.contributions)==0

def test_invalid_correction_removes_old_derived(system):
    c,d,h,u,code=prepare(system);f=Fake([row(code)]);cycle(d,f)
    with d.begin() as con:
        contributions.review(con,con.execute(select(db.contributions.c.id)).scalar_one(),'TEST','Test fixture')
    f.data[0]['properties']['Reps']['number']=-1
    cycle(d,f)
    assert count(d,db.contributions)==0 and count(d,db.learning_examples)==0

def test_missing_row_reconciles_only_complete_snapshot(system):
    c,d,h,u,code=prepare(system);f=Fake([row(code)]);cycle(d,f)
    class Broken(Fake):
        def pages(self):raise NotionError(503)
    with pytest.raises(NotionError):cycle(d,Broken([]))
    assert count(d,db.contributions)==1
    cycle(d,Fake([]));assert count(d,db.contributions)==0

def test_withdrawal_retry_and_no_resurrection(system):
    c,d,h,u,code=prepare(system);f=Fake([row(code)]);cycle(d,f)
    c.put('/api/v1/integrations/notion/consent',headers=h,json={'enabled':False})
    assert count(d,db.contributions)==0
    f.fail=True;assert cycle(d,f)['cleanup_pending']==1
    new=c.put('/api/v1/integrations/notion/consent',headers=h,json={'enabled':True}).json()['participant_code'];assert new!=code
    f.fail=False;cycle(d,f)
    assert count(d,db.contributions)==0 and count(d,db.notion_purges)==0 and len(f.purged)==1

@pytest.mark.parametrize('via',['learning','account','row'])
def test_revocations_queue_cleanup(system,via):
    c,d,h,u,code=prepare(system);f=Fake([row(code)]);cycle(d,f)
    if via=='learning':c.put('/api/v1/learning/consent',headers=h,json={'enabled':False})
    elif via=='account':assert c.delete('/api/v1/account',headers=h).status_code==204
    else:f.data[0]['properties']['Notion sharing consent']['checkbox']=False
    cycle(d,f)
    assert count(d,db.contributions)==0 and len(f.purged)==1

def test_snapshot_cannot_override_concurrent_optout(system):
    c,d,h,u,code=prepare(system)
    c.put('/api/v1/integrations/notion/consent',headers=h,json={'enabled':False})
    c.put('/api/v1/integrations/notion/consent',headers=h,json={'enabled':True})
    with d.begin() as con:ns.apply_snapshot(con,[row(code)],{u:code})
    assert count(d,db.contributions)==0

def test_api_requires_session_consent_and_isolates_identity(system):
    c,d,h=system
    assert c.put('/api/v1/integrations/notion/consent',headers=h,json={'enabled':True}).status_code==409
    key=c.post('/api/v1/api-keys',headers=h,json={'name':'train','scopes':['train','read']}).json()['key']
    assert c.put('/api/v1/integrations/notion/consent',headers={'Authorization':'Bearer '+key},json={'enabled':True}).status_code==403
    assert c.get('/api/v1/integrations/notion').status_code==401
    c,d,h,u,code=prepare(system)
    other=c.post('/api/v1/auth/register',json={'email':'notion-other@example.com','password':'long-other-password'}).json()['key']
    assert c.get('/api/v1/integrations/notion',headers={'Authorization':'Bearer '+other}).json()['participant_code'] is None
    cycle(d,Fake([row('P001')]))
    assert count(d,db.contributions)==0

def test_pagination_follows_cursors_and_fails_closed():
    client=NotionClient('not-real',ns.SOURCE_ID,sleep=lambda _:None)
    first=row('test');second=row('test');calls=[]
    def req(m,p,b):
        calls.append(b)
        return {'results':[second] if b.get('start_cursor') else [first],'has_more':not bool(b.get('start_cursor')),'next_cursor':'cursor1'}
    client.request=req
    assert len(client.pages())==2 and calls[1]['start_cursor']=='cursor1'
    client.request=lambda *a:{'results':[],'has_more':True,'next_cursor':'repeated'}
    with pytest.raises(NotionError):client.pages()

def test_known_page_cannot_move_to_other_participant(system):
    c,d,h,u,code=prepare(system);f=Fake([row(code)]);cycle(d,f)
    token=c.post('/api/v1/auth/register',json={'email':'second-notion@example.com','password':'another-long-password'}).json()['key'];h2={'Authorization':'Bearer '+token}
    c.put('/api/v1/profile',headers=h2,json={'display_name':'Test','adult':True,'goals':{'strength':100}})
    c.put('/api/v1/learning/consent',headers=h2,json={'enabled':True})
    code2=c.put('/api/v1/integrations/notion/consent',headers=h2,json={'enabled':True}).json()['participant_code']
    f.data[0]['properties']['Participant ID']['rich_text']=[{'plain_text':code2}]
    cycle(d,f);assert count(d,db.contributions)==0

def test_backup_restore_quarantines_notion(system,tmp_path):
    from fitness.backup import backup,restore
    c,d,h,u,code=prepare(system);cycle(d,Fake([row(code)]))
    backup(str(d.url),tmp_path/'backup.zip');restore(tmp_path/'backup.zip',tmp_path/'restored.db')
    restored=db.make_engine('sqlite:///'+str(tmp_path/'restored.db'))
    with restored.connect() as con:
        assert not con.execute(select(db.notion_links.c.enabled)).scalar_one()
        assert con.execute(select(func.count()).select_from(db.notion_imports)).scalar_one()==0
        assert con.execute(select(func.count()).select_from(db.notion_purges)).scalar_one()==0
    restored.dispose()

def test_source_change_retires_affected_model(system):
    c,d,h,u,code=prepare(system);f=Fake([row(code)]);cycle(d,f)
    with d.begin() as con:
        con.execute(insert(db.learning_models).values(id='fixture-model',status='passed',artifact={'synthetic':True},report={},dataset_hash='synthetic',review={}))
        con.execute(insert(db.learning_members).values(user_id=u,model_id='fixture-model',grant_token=learning.grant(con,u)['grant_token']))
        con.execute(insert(db.learning_deployment).values(id='global',model_id='fixture-model',mode='shadow'))
    f.data[0]['properties']['RPE']['number']=9;cycle(d,f)
    with d.connect() as con:
        assert con.execute(select(db.learning_models.c.artifact)).scalar_one()=={}
        assert con.execute(select(db.learning_models.c.status)).scalar_one()=='invalidated'
        assert con.execute(select(db.learning_deployment.c.model_id)).scalar_one() is None

def test_duplicate_set_numbers_rejected(system):
    c,d,h,u,code=prepare(system)
    assert cycle(d,Fake([row(code),row(code)]))['rejected']==1
    assert count(d,db.contributions)==0

def test_half_filled_draft_does_not_withdraw_existing_participant(system):
    c,d,h,u,code=prepare(system)
    f=Fake([row(code,**{'Learning consent':False,'Notion sharing consent':False})])
    cycle(d,f)
    assert c.get('/api/v1/integrations/notion',headers=h).json()['enabled']
    assert count(d,db.contributions)==0 and not f.purged
    f.data[0]['properties']['Learning consent']['checkbox']=True
    f.data[0]['properties']['Notion sharing consent']['checkbox']=True
    cycle(d,f);assert count(d,db.contributions)==1
    f.data[0]['properties']['Learning consent']['checkbox']=False
    cycle(d,f);assert count(d,db.contributions)==0 and len(f.purged)==1
