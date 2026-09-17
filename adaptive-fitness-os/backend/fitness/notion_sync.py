"""Consent-gated Notion -> app imports. No model training or promotion in sync."""
import os, time, uuid
from collections import defaultdict
from datetime import datetime, timezone
from pydantic import Field
from sqlalchemy import select, insert, update, delete
from . import db, learning, contributions
from .contracts import Contract

CONSENT_VERSION = 'notion-import-v1'
SOURCE_ID = 'f334c7a2-43bc-4663-a74c-55575df24f07'

class Consent(Contract):
    enabled: bool
    consent_version: str = Field(default=CONSENT_VERSION, max_length=40)

def configured():
    return bool(os.getenv('NOTION_TOKEN') and os.getenv('NOTION_DATA_SOURCE_ID'))

def status(c, user):
    link = c.execute(select(db.notion_links).where(db.notion_links.c.user_id == user)).mappings().first()
    rows = list(c.execute(select(db.notion_imports.c.status).where(db.notion_imports.c.user_id == user)).scalars())
    worker = c.execute(select(db.notion_worker_state.c.data).where(db.notion_worker_state.c.id == 'global')).scalar_one_or_none() or {}
    return {'enabled': bool(link and link['enabled']), 'participant_code': link['code'] if link and link['enabled'] else None,
            'consent_version': CONSENT_VERSION, 'configured': bool(worker.get('configured') or configured()), 'imported_workouts': rows.count('imported'),
            'needs_attention': sum(s != 'imported' for s in rows), 'last_success_at': worker.get('last_success_at'),
            'worker_status': worker.get('status', 'not_started'), 'direction': 'notion_to_app',
            'notice': 'Imports await review. Synchronization never trains or deploys a model.'}

def forget(c, user):
    """Called inside the consent/account deletion transaction, before FK cascades."""
    for page in c.execute(select(db.notion_pages.c.id).where(db.notion_pages.c.user_id == user)).scalars():
        if not c.execute(select(db.notion_purges.c.id).where(db.notion_purges.c.id == page)).first():
            c.execute(insert(db.notion_purges).values(id=page, attempts=0))
    c.execute(delete(db.notion_pages).where(db.notion_pages.c.user_id == user))
    c.execute(delete(db.notion_imports).where(db.notion_imports.c.user_id == user))
    c.execute(update(db.notion_links).where(db.notion_links.c.user_id == user).values(enabled=False, code=db.uid()))

def set_consent(c, user, request):
    c.execute(select(db.users.c.id).where(db.users.c.id == user).with_for_update())
    link = c.execute(select(db.notion_links).where(db.notion_links.c.user_id == user)).mappings().first()
    if request.enabled:
        g = learning.grant(c, user)
        profile = c.execute(select(db.profiles.c.data).where(db.profiles.c.user_id == user)).scalar_one_or_none()
        if not g or not g['enabled']: raise ValueError('Enable voluntary shared learning first')
        if not profile or not profile.get('adult'): raise ValueError('An adult app profile is required')
        if request.consent_version != CONSENT_VERSION: raise ValueError('Refresh the consent notice')
        if not link or not link['enabled']:
            values = dict(code=db.uid(), enabled=True, consent_version=CONSENT_VERSION, created_at=time.time())
            if link: c.execute(update(db.notion_links).where(db.notion_links.c.user_id == user).values(**values))
            else: c.execute(insert(db.notion_links).values(user_id=user, **values))
    else:
        # Remove imported records and retire derived models before removing mappings.
        old = list(c.execute(select(db.notion_imports.c.contribution_id).where(db.notion_imports.c.user_id == user)).scalars())
        if any(old):
            from .survey import reset_derived
            reset_derived(c, user)
            c.execute(delete(db.contributions).where(db.contributions.c.id.in_([x for x in old if x])))
        forget(c, user)
    c.execute(insert(db.audit).values(user_id=user, action='notion.opt_in' if request.enabled else 'notion.opt_out'))
    return status(c, user)

