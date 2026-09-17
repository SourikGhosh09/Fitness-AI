"""Deterministic experimental policy. Unknown safety metadata is never treated as safe."""
from .contracts import Profile, Readiness
VERSION='rules-0.1.0'
class SafetyStop(ValueError): pass

def safety(profile:Profile,ready:Readiness):
    if ready.red_flag: raise SafetyStop('Stop training and seek urgent medical help for severe or alarming symptoms.')
    if ready.pain: raise SafetyStop('Pause this workout. Pain needs clarification; seek qualified assessment when appropriate.')
    if profile.restrictions or profile.injuries or profile.movement_limitations: raise SafetyStop('Individual restrictions require a reviewed training plan before automatic recommendations.')

def readiness_score(r):
    return round(max(0,min(100,20*r.energy-6*r.soreness-4*r.stress+min(r.sleep_hours,8)*4)))

def adaptation(history):
    # One row per distinct prior SESSION, not per set; three sessions before adjustment.
    recent=history[-3:]
    if len(recent)<3: return {'factor':1.0,'reason':'Maintain while gathering at least three completed sessions.'}
    if all(h['rpe']>=9 or h.get('missed',False) for h in recent):
        return {'factor':0.9,'reason':'Three difficult sessions: reduce load and review recovery.'}
    if all(h['rpe']<=6 and not h.get('missed',False) for h in recent):
        return {'factor':1.025,'reason':'Three comfortable sessions: consider a small load increase.'}
    return {'factor':1.0,'reason':'Mixed performance: maintain and observe.'}

def rank(profile,ready,candidates,pattern,history=None):
    safety(profile,ready);out=[];history=history or {}
    for e in candidates:
        m=e['metadata']; d=e['data']
        if e['review_status']!='approved' or m.get('pattern')!=pattern: continue
        if pattern in profile.blocked_patterns or e['id'] in profile.disliked: continue
        if d['equipment'] not in profile.equipment or m.get('skill',99)>profile.experience: continue
        if not m.get('safety_reviewed',False): continue
        goal=sum(profile.goals.get(k,0)/100*v for k,v in m.get('suitability',{}).items())
        response=history.get(e['id'],{}).get('adherence',0.5)
        parts={'goal_match':round(goal,3),'equipment_match':1,'experience_match':1,'historical_response':response,'fatigue_penalty':round(m.get('fatigue',1)*(100-readiness_score(ready))/100,3)}
        score=0.5*goal+0.15+0.1+0.25*response-0.3*parts['fatigue_penalty']
        out.append({**e,'score':round(score,4),'reasoning':parts})
    return sorted(out,key=lambda e:(-e['score'],e['id']))

def plan(profile,ready,candidates,history=None):
    safety(profile,ready);score=readiness_score(ready)
    if score<25: return {'kind':'recovery','readiness':score,'minutes':10,'items':[],'preparation':[],'cooldown':['Rest and reassess how you feel.'],'reason':'Low readiness: recovery today.','engine_version':VERSION}
    history=history or {};items=[];patterns=['squat','horizontal_push','horizontal_pull','hinge','vertical_pull','anti_rotation']
    budget=profile.minutes-10
    for p in patterns:
        required_sets=2 if profile.experience<2 or score<50 else 3
        if budget<required_sets*3: break
        ranked=rank(profile,ready,candidates,p,history)
        if not ranked: continue
        e=ranked[0];m=e['metadata'];h=history.get(e['id'],{});a=adaptation(h.get('sessions',[]))
        sets=2 if profile.experience<2 or score<50 else 3
        reps=6 if profile.goals.get('strength',0)>=40 else 10
        prior=h.get('last_load')
        load=round(prior*a['factor'],2) if prior is not None and prior>0 else None
        item={'exercise_id':e['id'],'name':e['name'],'pattern':p,'sets':sets,'reps':reps,'load_kg':load,'rpe':6 if score<50 else 7,'rir':4 if score<50 else 3,'rest_seconds':120,'instructions':e['data']['instruction_steps'].get('en',[]),'reasoning':e['reasoning'],'adjustment':a,'progression':m.get('progression','rep'),'primary_muscles':[e['data']['target']],'secondary_muscles':e['data'].get('secondary_muscles',[])}
        items.append(item);budget-=sets*3
    if not items: raise SafetyStop('No approved compatible exercises. Review catalog metadata or update equipment; no workout was invented.')
    return {'kind':'training','readiness':score,'minutes':profile.minutes,'items':items,'preparation':['3 minutes of comfortable easy movement.']+[f"Rehearse {i['name']} with an easy variation; perform 1–2 progressively heavier preparation sets without fatigue." for i in items],'cooldown':['Gradually reduce effort with easy movement.','Use comfortable, pain-free mobility for '+', '.join(sorted({m for i in items for m in i['primary_muscles']}))+'. Stop any stretch that causes pain.'],'engine_version':VERSION,'reason':'Filtered by safety, equipment, reviewed skill and movement intent; ranked by goal and response.'}

def workload(items):
    result={}
    for i in items:
        for m in i['primary_muscles']:result[m]=result.get(m,0)+i['sets']
        for m in set(i['secondary_muscles'])-set(i['primary_muscles']):result[m]=result.get(m,0)+i['sets']*0.5
    return {'estimated_set_equivalents':result,'secondary_weight':0.5,'note':'Heuristic estimate; secondary contributions are not measured physiological dose.'}
