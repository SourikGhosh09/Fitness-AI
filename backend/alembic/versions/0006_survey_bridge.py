"""Authenticated Google Forms synchronization and pseudonymous participants."""
from alembic import op
import sqlalchemy as sa
revision='0006'
down_revision='0005'
def upgrade():
    op.create_table('survey_participants',sa.Column('id',sa.String(80),primary_key=True),sa.Column('user_id',sa.String(80),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),sa.Column('token_hash',sa.String(64),nullable=False),sa.Column('revoked',sa.Boolean(),nullable=False),sa.Column('created_at',sa.Float(),nullable=False),sa.UniqueConstraint('user_id'),sa.UniqueConstraint('token_hash'))
    op.create_index('ix_survey_participants_user_id','survey_participants',['user_id'])
    op.create_table('survey_responses',sa.Column('id',sa.String(80),primary_key=True),sa.Column('user_id',sa.String(80),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),sa.Column('response_key',sa.String(64),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('payload_hash',sa.String(64),nullable=False),sa.Column('contribution_id',sa.String(80),sa.ForeignKey('user_contributions.id',ondelete='SET NULL')),sa.Column('status',sa.String(20),nullable=False),sa.Column('created_at',sa.Float(),nullable=False),sa.UniqueConstraint('response_key'),sa.CheckConstraint('revision > 0'))
    op.create_index('ix_survey_responses_user_id','survey_responses',['user_id'])
    op.create_table('survey_receipts',sa.Column('id',sa.String(80),primary_key=True),sa.Column('expires_at',sa.Float(),nullable=False))
    op.create_index('ix_survey_receipts_expires_at','survey_receipts',['expires_at'])
def downgrade():
    op.drop_table('survey_receipts');op.drop_table('survey_responses');op.drop_table('survey_participants')