def prop(page, name):
    p = page.get('properties', {}).get(name, {})
    kind = p.get('type')
    if kind in ('rich_text', 'title'):
        return ''.join(t.get('plain_text', t.get('text', {}).get('content', '')) for t in p.get(kind, []))
    if kind == 'select': return (p.get(kind) or {}).get('name')
    if kind == 'date': return (p.get(kind) or {}).get('start')
    if kind in ('number', 'checkbox'): return p.get(kind)
    return None

def timestamp(raw):
    if not isinstance(raw, str): raise ValueError('missing_workout_date')
    dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()

def normalize(pages, key):
    """One contribution per exercise/session; sets must be contiguous and consistent."""
    ordered = sorted(pages, key=lambda p: prop(p, 'Set number') or 0)
    nums = [prop(p, 'Set number') for p in ordered]
    if nums != list(range(1, len(ordered)+1)) or len(ordered) > 20: raise ValueError('set_numbers_must_be_unique_and_contiguous')
    p = ordered[0]
    shared = ['Session ID', 'Exercise ID', 'Workout date', 'Experience', 'Sleep hours', 'Energy', 'Soreness', 'Stress', 'History mode', 'Enjoyment', 'Duration minutes']
    if any([prop(row, f) for f in shared] != [prop(p, f) for f in shared] for row in ordered): raise ValueError('inconsistent_session_context')
    if any(prop(row, 'Review') not in ('Pending',) for row in ordered): raise ValueError('not_pending_review')
    sets = []
    for row in ordered:
        if prop(row, 'Record type') != 'Participant': raise ValueError('synthetic_or_unclassified')
        if prop(row, 'Learning consent') is not True or prop(row, 'Notion sharing consent') is not True: raise ValueError('missing_consent')
        if prop(row, 'Consent version') != CONSENT_VERSION: raise ValueError('consent_version_mismatch')
        captured = timestamp(prop(row, 'Consent captured at'))
        if captured <= 0 or captured > time.time()+300: raise ValueError('invalid_consent_date')
        pain = prop(row, 'Pain')
        if pain not in (None, 'Unknown', 'None reported', 'Reported'): raise ValueError('invalid_pain_value')
        fields = {'reps':'Reps','load_kg':'Load kg','rpe':'RPE','planned_reps':'Planned reps','planned_load_kg':'Planned load kg','target_rpe':'Target RPE'}
        sets.append({**{k:prop(row,v) for k,v in fields.items()}, 'pain': {'None reported':False,'Reported':True}.get(pain), 'skipped':prop(row,'Skipped') is True})
    history = prop(p, 'History mode')
    if history not in (None, 'Unknown', 'First time', 'Recorded'): raise ValueError('invalid_history')
    return contributions.Contribution(event_id='notion_'+key[:40], session_id=prop(p,'Session ID'), exercise_id=prop(p,'Exercise ID'),
        occurred_at=timestamp(prop(p,'Workout date')), sets=sets, history_mode={None:'unknown','Unknown':'unknown','First time':'first_time','Recorded':'recorded'}[history],
        context={k:prop(p,v) for k,v in {'experience':'Experience','sleep_hours':'Sleep hours','energy':'Energy','soreness':'Soreness','stress':'Stress'}.items()},
        enjoyment=prop(p,'Enjoyment'), duration_minutes=prop(p,'Duration minutes'))

