"""Private operator queue for guided contributions. Not exposed to ordinary users."""
import argparse,json,os
from collections import Counter
from sqlalchemy import select
from . import db,contributions

def eligible_submissions(c):
    return c.execute(select(db.contributions).join(db.learning_consent,db.learning_consent.c.user_id==db.contributions.c.user_id).where(db.learning_consent.c.enabled==True,db.learning_consent.c.grant_token==db.contributions.c.grant_token).order_by(db.contributions.c.created_at,db.contributions.c.id)).mappings()

def summary(c):
    rows=list(eligible_submissions(c));reasons=Counter()
    for r in rows:
        for s in r['report']['sets']:reasons.update(s['reasons'])
    return {'contributors':len({r['user_id'] for r in rows}),'submissions':len(rows),'recorded_sets':sum(r['report']['sets_recorded'] for r in rows),
        'pending_review':sum(r['status']=='pending' for r in rows),'completeness_gaps':dict(reasons),
        'queue':[{'id':r['id'],'status':r['status'],'potential_training_sets':r['report']['potential_training_sets']} for r in rows if r['status']=='pending']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('report')
    p=sub.add_parser('show');p.add_argument('id')
    p=sub.add_parser('review');p.add_argument('id');p.add_argument('--reviewer',required=True);p.add_argument('--evidence',required=True)
    p=sub.add_parser('export');p.add_argument('--output',required=True)
    args=parser.parse_args();database=db.make_engine()
    try:
        with database.begin() as c:
            if args.action=='report':result=summary(c)
            elif args.action=='review':result=contributions.review(c,args.id,args.reviewer,args.evidence)
            elif args.action=='show':
                row=next((r for r in eligible_submissions(c) if r['id']==args.id),None)
                if not row:raise ValueError('Contribution not found or consent withdrawn')
                result=dict(row)
            else:
                rows=list(eligible_submissions(c))
                # Private, opt-in-only collection export. No account emails or names.
                fd=os.open(args.output,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'w') as output:
                    for row in rows:output.write(json.dumps(dict(row),allow_nan=False)+'\n')
                result={'exported':len(rows),'file':args.output,'notice':'Sensitive pseudonymous data. Encrypt and restrict access; reconcile consent changes before reusing this export.'}
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValueError,OSError) as e:parser.exit(2,str(e)+'\n')

if __name__=='__main__':main()
