"""Consent-aware data collection and a database-backed neural model registry."""
import hashlib,json,time
from collections import Counter,defaultdict
import numpy as np
from sqlalchemy import select,insert,update,delete,func
from . import db,neural,engine
from .learning_contracts import Features,TrainingRecord

MIN_ROWS=500
MIN_USERS=20

def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def grant(c,user):
    return c.execute(select(db.learning_consent).where(db.learning_consent.c.user_id==user)).mappings().first()

def set_consent(c,user,enabled):
    c.execute(select(db.users.c.id).where(db.users.c.id==user).with_for_update())
    old=grant(c,user)
    if old and old['enabled']==enabled:return
    if not enabled:forget(c,user)
    values={'enabled':enabled,'grant_token':db.uid(),'created_at':time.time()}
    if old:c.execute(update(db.learning_consent).where(db.learning_consent.c.user_id==user).values(**values))
    else:c.execute(insert(db.learning_consent).values(user_id=user,**values))
    c.execute(insert(db.audit).values(user_id=user,action='learning.opt_in' if enabled else 'learning.opt_out'))

def invalidate_models(c,user,reason='Training participation withdrawn; retrain from eligible data.'):
    # Erase every model influenced by this user, including validation/test participation.
    ids=list(c.execute(select(db.learning_members.c.model_id).where(db.learning_members.c.user_id==user)).scalars())
    if ids:
        c.execute(update(db.learning_deployment).where(db.learning_deployment.c.model_id.in_(ids)).values(model_id=None,mode='shadow'))
        c.execute(update(db.learning_models).where(db.learning_models.c.id.in_(ids)).values(status='invalidated',artifact={},report={'reason':reason}))
        c.execute(delete(db.learning_members).where(db.learning_members.c.model_id.in_(ids)))

def forget(c,user):
    from . import notion_sync
    notion_sync.forget(c,user)
    invalidate_models(c,user)
    c.execute(delete(db.learning_examples).where(db.learning_examples.c.user_id==user))
    c.execute(delete(db.contributions).where(db.contributions.c.user_id==user))

def status(c,user):
    g=grant(c,user)
    counts=dict(c.execute(select(db.learning_examples.c.quality,func.count()).where(db.learning_examples.c.user_id==user).group_by(db.learning_examples.c.quality)).all())
    deployed=active(c)
    submissions=list(c.execute(select(db.contributions.c.status,func.count()).where(db.contributions.c.user_id==user).group_by(db.contributions.c.status)))
    return {'account_id':user,'consent':bool(g and g['enabled']),'eligible_examples':counts.get('approved',0),'pending_review':counts.get('pending',0),
            'contributions':sum(n for _,n in submissions),'pending_contributions':dict(submissions).get('pending',0),
            'model_version':deployed['id'] if deployed else None,'mode':deployed['mode'] if deployed else 'rules',
            'message':'Your completed, matching sets can contribute to shared difficulty prediction. Participation is optional. Withdrawing deletes learning examples and retires affected models; operational workout history remains.'}

def add_record(c,user,record,source='import',quality='pending'):
    c.execute(select(db.users.c.id).where(db.users.c.id==user).with_for_update())
    g=grant(c,user)
    if not g or not g['enabled']:raise ValueError('Enable shared learning before contributing records')
    record=TrainingRecord.model_validate(record);data=record.model_dump();hashed=digest(data)
    old=c.execute(select(db.learning_examples).where(db.learning_examples.c.user_id==user,db.learning_examples.c.event_id==record.event_id)).mappings().first()
    if old:
        if old['payload_hash']!=hashed:raise ValueError('Event ID already exists with different data')
        return False
    if c.execute(select(db.exercises.c.id).where(db.exercises.c.id==record.exercise_id)).scalar_one_or_none() is None:
        raise ValueError('Unknown exercise ID')
    c.execute(insert(db.learning_examples).values(user_id=user,event_id=record.event_id,grant_token=g['grant_token'],source=source,quality=quality,payload_hash=hashed,data=data,review={}))
    return True

def snapshot(item,profile,ready,history,equipment):
    h=history.get(item['exercise_id'],{});sessions=h.get('sessions',[])
    load=item.get('load_kg')
    if load is None and equipment=='body weight':load=0
    if load is None:return None
    try:
        return Features(experience=profile.experience,**{k:getattr(ready,k) for k in ('sleep_hours','energy','soreness','stress')},
            reps=item['reps'],load_kg=load,target_rpe=item['rpe'],set_number=1,previous_load_kg=h.get('last_load') or 0,
            previous_rpe=sessions[-1]['rpe'] if sessions else item['rpe'],history_sessions=min(len(sessions),1000),pattern=item['pattern']).model_dump()
    except ValueError:return None

