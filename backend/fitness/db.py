import os, uuid, time
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Boolean, JSON, ForeignKey, UniqueConstraint, CheckConstraint, Index, event

def uid(): return str(uuid.uuid4())
metadata=MetaData()
def table(name,*cols): return Table(name,metadata,Column('id',String(80),primary_key=True,default=uid),*cols)
def owner(): return Column('user_id',String(80),ForeignKey('users.id',ondelete='CASCADE'),nullable=False,index=True)
def stamp(): return Column('created_at',Float,nullable=False,default=time.time)
users=table('users',Column('email',String(254),unique=True,nullable=False),Column('password_hash',String,nullable=False),stamp())
profiles=table('profiles',owner(),Column('data',JSON,nullable=False),Column('version',Integer,default=1,nullable=False),UniqueConstraint('user_id'))
goals=table('goals',owner(),Column('name',String(50),nullable=False),Column('priority',Integer,nullable=False),CheckConstraint('priority >= 0 AND priority <= 100'),UniqueConstraint('user_id','name'))
keys=table('api_keys',owner(),Column('name',String,nullable=False),Column('digest',String(64),unique=True,nullable=False),Column('scopes',JSON,nullable=False),Column('kind',String,nullable=False),Column('expires_at',Float,nullable=False),Column('revoked',Boolean,default=False,nullable=False),stamp())
exercises=table('exercises',Column('name',String,nullable=False,index=True),Column('source',String,nullable=False),Column('source_commit',String,nullable=False),Column('source_hash',String,nullable=False),Column('data',JSON,nullable=False))
exercise_metadata=table('exercise_metadata',Column('exercise_id',String(80),ForeignKey('exercises.id',ondelete='CASCADE'),nullable=False,unique=True),Column('data',JSON,nullable=False),Column('status',String,nullable=False),Column('reviewer',String),stamp())
media=table('exercise_media',Column('exercise_id',String(80),ForeignKey('exercises.id',ondelete='CASCADE'),nullable=False,index=True),Column('kind',String,nullable=False),Column('source_path',String,nullable=False),Column('attribution',String,nullable=False),Column('license_status',String,nullable=False,default='blocked'),UniqueConstraint('exercise_id','kind'))
media_grants=table('media_license_grants',Column('media_id',String(80),ForeignKey('exercise_media.id',ondelete='CASCADE'),nullable=False,index=True),Column('source_path',String,nullable=False),Column('source_commit',String(40),nullable=False),Column('rights_reference',String,nullable=False),Column('reviewed_by',String,nullable=False),Column('expires_at',Float,nullable=True),Column('revoked',Boolean,nullable=False,default=False),stamp())
relations=table('exercise_relations',Column('exercise_id',String(80),ForeignKey('exercises.id'),nullable=False),Column('related_id',String(80),ForeignKey('exercises.id'),nullable=False),Column('kind',String,nullable=False),UniqueConstraint('exercise_id','related_id','kind'))
workouts=table('workouts',owner(),Column('day',String(10),nullable=False),Column('status',String,nullable=False),Column('plan',JSON,nullable=False),Column('version',Integer,nullable=False,default=1),stamp(),UniqueConstraint('user_id','day'))
logs=table('performance_logs',owner(),Column('workout_id',String(80),ForeignKey('workouts.id',ondelete='CASCADE'),nullable=False,index=True),Column('exercise_id',String(80),ForeignKey('exercises.id'),nullable=False),Column('event_id',String(80),nullable=False),Column('set_number',Integer,nullable=False),Column('payload_hash',String(64),nullable=False),Column('data',JSON,nullable=False),stamp(),UniqueConstraint('user_id','event_id'),UniqueConstraint('workout_id','exercise_id','set_number'))
readiness=table('readiness_logs',owner(),Column('data',JSON,nullable=False),stamp())
decisions=table('recommendation_decisions',owner(),Column('workout_id',String(80),ForeignKey('workouts.id',ondelete='CASCADE')),Column('engine_version',String,nullable=False),Column('data',JSON,nullable=False),stamp())
xp=table('xp_transactions',owner(),Column('event',String,nullable=False),Column('amount',Integer,nullable=False),stamp(),CheckConstraint('amount >= 0'),UniqueConstraint('user_id','event'))
audit=table('audit_logs',owner(),Column('action',String,nullable=False),Column('resource_id',String),stamp())
# Sparse observations retain typed parent relations; evolving measurement payloads are versioned JSON.
for name in ['assessments','recovery_logs','pain_reports','progress_measurements','nutrition_profiles','nutrition_targets','meals','wearable_connections','wearable_measurements','camera_sessions','notifications','ai_interactions']:
    table(name,owner(),Column('schema_version',Integer,default=1,nullable=False),Column('data',JSON,nullable=False),stamp())
programs=table('programs',owner(),Column('name',String,nullable=False),Column('start_date',String(10)),Column('end_date',String(10)))
phases=table('program_phases',Column('program_id',String(80),ForeignKey('programs.id',ondelete='CASCADE'),nullable=False,index=True),Column('kind',String),Column('data',JSON,nullable=False))
achievements=table('achievements',Column('code',String,unique=True,nullable=False),Column('criteria',JSON,nullable=False))
challenges=table('challenges',Column('name',String,nullable=False),Column('rules',JSON,nullable=False))
Index('ix_logs_user_time',logs.c.user_id,logs.c.created_at)

def make_engine(url=None):
    url=url or os.getenv('DATABASE_URL','sqlite:///./fitness.db')
    engine=create_engine(url,connect_args={'check_same_thread':False} if url.startswith('sqlite') else {},pool_pre_ping=True)
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def pragmas(conn,_):
            conn.execute('PRAGMA foreign_keys=ON');conn.execute('PRAGMA busy_timeout=5000')
    return engine
