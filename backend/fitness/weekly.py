"""Schedule-aware weekly programming helpers for Fitness AI v0.3.0 Evolve.

This module does not claim to calculate biological recovery. It derives an
explainable weekly sequence from the user's selected training days, completed
workouts and recent set-equivalent history. Recovery labels are conservative
heuristics and remain subordinate to safety/readiness checks in ``engine``.
"""
from __future__ import annotations

from datetime import date, timedelta

VERSION = 'weekly-0.3.0'
WEEKDAYS = ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')

FULL_BODY = ['squat','horizontal_push','horizontal_pull','hinge','vertical_pull','anti_rotation']
UPPER = ['horizontal_push','horizontal_pull','vertical_pull','anti_rotation']
LOWER = ['squat','hinge','anti_rotation']


def split_templates(training_days: int) -> list[dict]:
    """Return a simple, bounded split using only movement patterns the engine supports."""
    n=max(1,min(7,int(training_days)))
    if n==1:
        raw=[('Full Body','Full-body fundamentals',FULL_BODY)]
    elif n==2:
        raw=[('Full Body A','Balanced full body',FULL_BODY),('Full Body B','Balanced full body',FULL_BODY)]
    elif n==3:
        raw=[('Full Body A','Full-body strength',FULL_BODY),('Full Body B','Full-body balance',FULL_BODY),('Full Body C','Full-body volume',FULL_BODY)]
    elif n==4:
        raw=[('Upper A','Upper-body strength',UPPER),('Lower A','Lower-body strength',LOWER),('Upper B','Upper-body volume',UPPER),('Lower B','Lower-body volume',LOWER)]
    elif n==5:
        raw=[('Upper A','Upper-body strength',UPPER),('Lower A','Lower-body strength',LOWER),('Full Body','Balanced full body',FULL_BODY),('Upper B','Upper-body volume',UPPER),('Lower B','Lower-body volume',LOWER)]
    else:
        raw=[]
        for i in range(n):
            cycle=i%3
            raw.append((f"Upper {1+i//3}" if cycle==0 else (f"Lower {1+i//3}" if cycle==1 else f"Full Body {1+i//3}"),
                        'Upper-body focus' if cycle==0 else ('Lower-body focus' if cycle==1 else 'Balanced full body'),
                        UPPER if cycle==0 else (LOWER if cycle==1 else FULL_BODY)))
    return [{'slot':i,'code':name.lower().replace(' ','_'),'title':name,'focus':focus,'patterns':list(patterns)} for i,(name,focus,patterns) in enumerate(raw)]


def _as_date(value) -> date | None:
    if isinstance(value,date):return value
    try:return date.fromisoformat(str(value))
    except (TypeError,ValueError):return None


def _workout_map(workouts: list[dict] | None) -> dict[str,dict]:
    return {str(w.get('day')):w for w in (workouts or []) if w.get('day')}


def muscle_recovery(history: dict, current_day: str | date) -> dict[str,dict]:
    """Summarize recency and recent work by muscle from completed history."""
    today=_as_date(current_day) or date.today();muscles={}
    for item in history.values():
        for session in item.get('sessions',[]):
            d=_as_date(session.get('day'))
            if d is None or d>today:continue
            sets=max(0,int(session.get('completed_sets',0)))
            primary=session.get('primary_muscles') or item.get('primary_muscles',[])
            secondary=session.get('secondary_muscles') or item.get('secondary_muscles',[])
            for muscle,weight in [(m,1.0) for m in primary]+[(m,0.5) for m in set(secondary)-set(primary)]:
                row=muscles.setdefault(muscle,{'last_trained':None,'trailing_3d_set_equivalents':0.0})
                if row['last_trained'] is None or d>_as_date(row['last_trained']):row['last_trained']=d.isoformat()
                if today-timedelta(days=2)<=d<=today:row['trailing_3d_set_equivalents']+=sets*weight
    for row in muscles.values():
        last=_as_date(row['last_trained']);days=(today-last).days if last else None
        row['days_since_training']=days
        row['trailing_3d_set_equivalents']=round(row['trailing_3d_set_equivalents'],2)
        if days is None:band='unknown'
        elif days==0:band='recently_trained'
        elif days==1:band='partial'
        else:band='recovered'
        row['band']=band
    return muscles


