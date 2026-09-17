"""Repeatable source import; media remains blocked and review overrides survive refresh."""
import argparse,hashlib,json,re
from pathlib import Path,PurePosixPath
from sqlalchemy import select,insert,update
from . import db
SOURCE='https://github.com/hasaneyldrm/exercises-dataset'
COMMIT='7455efae41b330c265e7cd4b78dfa848e7ce5ebd'
BLOB='3cbb77b678c40d7342897d38e4c61e9502f829a7'
PATTERNS=[('squat','squat'),('deadlift','hinge'),('lunge','lunge'),('bench press','horizontal_push'),('push-up','horizontal_push'),('row','horizontal_pull'),('pull-up','vertical_pull'),('pulldown','vertical_pull'),('shoulder press','vertical_push'),('pallof','anti_rotation')]
FIELDS='aliases movement_plane compound bilateral difficulty stability_requirement mobility_requirement endurance_suitability power_suitability mobility_suitability flexibility_suitability cardiovascular_suitability systemic_fatigue joint_loading contraindications progression_alternatives regression_alternatives substitutes rep_ranges tempo_compatibility warmup_suitability cooldown_suitability stretch_classification'.split()
def normalize(row):
    if not isinstance(row,dict) or not re.fullmatch(r'\d{4}',str(row.get('id',''))):raise ValueError('Invalid exercise ID')
    for field in ['name','equipment','target','body_part','attribution']:
        if not isinstance(row.get(field),str) or not row[field]:raise ValueError('Invalid '+field)
    if not isinstance(row.get('instruction_steps',{}).get('en'),list):raise ValueError('Missing English steps')
    for field,folder in [('image','images'),('gif_url','videos')]:
        p=PurePosixPath(row[field])
        if p.is_absolute() or '..' in p.parts or p.parts[0]!=folder or '\\' in row[field]:raise ValueError('Unsafe media path')
    pattern=next((p for word,p in PATTERNS if word in row['name'].lower()),None)
    meta={k:None for k in FIELDS}
    meta.update(pattern=pattern,skill=None,suitability={},fatigue=None,progression=None,safety_reviewed=False,provenance={'method':'name heuristic','version':'0.1','confidence':0.4 if pattern else 0,'source_commit':COMMIT})
    return {'id':'source:'+row['id'],'name':row['name'],'source':SOURCE,'source_commit':COMMIT,'source_hash':hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(),'data':row},meta

def run(path,engine,verify=True):
    raw=Path(path).read_bytes()
    if verify and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:raise ValueError('Source blob mismatch: review the new dataset revision before importing')
    rows=json.loads(raw);normalized=[normalize(r) for r in rows]
    if len({r[0]['id'] for r in normalized})!=len(rows):raise ValueError('Duplicate source IDs')
    with engine.begin() as c:
        for record,meta in normalized:
            exists=c.execute(select(db.exercises.c.source_hash).where(db.exercises.c.id==record['id'])).scalar_one_or_none()
            if exists:
                c.execute(update(db.exercises).where(db.exercises.c.id==record['id']).values(**record))
                if exists!=record['source_hash']:c.execute(update(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id==record['id']).values(status='needs_review'))
            else:
                c.execute(insert(db.exercises).values(**record))
                c.execute(insert(db.exercise_metadata).values(exercise_id=record['id'],data=meta,status='needs_review'))
            for field,kind in [('image','image'),('gif_url','gif')]:
                path=record['data'][field]
                old=c.execute(select(db.media).where(db.media.c.exercise_id==record['id'],db.media.c.kind==kind)).mappings().first()
                if old:
                    values={'source_path':path,'attribution':record['data']['attribution']}
                    if old['source_path']!=path:values['license_status']='blocked'
                    c.execute(update(db.media).where(db.media.c.id==old['id']).values(**values))
                else:
                    c.execute(insert(db.media).values(exercise_id=record['id'],kind=kind,source_path=path,attribution=record['data']['attribution'],license_status='blocked'))
    return {'records':len(rows),'media_references':len(rows)*2,'media_downloaded':0,'review_required':True,'source_commit':COMMIT,'sha256':hashlib.sha256(raw).hexdigest()}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');args=p.parse_args();print(json.dumps(run(args.path,db.make_engine()),indent=2))
