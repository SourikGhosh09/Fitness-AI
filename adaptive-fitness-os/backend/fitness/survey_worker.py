"""One dedicated worker: reconcile survey history, validate and train on changed data.

Automatic promotion is to shadow only. Existing live deployments are never replaced
by this worker; changing prescribed workouts retains the normal reviewed release path.
"""
import argparse,json,time
from sqlalchemy import select,update
from . import db,learning,contributions

def cycle(database,promote_shadow=True):
    reviewed=0
    with database.begin() as c:
        all_rows=list(c.execute(select(db.contributions).join(db.survey_participants,db.contributions.c.user_id==db.survey_participants.c.user_id).where(db.survey_participants.c.revoked==False).order_by(db.contributions.c.occurred_at,db.contributions.c.id)).mappings())
        fingerprints={}
        for row in all_rows:
            meta=c.execute(select(db.exercise_metadata.c.status,db.exercise_metadata.c.data).where(db.exercise_metadata.c.exercise_id==row['exercise_id'])).mappings().first()
            fingerprints[row['id']]=learning.digest(dict(meta) if meta else {})
        changed={row['user_id'] for row in all_rows if row['status']=='reviewed' and row['review'].get('metadata_fingerprint')!=fingerprints[row['id']]}
        from .survey import reset_derived
        for user in sorted(changed):
            c.execute(select(db.users.c.id).where(db.users.c.id==user).with_for_update())
            reset_derived(c,user)
        for row in all_rows:
            c.execute(select(db.users.c.id).where(db.users.c.id==row['user_id']).with_for_update())
            current=c.execute(select(db.contributions).where(db.contributions.c.id==row['id'])).mappings().first()
            if not current or current['status']!='pending':continue
            g=learning.grant(c,row['user_id'])
            if not g or not g['enabled'] or g['grant_token']!=current['grant_token']:continue
            data=contributions.Contribution.model_validate(current['data'])
            history=contributions.previous(c,row['user_id'],data)
            c.execute(update(db.contributions).where(db.contributions.c.id==row['id']).values(history_snapshot=history))
            contributions.review(c,row['id'],'survey-validator-v1','Automatic completeness, consent, approved exercise metadata and matching prescription checks only; self-reported answers, not human-verified facts.')
            audit=c.execute(select(db.contributions.c.review).where(db.contributions.c.id==row['id'])).scalar_one()
            c.execute(update(db.contributions).where(db.contributions.c.id==row['id']).values(review={**audit,'metadata_fingerprint':fingerprints[row['id']]}))
            reviewed+=1
    result=learning.train(database)
    model_id=result.get('model_id');model_status=result.get('model_status',result.get('status'))
    if promote_shadow and model_id and model_status=='passed':
        with database.begin() as c:
            deployed=learning.active(c)
            if not deployed or (deployed['mode']=='shadow' and deployed['id']!=model_id):
                learning.deploy(c,model_id,'shadow','survey-evaluation-worker','Passed numerical candidate gates; shadow evaluation only, no workout changes.')
                result['promoted']='shadow'
    return {'validated_submissions':reviewed,**result}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--once',action='store_true');p.add_argument('--interval-seconds',type=int,default=900);p.add_argument('--no-shadow-promotion',action='store_true');a=p.parse_args()
    if not 60<=a.interval_seconds<=86400:p.error('interval must be 60..86400 seconds')
    database=db.make_engine()
    while True:
        try:
            result=cycle(database,not a.no_shadow_promotion)
            print(json.dumps(result,allow_nan=False),flush=True)
        except Exception as exc:
            # Avoid leaking responses, participant codes or credentials in logs.
            print(json.dumps({'status':'retry_next_cycle','error_type':type(exc).__name__}),flush=True)
            if a.once:raise SystemExit(1)
        if a.once:return
        time.sleep(a.interval_seconds)
if __name__=='__main__':main()