def build_week(profile, history: dict, workouts: list[dict] | None, anchor_day: str | date) -> dict:
    """Build the current Monday-Sunday schedule and carry missed session slots forward.

    A missed day does not consume its session slot. The next available training
    day receives the earliest unfinished slot, so the sequence stays coherent
    instead of silently skipping a workout focus.
    """
    today=_as_date(anchor_day) or date.today();start=today-timedelta(days=today.weekday());end=start+timedelta(days=6)
    templates=split_templates(len(profile.days));by_day=_workout_map(workouts)
    scheduled=[start+timedelta(days=i) for i in range(7) if (start+timedelta(days=i)).weekday() in profile.days]

    completed_slots=set()
    for d in scheduled:
        row=by_day.get(d.isoformat())
        if not row or row.get('status')!='completed':continue
        template=(row.get('plan') or {}).get('session_template') or {}
        slot=template.get('slot')
        if isinstance(slot,int) and 0<=slot<len(templates):completed_slots.add(slot)
        else:
            # Backward compatibility for Momentum workouts that did not persist a slot.
            fallback=scheduled.index(d)
            if fallback<len(templates):completed_slots.add(fallback)

    unfinished=[i for i in range(len(templates)) if i not in completed_slots]
    has_any_history=bool(workouts) or any(item.get('sessions') for item in history.values())
    first_week_untracked=not has_any_history
    next_cursor=0;days=[];missed=0;assigned_future=[]
    for d in [start+timedelta(days=i) for i in range(7)]:
        iso=d.isoformat();row=by_day.get(iso);is_training=d.weekday() in profile.days
        if not is_training:
            days.append({'date':iso,'weekday':WEEKDAYS[d.weekday()],'scheduled':False,'status':'rest','title':'Rest / Recovery','focus':'No programmed resistance session','template':None})
            continue
        base_index=scheduled.index(d);base_template=templates[min(base_index,len(templates)-1)]
        if row and row.get('status')=='completed':
            stored=(row.get('plan') or {}).get('session_template') or base_template
            days.append({'date':iso,'weekday':WEEKDAYS[d.weekday()],'scheduled':True,'status':'completed','title':stored.get('title',base_template['title']),'focus':stored.get('focus',base_template['focus']),'template':stored,'workout_id':row.get('id')})
            continue
        if d<today:
            if first_week_untracked:
                days.append({'date':iso,'weekday':WEEKDAYS[d.weekday()],'scheduled':True,'status':'not_tracked','title':base_template['title'],'focus':base_template['focus'],'template':base_template,'workout_id':None,'reason':'No prior workout history exists yet, so earlier days in this first observed week are not treated as missed.'})
            else:
                missed+=1
                days.append({'date':iso,'weekday':WEEKDAYS[d.weekday()],'scheduled':True,'status':'missed','title':base_template['title'],'focus':base_template['focus'],'template':base_template,'workout_id':row.get('id') if row else None,'reason':'Scheduled session was not completed; its sequence slot remains due.'})
            continue
        if first_week_untracked:
            slot=base_template['slot']
        else:
            slot=unfinished[next_cursor] if next_cursor<len(unfinished) else min(base_index,len(templates)-1)
        if not first_week_untracked and next_cursor<len(unfinished):next_cursor+=1
        template=templates[slot];assigned_future.append(slot)
        status='today' if d==today else 'upcoming'
        if row and row.get('status')=='planned':status='planned' if d==today else 'upcoming_planned'
        elif row and row.get('status') in {'paused','invalidated'}:status=row.get('status')
        carryover=slot!=base_template['slot']
        days.append({'date':iso,'weekday':WEEKDAYS[d.weekday()],'scheduled':True,'status':status,'title':template['title'],'focus':template['focus'],'template':template,'workout_id':row.get('id') if row else None,'carryover':carryover,
                     'reason':'Earlier unfinished session carried forward to preserve sequence.' if carryover else 'Scheduled sequence slot for this training day.'})

    still_unfinished=[] if first_week_untracked else [templates[i] for i in unfinished if i not in assigned_future]
    next_session=next((d for d in days if d['scheduled'] and d['date']>=today.isoformat() and d['status'] not in {'completed','paused','invalidated'}),None)
    return {'policy':VERSION,'week_start':start.isoformat(),'week_end':end.isoformat(),'anchor_day':today.isoformat(),'training_days':sorted(profile.days),'days':days,'missed_sessions':missed,
            'next_session':next_session,'deferred_sessions':still_unfinished,'recovery_snapshot':muscle_recovery(history,today),
            'explanation':'Completed sessions consume their sequence slot. Missed sessions do not; the earliest unfinished focus moves to the next available training day.'}


def session_for_day(profile, history: dict, workouts: list[dict] | None, target_day: str | date) -> dict | None:
    target=_as_date(target_day) or date.today();week=build_week(profile,history,workouts,target)
    day=next((d for d in week['days'] if d['date']==target.isoformat()),None)
    return day.get('template') if day and day.get('scheduled') else None
