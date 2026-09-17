import json,time,hashlib,threading
from collections import defaultdict,deque
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from fastapi import FastAPI,Header,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select,insert,update,delete,func
from sqlalchemy.exc import IntegrityError
from . import db,security,engine,tutorials
from .contracts import *

def create_app(database=None):
    database=database or db.make_engine()
    app=FastAPI(title='Adaptive Fitness OS',version='0.1.0',description='Experimental adaptive training API. See release gates before real-world use.')
    app.state.database=database
    import os
    origins=[x for x in os.getenv('CORS_ORIGINS','').split(',') if x]
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Authorization','Content-Type'])
    buckets=defaultdict(deque);lock=threading.Lock()
    @app.middleware('http')
    async def guard(request:Request,call_next):
        from starlette.responses import JSONResponse
        # Single-process defense; production ingress MUST supply distributed limits.
        now=time.monotonic();key=request.client.host if request.client else 'unknown'
        with lock:
            if len(buckets)>10000:
                for ip in list(buckets):
                    if not buckets[ip] or buckets[ip][-1]<now-60: del buckets[ip]
            q=buckets[key]
            while q and q[0]<now-60:q.popleft()
            limited=len(q)>=120
            if not limited:q.append(now)
        if limited:return JSONResponse({'detail':'Rate limit exceeded'},429,headers={'Retry-After':'60'})
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        return response
    def auth(c,a,scope=None,session=False):return security.authenticate(c,a,scope,session)
    def profile(c,u):
        row=c.execute(select(db.profiles.c.data).where(db.profiles.c.user_id==u)).scalar_one_or_none()
        if not row:raise HTTPException(409,'Complete your profile first')
        return Profile(**row)
    def ready(c,u):
        r=c.execute(select(db.readiness).where(db.readiness.c.user_id==u).order_by(db.readiness.c.created_at.desc())).mappings().first()
        if not r or time.time()-r['created_at']>18*3600:raise HTTPException(409,'Complete a fresh readiness check')
        return Readiness(**r['data'])
    def catalog(c):
        rows=c.execute(select(db.exercises,db.exercise_metadata.c.data.label('metadata'),db.exercise_metadata.c.status.label('review_status')).join(db.exercise_metadata,db.exercises.c.id==db.exercise_metadata.c.exercise_id)).mappings()
        return [dict(r) for r in rows]
    def history(c,u):
        rows=c.execute(select(db.logs,db.workouts.c.plan.label('prescription')).join(db.workouts,db.logs.c.workout_id==db.workouts.c.id).where(db.logs.c.user_id==u,db.workouts.c.status=='completed').order_by(db.logs.c.created_at)).mappings();groups={}
        for r in rows:
            target=next((i['reps'] for i in r['prescription']['items'] if i['exercise_id']==r['exercise_id']),None)
            value={**r['data'],'target_reps':target}
            groups.setdefault(r['exercise_id'],{}).setdefault(r['workout_id'],[]).append(value)
        out={}
        for e,sessions in groups.items():
            summaries=[];last=None
            for values in sessions.values():
                summaries.append({'rpe':sum(v['rpe'] for v in values)/len(values),'missed':any(v['skipped'] or v['target_reps'] is None or v['reps']<v['target_reps'] for v in values)})
                last=values[-1]['load_kg']
            out[e]={'sessions':summaries,'last_load':last,'adherence':sum(not s['missed'] for s in summaries)/len(summaries)}
        return out
    def owned_workout(c,u,w):
        row=c.execute(select(db.workouts).where(db.workouts.c.id==w,db.workouts.c.user_id==u).with_for_update()).mappings().first()
        if not row:raise HTTPException(404,'Workout not found')
        return row
    @app.get('/healthz')
    def health():
        with database.connect() as c:c.execute(select(1))
        return {'status':'ok','version':'0.1.0'}
    @app.post('/api/v1/auth/register',status_code=201)
    def register(data:Credentials):
        try:
            with database.begin() as c:
                u=db.uid();c.execute(insert(db.users).values(id=u,email=data.email.lower(),password_hash=security.passwords.hash(data.password)))
                return security.issue(c,u,'Sign-in session',['read','train','coach'],'session',1)
        except IntegrityError:raise HTTPException(409,'Account unavailable; sign in or use another email')
    @app.post('/api/v1/auth/login')
    def login(data:Credentials):
        with database.begin() as c:
            u=c.execute(select(db.users).where(db.users.c.email==data.email.lower())).mappings().first()
            try:security.passwords.verify(u['password_hash'] if u else security.DUMMY,data.password)
            except security.VerificationError:raise HTTPException(401,'Invalid credentials')
            if not u:raise HTTPException(401,'Invalid credentials')
            return security.issue(c,u['id'],'Sign-in session',['read','train','coach'],'session',1)
    @app.post('/api/v1/auth/logout',status_code=204)
    def logout(authorization:str|None=Header(default=None)):
        with database.begin() as c:
            k=auth(c,authorization);c.execute(update(db.keys).where(db.keys.c.id==k['id']).values(revoked=True))
    @app.post('/api/v1/api-keys',status_code=201)
    def create_key(data:KeyRequest,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            k=auth(c,authorization,session=True);r=security.issue(c,k['user_id'],data.name,data.scopes,days=data.expires_days)
            c.execute(insert(db.audit).values(user_id=k['user_id'],action='api_key.created',resource_id=r['id']))
            return r
    @app.get('/api/v1/api-keys')
    def list_keys(authorization:str|None=Header(default=None)):
        with database.connect() as c:
            k=auth(c,authorization,session=True)
            return [dict(r) for r in c.execute(select(db.keys.c.id,db.keys.c.name,db.keys.c.scopes,db.keys.c.expires_at,db.keys.c.revoked).where(db.keys.c.user_id==k['user_id'],db.keys.c.kind=='api')).mappings()]
    @app.delete('/api/v1/api-keys/{key_id}',status_code=204)
    def revoke_key(key_id:str,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            k=auth(c,authorization,session=True)
            c.execute(update(db.keys).where(db.keys.c.id==key_id,db.keys.c.user_id==k['user_id']).values(revoked=True))
    @app.put('/api/v1/profile')
    def save_profile(data:Profile,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            u=auth(c,authorization,'train')['user_id']
            c.execute(select(db.users.c.id).where(db.users.c.id==u).with_for_update())
            old=c.execute(select(db.profiles.c.id).where(db.profiles.c.user_id==u)).scalar_one_or_none()
            if old:c.execute(update(db.profiles).where(db.profiles.c.id==old).values(data=data.model_dump(),version=db.profiles.c.version+1))
            else:c.execute(insert(db.profiles).values(user_id=u,data=data.model_dump()))
            c.execute(delete(db.goals).where(db.goals.c.user_id==u))
            for name,priority in data.goals.items():c.execute(insert(db.goals).values(user_id=u,name=name,priority=priority))
            c.execute(update(db.workouts).where(db.workouts.c.user_id==u,db.workouts.c.status=='planned').values(status='invalidated'))
            return data
    @app.get('/api/v1/profile')
    def get_profile(authorization:str|None=Header(default=None)):
        with database.connect() as c:return profile(c,auth(c,authorization,'read')['user_id'])
    @app.post('/api/v1/readiness')
    def readiness(data:Readiness,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            u=auth(c,authorization,'train')['user_id'];c.execute(insert(db.readiness).values(user_id=u,data=data.model_dump()))
            if data.pain or data.red_flag:c.execute(update(db.workouts).where(db.workouts.c.user_id==u,db.workouts.c.status=='planned').values(status='paused'))
            return {'score':engine.readiness_score(data),'training_blocked':data.pain or data.red_flag}
    @app.get('/api/v1/exercises')
    def exercises(q:str='',limit:int=30,offset:int=0,authorization:str|None=Header(default=None)):
        if len(q)>100 or not 1<=limit<=100 or offset<0:raise HTTPException(422,'Invalid search bounds')
        with database.connect() as c:
            auth(c,authorization,'read')
            rows=c.execute(select(db.exercises.c.id,db.exercises.c.name,db.exercises.c.data).where(db.exercises.c.name.ilike('%'+q+'%')).order_by(db.exercises.c.name).offset(offset).limit(limit)).mappings()
            return [{'id':r['id'],'name':r['name'],'equipment':r['data']['equipment'],'instructions':r['data']['instruction_steps'].get('en',[]),'tutorial_path':'/exercises/'+r['id']+'/tutorial'} for r in rows]
    @app.get('/api/v1/exercises/{exercise_id}/tutorial')
    def exercise_tutorial(exercise_id:str,authorization:str|None=Header(default=None)):
        with database.connect() as c:
            auth(c,authorization,'read')
            tutorial=tutorials.descriptor(c,exercise_id)
            if tutorial is None:raise HTTPException(404,'Exercise not found')
            return tutorial
    @app.get('/api/v1/exercises/{exercise_id}/media/{kind}')
    def exercise_media(exercise_id:str,kind:str,authorization:str|None=Header(default=None)):
        from starlette.responses import FileResponse
        with database.connect() as c:
            auth(c,authorization,'read')
            path=tutorials.asset_for_request(c,exercise_id,kind)
            if path is None:raise HTTPException(404,'Tutorial media is unavailable')
            mime='image/gif' if kind=='gif' else ('image/png' if path.suffix=='.png' else 'image/jpeg')
            return FileResponse(path,media_type=mime,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    @app.post('/api/v1/workouts/today')
    def today(authorization:str|None=Header(default=None)):
        try:
            with database.begin() as c:
                u=auth(c,authorization,'train')['user_id'];p=profile(c,u);r=ready(c,u);engine.safety(p,r)
                local_now=datetime.now(ZoneInfo(p.timezone))
                day=local_now.date().isoformat()
                c.execute(select(db.users.c.id).where(db.users.c.id==u).with_for_update())
                old=c.execute(select(db.workouts).where(db.workouts.c.user_id==u,db.workouts.c.day==day)).mappings().first()
                if old:
                    if old['status'] in ('paused','invalidated'):raise HTTPException(409,'Plan paused or outdated. Review restrictions and create a reviewed replacement plan.')
                    if old['status']=='planned' and engine.readiness_score(r)<old['plan'].get('readiness',0)-15:
                        raise HTTPException(409,'Readiness has dropped. Pause and review this saved plan before training.')
                    return {'id':old['id'],'status':old['status'],**old['plan']}
                if local_now.weekday() not in p.days:
                    plan={'kind':'recovery','readiness':engine.readiness_score(r),'minutes':0,'items':[],'preparation':[],'cooldown':['Planned rest day. Recovery supports progress.'],'engine_version':engine.VERSION}
                else:plan=engine.plan(p,r,catalog(c),history(c,u))
                w=db.uid();c.execute(insert(db.workouts).values(id=w,user_id=u,day=day,status='planned',plan=plan))
                c.execute(insert(db.decisions).values(user_id=u,workout_id=w,engine_version=engine.VERSION,data=plan))
                return {'id':w,'status':'planned',**plan}
        except engine.SafetyStop as e:raise HTTPException(409,str(e))
    @app.get('/api/v1/workouts/recent')
    def recent(authorization:str|None=Header(default=None)):
        with database.connect() as c:
            u=auth(c,authorization,'read')['user_id']
            return [dict(r) for r in c.execute(select(db.workouts).where(db.workouts.c.user_id==u).order_by(db.workouts.c.day.desc()).limit(20)).mappings()]
    @app.post('/api/v1/sets',status_code=201)
    def record_set(data:SetLog,authorization:str|None=Header(default=None)):
        payload=data.model_dump();hashed=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        try:
            with database.begin() as c:
                u=auth(c,authorization,'train')['user_id'];w=owned_workout(c,u,data.workout_id)
                old=c.execute(select(db.logs).where(db.logs.c.user_id==u,db.logs.c.event_id==data.event_id)).mappings().first()
                if old:
                    if old['payload_hash']!=hashed:raise HTTPException(409,'Event ID reused with different payload')
                    return {'id':old['id'],'duplicate':True}
                if w['status']!='planned':raise HTTPException(409,'Workout does not accept new sets')
                item=next((x for x in w['plan']['items'] if x['exercise_id']==data.exercise_id),None)
                if not item or data.set_number>item['sets']:raise HTTPException(422,'Set is not part of this workout')
                i=db.uid();c.execute(insert(db.logs).values(id=i,user_id=u,workout_id=data.workout_id,exercise_id=data.exercise_id,event_id=data.event_id,set_number=data.set_number,payload_hash=hashed,data=payload))
                if data.pain:
                    c.execute(update(db.workouts).where(db.workouts.c.id==w['id']).values(status='paused'))
                    c.execute(insert(db.metadata.tables['pain_reports']).values(user_id=u,data={'exercise_id':data.exercise_id,'workout_id':w['id']}))
                return {'id':i,'duplicate':False,'paused':data.pain}
        except IntegrityError:raise HTTPException(409,'Set already recorded; fetch current workout before retrying')
    @app.post('/api/v1/workouts/{workout_id}/complete')
    def complete(workout_id:str,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            u=auth(c,authorization,'train')['user_id'];w=owned_workout(c,u,workout_id)
            if w['status']=='completed':return {'status':'completed','duplicate':True}
            if w['status']!='planned':raise HTTPException(409,'Workout is paused or outdated')
            count=c.execute(select(func.count()).select_from(db.logs).where(db.logs.c.workout_id==workout_id)).scalar_one()
            if count!=sum(i['sets'] for i in w['plan']['items']):raise HTTPException(409,'Log or explicitly skip each prescribed set first')
            c.execute(update(db.workouts).where(db.workouts.c.id==workout_id).values(status='completed'))
            if profile(c,u).gamification:c.execute(insert(db.xp).values(user_id=u,event='workout:'+workout_id,amount=50 if w['plan']['kind']=='recovery' else 200))
            return {'status':'completed','duplicate':False}
    @app.post('/api/v1/workouts/{workout_id}/substitute')
    def substitute(workout_id:str,data:Substitute,authorization:str|None=Header(default=None)):
        try:
            with database.begin() as c:
                u=auth(c,authorization,'train')['user_id'];w=owned_workout(c,u,workout_id)
                if w['status']!='planned':raise HTTPException(409,'Workout is not active')
                if data.reason=='uncomfortable':
                    c.execute(update(db.workouts).where(db.workouts.c.id==workout_id).values(status='paused'))
                    return {'status':'paused','message':'Pause and clarify discomfort before replacing the movement.'}
                if c.execute(select(func.count()).select_from(db.logs).where(db.logs.c.workout_id==workout_id)).scalar_one():raise HTTPException(409,'Substitution is available before logging starts')
                p=profile(c,u);r=ready(c,u);plan=dict(w['plan']);items=[dict(i) for i in plan['items']]
                target=next((i for i in items if i['exercise_id']==data.exercise_id),None)
                if not target:raise HTTPException(404,'Exercise not found')
                used={i['exercise_id'] for i in items}
                choices=engine.rank(p,r,[e for e in catalog(c) if e['id'] not in used],target['pattern'])
                if not choices:raise HTTPException(409,'No approved compatible alternative')
                e=choices[0];target.update(exercise_id=e['id'],name=e['name'],load_kg=None,instructions=e['data']['instruction_steps'].get('en',[]),reasoning=e['reasoning'],primary_muscles=[e['data']['target']],secondary_muscles=e['data'].get('secondary_muscles',[]))
                plan['items']=items;plan['preparation']=['3 minutes of easy movement.']+[f"Rehearse {i['name']} and perform easy ramp-up sets." for i in items]
                c.execute(update(db.workouts).where(db.workouts.c.id==workout_id).values(plan=plan,version=w['version']+1))
                c.execute(insert(db.decisions).values(user_id=u,workout_id=workout_id,engine_version=engine.VERSION,data={'reason':data.reason,'replacement':target}))
                return {'id':workout_id,**plan}
        except engine.SafetyStop as e:raise HTTPException(409,str(e))
    @app.get('/api/v1/progress')
    def progress(authorization:str|None=Header(default=None)):
        with database.connect() as c:
            u=auth(c,authorization,'read')['user_id'];points=c.execute(select(func.coalesce(func.sum(db.xp.c.amount),0)).where(db.xp.c.user_id==u)).scalar_one()
            return {'xp':points,'level':1+points//1000,'exercise_history':history(c,u),'model':'deterministic rules; no trained ML model'}
    @app.post('/api/v1/nutrition/target')
    def nutrition(data:NutritionInput,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            u=auth(c,authorization,'train')['user_id'];p=profile(c,u)
            if not p.nutrition:raise HTTPException(409,'Enable optional nutrition in your profile first')
            if p.restrictions:raise HTTPException(409,'Individual dietary restrictions require professional review')
            target={'calories_estimate':max(1500,data.maintenance_estimate+data.adjustment),'protein_g':round(data.weight_kg*1.6),'fat_g':round(data.weight_kg*0.8),'meals':data.meals,'allergies':data.allergies,'note':'Approximate planning values for generally healthy adults; individual needs vary. No medical diet support.'}
            if 4*target['protein_g']+9*target['fat_g']>target['calories_estimate']:raise HTTPException(422,'Energy estimate is too low for these macro targets; seek an individualized target')
            target['carbohydrate_g']=max(0,round((target['calories_estimate']-4*target['protein_g']-9*target['fat_g'])/4))
            c.execute(insert(db.metadata.tables['nutrition_targets']).values(user_id=u,data=target));return target
    @app.post('/api/v1/coach')
    def coach(data:CoachRequest,authorization:str|None=Header(default=None)):
        with database.begin() as c:
            u=auth(c,authorization,'coach')['user_id'];text=data.message.lower()
            if any(w in text for w in ['pain','hurt','sore','dizzy','chest']):reply='Pause if you have pain or alarming symptoms. Update readiness so the safety layer can review your session.'
            elif 'why' in text:
                decision=c.execute(select(db.decisions.c.data).where(db.decisions.c.user_id==u).order_by(db.decisions.c.created_at.desc())).scalar()
                reply=json.dumps(decision) if decision else 'There is no saved programming decision yet.'
            elif any(w in text for w in ['replace','occupied','travel']):reply='Use Replace in your workout. Alternatives pass the same safety and equipment filters.'
            else:reply='I can explain saved decisions and help you find readiness or substitution controls. Natural-language model integration is not enabled in this build.'
            c.execute(insert(db.metadata.tables['ai_interactions']).values(user_id=u,data={'intent_length':len(data.message),'mode':'rules','reply':reply}))
            return {'reply':reply,'mode':'rules','state_changed':False}
    @app.get('/api/v1/integrations')
    def integrations(authorization:str|None=Header(default=None)):
        with database.connect() as c:auth(c,authorization,'read')
        return {'camera':{'enabled':False,'status':'not implemented'},'wearables':{'enabled':False,'status':'native adapters required'},'llm':{'enabled':False,'status':'provider integration required'}}
    @app.get('/api/v1/account/export')
    def export(authorization:str|None=Header(default=None)):
        with database.connect() as c:
            u=auth(c,authorization,session=True)['user_id']
            return {t.name:[dict(r) for r in c.execute(select(t).where(t.c.user_id==u)).mappings()] for t in db.metadata.tables.values() if 'user_id' in t.c and t.name!='api_keys'}
    @app.delete('/api/v1/account',status_code=204)
    def erase(authorization:str|None=Header(default=None)):
        with database.begin() as c:
            u=auth(c,authorization,session=True)['user_id'];c.execute(delete(db.users).where(db.users.c.id==u))
    return app
app=create_app()