def active(c):
    row=c.execute(select(db.learning_models,db.learning_deployment.c.mode).join(db.learning_deployment,db.learning_deployment.c.model_id==db.learning_models.c.id).where(db.learning_deployment.c.id=='global',db.learning_models.c.status=='passed')).mappings().first()
    if not row:return None
    members=list(c.execute(select(db.learning_members).where(db.learning_members.c.model_id==row['id'])).mappings())
    if len(members)!=row['report'].get('users') or not members:return None
    for m in members:
        g=grant(c,m['user_id'])
        if not g or not g['enabled'] or g['grant_token']!=m['grant_token']:return None
    try:
        if digest(row['artifact'])!=row['report'].get('artifact_hash'):return None
        if row['artifact'].get('version')!=neural.VERSION:return None
    except (ValueError,TypeError,AttributeError):return None
    return dict(row)

def annotate_plan(c,user,plan,profile,ready,history,catalog,exercise_ids=None):
    engine.safety(profile,ready)
    g=grant(c,user);plan.setdefault('learning_grant',g['grant_token'] if g and g['enabled'] else None)
    deployed=active(c);equipment={e['id']:e['data']['equipment'] for e in catalog}
    for item in plan['items']:
        if exercise_ids is not None and item['exercise_id'] not in exercise_ids:continue
        # Reopening or substituting another movement must not compound a reduction.
        if item.get('reasoning',{}).get('neural',{}).get('action')=='reduce_load_5_percent':continue
        f=snapshot(item,profile,ready,history,equipment.get(item['exercise_id']))
        item['learning_input']=f
        if not f or not deployed or item['exercise_id'] not in deployed['artifact'].get('exercise_ids',[]):continue
        try:prediction=neural.predict(deployed['artifact'],f)
        except (ValueError,KeyError,TypeError,OverflowError,IndexError):prediction=None
        if prediction is None:
            item['reasoning']['neural']={'status':'outside_validated_domain','action':'rules_unchanged'};continue
        action='shadow_only' if deployed['mode']=='shadow' else 'maintain'
        # Optional reviewed live mode may only reduce an existing load, never raise it.
        if deployed['mode']=='live' and f['history_sessions']>=3 and prediction>item['rpe']+1 and (item.get('load_kg') or 0)>0:
            item['load_kg']=round(item['load_kg']*0.95,2);action='reduce_load_5_percent'
            item['learning_input']={**f,'load_kg':item['load_kg']}
            item['adjustment']={'factor':0.95,'reason':'The reviewed model estimates higher effort at the proposed load; a conservative reduction was applied.'}
        item['reasoning']['neural']={'model_version':deployed['id'],'mode':deployed['mode'],'predicted_rpe_at_original_load':round(prediction,2),'original_load_kg':f['load_kg'],'action':action,'uncertainty':'Population validation error; not an individual confidence guarantee.'}
    engine.safety(profile,ready)
    return plan

def collect_completed(c,user,workout):
    g=grant(c,user)
    if not g or not g['enabled'] or workout['plan'].get('learning_grant')!=g['grant_token']:return 0
    items={i['exercise_id']:i for i in workout['plan']['items']};count=0
    rows=c.execute(select(db.logs).where(db.logs.c.workout_id==workout['id'])).mappings()
    for row in rows:
        outcome=row['data'];f=items[row['exercise_id']].get('learning_input')
        if not f or outcome['pain'] or outcome['skipped']:continue
        try:
            # Session creation provides stable chronology even if offline sets sync late.
            record=TrainingRecord(event_id=outcome['event_id'],session_id=workout['id'],exercise_id=row['exercise_id'],occurred_at=workout['created_at'],features={**f,'set_number':row['set_number']},actual_rpe=outcome['rpe'],actual_reps=outcome['reps'],actual_load_kg=outcome['load_kg'])
        except ValueError:continue
        count+=add_record(c,user,record,'app','approved')
    return count

def eligible(c):
    rows=c.execute(select(db.learning_examples).join(db.learning_consent,db.learning_consent.c.user_id==db.learning_examples.c.user_id).where(db.learning_consent.c.enabled==True,db.learning_examples.c.grant_token==db.learning_consent.c.grant_token,db.learning_examples.c.quality=='approved').order_by(db.learning_examples.c.created_at,db.learning_examples.c.id)).mappings()
    grouped=defaultdict(list)
    for row in rows:
        data=TrainingRecord.model_validate(row['data']).model_dump()
        grouped[row['user_id']].append({'sample_id':row['id'],'user_id':row['user_id'],'grant_token':row['grant_token'],**data})
    # Limit each contributor and remove duplicate session/exercise/set claims.
    result=[]
    for user,records in grouped.items():
        seen=set()
        for r in sorted(records,key=lambda r:(r['occurred_at'],r['sample_id']),reverse=True):
            key=(r['session_id'],r['exercise_id'],r['features']['set_number'])
            if key in seen:continue
            seen.add(key);result.append(r)
            if len(seen)>=1000:break
    return sorted(result,key=lambda r:(r['occurred_at'],r['sample_id']))

