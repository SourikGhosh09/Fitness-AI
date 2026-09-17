"""Operator CLI. Training and deployment are never exposed through user API keys."""
import argparse,csv,json,time
from pathlib import Path
from sqlalchemy import select,update
from . import db,learning
from .learning_contracts import Features,TrainingRecord

COLUMNS=['event_id','session_id','exercise_id','occurred_at',*Features.model_fields,'actual_rpe','actual_reps','actual_load_kg','pain','skipped']

def import_csv(database,path,user):
    path=Path(path)
    if path.stat().st_size>10*1024*1024:raise ValueError('CSV limit is 10 MB per import')
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=COLUMNS:raise ValueError('CSV columns must match the generated template exactly')
        records=[]
        for line,r in enumerate(reader,2):
            try:
                if r['pain'].lower()!='false' or r['skipped'].lower()!='false':raise ValueError('Only completed, pain-free matched sets are eligible')
                fields={k:r.pop(k) for k in Features.model_fields}
                r.update(features=fields,pain=False,skipped=False)
                records.append(TrainingRecord.model_validate(r))
            except (ValueError,AttributeError,KeyError) as e:raise ValueError(f'Invalid CSV row {line}: {e}') from e
    if not records:raise ValueError('CSV has no records; fill the template first')
    with database.begin() as c:
        added=sum(learning.add_record(c,user,r) for r in records)
    return {'added':added,'duplicates':len(records)-added,'status':'pending_operator_review'}

def review_imports(database,user,reviewer,evidence):
    if not reviewer.strip() or not evidence.strip():raise ValueError('Reviewer and evidence are required')
    with database.begin() as c:
        c.execute(select(db.users.c.id).where(db.users.c.id==user).with_for_update())
        g=learning.grant(c,user)
        if not g or not g['enabled']:raise ValueError('User has not consented')
        result=c.execute(update(db.learning_examples).where(db.learning_examples.c.user_id==user,db.learning_examples.c.grant_token==g['grant_token'],db.learning_examples.c.source=='import',db.learning_examples.c.quality=='pending').values(quality='approved',review={'reviewer':reviewer,'evidence':evidence,'reviewed_at':time.time()}))
    return {'approved':result.rowcount}

def main():
    parser=argparse.ArgumentParser(description='Fitness neural-network training and model management')
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('template');p.add_argument('--output',required=True)
    p=sub.add_parser('import-csv');p.add_argument('path');p.add_argument('--user-id',required=True)
    p=sub.add_parser('review-imports');p.add_argument('--user-id',required=True);p.add_argument('--reviewer',required=True);p.add_argument('--evidence',required=True)
    sub.add_parser('train');sub.add_parser('status');sub.add_parser('disable')
    p=sub.add_parser('watch');p.add_argument('--interval-hours',type=float,default=24)
    p=sub.add_parser('show');p.add_argument('model_id')
    p=sub.add_parser('activate');p.add_argument('model_id');p.add_argument('--mode',choices=['shadow','live'],default='shadow');p.add_argument('--reviewer',required=True);p.add_argument('--evidence',required=True)
    args=parser.parse_args()
    try:
        if args.action=='template':
            with Path(args.output).open('x',newline='',encoding='utf-8') as f:csv.writer(f,lineterminator="\n").writerow(COLUMNS)
            result={'template':args.output}
        else:
            database=db.make_engine()
            if args.action=='watch':
                if not 1<=args.interval_hours<=720:raise ValueError('Training interval must be 1–720 hours')
                try:
                    while True:
                        print(json.dumps(learning.train(database),allow_nan=False),flush=True)
                        time.sleep(args.interval_hours*3600)
                except KeyboardInterrupt:return
            if args.action=='import-csv':result=import_csv(database,args.path,args.user_id)
            elif args.action=='review-imports':result=review_imports(database,args.user_id,args.reviewer,args.evidence)
            elif args.action=='train':result=learning.train(database)
            else:
                with database.begin() as c:
                    if args.action=='activate':result=learning.deploy(c,args.model_id,args.mode,args.reviewer,args.evidence)
                    elif args.action=='disable':
                        c.execute(update(db.learning_deployment).values(model_id=None,mode='shadow'));result={'mode':'rules'}
                    elif args.action=='show':
                        r=c.execute(select(db.learning_models).where(db.learning_models.c.id==args.model_id)).mappings().first()
                        if not r:raise ValueError('Model not found')
                        result={k:r[k] for k in ('id','status','report','dataset_hash','review','created_at')}
                    else:
                        current=learning.active(c)
                        result={'active_model':current['id'] if current else None,'mode':current['mode'] if current else 'rules','eligible_records':len(learning.eligible(c)),
                            'models':[dict(r) for r in c.execute(select(db.learning_models.c.id,db.learning_models.c.status,db.learning_models.c.created_at)).mappings()]}
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValueError,OSError) as e:parser.exit(2,str(e)+'\n')

if __name__=='__main__':main()
