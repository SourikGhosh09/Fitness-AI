"""Serve authorized source-matched tutorial GIFs from the supplied local assets."""
import argparse
import json
import math
import re
import time
from urllib.parse import quote
from sqlalchemy import select, insert, update, or_
from . import db,media_assets
from .importer import SOURCE
ATTRIBUTION='© Gym visual — https://gymvisual.com/'

def valid_path(path,kind):
    prefix,suffix=('videos','gif') if kind=='gif' else ('images','(?:jpg|jpeg|png)')
    return bool(re.fullmatch(prefix+r'/[0-9]{4}-[A-Za-z0-9_-]+\.'+suffix,path))

def active_grant(conn,media,commit):
    return conn.execute(select(db.media_grants).where(
        db.media_grants.c.media_id==media['id'],
        db.media_grants.c.source_path==media['source_path'],
        db.media_grants.c.source_commit==commit,
        db.media_grants.c.revoked.is_(False),
        or_(db.media_grants.c.expires_at.is_(None),db.media_grants.c.expires_at>time.time()),
    ).order_by(db.media_grants.c.created_at.desc())).mappings().first()

def descriptor(conn,exercise_id):
    exercise=conn.execute(select(db.exercises).where(db.exercises.c.id==exercise_id)).mappings().first()
    if not exercise:return None
    result={'exercise_id':exercise_id,'status':'unavailable','animation_url':None,
            'poster_url':None,'source_page':None,'attribution':ATTRIBUTION,
            'width':180,'height':180,'cache_policy':'none','expires_at':None,'delivery':'authenticated_local'}
    commit=exercise['source_commit']
    if exercise['source']!=SOURCE or not re.fullmatch(r'[a-f0-9]{40}',commit):return result
    rows=conn.execute(select(db.media).where(db.media.c.exercise_id==exercise_id)).mappings().all()
    expires=[]
    for row in rows:
        if row['kind'] not in ('image','gif') or not valid_path(row['source_path'],row['kind']):continue
        if row['kind']=='gif':
            result['source_page']=f"{SOURCE}/blob/{commit}/{row['source_path']}"
            result['status']='license_required'
        grant=active_grant(conn,row,commit) if row['license_status']=='licensed' else None
        if not grant:continue
        if not media_assets.resolve_asset(row['source_path']):
            if row['kind']=='gif':result['status']='asset_missing'
            continue
        url=f"/api/v1/exercises/{quote(exercise_id,safe='')}/media/{row['kind']}"
        result['animation_url' if row['kind']=='gif' else 'poster_url']=url
        if grant['expires_at'] is not None:expires.append(grant['expires_at'])
    if result['animation_url']:result['status']='available'
    result['expires_at']=min(expires) if expires else None
    return result

def asset_for_request(conn,exercise_id,kind):
    """Recheck rights and bytes on each image request, including after descriptor retrieval."""
    if kind not in ('gif','image'):return None
    d=descriptor(conn,exercise_id)
    if not d or not d['animation_url' if kind=='gif' else 'poster_url']:return None
    row=conn.execute(select(db.media).where(db.media.c.exercise_id==exercise_id,db.media.c.kind==kind)).mappings().first()
    return media_assets.resolve_asset(row['source_path'],verify=True)

def grant_rights(conn,exercise_ids,rights_reference,reviewed_by,expires_at=None,reuse_existing=False):
    if not exercise_ids or not rights_reference.strip() or not reviewed_by.strip():
        raise ValueError('Explicit exercise scope, authorization reference and recorded-by identity are required')
    if expires_at is not None and (not math.isfinite(expires_at) or expires_at<=time.time()):
        raise ValueError('Expiry must be a future Unix timestamp, or null when none was stated')
    grants=[]
    for exercise_id in sorted(set(exercise_ids)):
        exercise=conn.execute(select(db.exercises).where(db.exercises.c.id==exercise_id)).mappings().one()
        if exercise['source']!=SOURCE or not re.fullmatch(r'[a-f0-9]{40}',exercise['source_commit']):
            raise ValueError('Authorization must identify a pinned source exercise')
        rows=conn.execute(select(db.media).where(db.media.c.exercise_id==exercise_id)).mappings().all()
        if not rows:raise ValueError('Exercise has no imported media references')
        for row in rows:
            if row['kind'] not in ('image','gif') or not valid_path(row['source_path'],row['kind']):raise ValueError('Invalid source media path')
            if reuse_existing:
                old=conn.execute(select(db.media_grants.c.id).where(db.media_grants.c.media_id==row['id'],db.media_grants.c.source_path==row['source_path'],db.media_grants.c.source_commit==exercise['source_commit'],db.media_grants.c.rights_reference==rights_reference)).first()
                # Setup must not undo explicit revocation or expiration.
                if old:continue
            key=db.uid()
            conn.execute(insert(db.media_grants).values(id=key,media_id=row['id'],source_path=row['source_path'],source_commit=exercise['source_commit'],rights_reference=rights_reference,reviewed_by=reviewed_by,expires_at=expires_at))
            conn.execute(update(db.media).where(db.media.c.id==row['id']).values(license_status='licensed'))
            grants.append(key)
    return grants

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Operator-only record of supplied media authorization. Does not acquire or independently verify a license.')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('grant').add_argument('manifest')
    sub.add_parser('revoke').add_argument('grant_ids',nargs='+')
    args=parser.parse_args()
    with db.make_engine().begin() as conn:
        if args.command=='grant':
            with open(args.manifest) as f:manifest=json.load(f)
            print(json.dumps({'grant_ids':grant_rights(conn,**manifest)}))
        else:
            conn.execute(update(db.media_grants).where(db.media_grants.c.id.in_(args.grant_ids)).values(revoked=True))
            print(json.dumps({'revoked':args.grant_ids}))
