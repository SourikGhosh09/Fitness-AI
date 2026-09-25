"""Deterministic adaptive programming policy.

Phase 2 adds bounded progression, readiness scaling, fatigue/deload detection and
trailing workload awareness. These are conservative engineering heuristics, not
validated physiological or clinical prescriptions. Unknown safety metadata is
never treated as safe.
"""
from datetime import date, timedelta
from .contracts import Profile, Readiness
from .sequencing import order_selected

VERSION='rules-0.2.0'
WEEKLY_VOLUME_POLICY='trailing-7d-set-equivalents-1'

class SafetyStop(ValueError): pass


def safety(profile:Profile,ready:Readiness):
    if ready.red_flag: raise SafetyStop('Stop training and seek urgent medical help for severe or alarming symptoms.')
    if ready.pain: raise SafetyStop('Pause this workout. Pain needs clarification; seek qualified assessment when appropriate.')
    if profile.restrictions or profile.injuries or profile.movement_limitations: raise SafetyStop('Individual restrictions require a reviewed training plan before automatic recommendations.')


def readiness_score(r):
    return round(max(0,min(100,20*r.energy-6*r.soreness-4*r.stress+min(r.sleep_hours,8)*4)))


def readiness_adjustment(score):
    """Bound how much a single session can change from the baseline prescription."""
    if score>=80:return {'band':'high','set_delta':0,'load_factor':1.0,'target_rpe':7,'target_rir':3,'progression_allowed':True}
    if score>=60:return {'band':'normal','set_delta':0,'load_factor':1.0,'target_rpe':7,'target_rir':3,'progression_allowed':True}
    if score>=45:return {'band':'reduced','set_delta':-1,'load_factor':0.95,'target_rpe':6,'target_rir':4,'progression_allowed':False}
    if score>=25:return {'band':'low','set_delta':-1,'load_factor':0.90,'target_rpe':6,'target_rir':4,'progression_allowed':False}
    return {'band':'recovery','set_delta':-2,'load_factor':0.0,'target_rpe':5,'target_rir':5,'progression_allowed':False}


def goal_prescription(profile):
    """Choose an initial rep/set/rest frame from the user's weighted goals."""
    g=profile.goals
    scores={
        'strength':g.get('strength',0)+0.5*g.get('power',0),
        'hypertrophy':g.get('hypertrophy',0)+0.5*g.get('recomposition',0),
        'endurance':g.get('muscular_endurance',0)+0.25*g.get('cardio',0),
        'general':g.get('general_health',0)+0.25*g.get('mobility',0)+0.25*g.get('flexibility',0),
    }
    mode=max(scores,key=lambda k:(scores[k],{'strength':4,'hypertrophy':3,'endurance':2,'general':1}[k]))
    if mode=='strength':return {'mode':mode,'rep_min':4,'rep_max':6,'start_reps':6,'sets':3,'rest_seconds':150}
    if mode=='hypertrophy':return {'mode':mode,'rep_min':8,'rep_max':12,'start_reps':10,'sets':3,'rest_seconds':90}
    if mode=='endurance':return {'mode':mode,'rep_min':12,'rep_max':15,'start_reps':12,'sets':2,'rest_seconds':60}
    return {'mode':'general','rep_min':8,'rep_max':10,'start_reps':10,'sets':3,'rest_seconds':90}


def adaptation(history,rep_min=None,rep_max=None):
    """Return a bounded next-session progression from distinct completed sessions.

    Old callers receive the original factor behavior. New Phase 2 callers can
    supply a rep range so comfortable success first progresses repetitions and
    only then increases load.
    """
    recent=history[-3:]
    base={'factor':1.0,'rep_delta':0,'action':'maintain','reason':'Maintain while gathering at least three completed sessions.'}
    if len(recent)<3:return base
    def valid_rpe(h):return h.get('rpe') is not None
    difficult=[h for h in recent if h.get('missed',False) or (valid_rpe(h) and h['rpe']>=9)]
    comfortable=all(valid_rpe(h) and h['rpe']<=6 and not h.get('missed',False) for h in recent)
    if len(difficult)>=2:
        return {'factor':0.9,'rep_delta':0,'action':'reduce_load','reason':'Repeated difficult or incomplete sessions: reduce load and rebuild comfortable performance.'}
    if comfortable:
        if rep_max is not None:
            achieved=[h.get('min_reps',h.get('avg_reps')) for h in recent]
            achieved=[x for x in achieved if x is not None]
            if achieved and min(achieved)<rep_max:
                return {'factor':1.0,'rep_delta':1,'action':'add_rep','reason':'Three comfortable successful sessions: add one repetition before increasing load.'}
        return {'factor':1.025,'rep_delta':0,'action':'increase_load','reason':'Three comfortable successful sessions at the top of the rep target: apply a small load increase.'}
    return {'factor':1.0,'rep_delta':0,'action':'maintain','reason':'Mixed performance: maintain and observe.'}