def apply_snapshot(c, pages, expected_links):
    """Only called after every query page is fetched. One transaction per snapshot.

    Missing rows remove derived imports conservatively, but do not assert that
    the Notion original was deleted. Existing page ownership is immutable.
    """
    by_code = defaultdict(list)
    for p in pages:
        if not p.get('archived') and not p.get('in_trash'):
            by_code[prop(p,'Participant ID')].append(p)
    result = {'imported':0, 'unchanged':0, 'rejected':0, 'withdrawn':0}
    for user, code in sorted(expected_links.items()):
        c.execute(select(db.users.c.id).where(db.users.c.id == user).with_for_update())
        link = c.execute(select(db.notion_links).where(db.notion_links.c.user_id == user)).mappings().first()
        g = learning.grant(c, user)
        if not link or not link['enabled'] or link['code'] != code or not g or not g['enabled']: continue
        owned = []; withdrawn = False
        for p in by_code.get(code, []):
            page_id = str(uuid.UUID(p['id']))
            if c.execute(select(db.notion_purges.c.id).where(db.notion_purges.c.id==page_id)).first(): continue
            old = c.execute(select(db.notion_pages).where(db.notion_pages.c.id==page_id)).mappings().first()
            if old and (old['user_id'] != user or old['code'] != code):
                result['rejected'] += 1; continue
            row_consent = prop(p,'Learning consent') is True and prop(p,'Notion sharing consent') is True and prop(p,'Consent version') == CONSENT_VERSION
            # A new, half-filled row has unchecked defaults, not a withdrawal.
            # Once consent was present, removing it does revoke the link.
            withdrawn = withdrawn or prop(p,'Sync status')=='Withdrawn' or bool(old and old['consented'] and (prop(p,'Learning consent') is False or prop(p,'Notion sharing consent') is False))
            if not old: c.execute(insert(db.notion_pages).values(id=page_id,user_id=user,code=code,consented=row_consent))
            elif row_consent and not old['consented']: c.execute(update(db.notion_pages).where(db.notion_pages.c.id==page_id).values(consented=True))
            owned.append(p)
        if withdrawn:
            set_consent(c,user,Consent(enabled=False)); result['withdrawn'] += 1; continue
        groups = defaultdict(list)
        for p in owned:
            key = learning.digest([prop(p,'Session ID'),prop(p,'Exercise ID')])
            groups[key].append(p)
        old_groups = {r['group_key']:r for r in c.execute(select(db.notion_imports).where(db.notion_imports.c.user_id==user)).mappings()}
        # Materialize and validate all groups before mutating derived records.
        desired = {}
        for key, group in groups.items():
            try:
                data = normalize(group,key)
                if not c.execute(select(db.exercises.c.id).where(db.exercises.c.id==data.exercise_id)).first(): raise ValueError('unknown_exercise')
                desired[key] = (learning.digest(data.model_dump()), data, None)
            except (ValueError,TypeError,KeyError):
                desired[key] = ('invalid', None, 'invalid_or_excluded_source')
        changed = [key for key, old in old_groups.items() if key not in desired or desired[key][0] != old['source_hash'] or (old['status']=='imported' and not old['contribution_id'])]
        if any(old_groups[k]['contribution_id'] for k in changed):
            from .survey import reset_derived
            reset_derived(c,user)
        for key in changed:
            old = old_groups[key]
            if old['contribution_id']: c.execute(delete(db.contributions).where(db.contributions.c.id==old['contribution_id']))
            c.execute(delete(db.notion_imports).where(db.notion_imports.c.id==old['id']))
        for key, (hashed, data, error) in desired.items():
            old = old_groups.get(key)
            if old and key not in changed:
                result['unchanged'] += 1; continue
            ident = None
            if data:
                # Never overwrite a contribution originating in the native app.
                conflict = c.execute(select(db.contributions.c.id).where(db.contributions.c.user_id==user, db.contributions.c.session_id==data.session_id, db.contributions.c.exercise_id==data.exercise_id)).first()
                if conflict: error = 'existing_app_contribution'
                else:
                    later = c.execute(select(db.contributions.c.id).where(db.contributions.c.user_id==user,db.contributions.c.occurred_at>data.occurred_at)).first()
                    if later:
                        from .survey import reset_derived
                        reset_derived(c,user)
                    ident = contributions.submit(c,user,data)['id']
            state = 'imported' if ident else 'needs_attention'
            c.execute(insert(db.notion_imports).values(user_id=user,group_key=key,source_hash=hashed,contribution_id=ident,status=state,error_code=error))
            result['imported' if ident else 'rejected'] += 1
    return result
