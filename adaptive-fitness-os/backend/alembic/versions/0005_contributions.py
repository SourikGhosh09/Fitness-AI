"""Guided user-contributed observations, separate from model-ready examples."""
from alembic import op
import sqlalchemy as sa
revision='0005'
down_revision='0004'
def upgrade():
    op.create_table('user_contributions',sa.Column('id',sa.String(80),primary_key=True),sa.Column('user_id',sa.String(80),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('event_id',sa.String(80),nullable=False),sa.Column('session_id',sa.String(80),nullable=False),sa.Column('exercise_id',sa.String(80),sa.ForeignKey('exercises.id'),nullable=False),
        sa.Column('occurred_at',sa.Float(),nullable=False),sa.Column('grant_token',sa.String(80),nullable=False),sa.Column('payload_hash',sa.String(64),nullable=False),sa.Column('status',sa.String(20),nullable=False),
        sa.Column('data',sa.JSON(),nullable=False),sa.Column('history_snapshot',sa.JSON()),sa.Column('report',sa.JSON(),nullable=False),sa.Column('review',sa.JSON(),nullable=False),sa.Column('created_at',sa.Float(),nullable=False),
        sa.UniqueConstraint('user_id','event_id'),sa.UniqueConstraint('user_id','session_id','exercise_id'),sa.CheckConstraint("status IN ('pending','reviewed')"))
    op.create_index('ix_user_contributions_user_id','user_contributions',['user_id'])
    op.create_index('ix_contributions_user_time','user_contributions',['user_id','occurred_at'])
def downgrade():op.drop_table('user_contributions')
