from fitness import engine
from fitness.contracts import Profile, Readiness


def profile(**changes):
    data={'display_name':'Phase 2','adult':True,'experience':2,'goals':{'strength':100},'equipment':['barbell'],'minutes':60,'days':[0,1,2,3,4,5,6]}
    data.update(changes)
    return Profile(**data)


def ready(**changes):
    data={'sleep_hours':8,'energy':5,'soreness':0,'stress':0}
    data.update(changes)
    return Readiness(**data)


def candidate(i='squat',pattern='squat',target='quads'):
    return {'id':i,'name':'Reviewed squat','source':'test','review_status':'approved',
            'metadata':{'pattern':pattern,'skill':1,'suitability':{'strength':1.0},'fatigue':0.3,'safety_reviewed':True,'progression':'rep'},
            'data':{'equipment':'barbell','target':target,'secondary_muscles':['glutes'],'instruction_steps':{'en':['Move with control.']}}}


def sessions(rpe=6,reps=5,missed=False):
    return [{'workout_id':f'w{i}','day':f'2026-09-{20+i:02d}','rpe':rpe,'missed':missed,'completed_sets':3,'target_sets':3,'target_reps':5,'avg_reps':reps,'min_reps':reps,'primary_muscles':['quads'],'secondary_muscles':['glutes']} for i in range(3)]


def test_double_progression_adds_rep_before_load():
    a=engine.adaptation(sessions(rpe=6,reps=5),4,6)
    assert a['action']=='add_rep'
    assert a['rep_delta']==1
    assert a['factor']==1.0


def test_double_progression_loads_after_top_of_range():
    a=engine.adaptation(sessions(rpe=6,reps=6),4,6)
    assert a['action']=='increase_load'
    assert a['factor']==1.025


def test_repeated_difficult_sessions_reduce_load():
    rows=sessions(rpe=9,reps=4)
    a=engine.adaptation(rows,4,6)
    assert a['action']=='reduce_load'
    assert a['factor']==0.9


def test_missing_effort_does_not_crash_or_progress():
    rows=sessions();rows[0]['rpe']=None;rows[1]['rpe']=None;rows[2]['rpe']=None
    a=engine.adaptation(rows,4,6)
    assert a['action']=='maintain'


def test_fatigue_deload_needs_recent_difficulty_plus_reduced_readiness():
    history={'squat':{'sessions':sessions(rpe=9,reps=4)}}
    state=engine.fatigue_state(history,55)
    assert state['deload'] is True
    assert state['level']=='high'


def test_weekly_workload_uses_primary_and_half_secondary_sets():
    history={'squat':{'sessions':sessions(rpe=7,reps=5)}}
    volume=engine.weekly_workload(history,'2026-09-22')
    assert volume['quads']==9
    assert volume['glutes']==4.5


def test_plan_exposes_phase2_programming_and_rep_range():
    p=profile();r=ready();history={'squat':{'sessions':sessions(rpe=6,reps=5),'last_load':50,'adherence':1,'primary_muscles':['quads'],'secondary_muscles':['glutes']}}
    result=engine.plan(p,r,[candidate()],history,'2026-09-23')
    assert result['engine_version']=='rules-0.2.0'
    assert result['programming']['goal_mode']=='strength'
    assert result['items'][0]['rep_range']==[4,6]
    assert result['items'][0]['adjustment']['action']=='add_rep'
    assert result['items'][0]['reps']==6


def test_reduced_readiness_blocks_progression_and_scales_session():
    p=profile();r=ready(sleep_hours=5,energy=2,soreness=2,stress=2)
    history={'squat':{'sessions':sessions(rpe=6,reps=6),'last_load':50,'adherence':1,'primary_muscles':['quads'],'secondary_muscles':['glutes']}}
    result=engine.plan(p,r,[candidate()],history,'2026-09-23')
    item=result['items'][0]
    assert result['programming']['readiness_band'] in {'reduced','low'}
    assert item['adjustment']['action'] in {'hold_for_readiness','deload'}
    assert item['sets']<=2
    assert item['load_kg']<=47.5
