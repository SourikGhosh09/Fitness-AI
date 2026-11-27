"""Explicit goal-priority ordering, downstream of selection and safety filtering."""
VERSION='sequence-policy-1'

def order_selected(items,candidates,goals):
    reviewed={e['id']:e['metadata'] for e in candidates if e['review_status']=='approved' and e['metadata'].get('safety_reviewed')}
    scored=[]
    for position,item in enumerate(items):
        m=reviewed.get(item['exercise_id'])
        if m is None:raise ValueError('Cannot order an exercise without approved safety metadata')
        score=sum(goals.get(k,0)/100*v for k,v in m.get('suitability',{}).items())
        scored.append((score,m.get('skill',0),position,item))
    result=[]
    for score,skill,position,item in sorted(scored,key=lambda x:(-x[0],-x[1],x[2])):
        result.append({**item,'order_reason':{'policy':VERSION,'goal_compatibility':round(score,4),'reviewed_skill_requirement':skill,
                     'reason':'Reviewed goal compatibility first, technical demand next; preserve original order for ties. Warm-up comes before these working sets.'}})
    return result
