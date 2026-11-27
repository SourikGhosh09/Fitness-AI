"""Free-form dated workout logbook."""
from alembic import op
import sqlalchemy as sa
revision='0008'
down_revision='0007'
def upgrade():
    op.create_table('workout_logs',sa.Column('id',sa.String(80),primary_key=True),sa.Column('user_id',sa.String(80),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),sa.Column('day',sa.String(10),nullable=False),sa.Column('version',sa.Integer(),nullable=False),sa.Column('data',sa.JSON(),nullable=False),sa.Column('created_at',sa.Float(),nullable=False),sa.Column('updated_at',sa.Float(),nullable=False),sa.UniqueConstraint('user_id','day'))
    op.create_index('ix_workout_logs_user_id','workout_logs',['user_id'])
def downgrade():
    op.drop_table('workout_logs')