def fatigue_state(history,score):
    """Aggregate exercise histories into distinct recent workouts to avoid double counting."""
    workouts={}
    for item in history.values():
        for session in item.get('sessions',[]):
            sid=session.get('workout_id')
            if not sid:continue
            row=workouts.setdefault(sid,{'day':session.get('day'),'rpes':[],'missed':False})
            if session.get('rpe') is not None:row['rpes'].append(session['rpe'])
            row['missed']=row['missed'] or bool(session.get('missed'))
    ordered=sorted(workouts.values(),key=lambda x:x.get('day') or '')[-4:]
    difficult=0
    for w in ordered:
        mean=sum(w['rpes'])/len(w['rpes']) if w['rpes'] else None
        if w['missed'] or (mean is not None and mean>=8.5):difficult+=1
    ratio=difficult/len(ordered) if ordered else 0
    deload=score<45 or (len(ordered)>=3 and ratio>=2/3 and score<70)
    level='high' if deload else ('elevated' if ratio>=0.5 or score<60 else 'normal')
    return {'level':level,'recent_workouts':len(ordered),'difficult_workouts':difficult,'difficult_ratio':round(ratio,2),'deload':deload,
            'reason':'Readiness and recent completed-session difficulty are used only as a bounded conservative heuristic.'}


def weekly_workload(history,current_day=None):
    """Estimate completed set-equivalents in the trailing seven calendar days."""
    try:today=date.fromisoformat(current_day) if current_day else date.today()
    except ValueError:today=date.today()
    earliest=today-timedelta(days=6);result={}
    for item in history.values():
        for s in item.get('sessions',[]):
            try:d=date.fromisoformat(s.get('day',''))
            except (ValueError,TypeError):continue
            if not earliest<=d<=today:continue
            sets=max(0,int(s.get('completed_sets',0)))
            primary=s.get('primary_muscles') or item.get('primary_muscles',[])
            secondary=s.get('secondary_muscles') or item.get('secondary_muscles',[])
            for m in primary:result[m]=result.get(m,0)+sets
            for m in set(secondary)-set(primary):result[m]=result.get(m,0)+sets*0.5
    return {k:round(v,2) for k,v in result.items()}


def weekly_set_cap(profile):
    # Conservative engineering guardrail, not a claim of an optimal physiological dose.
    if profile.experience<=1:return 10
    if profile.experience<=3:return 14
    return 18


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


