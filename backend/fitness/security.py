import hashlib,secrets,time
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import HTTPException
from sqlalchemy import select,insert
from . import db
passwords=PasswordHasher()
DUMMY=passwords.hash(secrets.token_urlsafe(20))
def digest(token):return hashlib.sha256(token.encode()).hexdigest()
def issue(conn,user_id,name,scopes,kind='api',days=30):
    secret=('afo_live_' if kind=='api' else 'afo_session_')+secrets.token_urlsafe(32)
    key_id=db.uid();expires=time.time()+days*86400
    conn.execute(insert(db.keys).values(id=key_id,user_id=user_id,name=name,scopes=scopes,kind=kind,digest=digest(secret),expires_at=expires))
    return {'id':key_id,'key':secret,'expires_at':expires,'scopes':scopes}
def authenticate(conn,authorization,scope=None,session_only=False):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Bearer token required')
    key=conn.execute(select(db.keys).where(db.keys.c.digest==digest(authorization[7:]))).mappings().first()
    if not key or key['revoked'] or key['expires_at']<=time.time():raise HTTPException(401,'Invalid or expired credential')
    if session_only and key['kind']!='session':raise HTTPException(403,'Sign-in session required')
    if scope and scope not in key['scopes']:raise HTTPException(403,'Insufficient scope')
    return key