def partitions(rows):
    users=sorted({r['user_id'] for r in rows});rng=np.random.default_rng(42)
    if len(users)>=5:
        rng.shuffle(users);n=max(1,len(users)//5)
        sets=[set(users[2*n:]),set(users[n:2*n]),set(users[:n])]
        return [[r for r in rows if r['user_id'] in s] for s in sets],'held_out_users'
    # Small personal pilots can train experimentally, but cannot pass the shared release gate.
    sessions=sorted({(r['user_id'],r['session_id']) for r in rows},key=lambda s:min(r['occurred_at'] for r in rows if (r['user_id'],r['session_id'])==s))
    n=max(1,len(sessions)//5);sets=[set(sessions[:-2*n]),set(sessions[-2*n:-n]),set(sessions[-n:])]
    return [[r for r in rows if (r['user_id'],r['session_id']) in s] for s in sets],'chronological_sessions_experimental'

def metrics(artifact,rows,mean):
    predictions=np.array([neural.predict(artifact,r['features'],False) for r in rows]);y=np.array([r['actual_rpe'] for r in rows])
    def user_mean(errors):
        groups=defaultdict(list)
        for r,e in zip(rows,errors):groups[r['user_id']].append(float(e))
        return float(np.mean([np.mean(v) for v in groups.values()]))
    error=np.abs(predictions-y)
    return {'mae':user_mean(error),'target_baseline_mae':user_mean(np.abs(np.array([r['features']['target_rpe'] for r in rows])-y)),
            'mean_baseline_mae':user_mean(np.abs(mean-y)),'p90_absolute_error':float(np.quantile(error,0.9)),'rows':len(rows),'users':len({r['user_id'] for r in rows})}

def train(database):
    with database.connect() as c:rows=eligible(c);current=active(c)
    hash_value=digest(rows)
    with database.connect() as c:
        old=c.execute(select(db.learning_models.c.id,db.learning_models.c.status).where(db.learning_models.c.dataset_hash==hash_value)).mappings().first()
        if old:return {'status':'unchanged_data','model_id':old['id'],'model_status':old['status']}
    groups,method=partitions(rows)
    if len(rows)<30 or any(len(g)<5 for g in groups):
        return {'status':'waiting_for_data','eligible_rows':len(rows),'message':'Need at least 30 matched sets across enough users or at least 5 distinct sessions to form separate training, validation and test sets.'}
    train_rows,val_rows,test_rows=groups
    future=[]
    if method=='held_out_users':
        past=[]
        for user in sorted({r['user_id'] for r in train_rows}):
            records=[r for r in train_rows if r['user_id']==user]
            sessions=sorted({r['session_id'] for r in records},key=lambda s:min(r['occurred_at'] for r in records if r['session_id']==s))
            holdout=set(sessions[-max(1,len(sessions)//5):]) if len(sessions)>=5 else set()
            future.extend(r for r in records if r['session_id'] in holdout)
            past.extend(r for r in records if r['session_id'] not in holdout)
        train_rows=past;groups=[train_rows,val_rows,test_rows]
    artifact=neural.fit(train_rows,val_rows);artifact['exercise_ids']=sorted({r['exercise_id'] for r in train_rows})
    mean=float(np.mean([r['actual_rpe'] for r in train_rows]))
    reports={k:metrics(artifact,g,mean) for k,g in zip(('validation','test'),(val_rows,test_rows))}
    if future:reports['future_sessions']=metrics(artifact,future,mean)
    failures=[];users={r['user_id'] for r in rows}
    if len(rows)<MIN_ROWS or len(users)<MIN_USERS:failures.append(f'Shared release requires at least {MIN_ROWS} eligible sets and {MIN_USERS} contributors; these are engineering gates, not proof of clinical validity.')
    if len(future)<30 or len({r['user_id'] for r in future})<5:failures.append('Need at least 30 future-session examples from 5 training users for longitudinal evaluation')
    for name,m in reports.items():
        if m['mae']>1 or m['p90_absolute_error']>2:failures.append(name+': absolute error gate failed')
        if m['mae']>=min(m['target_baseline_mae'],m['mean_baseline_mae'])*0.95:failures.append(name+': did not improve both baselines by 5%')
    slices={}
    for label,predicate in [('beginner',lambda r:r['features']['experience']<=1),('experienced',lambda r:r['features']['experience']>1)]:
        subset=[r for r in test_rows if predicate(r)]
        if len(subset)>=20:
            m=metrics(artifact,subset,mean);slices[label]=m
            if m['mae']>1.5 or m['mae']>min(m['target_baseline_mae'],m['mean_baseline_mae'])+0.1:failures.append(label+': subgroup regression')
    champion=None
    if current:
        prior_members=set(current['report'].get('sample_ids',[]))
        novel=[r for r in test_rows if r['sample_id'] not in prior_members]
        if len(novel)<30:failures.append('Need 30 new held-out test records for comparison with the deployed model')
        else:
            old=metrics(current['artifact'],novel,mean);new=metrics(artifact,novel,mean);champion={'old_mae':old['mae'],'new_mae':new['mae']}
            if new['mae']>=old['mae']:failures.append('Did not improve on deployed model on new test records')
    report={'status':'passed' if not failures else 'experimental','rows':len(rows),'users':len(users),'split':method,'metrics':reports,'subgroups':slices,'champion_comparison':champion,
            'failures':failures,'sample_ids':[r['sample_id'] for r in rows],'split_sample_ids':{k:[r['sample_id'] for r in g] for k,g in zip(('train','validation','test'),groups)},
            'artifact_hash':digest(artifact),'limitations':['Self-reported RPE; matched completed prescriptions only.','Selection bias; no causal benefit or medical validity demonstrated.','Shadow evaluation and professional review required before live use.']}
    report['split_sample_ids']['future_sessions']=[r['sample_id'] for r in future]
    model_id=db.uid()
    with database.begin() as c:
        # Serialize with consent withdrawal and ensure no removed examples are resurrected.
        for u in sorted(users):c.execute(select(db.users.c.id).where(db.users.c.id==u).with_for_update())
        latest={r['sample_id'] for r in eligible(c)}
        if not set(report['sample_ids'])<=latest:raise ValueError('Training data changed or consent withdrawn; discard candidate and retry')
        c.execute(insert(db.learning_models).values(id=model_id,status=report['status'],artifact=artifact,report=report,dataset_hash=hash_value,review={}))
        for u in sorted(users):
            token=next(r['grant_token'] for r in rows if r['user_id']==u)
            g=grant(c,u)
            if not g or not g['enabled'] or g['grant_token']!=token:raise ValueError('Consent changed during training')
            c.execute(insert(db.learning_members).values(user_id=u,model_id=model_id,grant_token=token))
    return {'model_id':model_id,**{k:v for k,v in report.items() if k not in ('sample_ids','split_sample_ids','artifact_hash')}}

def deploy(c,model_id,mode,reviewer,evidence):
    if mode not in ('shadow','live') or not reviewer.strip() or not evidence.strip():raise ValueError('Mode, reviewer and review evidence are required')
    model=c.execute(select(db.learning_models).where(db.learning_models.c.id==model_id)).mappings().first()
    if not model or model['status']!='passed' or digest(model['artifact'])!=model['report'].get('artifact_hash'):raise ValueError('Model is missing, altered or has not passed evaluation')
    members=list(c.execute(select(db.learning_members).where(db.learning_members.c.model_id==model_id)).mappings())
    for m in sorted(members,key=lambda m:m['user_id']):
        c.execute(select(db.users.c.id).where(db.users.c.id==m['user_id']).with_for_update())
        g=grant(c,m['user_id'])
        if not g or not g['enabled'] or g['grant_token']!=m['grant_token']:raise ValueError('Model participation is no longer valid')
    if len(members)!=model['report'].get('users') or not members:raise ValueError('Model has no valid provenance')
    # Same user-before-model lock order as consent withdrawal avoids a deadlock.
    model=c.execute(select(db.learning_models).where(db.learning_models.c.id==model_id).with_for_update()).mappings().first()
    if not model or model['status']!='passed':raise ValueError('Model was retired during activation')
    review={'reviewer':reviewer,'evidence':evidence,'mode':mode,'reviewed_at':time.time()}
    history=model['review'].get('history',[])
    c.execute(update(db.learning_models).where(db.learning_models.c.id==model_id).values(review={'history':[*history,review],'latest':review}))
    old=c.execute(select(db.learning_deployment).where(db.learning_deployment.c.id=='global').with_for_update()).first()
    if old:c.execute(update(db.learning_deployment).where(db.learning_deployment.c.id=='global').values(model_id=model_id,mode=mode))
    else:c.execute(insert(db.learning_deployment).values(id='global',model_id=model_id,mode=mode))
    return {'model_id':model_id,'mode':mode,'review':review}