def plan(profile,ready,candidates,history=None,current_day=None):
    safety(profile,ready);score=readiness_score(ready)
    if score<25:return {'kind':'recovery','readiness':score,'minutes':10,'items':[],'preparation':[],'cooldown':['Rest and reassess how you feel.'],'reason':'Low readiness: recovery today.','engine_version':VERSION,'programming':{'policy':VERSION,'readiness_band':'recovery','deload':True}}
    history=history or {};items=[];patterns=['squat','horizontal_push','horizontal_pull','hinge','vertical_pull','anti_rotation']
    baseline=goal_prescription(profile);readiness=readiness_adjustment(score);fatigue=fatigue_state(history,score);weekly=weekly_workload(history,current_day);cap=weekly_set_cap(profile)
    budget=profile.minutes-10
    deload=fatigue['deload']
    skipped_for_volume=[]
    for p in patterns:
        base_sets=min(baseline['sets'],2) if profile.experience<2 else baseline['sets']
        planned_sets=max(1,base_sets+readiness['set_delta']-(1 if deload else 0))
        if budget<planned_sets*3:break
        ranked=rank(profile,ready,candidates,p,history)
        if not ranked:continue
        e=ranked[0];m=e['metadata'];h=history.get(e['id'],{});a=adaptation(h.get('sessions',[]),baseline['rep_min'],baseline['rep_max'])
        primary=[e['data']['target']];secondary=e['data'].get('secondary_muscles',[])
        primary_volume=max((weekly.get(muscle,0) for muscle in primary),default=0)
        remaining=max(0,int(cap-primary_volume))
        if remaining<=0:
            skipped_for_volume.append({'exercise_id':e['id'],'pattern':p,'reason':'Trailing seven-day primary-muscle set-equivalent guardrail reached.'})
            continue
        sets=min(planned_sets,remaining)
        prior=h.get('last_load')
        reps=baseline['start_reps']
        if h.get('sessions'):
            last=h['sessions'][-1]
            prior_target=last.get('target_reps')
            if isinstance(prior_target,int):reps=max(baseline['rep_min'],min(baseline['rep_max'],prior_target))
        progression_allowed=readiness['progression_allowed'] and not deload
        if progression_allowed and a['action']=='add_rep':reps=min(baseline['rep_max'],reps+a['rep_delta'])
        elif progression_allowed and a['action']=='increase_load':reps=baseline['rep_min']
        load_factor=readiness['load_factor']*(a['factor'] if progression_allowed or a['factor']<1 else 1.0)*(0.9 if deload else 1.0)
        load=round(prior*load_factor,2) if prior is not None and prior>0 else None
        action=a['action'] if progression_allowed else ('deload' if deload else 'hold_for_readiness')
        reason=a['reason'] if progression_allowed else ('Recent difficulty/readiness triggered a temporary deload: reduce volume and load.' if deload else 'Readiness is below the progression threshold: preserve technique and reduce session demand.')
        item={'exercise_id':e['id'],'name':e['name'],'pattern':p,'sets':sets,'reps':reps,'rep_range':[baseline['rep_min'],baseline['rep_max']],
              'load_kg':load,'rpe':readiness['target_rpe'],'rir':readiness['target_rir'],'rest_seconds':baseline['rest_seconds'],
              'instructions':e['data']['instruction_steps'].get('en',[]),'reasoning':e['reasoning'],
              'adjustment':{**a,'action':action,'reason':reason,'effective_load_factor':round(load_factor,4)},
              'progression':m.get('progression','rep'),'primary_muscles':primary,'secondary_muscles':secondary,
              'weekly_primary_set_equivalents_before':round(primary_volume,2),'weekly_set_cap':cap}
        items.append(item);budget-=sets*3
        for muscle in primary:weekly[muscle]=weekly.get(muscle,0)+sets
        for muscle in set(secondary)-set(primary):weekly[muscle]=weekly.get(muscle,0)+sets*0.5
    if not items:
        if skipped_for_volume:
            return {'kind':'recovery','readiness':score,'minutes':10,'items':[],'preparation':[],'cooldown':['Use easy pain-free movement and recover before adding more training volume.'],
                    'reason':'Recent completed workload reached the conservative trailing seven-day guardrail for available movements.','engine_version':VERSION,
                    'programming':{'policy':VERSION,'goal_mode':baseline['mode'],'readiness_band':readiness['band'],'fatigue':fatigue,'deload':deload,'weekly_set_cap':cap,'weekly_volume':weekly,'volume_limited':skipped_for_volume}}
        raise SafetyStop('No approved compatible exercises. Review catalog metadata or update equipment; no workout was invented.')
    items=order_selected(items,candidates,profile.goals)
    session_workload=workload(items)
    programming={'policy':VERSION,'goal_mode':baseline['mode'],'rep_range':[baseline['rep_min'],baseline['rep_max']],
                 'readiness_band':readiness['band'],'fatigue':fatigue,'deload':deload,'weekly_volume_before':weekly_workload(history,current_day),
                 'weekly_set_cap':cap,'session_workload':session_workload,'volume_limited':skipped_for_volume,
                 'note':'Adaptive values are conservative experimental heuristics and remain subordinate to safety and reviewed exercise metadata.'}
    return {'kind':'training','readiness':score,'minutes':profile.minutes,'items':items,
            'preparation':['3 minutes of comfortable easy movement.']+[f"Rehearse {i['name']} with an easy variation; perform 1–2 progressively heavier preparation sets without fatigue." for i in items],
            'cooldown':['Gradually reduce effort with easy movement.','Use comfortable, pain-free mobility for '+', '.join(sorted({m for i in items for m in i['primary_muscles']}))+'. Stop any stretch that causes pain.'],
            'engine_version':VERSION,'reason':'Safety-filtered exercises are ranked by goal and response, then bounded by readiness, recent difficulty and trailing workload.','programming':programming}


def workload(items):
    result={}
    for i in items:
        for m in i['primary_muscles']:result[m]=result.get(m,0)+i['sets']
        for m in set(i['secondary_muscles'])-set(i['primary_muscles']):result[m]=result.get(m,0)+i['sets']*0.5
    return {'estimated_set_equivalents':{k:round(v,2) for k,v in result.items()},'secondary_weight':0.5,'note':'Heuristic estimate; secondary contributions are not measured physiological dose.'}
