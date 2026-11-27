"""Consent, immutable learning examples, model registry and deployment pointer."""
from alembic import op
import sqlalchemy as sa
revision='0004'
down_revision='0003'

def upgrade():
    def base(): return sa.Column('id',sa.String(80),primary_key=True)
    def owner(): return sa.Column('user_id',sa.String(80),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    def stamp(): return sa.Column('created_at',sa.Float(),nullable=False)
    op.create_table('learning_consent',base(),owner(),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('grant_token',sa.String(80),nullable=False),stamp(),sa.UniqueConstraint('user_id'))
    op.create_table('learning_examples',base(),owner(),sa.Column('event_id',sa.String(100),nullable=False),sa.Column('grant_token',sa.String(80),nullable=False),sa.Column('source',sa.String(20),nullable=False),sa.Column('quality',sa.String(20),nullable=False),sa.Column('payload_hash',sa.String(64),nullable=False),sa.Column('data',sa.JSON(),nullable=False),sa.Column('review',sa.JSON(),nullable=False),stamp(),sa.UniqueConstraint('user_id','event_id'),sa.CheckConstraint("quality IN ('pending','approved')"))
    op.create_table('learning_models',base(),sa.Column('status',sa.String(20),nullable=False),sa.Column('artifact',sa.JSON(),nullable=False),sa.Column('report',sa.JSON(),nullable=False),sa.Column('dataset_hash',sa.String(64),nullable=False,unique=True),sa.Column('review',sa.JSON(),nullable=False),stamp())
    op.create_table('learning_members',base(),owner(),sa.Column('model_id',sa.String(80),sa.ForeignKey('learning_models.id',ondelete='CASCADE'),nullable=False),sa.Column('grant_token',sa.String(80),nullable=False),sa.UniqueConstraint('user_id','model_id'))
    op.create_table('learning_deployment',base(),sa.Column('model_id',sa.String(80),sa.ForeignKey('learning_models.id',ondelete='SET NULL')),sa.Column('mode',sa.String(10),nullable=False),sa.CheckConstraint("id = 'global'"),sa.CheckConstraint("mode IN ('shadow','live')"))
    for t in ('learning_consent','learning_examples','learning_members'):
        op.create_index('ix_'+t+'_user_id',t,['user_id'])
    op.create_index('ix_learning_members_model_id','learning_members',['model_id'])
    op.create_index('ix_learning_eligible','learning_examples',['user_id','quality'])
    op.execute("INSERT INTO learning_deployment (id, model_id, mode) VALUES ('global', NULL, 'shadow')")

def downgrade():
    for t in ('learning_deployment','learning_members','learning_models','learning_examples','learning_consent'):op.drop_table(t)
