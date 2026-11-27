from fitness import engine, weekly
from fitness.contracts import Profile, Readiness


def profile(days=None, **changes):
    data={'display_name':'Evolve','adult':True,'experience':2,'goals':{'strength':60,'hypertrophy':40},'equipment':['barbell'],'minutes':60,'days':days or [0,1,2,4,5]}
    data.update(changes)
    return Profile(**data)


def ready():
    return Readiness(sleep_hours=8,energy=5,soreness=0,stress=0)


def candidate(i,pattern,target):
    return {'id':i,'name':i,'source':'test','review_status':'approved',
            'metadata':{'pattern':pattern,'skill':1,'suitability':{'strength':1.0,'hypertrophy':0.8},'fatigue':0.2,'safety_reviewed':True,'progression':'rep'},
            'data':{'equipment':'barbell','target':target,'secondary_muscles':[],'instruction_steps':{'en':['Control the movement.']}}}


def test_five_day_split_has_upper_lower_full_body_structure():
    templates=weekly.split_templates(5)
    assert [x['title'] for x in templates]==['Upper A','Lower A','Full Body','Upper B','Lower B']
    assert 'squat' not in templates[0]['patterns']
    assert 'squat' in templates[1]['patterns']
    assert len(templates[2]['patterns'])==6


def test_missed_session_is_carried_to_next_available_day():
    p=profile(days=[0,1,2,4,5])
    week=weekly.build_week(p,{},[{'id':'old','day':'2026-09-14','status':'completed','plan':{}}], '2026-09-22')  # Tuesday; Monday was missed.
    monday=next(x for x in week['days'] if x['date']=='2026-09-21')
    tuesday=next(x for x in week['days'] if x['date']=='2026-09-22')
    assert monday['status']=='missed'
    assert tuesday['title']=='Upper A'
    assert tuesday['carryover'] is True
    assert week['missed_sessions']==1


def test_completed_slot_is_not_repeated_after_missed_day():
    p=profile(days=[0,1,2,4,5])
    workouts=[{'id':'w0','day':'2026-09-21','status':'completed','plan':{'session_template':weekly.split_templates(5)[0]}}]
    week=weekly.build_week(p,{},workouts,'2026-09-22')
    tuesday=next(x for x in week['days'] if x['date']=='2026-09-22')
    assert tuesday['title']=='Lower A'
    assert tuesday['carryover'] is False


def test_recovery_snapshot_uses_completed_history_recency():
    history={'squat':{'sessions':[{'day':'2026-09-21','completed_sets':3,'primary_muscles':['quads'],'secondary_muscles':['glutes']} ]}}
    snapshot=weekly.muscle_recovery(history,'2026-09-22')
    assert snapshot['quads']['days_since_training']==1
    assert snapshot['quads']['band']=='partial'
    assert snapshot['quads']['trailing_3d_set_equivalents']==3
    assert snapshot['glutes']['trailing_3d_set_equivalents']==1.5


def test_day_specific_plan_only_uses_template_patterns():
    p=profile();template=weekly.split_templates(5)[1]
    catalog=[candidate('sq','squat','quads'),candidate('hinge','hinge','hamstrings'),candidate('push','horizontal_push','chest')]
    result=engine.plan(p,ready(),catalog,{},'2026-09-22',patterns=template['patterns'],session_template=template)
    assert result['engine_version']=='rules-0.3.0'
    assert result['session_template']['title']=='Lower A'
    assert {i['pattern'] for i in result['items']} <= set(template['patterns'])
    assert 'horizontal_push' not in {i['pattern'] for i in result['items']}


def test_conservative_regeneration_reduces_or_holds_sets():
    p=profile();template=weekly.split_templates(5)[0]
    catalog=[candidate('push','horizontal_push','chest'),candidate('pull','horizontal_pull','back'),candidate('vpull','vertical_pull','lats'),candidate('core','anti_rotation','core')]
    normal=engine.plan(p,ready(),catalog,{},'2026-09-22',patterns=template['patterns'],session_template=template)
    conservative=engine.plan(p,ready(),catalog,{},'2026-09-22',patterns=template['patterns'],session_template=template,conservative=True)
    assert conservative['programming']['conservative'] is True
    assert sum(i['sets'] for i in conservative['items']) < sum(i['sets'] for i in normal['items'])

def test_brand_new_user_does_not_get_fabricated_misses_or_deferred_past_slots():
    p=profile(days=[0,1,2,4,5])
    week=weekly.build_week(p,{},[],'2026-09-25')
    assert week['missed_sessions']==0
    assert week['deferred_sessions']==[]
    assert all(d['status']!='missed' for d in week['days'])
    friday=next(d for d in week['days'] if d['date']=='2026-09-25')
    assert friday['title']=='Upper B'
    assert friday['carryover'] is False
