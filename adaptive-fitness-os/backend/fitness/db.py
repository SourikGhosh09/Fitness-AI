import os, uuid, time
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Boolean, JSON, ForeignKey, UniqueConstraint, CheckConstraint, Index, event
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

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

# Learning data is isolated from operational workout history and is opt-in.
learning_consent=table('learning_consent',owner(),Column('enabled',Boolean,nullable=False),Column('grant_token',String(80),nullable=False),stamp(),UniqueConstraint('user_id'))
learning_examples=table('learning_examples',owner(),Column('event_id',String(100),nullable=False),Column('grant_token',String(80),nullable=False),Column('source',String(20),nullable=False),Column('quality',String(20),nullable=False),Column('payload_hash',String(64),nullable=False),Column('data',JSON,nullable=False),Column('review',JSON,nullable=False,default=dict),stamp(),UniqueConstraint('user_id','event_id'),CheckConstraint("quality IN ('pending','approved')"))
learning_models=table('learning_models',Column('status',String(20),nullable=False),Column('artifact',JSON,nullable=False),Column('report',JSON,nullable=False),Column('dataset_hash',String(64),nullable=False,unique=True),Column('review',JSON,nullable=False,default=dict),stamp())
learning_members=table('learning_members',owner(),Column('model_id',String(80),ForeignKey('learning_models.id',ondelete='CASCADE'),nullable=False,index=True),Column('grant_token',String(80),nullable=False),UniqueConstraint('user_id','model_id'))
learning_deployment=table('learning_deployment',Column('model_id',String(80),ForeignKey('learning_models.id',ondelete='SET NULL')),Column('mode',String(10),nullable=False),CheckConstraint("id = 'global'"),CheckConstraint("mode IN ('shadow','live')"))
Index('ix_learning_eligible',learning_examples.c.user_id,learning_examples.c.quality)
contributions=table('user_contributions',owner(),Column('event_id',String(80),nullable=False),Column('session_id',String(80),nullable=False),Column('exercise_id',String(80),ForeignKey('exercises.id'),nullable=False),Column('occurred_at',Float,nullable=False),Column('grant_token',String(80),nullable=False),Column('payload_hash',String(64),nullable=False),Column('status',String(20),nullable=False),Column('data',JSON,nullable=False),Column('history_snapshot',JSON),Column('report',JSON,nullable=False),Column('review',JSON,nullable=False),stamp(),UniqueConstraint('user_id','event_id'),UniqueConstraint('user_id','session_id','exercise_id'),CheckConstraint("status IN ('pending','reviewed')"))
Index('ix_contributions_user_time',contributions.c.user_id,contributions.c.occurred_at)

def make_engine(url=None):
    serverless=os.getenv('VERCEL')=='1'
    url=url or os.getenv('DATABASE_URL')
    if not url:
        if serverless:
            raise ValueError('Vercel requires DATABASE_URL for an external PostgreSQL database')
        url='sqlite:///./fitness.db'
    # Provider URLs commonly omit SQLAlchemy's installed psycopg 3 driver.
    if isinstance(url,str) and url.startswith('postgres://'):
        url='postgresql+psycopg://'+url[len('postgres://'):]
    elif isinstance(url,str) and url.startswith('postgresql://'):
        url='postgresql+psycopg://'+url[len('postgresql://'):]
    parsed=make_url(url)
    sqlite=parsed.get_backend_name()=='sqlite'
    if serverless and (parsed.drivername!='postgresql+psycopg' or
                       parsed.query.get('sslmode') not in {'require','verify-ca','verify-full'}):
        raise ValueError('Vercel requires PostgreSQL with psycopg and TLS (sslmode=require or stronger)')
    options={'pool_pre_ping':True}
    connect_args={'check_same_thread':False} if sqlite else {}
    if serverless:
        # The provider's pooled endpoint owns pooling; avoid idle per-instance pools.
        options['poolclass']=NullPool
        connect_args.update(connect_timeout=10,prepare_threshold=None)
    engine=create_engine(parsed,connect_args=connect_args,**options)
    if sqlite:
        @event.listens_for(engine,'connect')
        def pragmas(conn,_):
            conn.execute('PRAGMA foreign_keys=ON');conn.execute('PRAGMA busy_timeout=5000')
    return engine

# The survey bridge issues private pseudonymous links; it cannot log in as users.
survey_participants=table('survey_participants',owner(),Column('token_hash',String(64),nullable=False,unique=True),Column('revoked',Boolean,nullable=False,default=False),stamp(),UniqueConstraint('user_id'))
survey_responses=table('survey_responses',owner(),Column('response_key',String(64),nullable=False,unique=True),Column('revision',Integer,nullable=False),Column('payload_hash',String(64),nullable=False),Column('contribution_id',String(80),ForeignKey('user_contributions.id',ondelete='SET NULL')),Column('status',String(20),nullable=False),stamp(),CheckConstraint('revision > 0'))
survey_receipts=table('survey_receipts',Column('expires_at',Float,nullable=False,index=True))

# Notion is an opt-in collection source, not the owner of app consent or model state.
notion_links=table('notion_links',owner(),Column('code',String(80),nullable=False,unique=True),Column('enabled',Boolean,nullable=False),Column('consent_version',String(40),nullable=False),stamp(),UniqueConstraint('user_id'))
notion_pages=table('notion_pages',owner(),Column('code',String(80),nullable=False),Column('consented',Boolean,nullable=False,default=False))
notion_imports=table('notion_imports',owner(),Column('group_key',String(64),nullable=False),Column('source_hash',String(64),nullable=False),Column('contribution_id',String(80),ForeignKey('user_contributions.id',ondelete='SET NULL')),Column('status',String(40),nullable=False),Column('error_code',String(80)),UniqueConstraint('user_id','group_key'))
# No user foreign key: queued remote cleanup must survive account deletion.
notion_purges=table('notion_purges',Column('attempts',Integer,nullable=False,default=0))
notion_worker_state=table('notion_worker_state',Column('data',JSON,nullable=False))
