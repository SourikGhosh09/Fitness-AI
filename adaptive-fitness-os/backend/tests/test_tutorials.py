import json,time,hashlib
from pathlib import Path
import pytest
from sqlalchemy import select,update
from fitness import db
from fitness.importer import run,COMMIT
from fitness.tutorials import grant_rights,valid_path
from test_system import system

@pytest.fixture
def exercise(system,tmp_path,monkeypatch):
    c,d,h=system
    row={'id':'0001','name':'Test tutorial','equipment':'body weight','target':'abs','body_part':'waist','attribution':'© Gym visual — https://gymvisual.com/','instruction_steps':{'en':['Test instruction']},'image':'images/0001-2gPfomN.jpg','gif_url':'videos/0001-2gPfomN.gif'}
    original=Path(__file__).resolve().parents[2]/'data/tutorial-media'
    assets={}
    for key in ('image','gif_url'):
        rel=row[key];raw=(original/rel).read_bytes();dest=tmp_path/'tutorial-media'/rel
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        assets[rel]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    (tmp_path/'tutorial-media-manifest.json').write_text(json.dumps({'assets':assets}))
    monkeypatch.setenv('FITNESS_DATA_DIR',str(tmp_path))
    source=tmp_path/'source.json';source.write_text(json.dumps([row]));run(source,d,False)
    return c,d,h,source,row

def get(c,h):return c.get('/api/v1/exercises/source:0001/tutorial',headers=h)
def approve(d):
    with d.begin() as conn:return grant_rights(conn,['source:0001'],'TEST ONLY synthetic rights evidence','TEST reviewer',time.time()+600)

def test_default_reference_only(exercise):
    c,d,h,_,_=exercise;r=get(c,h);assert r.status_code==200
    data=r.json();assert data['status']=='license_required';assert data['animation_url'] is None;assert data['poster_url'] is None
    assert data['source_page']==f'https://github.com/hasaneyldrm/exercises-dataset/blob/{COMMIT}/videos/0001-2gPfomN.gif'
    assert 'Gym visual' in data['attribution']

def test_approved_mapping(exercise):
    c,d,h,_,_=exercise;approve(d);data=get(c,h).json()
    assert data['status']=='available'
    assert data['animation_url']=='/api/v1/exercises/source%3A0001/media/gif'
    assert data['poster_url']=='/api/v1/exercises/source%3A0001/media/image'
    assert data['cache_policy']=='none';assert data['width']==data['height']==180
    assert 'rights_reference' not in data and 'reviewed_by' not in data

@pytest.mark.parametrize('change',[{'revoked':True},{'expires_at':1}])
def test_revoked_or_expired_denied(exercise,change):
    c,d,h,_,_=exercise;approve(d)
    with d.begin() as conn:conn.execute(update(db.media_grants).values(**change))
    data=get(c,h).json();assert data['animation_url'] is None;assert data['status']=='license_required'

def test_changed_path_invalidates_grant(exercise):
    c,d,h,path,row=exercise;approve(d);row['gif_url']='videos/0001-different.gif';path.write_text(json.dumps([row]));run(path,d,False)
    data=get(c,h).json();assert data['animation_url'] is None;assert data['source_page'].endswith('/videos/0001-different.gif')
    with d.connect() as conn:assert conn.execute(select(db.media.c.license_status).where(db.media.c.kind=='gif')).scalar_one()=='blocked'

def test_changed_commit_invalidates_grant(exercise):
    c,d,h,_,_=exercise;approve(d)
    with d.begin() as conn:conn.execute(update(db.exercises).values(source_commit='a'*40))
    assert get(c,h).json()['animation_url'] is None

def test_reimport_preserves_current_rights(exercise):
    c,d,h,path,_=exercise;approve(d);run(path,d,False)
    assert get(c,h).json()['status']=='available'

def test_auth_missing_unknown_exercise(exercise):
    c,d,h,_,_=exercise
    assert c.get('/api/v1/exercises/source:0001/tutorial').status_code==401
    assert c.get('/api/v1/exercises/unknown/tutorial',headers=h).status_code==404

def test_unsafe_asset_path_never_released(exercise):
    c,d,h,_,_=exercise;approve(d)
    with d.begin() as conn:conn.execute(update(db.media).where(db.media.c.kind=='gif').values(source_path='videos/../../secret.gif'))
    data=get(c,h).json();assert data['animation_url'] is None;assert data['source_page'] is None

@pytest.mark.parametrize('path',['https://evil.example/a.gif','videos/../../x.gif','videos/0001-x.gif?token=secret','videos/0001-x.gif#fragment'])
def test_path_validation(path):assert not valid_path(path,'gif')

def test_grant_requires_evidence(exercise):
    _,d,_,_,_=exercise
    with d.begin() as conn:
        with pytest.raises(ValueError):grant_rights(conn,['source:0001'],'','reviewer',time.time()+600)


def test_authenticated_gif_bytes(exercise):
    c,d,h,path,row=exercise;approve(d);url=get(c,h).json()['animation_url']
    assert c.get(url).status_code==401
    response=c.get(url,headers=h)
    assert response.status_code==200
    assert response.headers['content-type']=='image/gif'
    assert response.headers['cache-control']=='no-store'
    assert response.content==(path.parent/'tutorial-media'/row['gif_url']).read_bytes()
    assert response.content[:6] in (b'GIF87a',b'GIF89a')

def test_revocation_blocks_previously_issued_url(exercise):
    c,d,h,_,_=exercise;approve(d);url=get(c,h).json()['animation_url']
    with d.begin() as conn:conn.execute(update(db.media_grants).values(revoked=True))
    assert c.get(url,headers=h).status_code==404

def test_missing_asset_not_announced_available(exercise):
    c,d,h,path,row=exercise;approve(d)
    (path.parent/'tutorial-media'/row['gif_url']).unlink()
    response=get(c,h).json();assert response['status']=='asset_missing';assert response['animation_url'] is None

def test_tampered_asset_not_served(exercise):
    c,d,h,path,row=exercise;approve(d);asset=path.parent/'tutorial-media'/row['gif_url']
    original=asset.read_bytes();asset.write_bytes(b'X'+original[1:])
    assert c.get('/api/v1/exercises/source:0001/media/gif',headers=h).status_code==404

def test_no_expiry_owner_authorization(exercise):
    c,d,h,_,_=exercise
    with d.begin() as conn:grant_rights(conn,['source:0001'],'owner authorization','recorded from owner',None)
    r=get(c,h).json();assert r['status']=='available';assert r['expires_at'] is None
    assert c.get(r['animation_url'],headers=h).status_code==200

def test_repeat_setup_never_revives_revoked_grant(exercise):
    c,d,h,_,_=exercise
    with d.begin() as conn:
        ids=grant_rights(conn,['source:0001'],'owner scope','owner',None,reuse_existing=True)
        conn.execute(update(db.media_grants).where(db.media_grants.c.id.in_(ids)).values(revoked=True))
        again=grant_rights(conn,['source:0001'],'owner scope','owner',None,reuse_existing=True)
        assert again==[]
    assert get(c,h).json()['status']=='license_required'

def test_media_scope_and_invalid_kind(exercise):
    c,d,h,_,_=exercise;approve(d)
    key=c.post('/api/v1/api-keys',headers=h,json={'name':'train only','scopes':['train']}).json()['key']
    assert c.get('/api/v1/exercises/source:0001/media/gif',headers={'Authorization':'Bearer '+key}).status_code==403
    assert c.get('/api/v1/exercises/source:0001/media/secret',headers=h).status_code==404
