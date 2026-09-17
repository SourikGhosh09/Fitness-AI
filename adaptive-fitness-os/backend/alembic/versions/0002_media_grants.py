"""Record reviewed media rights separately from source exercise data."""
from alembic import op
import sqlalchemy as sa
revision = '0002'
down_revision = '0001'

def upgrade():
    op.create_table('media_license_grants',
        sa.Column('id', sa.String(80), primary_key=True),
        sa.Column('media_id', sa.String(80), sa.ForeignKey('exercise_media.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_path', sa.String(), nullable=False),
        sa.Column('source_commit', sa.String(40), nullable=False),
        sa.Column('rights_reference', sa.String(), nullable=False),
        sa.Column('reviewed_by', sa.String(), nullable=False),
        sa.Column('expires_at', sa.Float(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False))
    op.create_index('ix_media_license_grants_media_id', 'media_license_grants', ['media_id'])

def downgrade():
    op.drop_table('media_license_grants')
