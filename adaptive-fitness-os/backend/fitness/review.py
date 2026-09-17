"""Operator-only review import. Input must be authored by a qualified reviewer."""
import argparse,json
from sqlalchemy import select,update
from . import db

def apply(path,reviewer,engine):
    rows=json.load(open(path))
    with engine.begin() as c:
        for r in rows:
            m=r['metadata']
            if not m.get('safety_reviewed') or not isinstance(m.get('skill'),int) or not 0<=m['skill']<=6 or not 0<=m.get('fatigue',-1)<=1 or not m.get('pattern') or not m.get('suitability'):raise ValueError('Incomplete reviewed metadata')
            if any(not isinstance(v,(int,float)) or not 0<=v<=1 for v in m['suitability'].values()):raise ValueError('Suitability must be 0–1')
            old=c.execute(select(db.exercise_metadata.c.data).where(db.exercise_metadata.c.exercise_id==r['exercise_id'])).scalar_one()
            merged={**old,**m,'review_note':r['review_note']}
            c.execute(update(db.exercise_metadata).where(db.exercise_metadata.c.exercise_id==r['exercise_id']).values(data=merged,status='approved',reviewer=reviewer))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--reviewer',required=True);a=p.parse_args();apply(a.path,a.reviewer,db.make_engine())
