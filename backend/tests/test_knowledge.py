import copy
import hashlib
import json
import numpy as np
import pytest
from sqlalchemy import insert,select,func
from fitness import knowledge,knowledge_model as model,db
from fitness.media_assets import data_dir
from fitness.sequencing import order_selected
from test_system import system,workout

def test_actual_model_integrity_and_heldout_partitions():
    rows=json.loads((data_dir()/'exercises.json').read_text(encoding='utf-8'));parts=model.split_rows(rows)
    groups={k:{model.family(r['name']) for r in v} for k,v in parts.items()}
    assert not groups['train']&groups['validation'] and not groups['test']&(groups['train']|groups['validation'])
    artifact=knowledge.read('exercise-model.json');report=knowledge.read('training-report.json')
    assert len(rows)==report['source_count']==1324
    assert artifact['source_sha256']==hashlib.sha256((data_dir()/'exercises.json').read_bytes()).hexdigest()
    assert artifact['vocabulary']==sorted({t for r in parts['train'] for t in model.features(r['name'])})
    for part in parts:assert report['partitions'][part]['exercise_ids']==[str(r['id']) for r in parts[part]]
    x=model.encode([r['name'] for r in parts['test']],artifact['vocabulary'])
    y=np.array([artifact['labels'].index(r['target']) for r in parts['test']])
    actual=model.metrics(y,model.forward(x,model.validate(artifact))[0],artifact['labels'])
    assert actual==report['metrics']['test']
    assert actual['accuracy']>report['test_majority_baseline']
    assert knowledge.model_status()['status']=='trained_experimental'

def test_gradients_match_finite_differences():
    rng=np.random.default_rng(2);x=rng.normal(size=(4,3));y=np.array([0,1,1,0]);cw=np.array([.7,1.3])
    weights=[rng.normal(size=(3,2)),rng.normal(size=2),rng.normal(size=(2,2)),rng.normal(size=2)]
    gs=model.gradients(x,y,weights,cw)
    def loss():
        p=model.forward(x,weights)[0]
        return -(np.log(p[np.arange(len(y)),y])*cw[y]).mean()
    for w,g in zip(weights,gs):
        for index in np.ndindex(w.shape):
            old=w[index];w[index]=old+1e-6;high=loss();w[index]=old-1e-6;low=loss();w[index]=old
            assert g[index]==pytest.approx((high-low)/2e-6,abs=1e-6)

def test_grouping_and_unknown_name():
    assert model.family('barbell bench press')==model.family('dumbbell incline bench press')
    result=knowledge.classify('zzxxq vvqqz')
    assert result['status']=='uncertain' and result['suggestions']==[]

def test_corrupt_model_rejected():
    artifact=copy.deepcopy(knowledge.read('exercise-model.json'));artifact['weights'][0][0][0]=float('nan')
    with pytest.raises(ValueError):model.predict(artifact,'barbell curl')
    artifact['weights']=[]
    with pytest.raises(ValueError):model.validate(artifact)

def test_source_change_disables_inference(tmp_path,monkeypatch):
    root=data_dir()
    (tmp_path/'knowledge').mkdir()
    for name in ['exercise-model.json','training-report.json']:(tmp_path/'knowledge'/name).write_bytes((root/'knowledge'/name).read_bytes())
    (tmp_path/'exercises.json').write_text('[]')
    monkeypatch.setenv('FITNESS_DATA_DIR',str(tmp_path))
    assert knowledge.classify('barbell curl')['status']=='unavailable'

def test_every_source_target_has_educational_entry():
    rows=json.loads((data_dir()/'exercises.json').read_text(encoding='utf-8'))
    for target in {r['target'] for r in rows}:assert knowledge.muscle(target)
    assert knowledge.muscle('chest')['id']=='pectorals'
    assert knowledge.muscle('spine')['kind']=='source_region_label'
    assert knowledge.muscle('cardio')['kind']=='source_system_label'
    assert knowledge.muscle('nonexistent') is None

def test_source_labels_override_any_prediction(system,monkeypatch):
    c,d,h=system
    with d.begin() as con:
        con.execute(insert(db.exercises).values(id='source:42',name='barbell close-grip bench press',source='supplied source',source_commit='test',source_hash='hash',data={'target':'triceps','secondary_muscles':['pectorals'],'equipment':'barbell','instruction_steps':{'en':['Source instructions']}}))
    monkeypatch.setattr(knowledge,'classify',lambda _:pytest.fail('Source lookup must not call the classifier'))
    result=c.get('/api/v1/exercises/source:42/knowledge',headers=h)
    assert result.status_code==200 and result.json()['primary_target']=='triceps'
    reply=c.post('/api/v1/coach',headers=h,json={'message':'What does barbell close-grip bench press target?'}).json()
    assert reply['mode']=='sourced_knowledge' and 'triceps' in reply['reply'] and not reply['state_changed']

def test_anatomy_query_is_not_pain_but_symptoms_take_priority(system):
    c,d,h=system
    good=c.post('/api/v1/coach',headers=h,json={'message':'What does chest do?'}).json()
    assert good['mode']=='sourced_knowledge' and 'Pectoralis' in good['reply']
    for message in ['I have chest pain. Which exercise first?','My shoulder hurts, tell me about biceps','My elbow is painful']:
        bad=c.post('/api/v1/coach',headers=h,json={'message':message}).json()
        assert bad['mode']=='rules' and not bad['state_changed']
    assert 'urgent' in c.post('/api/v1/coach',headers=h,json={'message':'chest pain'}).json()['reply']

def test_knowledge_auth_validation_and_no_workout_mutation(system):
    c,d,h=system
    for path in ['/knowledge/status','/knowledge/order','/knowledge/muscles','/knowledge/classify?name=curl','/exercises/missing/knowledge']:
        assert c.get('/api/v1'+path).status_code==401
    assert c.get('/api/v1/knowledge/classify?name=x',headers=h).status_code==422
    assert c.get('/api/v1/knowledge/muscles?q=unknown',headers=h).status_code==404
    assert c.get('/api/v1/exercises/missing/knowledge',headers=h).status_code==404
    w=workout(system)
    result=c.get('/api/v1/knowledge/order',headers=h).json()
    assert result['planned_exercises'][0]['exercise_id']==w['items'][0]['exercise_id']
    other=c.post('/api/v1/auth/register',json={'email':'knowledge-other@example.com','password':'another-long-password-42'}).json()['key']
    assert c.get('/api/v1/knowledge/order',headers={'Authorization':'Bearer '+other}).json()['planned_exercises']==[]
    c.post('/api/v1/coach',headers=h,json={'message':'Which exercise do I do first then next?'})
    with d.connect() as con:
        saved=con.execute(select(db.workouts.c.plan).where(db.workouts.c.id==w['id'])).scalar_one()
        assert [x['exercise_id'] for x in saved['items']]==[x['exercise_id'] for x in w['items']]
        assert con.execute(select(func.count()).select_from(db.logs)).scalar_one()==0

def test_ordering_priority_and_safety_gate():
    items=[{'exercise_id':'a','name':'a'},{'exercise_id':'b','name':'b'}]
    candidates=[{'id':'a','review_status':'approved','metadata':{'safety_reviewed':True,'suitability':{'strength':.2},'skill':0}},
                {'id':'b','review_status':'approved','metadata':{'safety_reviewed':True,'suitability':{'strength':.9},'skill':0}}]
    assert [x['exercise_id'] for x in order_selected(items,candidates,{'strength':100})]==['b','a']
    assert items[0]['exercise_id']=='a'
    candidates[0]['review_status']='needs_review'
    with pytest.raises(ValueError):order_selected(items,candidates,{'strength':100})
